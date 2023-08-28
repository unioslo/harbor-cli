from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import Optional
from typing import Sequence
from typing import Tuple
from typing import TypedDict
from typing import Union

import tomli
import tomli_w
from harborapi.models.base import BaseModel as HarborBaseModel
from pydantic import Field
from pydantic import root_validator
from pydantic import SecretStr
from pydantic import validator
from strenum import StrEnum

from .dirs import CONFIG_DIR
from .dirs import DATA_DIR
from .dirs import LOGS_DIR
from .exceptions import ConfigError
from .exceptions import ConfigFileNotFoundError
from .exceptions import CredentialsError
from .exceptions import HarborCLIError
from .exceptions import OverwriteError
from .format import OutputFormat
from .logs import logger
from .logs import LogLevel
from .output.console import warning
from .style import STYLE_TABLE_HEADER
from .utils import replace_none
from .utils.keyring import get_password
from .utils.keyring import KeyringUnsupportedError


DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.toml"
DEFAULT_HISTORY_FILE = DATA_DIR / "history"

ENV_VAR_PREFIX = "HARBOR_CLI_"


def config_env_var(key: str) -> str:
    """Return the environment variable name for a config key."""
    return ENV_VAR_PREFIX + key.upper().replace(".", "_")


def env_var(option: str) -> str:
    """Return the environment variable name for a CLI option."""
    return ENV_VAR_PREFIX + option.upper().replace("-", "_")


class EnvVar(StrEnum):
    CONFIG = env_var("config")
    URL = env_var("url")
    USERNAME = env_var("username")
    SECRET = env_var("secret")
    BASICAUTH = env_var("basicauth")
    CREDENTIALS_FILE = env_var("credentials_file")
    HARBOR_VALIDATE_DATA = env_var("harbor_validate_data")
    HARBOR_RAW_MODE = env_var("harbor_raw_mode")
    HARBOR_VERIFY_SSL = env_var("harbor_verify_ssl")
    HARBOR_RETRY_ENABLED = env_var("harbor_retry_enabled")
    HARBOR_RETRY_MAX_TRIES = env_var("harbor_retry_max_tries")
    HARBOR_RETRY_MAX_TIME = env_var("harbor_retry_max_time")
    TABLE_DESCRIPTION = env_var("table_description")
    TABLE_MAX_DEPTH = env_var("table_max_depth")
    TABLE_COMPACT = env_var("table_compact")
    JSON_INDENT = env_var("json_indent")
    JSON_SORT_KEYS = env_var("json_sort_keys")
    OUTPUT_FORMAT = env_var("output_format")
    PAGING = env_var("paging")
    PAGER = env_var("pager")
    CONFIRM_DELETION = env_var("confirm_deletion")
    CONFIRM_ENUMERATION = env_var("confirm_enumeration")
    WARNINGS = env_var("warnings")
    CACHE_ENABLED = env_var("cache_enabled")
    CACHE_TTL = env_var("cache_ttl")

    def __str__(self) -> str:
        return self.value


def load_toml_file(config_file: Path) -> dict[str, Any]:
    """Load a TOML file and return the contents as a dict.

    Parameters
    ----------
    config_file : Path,
        Path to the TOML file to load.

    Returns
    -------
    Dict[str, Any]
        A TOML file as a dictionary
    """
    conf = tomli.loads(config_file.read_text())
    return conf


# We use the harborapi.models.BaseModel as our base class
# for the config models. This isn't ideal, and we should instead
# be able to import as_table from harborapi and add it to our own
# BaseModel class. But for now, this works.
#
# The reason we can't do the above is because as_table is a bound method
# on the harborapi.models.BaseModel class, and we can't add it to our own
# until the method is moved out of the class.
class BaseModel(HarborBaseModel):
    """Base model shared by all config models."""

    # https://pydantic-docs.helpmanual.io/usage/model_config/#change-behaviour-globally

    @root_validator(pre=True)
    def _pre_root_validator(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Checks for unknown fields and logs a warning if any are found.

        Since we use `extra = "allow"`, it can be useful to check for unknown
        fields and log a warning if any are found, otherwise they will be
        silently ignored.

        See: Config class below.
        """
        for key in values:
            if key not in cls.__fields__:
                logger.warning(
                    "{}: Got unknown config key {!r}.",
                    getattr(cls, "__name__", str(cls)),
                    key,
                )
        return values

    class Config:
        # Allow for future fields to be added to the config file without
        # breaking older versions of Harbor CLI
        extra = "allow"
        validate_assignment = True


class HarborCredentialsKwargs(TypedDict):
    url: str
    username: str
    secret: str
    basicauth: str
    credentials_file: Optional[Path]


class RetrySettings(BaseModel):
    """Retry settings for API requests."""

    enabled: bool = True
    max_tries: int = 5
    max_time: float = 10.0
    # TODO: add remaining settings


class HarborSettings(BaseModel):
    url: str = ""
    username: str = ""
    secret: SecretStr = SecretStr("")
    basicauth: SecretStr = SecretStr("")
    credentials_file: Optional[Path] = ""  # type: ignore # validator below
    validate_data: bool = Field(True, alias="validate")
    raw_mode: bool = False
    verify_ssl: bool = True
    retry: RetrySettings = RetrySettings()
    keyring: bool = False

    @validator("credentials_file", pre=True)
    def _empty_string_is_none(cls, v: Any) -> Any:
        """We can't serialize None to TOML, so we convert it to an empty string.
        However, passing an empty string to Path() will return the current working
        directory, so we need to convert it back to None."""
        # I really wish TOML had a None type...
        if v == "":
            return None
        return v

    @validator("credentials_file", always=True)
    def _validate_credentials_file(cls, v: Path | None) -> Path | None:
        if v is not None:
            if not v.exists():
                raise ValueError(f"Credentials file {v} does not exist")
            elif not v.is_file():
                raise ValueError(f"Credentials file {v} is not a file")
        return v

    @property
    def secret_value(self) -> str:
        """Returns the secret value from the keyring if enabled, otherwise
        returns the secret value from the config file."""
        if self.keyring:
            try:
                return get_password(self.username) or ""
            except KeyringUnsupportedError:
                warning(
                    "Keyring is not supported on this platform. "
                    "Using secret from config file."
                )
                self.keyring = False  # patch it so we don't try again
                return self.secret.get_secret_value()
        else:
            return self.secret.get_secret_value()

    @property
    def has_auth_method(self) -> bool:
        """Returns True if any of the auth methods are set."""
        return bool(
            (self.username and self.secret_value)
            or self.basicauth
            or self.credentials_file
        )

    @property
    def credentials(self) -> HarborCredentialsKwargs:
        """Fetches kwargs that can be passed to HarborAsyncClient for
        user authentication.

        Returns
        -------
        HarborCredentialsKwargs
            A dictionary with either base64 credentials, username and password
            or a path to a credentials file.
        """
        return HarborCredentialsKwargs(
            url=self.url,
            username=self.username,
            secret=self.secret_value,
            basicauth=self.basicauth.get_secret_value(),
            credentials_file=self.credentials_file,
        )

    def ensure_authable(self) -> bool:
        """Ensures that the credentials are sufficient to authenticate with the Habror API.
        Raises CredentialsError if not.
        """
        if not self.url:
            raise CredentialsError("A Harbor API URL is required")

        # require one of the auth methods to be set
        if not self.has_auth_method:
            raise CredentialsError(
                "A harbor authentication method must be specified. "
                "One of 'username'+'secret', 'basicauth', or 'credentials_file' must be specified. "
                "See the documentation for more information."
            )
        return True

    def clear_credentials(self) -> None:
        """Clears the credentials from the current configuration."""
        self.username = ""
        self.secret = ""  # type: ignore # pydantic.SecretStr
        self.basicauth = ""  # type: ignore # pydantic.SecretStr
        self.credentials_file = None


class LoggingSettings(BaseModel):
    enabled: bool = True
    structlog: bool = False
    level: LogLevel = LogLevel.WARNING
    directory: Path = LOGS_DIR
    filename: str = "harbor_cli-{time}.log"
    timeformat: str = "%Y-%m-%d"
    retention: int = 30

    @property
    def path(self) -> Path:
        """Full time-formatted path to log file."""
        return self.directory / self.filename.format(
            time=datetime.now().strftime(self.timeformat)
        )


class TableStyleSettings(BaseModel):
    title: Optional[str] = None
    header: Optional[str] = STYLE_TABLE_HEADER
    rows: Optional[Tuple[str, str]] = None
    border: Optional[str] = None
    footer: Optional[str] = None
    caption: Optional[str] = None
    expand: bool = True
    show_header: bool = True
    bool_emoji: bool = False
    # TODO: box

    @validator("rows", pre=True)
    def _validate_rows(
        cls, v: Optional[Union[Tuple[str, str], str]]
    ) -> Optional[Tuple[str, ...]]:
        """Validates the rows field.

        Strings are turned into tuples of length 2 where both elements
        are the string value. e.g. "black" becomes ("black", "black").

        Sequences are truncated to length 2. If the sequence is length 1,
        the first element is repeated. e.g. ("black",) becomes ("black", "black"),
        and ("black", "white", "red") becomes ("black", "white").

        None, empty strings, and empty sequences are converted to None.
        """
        # TODO: refactor this to separate function so it can be used by other
        # validators, and so that we can have one central set of tests,
        # that covers all validators using the function.

        if not v:  # catches None, "", and empty sequence
            return None
        if isinstance(v, str):
            return (v, v)
        if not isinstance(v, Sequence):
            raise TypeError("TableStyleSettings.rows must be a sequence.")

        vv = tuple(v)

        # If all elements are None or empty, return None
        if all(not x for x in vv):
            return None

        # vv is guaranteed to be a non-empty tuple at this point
        if len(vv) > 2:
            vv = vv[:2]
        elif len(vv) == 1:
            vv = (vv[0], v[0])
        return vv

    # TODO add * validator that turns empty strings into None?
    @validator("*")
    def _empty_string_is_none(cls, v: Any) -> Any:
        """TOML has no None support, but we need to pass these kwargs to
        Rich's Table constructor, which does uses None. So we convert
        empty strings to None."""
        if v == "":
            return None
        return v

    def as_rich_kwargs(self) -> dict[str, Optional[Union[str, Tuple[str, str], bool]]]:
        """Converts the TableStyleSettings to a dictionary that can be passed
        to Rich's Table constructor.

        Returns
        -------
        Dict[str, Optional[str]]
            A dictionary of Rich Table style settings.
        """
        # TODO: define return type as a TypedDict, which can then be used
        # to type check the kwargs we pass to Rich's Table constructor.
        return {
            "border_style": self.border,
            "caption_style": self.caption,
            "expand": self.expand,
            "footer_style": self.footer,
            "header_style": self.header,
            "row_styles": self.rows,
            "show_header": self.show_header,
            "title_style": self.title,
        }


class TableSettings(BaseModel):
    """Settings for the table output format."""

    description: bool = False
    max_depth: int = 0
    compact: bool = True
    style: TableStyleSettings = TableStyleSettings()
    # max_width: Optional[int] = None
    # max_lines: Optional[int] = None

    @validator("max_depth", pre=True)
    def check_max_depth(cls, v: Any) -> Any:
        """Converts max_depth to an integer, and checks that it is not negative."""
        if v is None:
            return 0
        try:
            v = int(v)
        except ValueError:
            raise ValueError("max_depth must be an integer")
        # We used to accept negative integers, and to avoid breaking
        # existing configs immediately, we just check if the value is negative,
        # and if so, return 0.
        # In the future, we will use Field(..., ge=0) to enforce it.
        if v < 0:
            warning(
                "max_depth will stop accepting negative values in a future version. Use 0 instead."
            )
            return 0
        return v


class JSONSettings(BaseModel):
    indent: int = 2
    sort_keys: bool = False


class OutputSettings(BaseModel):
    format: OutputFormat = OutputFormat.TABLE
    paging: bool = Field(
        False,
        description="Show output in pager (if supported). Default pager does not support color output currently.",
    )
    pager: str = Field("", description="Pager to use if paging is enabled.")
    # Naming: Don't shadow the built-in .json() method
    # The config file can still use the key "json" because of the alias
    table: TableSettings = Field(default_factory=TableSettings)
    JSON: JSONSettings = Field(default_factory=JSONSettings, alias="json")

    @validator("pager")
    def set_pager(cls, v: Optional[str]) -> Optional[str]:
        """Validator that sets the MANPAGER environment variable if a pager is set.
        https://rich.readthedocs.io/en/stable/console.html#paging
        """
        if not v:
            return v
        os.environ["MANPAGER"] = v
        os.environ["PAGER"] = v
        return v

    class Config:
        allow_population_by_field_name = True


class GeneralSettings(BaseModel):
    """General settings for Harbor CLI."""

    confirm_deletion: bool = Field(
        True,
        description=(
            "Show confirmation prompt for resource deletion "
            "commands. E.g. `project delete`"
        ),
    )
    confirm_enumeration: bool = Field(
        True,
        description=(
            "Show confirmation prompt for certain resource enumeration "
            "commands when invoked without a limit or filter. E.g. `auditlog list`"
        ),
    )
    warnings: bool = Field(
        True,
        description="Show warning messages in terminal. Warnings are always logged regardless of this option.",
    )


class REPLSettings(BaseModel):
    history: bool = Field(True, description="Enable persistent history in the REPL.")
    history_file: Path = Field(
        DEFAULT_HISTORY_FILE,
        description="Path to custom location of history file.",
    )

    @validator("history_file", always=True)
    def _create_history_file_if_not_exists(
        cls, v: Path, values: dict[str, Any]
    ) -> Path:
        history_enabled = values.get("history", False)
        if not history_enabled:
            return v
        if not v.exists():
            v.parent.mkdir(parents=True, exist_ok=True)
            v.touch()
        return v


class CacheSettings(BaseModel):
    enabled: bool = Field(
        False,
        description="Enable in-memory caching of API responses. This can significantly speed up Harbor CLI, but should be considered experimental for now.",
    )
    ttl: int = Field(
        300,
        description="Time to live for cached responses, in seconds.",
    )
    # TODO: implement max_size
    # max_size: int = Field(
    #     1000,
    #     description="Maximum number of cached responses.",
    # )


class HarborCLIConfig(BaseModel):
    harbor: HarborSettings = Field(default_factory=HarborSettings)
    general: GeneralSettings = Field(default_factory=GeneralSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    repl: REPLSettings = Field(default_factory=REPLSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    config_file: Optional[Path] = Field(
        None, exclude=True, description="Path to config file (if any)."
    )  # populated by CLI if loaded from file

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
        }

    def __copy__(self) -> HarborCLIConfig:
        """Create a copy of the config object that includes the config file
        path, so that it can be saved to the same file."""
        return self.copy(update={"config_file": self.config_file})

    def __deepcopy__(self, memo: dict) -> HarborCLIConfig:
        """Create a copy of the config object that includes the config file
        path, so that it can be saved to the same file."""
        return self.copy(update={"config_file": self.config_file}, deep=True)

    @classmethod
    def from_file(
        cls, config_file: Path | None = DEFAULT_CONFIG_FILE, create: bool = False
    ) -> HarborCLIConfig:
        """Create a Config object from a TOML file.

        Parameters
        ----------
        config_file : Path
            Path to the TOML file.
            If `None`, the default configuration file is used.
        create : bool
            If `True`, the config file will be created if it does not exist.

        Returns
        -------
        Config
            A Config object.
        """
        if config_file is None:
            config_file = DEFAULT_CONFIG_FILE

        if not config_file.exists():
            if create:
                create_config(config_file)
            else:
                raise ConfigFileNotFoundError(
                    f"Config file {config_file} does not exist."
                )
        elif not config_file.is_file():
            raise ConfigError(f"Config file {config_file} is not a file.")

        try:
            config = load_toml_file(config_file)
        except Exception as e:
            raise ConfigError(f"Could not load config file {config_file}: {e}") from e
        return cls(**config, config_file=config_file)

    def save(self, path: Path | None = None) -> None:
        if not path and not self.config_file:
            raise ValueError("Cannot save config: no config file specified")
        p = path or self.config_file
        assert p is not None  # p shouldn't be None here! am i dumb???
        save_config(self, p)

    def toml(
        self,
        expose_secrets: bool = True,
        tomli_kwargs: dict[str, Any] | None = {},
        **kwargs: Any,
    ) -> str:
        """Return a TOML representation of the config object.
        In order to serialize all types properly, the serialization takes
        a round-trip through the Pydantic JSON converter.

        Parameters
        ----------
        expose_secrets : bool
            If `True`, secrets will be included in the TOML output.
            If `False`, secrets will be replaced with strings of asterisks.
            By default, secrets are included.
        tomli_kwargs : dict
            Dict of keyword arguments passed to `tomli_w.dumps()`.
        **kwargs
            Keyword arguments passed to `BaseModel.json()`.

        Returns
        -------
        str
            TOML representation of the config as a string.

        See Also
        --------
        `BaseModel.json()` <https://pydantic-docs.helpmanual.io/usage/exporting_models/#modeljson>
        """
        tomli_kwargs = tomli_kwargs or {}

        # Roundtrip through JSON to get dict of builtin types
        #
        # Also replace None values with empty strings, because:
        # 1. TOML doesn't have a None type
        # 2. Show users that these values _can_ be configured
        dict_basic_types = replace_none(json.loads(self.json(**kwargs)))

        if not expose_secrets:
            for key in ["secret", "basicauth", "credentials_file"]:
                if (
                    key in dict_basic_types["harbor"]
                    and dict_basic_types["harbor"][key]  # ignore empty values
                ):
                    dict_basic_types["harbor"][key] = "********"

        return tomli_w.dumps(dict_basic_types)


def create_config(config_path: Path | None, overwrite: bool = False) -> Path:
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.touch(exist_ok=overwrite)
    except FileExistsError as e:
        raise OverwriteError(f"Config file {config_path} already exists.") from e
    except Exception as e:
        raise ConfigError(f"Could not create config file {config_path}: {e}") from e

    # Write sample config to the created file
    config_path.write_text(sample_config())

    return config_path


def load_config(config_path: Path | None = None) -> HarborCLIConfig:
    """Load the config file."""
    try:
        return HarborCLIConfig.from_file(config_path)
    except HarborCLIError:
        raise
    except Exception as e:
        raise ConfigError(f"Could not load config file {config_path}: {e}") from e


def save_config(config: HarborCLIConfig, config_path: Path) -> None:
    """Save the config file."""
    try:
        config_path.write_text(config.toml(exclude_none=True))
    except Exception as e:
        raise ConfigError(f"Could not save config file {config_path}: {e}") from e


def sample_config(exclude_none: bool = False) -> str:
    """Returns the contents of a sample config file as a TOML string.

    Parameters
    ----------
    exclude_none : bool
        If `True`, fields with `None` values will be excluded from the sample
        config, otherwise they will be included with empty strings as field values.
        Defaults to `False` - all fields will be included.

    Returns
    -------
    str
        Sample config file contents in TOML format.
    """
    config = HarborCLIConfig()
    return config.toml(exclude_none=exclude_none)

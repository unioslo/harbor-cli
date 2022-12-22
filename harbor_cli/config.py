from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import TypedDict

import tomli
import tomli_w
from harborapi.models.base import BaseModel as HarborBaseModel
from loguru import logger
from pydantic import Field
from pydantic import root_validator
from pydantic import validator

from .dirs import CONFIG_DIR
from .exceptions import CredentialsError
from .logs import LogLevel
from .output.format import OutputFormat
from .utils import replace_none


DEFAULT_CONFIG_FILE = CONFIG_DIR / "config.toml"


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
    def _pre_root_validator(cls, values: dict) -> dict:
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


class HarborCredentialsKwargs(TypedDict):
    url: str
    username: str
    secret: str
    credentials: str
    credentials_file: Path | None


class HarborSettings(BaseModel):
    url: str = ""
    username: str = ""
    secret: str = ""
    credentials_base64: str = ""
    credentials_file: Path | None = None

    @validator("credentials_file", pre=True)
    def _empty_string_is_none(cls, v: Any) -> Any:
        if v == "":
            return None
        return v

    @validator("credentials_file")
    def _validate_credentials_file(cls, v: Path | None) -> Path | None:
        if v is not None:
            if not v.exists():
                raise ValueError(f"Credentials file {v} does not exist")
            elif not v.is_file():
                raise ValueError(f"Credentials file {v} is not a file")
        return v

    def ensure_authable(self) -> bool:
        """Ensures that the credentials are sufficient to authenticate with the Habror API.
        Raises CredentialsError if not.
        """
        if not self.url:
            raise CredentialsError("A Harbor API URL is required")

        # require one of the auth methods to be set
        if not (
            self.username
            and self.secret
            or self.credentials_base64
            or self.credentials_file
        ):
            raise CredentialsError(
                "A harbor authentication method must be specified. "
                "One of 'username'+'secret', 'credentials_base64', or 'credentials_file' must be specified. "
                "See the documentation for more information."
            )
        return True

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
            secret=self.secret,
            credentials=self.credentials_base64,
            credentials_file=self.credentials_file,
        )


class LoggingSettings(BaseModel):
    enabled: bool = True
    structlog: bool = False
    level: LogLevel = LogLevel.INFO


class TableSettings(BaseModel):
    """Settings for the table output format."""

    description: bool = False
    max_depth: int | None = -1

    @validator("max_depth", pre=True)
    def negative_is_none(cls, v: int | None) -> int | None:
        """TOML has no None type, so we interpret negative values as None.
        This validator converts negative values to None.

        TODO: convert None to -1 when writing to TOML!
        """
        if v is None:
            return v
        elif v < 0:
            return None
        return v


class JSONSettings(BaseModel):
    indent: int = 2
    sort_keys: bool = True


class OutputSettings(BaseModel):
    format: OutputFormat = OutputFormat.TABLE
    # Don't shadow the built-in .json() method
    # The config file can still use the key "json" because of the alias
    table: TableSettings = Field(default_factory=TableSettings)
    JSON: JSONSettings = Field(default_factory=JSONSettings, alias="json")

    class Config:
        allow_population_by_field_name = True


class HarborCLIConfig(BaseModel):
    harbor: HarborSettings = Field(default_factory=HarborSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    config_file: Path | None = Field(
        None, exclude=True, description="Path to config file (if any)."
    )  # populated by CLI if loaded from file

    @classmethod
    def from_file(
        cls, config_file: Path = DEFAULT_CONFIG_FILE, create: bool = False
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
        if not config_file.exists():
            if create:
                create_config(config_file)
            else:
                raise FileNotFoundError(f"Config file {config_file} does not exist.")
        config = load_toml_file(config_file)
        return cls(**config, config_file=config_file)


def create_config(config_path: Path | None, overwrite: bool = False) -> Path:
    if config_path is None:
        config_path = DEFAULT_CONFIG_FILE

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.touch(exist_ok=overwrite)
    except FileExistsError:
        raise FileExistsError(f"Config file {config_path} already exists.")
    except Exception as e:
        logger.bind(exc=e).error("Failed to create config file")
        raise Exception(f"Could not create config file {config_path}: {e}")

    # Write sample config to the created file
    config_path.write_text(sample_config())

    return config_path


def load_config() -> HarborCLIConfig | None:
    """Load the config file."""
    try:
        return HarborCLIConfig.from_file()
    except Exception as e:
        logger.error("Could not load config file: {}", e)
        return None


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
    # We need to create an intermediate JSON dump to get rid of non tomli-w
    # compatible objects such as Path objects.
    #
    # The built-in pydantic `.json()` method handles these types gracefully,
    # whereas tomli_w does not. Hence the intermediate step.
    return tomli_w.dumps(
        replace_none(json.loads(config.json(exclude_none=exclude_none)))
    )

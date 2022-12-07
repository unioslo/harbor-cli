from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import TypedDict

import tomli
import tomli_w
from loguru import logger
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field
from pydantic import root_validator
from pydantic import validator
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.table import Column
from rich.table import Table

from .dirs import CONFIG_DIR
from .exceptions import CredentialsError
from .logs import LogLevel
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


class BaseModel(PydanticBaseModel):
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
        clsname = getattr(cls, "__name__", str(cls))
        for key in values:
            if key not in cls.__fields__:
                logger.warning(
                    "{}: Got unknown config key {!r}.",
                    clsname,
                    key,
                )
        return values

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation of the model.

        Returns a table with the model's fields and values.

        If the model has a nested model, the nested model's table representation
        is printed after the main table. Should support multiple levels of
        nested models, but not tested.

        See: https://rich.readthedocs.io/en/latest/protocol.html#console-render
        """
        try:
            name = self.__name__  # type: ignore # this is populated by Pydantic
        except AttributeError:
            name = self.__class__.__name__
        table = Table(
            Column(
                header="Setting", justify="left", style="green", header_style="bold"
            ),
            Column(header="Value", style="blue", justify="left"),
            Column(header="Description", style="yellow", justify="left"),
            title=f"[bold]{name}[/bold]",
            title_style="magenta",
            title_justify="left",
        )
        subtables = []  # type: list[BaseModel]
        for field_name, field in self.__fields__.items():
            # Try to use field title if available
            field_title = field.field_info.title or field_name

            attr = getattr(self, field_name)
            try:
                # issubclass is prone to TypeError, so we use try/except
                if issubclass(field.type_, BaseModel) and attr is not None:
                    if isinstance(attr, (list, set)):  # check iterable types?
                        subtables.extend(attr)
                    else:
                        subtables.append(attr)
                    continue
            except:  # noqa: E722
                pass
            table.add_row(field_title, str(attr), field.field_info.description)

        if table.rows:
            yield table
        yield from subtables

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


class HarborCLIConfig(BaseModel):
    harbor: HarborSettings = Field(default_factory=HarborSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
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
        return cls(**config, config_file=config_file)  # type: ignore # mypy bug until Self type is supported


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

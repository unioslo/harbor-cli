from __future__ import annotations


class HarborCLIError(Exception):
    """Base class for all exceptions."""


class ConfigError(HarborCLIError):
    """Error loading the configuration file."""


class ConfigFileNotFoundError(ConfigError, FileNotFoundError):
    """Configuration file not found."""


class DirectoryCreateError(HarborCLIError, OSError):
    """Error creating a required program directory."""


class CredentialsError(HarborCLIError):
    """Error loading credentials."""

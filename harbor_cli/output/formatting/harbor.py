from __future__ import annotations

from .builtin import bool_str


def boolstr_str(boolstr: str | bool | None, default: bool | None = False) -> str:
    """Format a boolean string as a string.

    ProjectMetadata has fields that can be the strings
    'true' or 'false', or None. This function converts
    those values to a boolean if possible, then passes
    it to bool_str.

    Parameters
    ----------
    boolstr : str | bool | None
        A string that is either 'true', 'false', or None,
        OR a boolean value, in case the API changes in the future
        and these fields are returned as booleans instead of strings.

    Returns
    -------
    str
        A string representation of the value created by `bool_str()`

    See Also
    --------
    [harbor_cli.output.formatting.builtin.bool_str][]
    <https://pederhan.github.io/harborapi/usage/models/#string-fields-with-true-and-false-values-in-api-spec>
    """
    # Strings that do not match either 'true' or 'false' are
    # treated as `None` by default, and then we let `bool_str`
    # figure out what that means. This is a narrow edge case, and
    # a direct result of Harbor's own mistakes, so we don't spend
    # too much energy trying to make this perfect here.
    if boolstr is None:
        return bool_str(boolstr)
    elif boolstr == "true":
        return bool_str(True)
    elif boolstr == "false":
        return bool_str(False)
    elif isinstance(boolstr, bool):  # spec has changed, is now a bool
        # NOTE: could add some sort of alert that the spec has changed here
        return bool_str(boolstr)
    else:
        return bool_str(default)

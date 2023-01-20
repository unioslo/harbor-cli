from __future__ import annotations


def is_builtin_obj(obj: object) -> bool:
    return obj.__class__.__module__ == "builtins"

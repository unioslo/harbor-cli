from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(Path(__file__).parent.as_posix())

from . import gen_cli_data  # noqa
from . import gen_cli_options  # noqa
from . import gen_command_list  # noqa
from . import gen_command_pages  # noqa
from . import gen_formats  # noqa


def main(*args, **kwargs) -> None:
    for mod in [
        gen_cli_data,
        gen_cli_options,
        gen_command_list,
        gen_command_pages,
        gen_formats,
    ]:
        mod.main()


if __name__ == "__main__":
    main()

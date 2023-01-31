from __future__ import annotations

import yaml  # type: ignore
from common import DATA_PATH

from harbor_cli.format import OutputFormat


fmts = [fmt.value for fmt in OutputFormat]

with open(DATA_PATH / "formats.yaml", "w") as f:
    yaml.dump(fmts, f, default_flow_style=False)

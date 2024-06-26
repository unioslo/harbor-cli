# SPDX-FileCopyrightText: 2022-present University of Oslo <pederhan@uio.no>
#
# SPDX-License-Identifier: MIT
from __future__ import annotations
from ._patches import patch_all

patch_all()

from . import logs  # type: ignore # noreorder # configure logger first as side-effect
from . import *

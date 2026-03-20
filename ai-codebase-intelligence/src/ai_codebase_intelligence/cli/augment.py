"""Augment CLI command — 1:1 port of gitnexus cli/augment.js."""
from __future__ import annotations

import os
import sys


def augment_command(pattern: str) -> None:
    if not pattern or len(pattern) < 3:
        sys.exit(0)
    try:
        from ..core.augmentation.engine import augment
        result = augment(pattern, os.getcwd())
        if result:
            sys.stderr.write(result + "\n")
    except Exception:
        sys.exit(0)

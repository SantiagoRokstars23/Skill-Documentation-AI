"""Permite ``python -m cli`` como alternativa al entry point instalado ``spring-doc``."""

from __future__ import annotations

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())

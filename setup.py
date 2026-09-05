"""Extends the setuptools build with a step that vendors Node.js + pyright
into the wheel being built, for the platform actually doing the build (see
mirrors_pyright/_fetch.py for why that's the right place to do this).
"""

from __future__ import annotations

import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


class build_py(_build_py):
    @override
    def run(self) -> None:
        super().run()
        sys.path.insert(0, str(Path(__file__).parent))
        from mirrors_pyright import __version__
        from mirrors_pyright._fetch import fetch_vendor

        vendor_dir = Path(self.build_lib) / "mirrors_pyright" / "_vendor"
        fetch_vendor(vendor_dir, pyright_version=__version__)


setup(cmdclass={"build_py": build_py})

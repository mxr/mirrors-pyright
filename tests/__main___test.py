from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from mirrors_pyright.__main__ import _node_bin
from mirrors_pyright.__main__ import _vendor_dir
from mirrors_pyright.__main__ import main


def test_vendor_dir():
    assert _vendor_dir() == Path(__file__).parent.parent / "mirrors_pyright" / "_vendor"


@pytest.mark.parametrize(
    ("plat", "expected"),
    (
        pytest.param("win32", Path("/vendor/node/node.exe"), id="windows"),
        pytest.param("linux", Path("/vendor/node/bin/node"), id="posix"),
    ),
)
def test_node_bin(plat, expected):
    with patch.object(sys, "platform", plat):
        assert _node_bin(Path("/vendor")) == expected


@patch.object(Path, "exists", return_value=False)
def test_main_missing_vendor_assets(exists):
    with pytest.raises(SystemExit, match="Node runtime not found"):
        main()


@patch.object(sys, "argv", ["pyright", "--version"])
@patch("os.execv")
@patch.object(Path, "exists", return_value=True)
@patch.object(sys, "platform", "darwin")
def test_main_posix_execs_node(exists, execv):
    main()

    vendor_dir = _vendor_dir()
    execv.assert_called_once_with(
        str(vendor_dir / "node" / "bin" / "node"),
        [
            str(vendor_dir / "node" / "bin" / "node"),
            str(vendor_dir / "pyright" / "index.js"),
            "--version",
        ],
    )


@patch.object(sys, "argv", ["pyright", "--version"])
@patch("subprocess.call", return_value=0)
@patch.object(Path, "exists", return_value=True)
@patch.object(sys, "platform", "win32")
def test_main_windows_uses_subprocess(exists, call):
    with pytest.raises(SystemExit) as excinfo:
        main()

    vendor_dir = _vendor_dir()
    call.assert_called_once_with(
        [
            str(vendor_dir / "node" / "node.exe"),
            str(vendor_dir / "pyright" / "index.js"),
            "--version",
        ]
    )
    assert excinfo.value.code == 0

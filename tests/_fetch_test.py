from __future__ import annotations

import io
import platform
import sys
import tarfile
import zipfile
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from mirrors_pyright._fetch import NODE_VERSION
from mirrors_pyright._fetch import _download
from mirrors_pyright._fetch import _fetch_node
from mirrors_pyright._fetch import _fetch_pyright
from mirrors_pyright._fetch import _node_platform_arch
from mirrors_pyright._fetch import fetch_vendor


def _tar_gz(members):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in members:
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _zip(members):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members:
            zf.writestr(name, data)
    return buf.getvalue()


@pytest.mark.parametrize(
    ("system_name", "machine_name", "expected"),
    (
        pytest.param("Darwin", "x86_64", ("darwin", "x64"), id="darwin-x86_64"),
        pytest.param("Darwin", "arm64", ("darwin", "arm64"), id="darwin-arm64"),
        pytest.param("Linux", "aarch64", ("linux", "arm64"), id="linux-aarch64"),
        pytest.param("Windows", "AMD64", ("win", "x64"), id="windows-amd64"),
    ),
)
@patch.object(platform, "machine")
@patch.object(platform, "system")
def test_node_platform_arch(system, machine, system_name, machine_name, expected):
    system.return_value = system_name
    machine.return_value = machine_name
    assert _node_platform_arch() == expected


@patch.object(platform, "machine")
@patch.object(platform, "system")
def test_node_platform_arch_unknown_system(system, machine):
    system.return_value = "SunOS"
    machine.return_value = "x86_64"
    with pytest.raises(RuntimeError, match="platform 'SunOS'"):
        _node_platform_arch()


@patch.object(platform, "machine")
@patch.object(platform, "system")
def test_node_platform_arch_unknown_machine(system, machine):
    system.return_value = "Linux"
    machine.return_value = "sparc"
    with pytest.raises(RuntimeError, match="architecture 'sparc'"):
        _node_platform_arch()


@patch("urllib.request.urlopen")
def test_download(urlopen):
    resp = Mock()
    resp.read.return_value = b"data"
    urlopen.return_value.__enter__.return_value = resp

    assert _download("https://example.com") == b"data"
    urlopen.assert_called_once_with("https://example.com")


@patch("mirrors_pyright._fetch._download")
def test_fetch_pyright(download, tmp_path):
    download.return_value = _tar_gz(
        (
            ("package/index.js", b"entry"),
            ("package/dist/pyright.js", b"code"),
            ("package/dist/pyright.js.map", b"skip me"),
            ("not-package/other", b"skip me too"),
        )
    )
    dest = tmp_path / "pyright"

    _fetch_pyright("1.1.413", dest)

    assert (dest / "index.js").read_bytes() == b"entry"
    assert (dest / "dist" / "pyright.js").read_bytes() == b"code"
    assert not (dest / "dist" / "pyright.js.map").exists()
    assert not (dest / "not-package").exists()


@pytest.mark.parametrize(
    ("node_platform", "archive", "member"),
    (
        pytest.param("linux", _tar_gz, "bin/node", id="posix"),
        pytest.param("win", _zip, "node.exe", id="windows"),
    ),
)
@patch("mirrors_pyright._fetch._download")
def test_fetch_node(download, tmp_path, node_platform, archive, member):
    archive_stem = f"node-v24.20.0-{node_platform}-x64"
    download.return_value = archive(((f"{archive_stem}/{member}", b"binary"),))
    dest = tmp_path / "node"

    _fetch_node("24.20.0", node_platform, "x64", dest)

    node = dest / member
    assert node.read_bytes() == b"binary"
    # NTFS doesn't preserve unix permission bits, even for a posix-style archive.
    if node_platform != "win" and sys.platform != "win32":  # pragma: win32 no cover
        assert node.stat().st_mode & 0o777 == 0o755


@patch("mirrors_pyright._fetch._fetch_node")
@patch("mirrors_pyright._fetch._fetch_pyright")
@patch("mirrors_pyright._fetch._node_platform_arch")
def test_fetch_vendor(node_platform_arch, fetch_pyright, fetch_node, tmp_path):
    node_platform_arch.return_value = ("darwin", "arm64")
    vendor_dir = tmp_path / "_vendor"

    fetch_vendor(vendor_dir, pyright_version="1.1.413")

    fetch_pyright.assert_called_once_with("1.1.413", vendor_dir / "pyright")
    fetch_node.assert_called_once_with(
        NODE_VERSION, "darwin", "arm64", vendor_dir / "node"
    )

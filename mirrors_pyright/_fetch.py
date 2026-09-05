from __future__ import annotations

import io
import platform
import tarfile
import urllib.request
import zipfile
from typing import TYPE_CHECKING
from typing import cast

if TYPE_CHECKING:
    from pathlib import Path

# Node.js version is an implementation detail, bumped independently of
# pyright. Pin an LTS release known to work.
NODE_VERSION = "24.20.0"


def _node_platform_arch() -> tuple[str, str]:
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Darwin":
        node_platform = "darwin"
    elif system == "Linux":
        node_platform = "linux"
    elif system == "Windows":
        node_platform = "win"
    else:
        raise RuntimeError(
            f"mirrors-pyright has no vendored Node.js build for platform {system!r}"
        )

    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(
            f"mirrors-pyright has no vendored Node.js build for architecture {machine!r}"
        )

    return node_platform, arch


def _download(url: str) -> bytes:
    print(f"mirrors-pyright: fetching {url}", flush=True)
    with urllib.request.urlopen(url) as resp:
        return cast("bytes", resp.read())


def _fetch_pyright(version: str, dest: Path) -> None:
    data = _download(f"https://registry.npmjs.org/pyright/-/pyright-{version}.tgz")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar.getmembers():
            # npm tarballs nest everything under a top-level "package/" dir.
            if not member.name.startswith("package/"):
                continue
            relative = member.name[len("package/") :]
            if not relative or relative.endswith(".map"):
                continue
            member.name = relative
            tar.extract(member, dest)


def _fetch_node(version: str, node_platform: str, arch: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    archive_stem = f"node-v{version}-{node_platform}-{arch}"

    if node_platform == "win":
        data = _download(f"https://nodejs.org/dist/v{version}/{archive_stem}.zip")
        with (
            zipfile.ZipFile(io.BytesIO(data)) as zf,
            zf.open(f"{archive_stem}/node.exe") as src,
            open(dest / "node.exe", "wb") as out,
        ):
            out.write(src.read())
    else:
        data = _download(f"https://nodejs.org/dist/v{version}/{archive_stem}.tar.gz")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            member = tar.getmember(f"{archive_stem}/bin/node")
            member.name = "bin/node"
            tar.extract(member, dest)
        (dest / "bin" / "node").chmod(0o755)


def fetch_vendor(vendor_dir: Path, pyright_version: str) -> None:
    _fetch_node(NODE_VERSION, *_node_platform_arch(), vendor_dir / "node")
    _fetch_pyright(pyright_version, vendor_dir / "pyright")

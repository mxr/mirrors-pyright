from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _vendor_dir() -> Path:
    return Path(__file__).parent / "_vendor"


def _node_bin(vendor_dir: Path) -> Path:
    if sys.platform == "win32":
        return vendor_dir / "node" / "node.exe"
    return vendor_dir / "node" / "bin" / "node"


def main() -> None:
    vendor_dir = _vendor_dir()
    node = _node_bin(vendor_dir)
    # pyright's own index.js sets up __rootDirectory (used to locate the
    # bundled typeshed-fallback stubs) before requiring dist/pyright.js, so
    # we invoke it rather than dist/pyright.js directly.
    pyright_entry = vendor_dir / "pyright" / "index.js"

    for label, path in (("Node runtime", node), ("pyright entrypoint", pyright_entry)):
        if not path.exists():
            sys.exit(
                f"mirrors-pyright: {label} not found at {path}\n"
                "This install is missing its vendored assets - reinstall mirrors-pyright, "
                "or file a bug at https://github.com/mxr/mirrors-pyright/issues"
            )

    argv = [str(node), str(pyright_entry), *sys.argv[1:]]
    if sys.platform == "win32":
        sys.exit(subprocess.call(argv))
    else:
        os.execv(str(node), argv)


if __name__ == "__main__":
    main()

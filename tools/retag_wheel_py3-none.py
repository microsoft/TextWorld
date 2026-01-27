"""
Rewrite wheel tags from cp312-cp312-PLATFORM to py3-none-PLATFORM.

This is appropriate when the wheel contains OS-specific non-Python binaries
(e.g., Inform7) but no Python extension modules (ABI-independent).
"""

import argparse
import os
import re
import zipfile
from pathlib import Path


WHEEL_TAG_RE = re.compile(r"^Tag:\s*(\S+)\s*$")


def parse_platform_tag(filename: str) -> str:
    # {dist}-{ver}-{python tag}-{abi tag}-{platform tag}.whl
    m = re.match(r"^.+-[^-]+-[^-]+-(?P<plat>.+)\.whl$", filename)
    if not m:
        raise ValueError(f"Cannot parse wheel filename: {filename}")
    return m.group("plat")


def retag(path: Path) -> Path:
    plat = parse_platform_tag(path.name)
    new_name = re.sub(r"-[^-]+-[^-]+-" + re.escape(plat) + r"\.whl$", f"-py3-none-{plat}.whl", path.name)
    # If the regex didn't match (unexpected format), fall back to explicit construction:
    if new_name == path.name:
        # Use a more explicit split
        parts = path.name[:-4].split("-")
        if len(parts) < 5:
            raise ValueError(f"Unexpected wheel name: {path.name}")
        new_name = "-".join(parts[:-3] + ["py3", "none", parts[-1]]) + ".whl"

    out = path.with_name(new_name)

    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        wheel_files = [n for n in zin.namelist() if n.endswith(".dist-info/WHEEL")]
        if len(wheel_files) != 1:
            raise RuntimeError(f"Expected exactly one .dist-info/WHEEL, found: {wheel_files}")
        wheel_meta = wheel_files[0]

        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == wheel_meta:
                text = data.decode("utf-8")
                lines = text.splitlines(True)

                kept = []
                for line in lines:
                    if WHEEL_TAG_RE.match(line.strip()):
                        continue
                    kept.append(line)

                kept.append(f"Tag: py3-none-{plat}\n")
                data = "".join(kept).encode("utf-8")

            zout.writestr(info, data)

    # Remove original so only retagged wheel remains
    os.remove(path)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wheel", nargs="+")
    args = ap.parse_args()

    for w in args.wheel:
        out = retag(Path(w))
        print(f"Retagged: {w} -> {out.name}")


if __name__ == "__main__":
    main()

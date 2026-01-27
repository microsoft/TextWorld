"""Retag wheel from cpXYZ-cpXYZ-PLATFORM to py3-none-PLATFORM."""

import argparse
import os
import zipfile
from pathlib import Path


def retag(path: Path) -> Path:
    # Extract platform tag from filename: name-ver-pytag-abi-platform.whl
    parts = path.stem.split("-")
    platform = parts[-1]
    new_name = "-".join(parts[:-3] + ["py3", "none", platform]) + ".whl"
    out = path.with_name(new_name)

    with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(
        out, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        wheel_meta = next(n for n in zin.namelist() if n.endswith(".dist-info/WHEEL"))

        for info in zin.infolist():
            data = zin.read(info.filename)

            if info.filename == wheel_meta:
                lines = data.decode("utf-8").splitlines(keepends=True)
                # Remove existing Tag: lines and add new one
                lines = [l for l in lines if not l.strip().startswith("Tag:")]
                if lines and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"
                lines.append(f"Tag: py3-none-{platform}\n")
                data = "".join(lines).encode("utf-8")

            zout.writestr(info, data)

    try:
        os.remove(path)
    except OSError:
        pass

    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dest_dir", type=Path, help="Directory containing wheels to retag")
    args = parser.parse_args()

    if not args.dest_dir.is_dir():
        raise ValueError(f"Directory not found: {args.dest_dir}")

    wheels = list(args.dest_dir.glob("*.whl"))
    if not wheels:
        print(f"No wheels found in {args.dest_dir}")
        return

    for wheel in wheels:
        out = retag(wheel)
        print(f"Retagged: {wheel.name} -> {out.name}")


if __name__ == "__main__":
    main()

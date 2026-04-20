from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
DIST_DIR = ROOT / "backend-dist"
SPEC_DIR = BUILD_DIR / "backend-spec"
WORK_DIR = BUILD_DIR / "backend-pyinstaller"
ENTRYPOINT = ROOT / "backend" / "main.py"


def main() -> int:
    DIST_DIR.mkdir(exist_ok=True)
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "ScriptMasterBackend",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(WORK_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--paths",
        str(ROOT / "backend"),
        "--hidden-import",
        "openpyxl",
        "--collect-submodules",
        "uvicorn",
        "--collect-submodules",
        "fastapi",
        "--collect-submodules",
        "starlette",
        "--add-data",
        f"{ROOT / 'backend' / 'config'};config",
        str(ENTRYPOINT),
    ]

    subprocess.run(command, cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

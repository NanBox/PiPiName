#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
VENV_DIR = PROJECT_ROOT / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
RUNTIME_CHECK = "import fastapi, opencc, uvicorn"

if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))


def ensure_runtime() -> None:
    if os.environ.get("PIPINAME_NO_BOOTSTRAP") == "1":
        return
    if Path(sys.prefix).resolve() == VENV_DIR.resolve():
        if not has_runtime(VENV_PYTHON):
            install_runtime(VENV_PYTHON)
        return

    if not VENV_PYTHON.exists():
        print("首次运行，正在创建本地运行环境 .venv ...")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)], cwd=PROJECT_ROOT)
    if not has_runtime(VENV_PYTHON):
        install_runtime(VENV_PYTHON)

    env = os.environ.copy()
    env["PIPINAME_BOOTSTRAPPED"] = "1"
    os.execve(str(VENV_PYTHON), [str(VENV_PYTHON), str(PROJECT_ROOT / "main.py"), *sys.argv[1:]], env)


def has_runtime(python: Path) -> bool:
    return subprocess.run(
        [str(python), "-c", RUNTIME_CHECK],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def install_runtime(python: Path) -> None:
    print("正在安装运行依赖 ...")
    subprocess.check_call([str(python), "-m", "pip", "install", "."], cwd=PROJECT_ROOT)


ensure_runtime()

from pipiname.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["web", "--open"], prog="./main.py"))

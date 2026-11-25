#!/usr/bin/env python3
"""Portable commands used by students and by the course documentation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen


# Keep the logical path on Windows. Resolving a junction can reintroduce a
# non-ASCII profile path that breaks Gradle worker classpaths.
ROOT = Path(__file__).absolute().parents[1]
CAR_SERVICE = ROOT / "apps" / "car-rental-service"
PRICING_SERVICE = ROOT / "apps" / "pricing-service"


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def gradle_command() -> list[str]:
    if os.name == "nt":
        return ["cmd", "/c", "gradlew.bat"]
    return ["./gradlew"]


def test_java() -> None:
    run([*gradle_command(), "clean", "test"], cwd=CAR_SERVICE)


def test_python() -> None:
    venv_python = PRICING_SERVICE / ".venv" / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    python = venv_python if venv_python.exists() else Path(sys.executable)
    run([str(python), "-m", "pytest"], cwd=PRICING_SERVICE)


def test() -> None:
    test_java()
    test_python()


def compose_up() -> None:
    require_command("docker")
    run(["docker", "compose", "up", "--build", "--detach"])


def compose_down() -> None:
    require_command("docker")
    run(["docker", "compose", "down"])


def wait_for(url: str, *, timeout_seconds: int = 45) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=3) as response:
                if 200 <= response.status < 300:
                    print(f"OK {url}")
                    return
        except (URLError, TimeoutError) as error:
            last_error = error
        time.sleep(1)

    raise RuntimeError(f"Service unavailable at {url}: {last_error}")


def smoke() -> None:
    wait_for("http://localhost:8080/health")
    wait_for("http://localhost:8080/cars")
    wait_for("http://localhost:8000/health")
    request = Request(
        "http://localhost:8000/quotes",
        data=json.dumps({"category": "standard", "days": 2}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:
        quote = json.load(response)
    if quote.get("total") != 120.0 or quote.get("currency") != "EUR":
        raise RuntimeError(f"Unexpected pricing response: {quote}")
    print("OK pricing quote")


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"Required command not found: {command}")


def prerequisites() -> None:
    checks = {
        "Python": sys.executable,
        "Java": shutil.which("java"),
        "Docker": shutil.which("docker"),
    }
    missing = False

    for name, location in checks.items():
        if location:
            print(f"OK {name}: {location}")
        else:
            print(f"MISSING {name}")
            missing = True

    if missing:
        raise RuntimeError("One or more prerequisites are missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "prerequisites",
            "test",
            "test-java",
            "test-python",
            "compose-up",
            "compose-down",
            "smoke",
        ],
    )
    args = parser.parse_args()

    commands = {
        "prerequisites": prerequisites,
        "test": test,
        "test-java": test_java,
        "test-python": test_python,
        "compose-up": compose_up,
        "compose-down": compose_down,
        "smoke": smoke,
    }

    try:
        commands[args.command]()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Idempotent CPU backend setup, bootstrapped by uv (no system Python required)."""

from pathlib import Path
import argparse, json, os, shutil, socket, subprocess, sys, time, urllib.request, urllib.error

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".venv-backend-cpu"


def python_path():
    return ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def installation_steps(uv):
    python = str(python_path())
    steps = []
    if not python_path().exists():
        steps.append([uv, "venv", "--python", "3.12", str(ENV)])
    steps.extend(
        [
            [
                uv,
                "pip",
                "install",
                "--python",
                python,
                "torch==2.11.0",
                "torchvision==0.26.0",
                "--index-url",
                "https://download.pytorch.org/whl/cpu",
            ],
            [
                uv,
                "pip",
                "install",
                "--python",
                python,
                "-r",
                str(ROOT / "requirements.txt"),
                "--excludes",
                str(ROOT / "requirements-exclude.txt"),
            ],
            [
                python,
                str(ROOT / "scripts/repair_opencv.py"),
                "--uv",
                uv,
                "--python",
                python,
            ],
            [
                python,
                str(ROOT / "scripts/import_ann.py"),
                str(ROOT / "trained-models/baseline"),
            ],
            [python, str(ROOT / "scripts/download_models.py")],
        ]
    )
    return steps


def prepare_config():
    target = ROOT / ".env"
    if not target.exists():
        with target.open("x", encoding="utf-8") as f:
            f.write(
                "DEVICE=cpu\nHOST=127.0.0.1\nPORT=8765\nMAX_INFLIGHT=1\nALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000\n"
            )
    print(
        "Existing .env preserved. CPU launcher forces DEVICE=cpu and defaults MAX_INFLIGHT=1.",
        flush=True,
    )


def start_backend():
    python = python_path()
    if not python.is_file():
        raise RuntimeError("CPU environment missing. Run INSTALL_BACKEND first.")
    # Read host/port without executing dotenv or modifying its contents.
    settings = {}
    if (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip()
    env = os.environ.copy()
    env["DEVICE"] = "cpu"
    env["MAX_INFLIGHT"] = env.get("MAX_INFLIGHT", settings.get("MAX_INFLIGHT", "1"))
    host = env.get("HOST", settings.get("HOST", "127.0.0.1"))
    port = int(env.get("PORT", settings.get("PORT", "8765")))
    probe = "127.0.0.1" if host == "0.0.0.0" else host
    with socket.socket() as sock:
        sock.settimeout(1)
        if sock.connect_ex((probe, port)) == 0:
            raise RuntimeError(
                f"Port {port} already occupied; no existing process was stopped."
            )
    print(
        f"Starting CPU backend on {host}:{port}. Keep this terminal open; Ctrl+C stops it.",
        flush=True,
    )
    process = subprocess.Popen(
        [str(python), "-u", str(ROOT / "scripts/serve.py")], cwd=ROOT, env=env
    )
    try:
        deadline = time.monotonic() + 600
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(
                    "Backend exited. See the error above (Linux may need libgl1/libglib2.0-0)."
                )
            try:
                with urllib.request.urlopen(
                    f"http://{probe}:{port}/health", timeout=3
                ) as response:
                    health = json.load(response)
                states = health.get("models", {})
                if states and all(
                    m.get("state") in ("ready", "error") for m in states.values()
                ):
                    print(
                        json.dumps(
                            {"models": states, "device": health.get("device")}, indent=2
                        ),
                        flush=True,
                    )
                    failed = [
                        name
                        for name, item in states.items()
                        if item.get("state") != "ready"
                    ]
                    if failed:
                        raise RuntimeError("Models failed: " + ", ".join(failed))
                    print(
                        f"READY: http://{probe}:{port}/docs | /health | /ready",
                        flush=True,
                    )
                    break
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(2)
        else:
            raise RuntimeError(
                "Model startup exceeded 10 minutes; check hardware/dependency logs."
            )
        process.wait()
        if process.returncode:
            raise RuntimeError(f"Backend exited with code {process.returncode}")
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uv", default=shutil.which("uv"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--install-only", action="store_true")
    parser.add_argument("--start-only", action="store_true")
    parser.add_argument("--repair-opencv", action="store_true")
    args = parser.parse_args()
    if args.start_only:
        return start_backend()
    if not args.uv:
        raise RuntimeError(
            "uv not found. Use INSTALL_BACKEND.cmd or install_backend.sh."
        )
    if args.repair_opencv:
        from repair_opencv import repair

        if not python_path().exists():
            raise RuntimeError("Run INSTALL_BACKEND first.")
        repair(args.uv, str(python_path()))
        print("Repair complete. Run START_BACKEND.cmd / bash start_backend.sh.")
        return
    steps = installation_steps(args.uv)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "profile": "CPU / one worker",
                    "environment": str(ENV),
                    "steps": steps,
                    "config": "create only if missing; preserve existing .env",
                    "start": not args.install_only,
                },
                indent=2,
            )
        )
        return
    for index, command in enumerate(steps, 1):
        print(
            f"\n[{index}/{len(steps)}] {Path(command[0]).name}: "
            + " ".join(command[1:]),
            flush=True,
        )
        subprocess.run(command, cwd=ROOT, check=True)
    prepare_config()
    print(
        "Installation complete. Models downloaded/imported. No firewall, TLS, or system service changed.",
        flush=True,
    )
    if not args.install_only:
        start_backend()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(130)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

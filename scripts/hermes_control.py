"""Hermes starts stock NitroGen (serve + play.py). No input remapping."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def find_ckpt() -> Path | None:
    hits = list(Path.home().glob("**/.cache/huggingface/hub/models--nvidia--NitroGen/**/ng.pt"))
    hits += list(ROOT.glob("**/ng.pt"))
    return hits[0] if hits else None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--process", required=True, help="Exact exe, e.g. javaw.exe or celeste.exe")
    p.add_argument("--ckpt", default=None)
    p.add_argument("--port", type=int, default=5555)
    p.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl+C")
    p.add_argument("--allow-menu", action="store_true")
    args = p.parse_args()

    ckpt = Path(args.ckpt) if args.ckpt else find_ckpt()
    if not ckpt or not ckpt.exists():
        print("MISSING_CKPT: hf download nvidia/NitroGen ng.pt")
        return 2

    py = sys.executable
    serve = subprocess.Popen([py, str(ROOT / "scripts" / "serve.py"), str(ckpt), "--port", str(args.port)])
    time.sleep(2)
    play_cmd = [py, str(ROOT / "scripts" / "play.py"), "--process", args.process, "--port", str(args.port)]
    if args.allow_menu:
        play_cmd.append("--allow-menu")
    play = subprocess.Popen(play_cmd)
    try:
        if args.seconds > 0:
            t0 = time.time()
            while time.time() - t0 < args.seconds:
                if play.poll() is not None:
                    break
                time.sleep(0.5)
        else:
            play.wait()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in (play, serve):
            if proc.poll() is None:
                proc.terminate()
        time.sleep(0.4)
        for proc in (play, serve):
            if proc.poll() is None:
                proc.kill()
    print("stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

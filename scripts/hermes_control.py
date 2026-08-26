"""Hermes is the brain. Stock NitroGen is the hands (ViGEm pad).

Commands:
  status
  start --process <exe> [--seconds N] [--ckpt PATH] [--port 5555]
  stop
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "hermes" / "cache" / "nitrogen_state.json"


def find_ckpt() -> Path | None:
    hits = list(ROOT.glob("**/ng.pt"))
    hub = Path.home() / ".cache" / "huggingface" / "hub"
    if hub.exists():
        hits += list(hub.glob("models--nvidia--NitroGen/**/ng.pt"))
    return hits[0] if hits else None


def port_up(port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.4)
    try:
        s.connect(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(d: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def cmd_status(port: int) -> int:
    st = load_state()
    ckpt = find_ckpt()
    print(
        json.dumps(
            {
                "ckpt": str(ckpt) if ckpt else None,
                "port_up": port_up(port),
                "serve_pid": st.get("serve_pid"),
                "serve_alive": alive(st.get("serve_pid")),
                "play_pid": st.get("play_pid"),
                "play_alive": alive(st.get("play_pid")),
                "process": st.get("process"),
                "role": "hermes=brain nitrogen=hands",
            }
        )
    )
    return 0


def cmd_stop() -> int:
    st = load_state()
    for key in ("play_pid", "serve_pid"):
        pid = st.get(key)
        if not pid or not alive(pid):
            continue
        try:
            os.kill(pid, 15)
        except OSError:
            pass
    time.sleep(0.4)
    for key in ("play_pid", "serve_pid"):
        pid = st.get(key)
        if pid and alive(pid):
            try:
                os.kill(pid, 9)
            except OSError:
                pass
    save_state({})
    print("stopped")
    return 0


def cmd_start(process: str, port: int, seconds: float, ckpt: Path | None, allow_menu: bool) -> int:
    if not ckpt or not ckpt.exists():
        print("MISSING_CKPT: hf download nvidia/NitroGen ng.pt")
        return 2
    cmd_stop()
    py = sys.executable
    serve = subprocess.Popen(
        [py, str(ROOT / "scripts" / "serve.py"), str(ckpt), "--port", str(port)],
        cwd=str(ROOT),
    )
    for _ in range(40):
        if port_up(port):
            break
        if serve.poll() is not None:
            print("SERVE_DIED")
            return 3
        time.sleep(0.25)
    play_cmd = [py, str(ROOT / "scripts" / "play.py"), "--process", process, "--port", str(port)]
    if allow_menu:
        play_cmd.append("--allow-menu")
    play = subprocess.Popen(play_cmd, cwd=str(ROOT))
    save_state(
        {
            "serve_pid": serve.pid,
            "play_pid": play.pid,
            "process": process,
            "port": port,
            "ckpt": str(ckpt),
        }
    )
    print(json.dumps({"started": True, "process": process, "serve_pid": serve.pid, "play_pid": play.pid}))
    if seconds <= 0:
        return 0
    t0 = time.time()
    while time.time() - t0 < seconds:
        if play.poll() is not None:
            break
        time.sleep(0.4)
    return cmd_stop()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["status", "start", "stop"])
    p.add_argument("--process", default="")
    p.add_argument("--ckpt", default=None)
    p.add_argument("--port", type=int, default=5555)
    p.add_argument("--seconds", type=float, default=0)
    p.add_argument("--allow-menu", action="store_true")
    args = p.parse_args()
    if args.command == "status":
        return cmd_status(args.port)
    if args.command == "stop":
        return cmd_stop()
    if not args.process:
        print("NEED --process exact.exe")
        return 2
    ckpt = Path(args.ckpt) if args.ckpt else find_ckpt()
    return cmd_start(args.process, args.port, args.seconds, ckpt, args.allow_menu)


if __name__ == "__main__":
    raise SystemExit(main())

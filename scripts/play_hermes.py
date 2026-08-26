"""Play a Windows game with NitroGen, using Hermes raw keyboard/mouse.

Requires a running `python scripts/serve.py <ng.pt>` on --port.

Example (Minecraft 26.2):
  python scripts/play_hermes.py --process javaw.exe --seconds 60
"""
from __future__ import annotations

import argparse
import time
from collections import OrderedDict

import numpy as np
from PIL import Image

from nitrogen.game_env import GamepadEnv, get_process_info
from nitrogen.hermes_kb import HermesKeyboardMouse
from nitrogen.inference_client import ModelClient
from nitrogen.shared import BUTTON_ACTION_TOKENS

import cv2


def preprocess_img(main_image):
    main_cv = cv2.cvtColor(np.array(main_image), cv2.COLOR_RGB2BGR)
    final_image = cv2.resize(main_cv, (256, 256), interpolation=cv2.INTER_AREA)
    return Image.fromarray(cv2.cvtColor(final_image, cv2.COLOR_BGR2RGB))


ZERO = OrderedDict(
    [
        ("WEST", 0),
        ("SOUTH", 0),
        ("BACK", 0),
        ("DPAD_DOWN", 0),
        ("DPAD_LEFT", 0),
        ("DPAD_RIGHT", 0),
        ("DPAD_UP", 0),
        ("GUIDE", 0),
        ("AXIS_LEFTX", np.array([0], dtype=np.long)),
        ("AXIS_LEFTY", np.array([0], dtype=np.long)),
        ("LEFT_SHOULDER", 0),
        ("LEFT_TRIGGER", np.array([0], dtype=np.long)),
        ("AXIS_RIGHTX", np.array([0], dtype=np.long)),
        ("AXIS_RIGHTY", np.array([0], dtype=np.long)),
        ("LEFT_THUMB", 0),
        ("RIGHT_THUMB", 0),
        ("RIGHT_SHOULDER", 0),
        ("RIGHT_TRIGGER", np.array([0], dtype=np.long)),
        ("START", 0),
        ("EAST", 0),
        ("NORTH", 0),
    ]
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--process", default="javaw.exe")
    p.add_argument("--port", type=int, default=5555)
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--gamepad", action="store_true", help="Use ViGEm pad (stock NitroGen)")
    p.add_argument("--allow-menu", action="store_true")
    args = p.parse_args()

    policy = ModelClient(port=args.port)
    policy.reset()
    info = policy.info()
    ratio = info["action_downsample_ratio"]
    print("policy", info.get("ckpt_path"), "downsample", ratio)

    env = GamepadEnv(game=args.process, game_speed=1.0, env_fps=60, async_mode=True)
    hwnd = None
    try:
        import win32gui

        def find(h, acc):
            if win32gui.IsWindowVisible(h) and args.process.lower() in (
                win32gui.GetWindowText(h) or ""
            ).lower():
                acc.append(h)
            return True

        found = []
        win32gui.EnumWindows(lambda h, a: find(h, a) or True, found)
        hwnd = found[0] if found else None
    except Exception:
        hwnd = None
    if hwnd is None:
        # fallback: first visible window of pid
        try:
            import win32gui
            import win32process

            pid = get_process_info(args.process)["pid"]
            acc = []

            def cb(h, _):
                _, p = win32process.GetWindowThreadProcessId(h)
                if p == pid and win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h):
                    acc.append(h)
                return True

            win32gui.EnumWindows(cb, None)
            hwnd = acc[0] if acc else 0
        except Exception:
            hwnd = 0

    kb = None if args.gamepad else HermesKeyboardMouse(hwnd or 0)
    env.reset()
    obs, *_ = env.step(action=ZERO)
    end = time.time() + args.seconds
    step = 0
    try:
        while time.time() < end:
            pred = policy.predict(preprocess_img(obs))
            j_left, j_right, buttons = pred["j_left"], pred["j_right"], pred["buttons"]
            n = len(buttons)
            for i in range(n):
                a = ZERO.copy()
                xl, yl = j_left[i]
                xr, yr = j_right[i]
                a["AXIS_LEFTX"] = np.array([int(xl * 32767)], dtype=np.long)
                a["AXIS_LEFTY"] = np.array([int(yl * 32767)], dtype=np.long)
                a["AXIS_RIGHTX"] = np.array([int(xr * 32767)], dtype=np.long)
                a["AXIS_RIGHTY"] = np.array([int(yr * 32767)], dtype=np.long)
                for name, value in zip(BUTTON_ACTION_TOKENS, buttons[i]):
                    if "TRIGGER" in name:
                        a[name] = np.array([value * 255], dtype=np.long)
                    else:
                        a[name] = 1 if value > 0.5 else 0
                if not args.allow_menu:
                    a["GUIDE"] = a["START"] = a["BACK"] = 0
                for _ in range(ratio):
                    if kb:
                        kb.apply(a)
                    obs, *_ = env.step(action=a if args.gamepad else ZERO)
            step += 1
            print("step", step)
    finally:
        if kb:
            kb.release_all()
        env.unpause()
        env.close()
    print("done steps", step)


if __name__ == "__main__":
    main()

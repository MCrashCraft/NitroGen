"""Map NitroGen gamepad actions to raw WASD + mouse (Minecraft / keyboard games).

NitroGen outputs Xbox-style sticks/buttons. Hermes has no virtual pad in the
computer_use tool, and Minecraft on this PC listens to raw mouse/keys.
"""
from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
KEYEVENTF_KEYUP = 0x0002

VK = {
    "w": 0x57,
    "a": 0x41,
    "s": 0x53,
    "d": 0x44,
    "space": 0x20,
    "e": 0x45,
    "shift": 0x10,
}


def _axis(val) -> float:
    if hasattr(val, "__len__"):
        val = val[0]
    v = float(val)
    if abs(v) > 1.5:
        v = v / 32767.0
    return max(-1.0, min(1.0, v))


def _trigger(val) -> float:
    if hasattr(val, "__len__"):
        val = val[0]
    v = float(val)
    if v > 1.5:
        v = v / 255.0
    return max(0.0, min(1.0, v))


class HermesKeyboardMouse:
    """Apply one NitroGen action dict as raw input. Does not steal between steps
    except SetForegroundWindow on the game hwnd."""

    def __init__(self, hwnd: int, look_scale: float = 18.0, stick_dead: float = 0.25):
        self.hwnd = hwnd
        self.look_scale = look_scale
        self.stick_dead = stick_dead
        self._held: set[str] = set()
        self._lmb = False

    def _down(self, name: str) -> None:
        if name in self._held:
            return
        user32.keybd_event(VK[name], 0, 0, 0)
        self._held.add(name)

    def _up(self, name: str) -> None:
        if name not in self._held:
            return
        user32.keybd_event(VK[name], 0, KEYEVENTF_KEYUP, 0)
        self._held.discard(name)

    def _set(self, name: str, on: bool) -> None:
        if on:
            self._down(name)
        else:
            self._up(name)

    def apply(self, action: dict) -> None:
        if self.hwnd and user32.IsWindow(self.hwnd):
            user32.SetForegroundWindow(self.hwnd)

        lx = _axis(action.get("AXIS_LEFTX", 0))
        ly = _axis(action.get("AXIS_LEFTY", 0))
        rx = _axis(action.get("AXIS_RIGHTX", 0))
        ry = _axis(action.get("AXIS_RIGHTY", 0))
        rt = _trigger(action.get("RIGHT_TRIGGER", 0))
        south = bool(action.get("SOUTH"))
        west = bool(action.get("WEST"))
        north = bool(action.get("NORTH"))
        dpad_up = bool(action.get("DPAD_UP"))

        self._set("d", lx > self.stick_dead)
        self._set("a", lx < -self.stick_dead)
        # NitroGen Y: forward is typically negative on left stick after Windows flip
        self._set("w", ly < -self.stick_dead or dpad_up)
        self._set("s", ly > self.stick_dead)
        self._set("space", south)
        self._set("shift", west)
        if north:
            self._set("e", True)
            time.sleep(0.04)
            self._set("e", False)

        dx = int(rx * self.look_scale)
        dy = int(ry * self.look_scale)
        if dx or dy:
            user32.mouse_event(MOUSEEVENTF_MOVE, dx, dy, 0, 0)

        mine = rt > 0.4 or bool(action.get("RIGHT_SHOULDER"))
        if mine and not self._lmb:
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self._lmb = True
        elif not mine and self._lmb:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self._lmb = False

    def release_all(self) -> None:
        for name in list(self._held):
            self._up(name)
        if self._lmb:
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self._lmb = False

# NitroGen + Hermes (stock)

Fork: https://github.com/MCrashCraft/NitroGen (branch `hermes-overlay`)  
Upstream: https://github.com/MineDojo/NitroGen

Hermes **starts and stops** NitroGen. NitroGen plays **like the original**: screenshot → `ng.pt` → **ViGEm Xbox pad**. Any Windows game the stock agent can drive.

No WASD remapper. No Minecraft-only mapper.

## Hermes job

1. Game is already open (user’s copy).
2. Start `scripts/serve.py <ng.pt>` if port 5555 is down.
3. Start `scripts/play.py --process <exact.exe>` (Task Manager name).
4. Stop both when he says stop.

Helper: `python scripts/hermes_control.py --process javaw.exe --seconds 60`

## Need

- `pip install -e .` in this repo
- `hf download nvidia/NitroGen ng.pt`
- [ViGEmBus](https://github.com/nefarius/ViGEmBus) (stock `vgamepad`)

## Not

A planner. One-frame reflex. Hermes picks the `.exe` and the clock. NitroGen presses the pad.

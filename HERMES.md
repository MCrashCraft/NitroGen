# NitroGen + Hermes (this PC)

Fork: https://github.com/MCrashCraft/NitroGen (branch `hermes-overlay`)  
Upstream: https://github.com/MineDojo/NitroGen  
Model: https://huggingface.co/nvidia/NitroGen (`ng.pt`)

NitroGen is a **500M** pixel → **gamepad** model. It is **not** a planner. Windows games only.

## Hermes overlay (this fork)

- `nitrogen/hermes_kb.py` — maps sticks/buttons to **raw WASD + mouse** (Minecraft).
- `scripts/play_hermes.py` — capture via stock `GamepadEnv`, act via Hermes keys unless `--gamepad`.

Stock `play.py` still uses ViGEm (`vgamepad`). Use that for pad-only games.

## Run

```
cd C:\Users\micha\Desktop\NitroGen
python -m venv .venv
.venv\Scripts\pip install -e .
hf download nvidia/NitroGen ng.pt
.venv\Scripts\python scripts\serve.py <path_to_ng.pt>
.venv\Scripts\python scripts\play_hermes.py --process javaw.exe --seconds 60
```

Minecraft process is `javaw.exe`. Stay off the mouse while it runs.

## Anya

Load `gaming-agent-noobie`. Prefer NitroGen for fast react. Keep scout+raw hold-mine for “aim at birch then hold.”

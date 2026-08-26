# Hermes = brain. NitroGen = hands.

Fork: https://github.com/MCrashCraft/NitroGen (`hermes-overlay`)  
Upstream: https://github.com/MineDojo/NitroGen

**Hermes** chooses the game, when to start, when to stop.  
**NitroGen** is stock: one frame → ViGEm Xbox pad. Any Windows game.

No WASD remapper.

## Commands (Anya runs these)

```
python scripts/hermes_control.py status
python scripts/hermes_control.py start --process celeste.exe --seconds 60
python scripts/hermes_control.py stop
```

`--process` = Task Manager exe name. Game must already be open.

## Need

- `pip install -e .`
- `hf download nvidia/NitroGen ng.pt`
- ViGEmBus (stock vgamepad)

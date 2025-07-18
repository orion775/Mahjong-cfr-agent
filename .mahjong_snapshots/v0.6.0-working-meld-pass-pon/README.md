# Mahjong CFR Agent (WIP)

This project is a carefully layered implementation of a 4-player Mahjong engine designed to support training an AI agent using Counterfactual Regret Minimization (CFR). The main goals are as follows:

1. Build a fully functional, testable Mahjong game engine (currently in progress)
2. Implement CFR-based self-play agents
3. If time permits, explore deep learning enhancements
4. Eventually, support online play against human players through a simple input/output interface

---

## What Has Been Completed So Far

### Tile System

* `Tile` class implemented with proper equality and hashing
* Includes suit tiles (Man, Pin, Sou), wind tiles, and dragon tiles
* Each tile is assigned a unique integer ID for use in CFR

### Action Space

* Discard actions (IDs 0-33)
* PON actions (IDs 34-67)
* PASS action (ID 68)
* CHI actions are planned but not implemented yet

### Game Engine

* Wall generation and initial dealing of 13 tiles to each player
* Turn structure supporting draw and discard phases
* Keeps track of player discards
* Current supported actions:

  * Drawing from the wall
  * Discarding a tile by tile\_id
  * Passing
  * PON (including correct meld registration and tile removal)

### Player Class

* Manages hand, melds, and player seat
* Methods for drawing, discarding, and calling melds
* Melds are stored as tuples such as ("PON", \[tile1, tile2, tile3])

### CFR Compatibility

* Tile IDs and action IDs are aligned to facilitate CFR training
* Codebase is built with testability in mind
* Engine and state representation are structured for future info set generation

---

## Test-Driven Development

Every function and module is tested using the unittest framework:

* `test_tile.py` for tile comparison and identity
* `test_action_space.py` for action ID mappings and boundaries
* `test_player.py` for draw, discard, and meld behaviors
* `test_game_state.py` for turn progression and action handling

---

## Debug History: PON Action

### Issue

PON actions were not registering during unit tests, even though the correct action ID was passed.

### Root Causes

1. Test used `Tile()` instances not present in the actual hand
2. Meld logic required exact object identity or matching tile\_id with correct equality checks
3. `step()` method automatically advanced the turn after a discard, skipping the opportunity to PON

### Fix (for tests)

In the unit test, we simulate an interrupt scenario:

```python
state.turn_index = 1  # Force South's turn
state.awaiting_discard = True  # Force discard phase to allow PON
```

### Future Fix

Implement a proper interrupt system that allows players to react to discards with melds before the turn advances.

---

## Development Conventions

* PowerShell snapshot script used to save project state into `.mahjong_snapshots/`
* Git is used with clear, incremental commits
* Snapshots avoid cluttering the Git history with partial experiments

---

## Next Steps

* Implement CHI logic (sequence melds)
* Add terminal state check (`is_terminal`) and winner determination (`get_winner`)
* Begin defining CFR-compatible `get_info_set()` method
* Scaffold the CFR self-play loop

---

## Plans for Later

* Build a minimal API interface to allow human-vs-agent matches
* If time permits, implement a Deep CFR variant using neural networks
* Integrate oracle-guided rollouts as seen in Suphx

---

## How to Resume Work on This Project

In a new ChatGPT session, paste this README and say:

> This is a CFR-based Mahjong agent project. I want to continue development from this point.

This will provide all the necessary context to continue right where you left off.

---

*Last updated after resolving the PON logic and tile matching issues.*

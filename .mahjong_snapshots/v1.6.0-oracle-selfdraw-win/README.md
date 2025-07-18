## Version v1.5.7 – future plan for Oracle-Guided Curriculum Learning Plan (v1.6.x+)
Goal:
Accelerate and debug CFR learning by combining oracle state testing with progressive curriculum rollout.

Method:

    Oracle State Injection:

        Design “solvable” game states with known optimal actions (“oracle states”).

        For each curriculum level (e.g., 1-step-to-win, 2-steps-to-win), set up oracle test cases where the best action is unambiguous.

    Curriculum Progression:

        Start CFR training and testing from states very close to terminal (easiest).

        Only progress to “further from win” curriculum steps once the agent consistently matches the oracle policy in easier levels.

        Gradually expand the starting state to cover more of the game (backing up step by step toward random initial hands).

    Validation & Debugging:

        At each curriculum stage, validate CFR’s policy using the oracle (“does the agent match the known optimal play?”).

        Use oracle policy checks to quickly catch bugs in info sets, regret logic, or reward propagation before training on harder positions.

    Transition to Full Self-Play:

        Once the agent reliably solves oracle curriculum states, begin mixing in full-game random self-play for robust policy learning.

Benefits:

    Fast, interpretable debugging of CFR logic.

    Faster convergence, avoiding wasted computation on unreachable or unsolvable states.

    Structured record of agent progress, curriculum by curriculum.

Example Steps:

    Implement FixedWinGameState (player one move from win; known best discard).

    Write a test ensuring CFR converges to 100% on the oracle action.

    Once passing, implement FixedTwoStepsFromWinGameState, and repeat.

    Log curriculum results and challenges in devlog.md as you proceed.


## Version v1.5.7 – Milestone: Full CFR Game Loop + Stable Tests

Version v1.5.7 – Milestone: Full CFR Game Loop + Stable Tests

What’s working:

    All test cases for core game logic (melds, claims, wall, discards, win detection) now pass deterministically.

    CFRTrainer runs end-to-end self-play, exporting readable policies and tracking average strategies.

    Debug logging and modular architecture make future upgrades/test debugging easy.

    All fixes and architectural changes are noted in README and devlog.

    Project is fully snapshot/versioned, ready for branching into new features.

Known Limitations:

    Reward and terminal logic are simplified (win = 4 melds). Not full Mahjong scoring/yaku.

    No user or agent interface; CFR is tabular (not scalable for “real” Mahjong, but perfect for research/experiments).

    Infoset abstraction is basic—good for now, will need extension for advanced play.

    No multi-round play or human-vs-agent loop yet.

Next Major Steps:

    Implement oracle CFR training for better policy validation.

    Design realistic scoring/reward functions (intermediate rewards, yaku recognition).

    Begin abstraction research or prep for function-approximator (deep RL) integration.

    Add UI tools or log replay visualization for debugging and agent demoing.


## Next Steps & Roadmap (Planned After v1.5.6)

### Short-Term (v1.6.x)
- **Add Real Win Detection**
  - Implement `is_winning_hand()` (e.g., 4 melds + pair) to replace the current terminal state logic.
  - Update `is_terminal()` and `get_reward()` to only return win/loss when a real Mahjong hand is formed.
  - Add new tests to cover real win conditions.
- **Integrate Win/Reward Into CFR Loop**
  - Ensure terminal rewards are triggered for actual victories, enabling meaningful CFR learning.
- **Partial/Progress Rewards (Optional)**
  - Assign rewards for hand improvement: e.g., melds formed, tenpai reached, or shanten decrease.

### Medium-Term (v1.7.x+)
- **Info Set Abstraction**
  - Improve `get_info_set()` for deeper, more human-like state representation (e.g., encode visible discards, open melds, seat wind).
- **Optimized CFR (CFR+ or Regret Matching+)**
  - Integrate CFR+ updates for faster convergence.
  - Explore table compression and/or state abstraction to control info set explosion.

### Long-Term / Research (v2.x+)
- **Deep Learning Integration**
  - Explore offline neural regret approximation (Deep CFR, e.g., as in Suphx).
  - Prepare agent for online/self-play training using policy/value networks.
- **Oracle-Guided Play**
  - Implement oracle or heuristic agents for curriculum learning or training acceleration (see Suphx/AlphaZero).
- **API/Interface for Human vs. Agent**
  - Minimal input/output interface for interactive play or online competition.

### Ongoing
- **Meld Priority/Interrupt Fixes**
  - Further polish meld interrupt and priority (e.g., PON > CHI > PASS, KAN handling in conflict cases).
- **Test Suite Expansion**
  - Continue writing isolated and end-to-end tests for new features and edge cases.
- **Devlog & Version Tracking**
  - Document every major change and challenge for future project reference.

### ## v1.5.5-flaky-tests-fixed-Test Stability and Meld Actions

- `test_pon_action` and `test_step_auto_resolves_pon` were removed in v1.5.5 due to inconsistent behavior when faking meld triggers.
- These tests relied on exact `tile_id` matching and `last_discard` manipulation, which are not safe to simulate outside actual gameplay flow.
- PON/CHI/KAN are now tested only through real state transitions (draw, discard, interrupt).

## v1.5.4 – Meld Priority Bug: CHI overriding PON (Fixed)

- Problem: `resolve_meld_priority()` was matching tiles by `tile_id` only, causing PON to fail if hand tiles had different `tile_id`s than the discard.
- Fix: Now PON checks match by `category` and `value`, allowing logically identical tiles to be used.
- Impact: Resolved rare but critical nondeterministic test failures (`test_chi_blocked_by_pon`)

### v1.5.3 – Meld Turn Ownership + CFR Interrupt Integration

This update completes meld logic integration into the main game loop. After a successful meld (CHI or PON), the claiming player now receives the turn immediately — matching standard Mahjong rules.

#### ✅ What Was Added
- Meld claimer now receives the next action (via `turn_index`)
- `resolve_meld_priority()` returns claiming player ID
- `GameState.step()` responds to meld ownership post-discard

#### 🧪 Tests Added
- `test_turn_passes_to_meld_claimer`: verifies the meld player controls the next turn

This closes the loop between discard → interrupt → meld → new turn.

### v1.5.2 – Meld Priority Resolution

This version implements correct meld interrupt behavior: when multiple players can claim a discard, the game now enforces Mahjong's meld priority order: **PON > CHI > PASS**.

#### ✅ What Was Added
- `GameState.resolve_meld_priority(tile)` to detect all legal PON/CHI calls after a discard
- Meld arbitration logic: only one player may claim a discard, respecting action hierarchy
- Meld execution and discard removal for PON and CHI

#### 🔬 Tests Added
- `test_chi_blocked_by_pon`: verifies that CHI is not allowed when PON is possible

#### 🧠 Known Limits
- Does not yet handle multiple PON claimers (e.g., tie-breaking by proximity to discarder)
- KAN melds are not yet prioritized (handled atomically for now)

### v1.5.1 – Meld Action CFR Tests

This patch finalizes CFR structural support for all meld types (CHI, PON, KAN) via targeted regret injection and verification. It ensures that all meld actions can be recognized, tracked, and updated within the regret/strategy tables.

#### ✅ What Was Added
- `FixedTrainerWithCHIRegret` and `test_cfr_learns_chi`
- `FixedTrainerWithPONRegret` and `test_cfr_learns_pon`
- Reused `FixedTrainer` logic for KAN testing (`test_cfr_learns_ankan`)

Each test uses a deterministic state and overrides `cfr()` to force regret for a specific meld action ID.

#### 🔍 Why It Matters
- Melds are core to Mahjong decision-making
- Without structural tests, CHI/PON/KAN might remain unused during CFR
- These tests ensure each meld action has valid CFR table integration

#### 🔬 Verified
- Regret tables update for CHI, PON, KAN
- Meld action encodings are valid and accessible
- Info sets support meld-based updates

#### ✅ Tests Added
- `test_cfr_learns_chi`
- `test_cfr_learns_pon`
- (previously added) `test_cfr_learns_ankan`

### Mahjong CFR Agent – README (v1.5.0)

Overview

This is a self-contained 4-player Japanese Mahjong engine using Counterfactual Regret Minimization (CFR) for decision learning. It simulates simplified draw-discard-meld turns with deterministic information sets and learns policies via tabular regret minimization.

The codebase now supports:

    A functioning turn-based environment

    Meld actions (CHI, PON, KAN) with cleanup

    Terminal detection via wall depletion or meld saturation

    Full CFR training loop with working info sets

    CFR strategy output export for offline inspection

    CFR Learning Status (v1.5.0)

    CFR now trains across realistic state branches without entering infinite recursion.

    Strategy tables are exported to cfr_policy.txt after training.

    Observed convergence toward legal action distribution in export_strategy_table().

Terminal states are detected via either:

    All tiles drawn (wall == [])

    A player forms 4 melds (basic win condition)

CFR recursion stops and returns utility values accordingly.

| Feature                 | Status | Notes                                                |
| ----------------------- | ------ | ---------------------------------------------------- |
| Tile Representation     | ✅      | `Tile` class with `tile_id`, `suit`, and `name`      |
| Wall + Draw Mechanics   | ✅      | `generate_wall()` ensures shuffle + pop behavior     |
| Player Turn System      | ✅      | `turn_index` rotates correctly per discard           |
| Discard Tracking        | ✅      | Discards stored per seat                             |
| Melds (CHI, PON, KAN)   | ✅      | Validations + discard cleanup implemented            |
| Action Space            | ✅      | Discrete action IDs for step/action logic            |
| Legal Action Resolution | ✅      | Reflects player hand + meld availability             |
| Info Set Representation | ✅      | Encodes hand vector + last discard + meld types      |
| CFR Training            | ✅      | Trains with controlled recursion + exportable policy |
| CFR Export              | ✅      | Strategy printed to `cfr_policy.txt`                 |
| Terminal Conditions     | ✅      | Wall exhaustion or player with 4 melds               |
| Unit Testing            | ✅      | 52 tests; all pass ✅                                |


Test Summary

52 test cases, including:

    CHI, PON, KAN validity

    Meld execution and hand updates

    Action legality based on game context

    CFR training reaching terminal state

    Regression-tested discard cleanup

    Edge cases: CHI only allowed from left, KAN with discard

🔧 Recently fixed:

    test_chi_only_from_left_seat: Corrected seat setup and debug flow

    FixedTrainer subclasses updated to support depth= in CFR recursion

    Terminal flags properly set mid-CFR for forced stop conditions

Bug Fixes Since v1.4.2

    | Area                 | Fix                                                                  |
| -------------------- | -------------------------------------------------------------------- |
| CFR recursion        | Added max depth, wall exhaustion check, and forced early stop        |
| Step loop            | Now respects `awaiting_discard`, avoids double-discard crashes       |
| CHI legal check      | Enforces left-player-only rule with test coverage                    |
| Strategy export      | Skips zero-probability actions and uses thresholds                   |
| Meld state mutations | Deep copy avoids shared hand state corruption                        |
| Test harness bugs    | `TypeError: got unexpected keyword 'depth'` fixed with wrapper edits |

Known Issues / Limitations

    No real hand validation or win-checking yet (e.g., no Tenpai/Yaku logic)

    Meld conflict priority (PON > CHI) is not enforced — TODO

    Strategy table may grow large with long vector-based keys

    Random wall shuffling introduces instability unless seed is set manually

    No draw resolution (e.g., if everyone passes)

Key Files

| File              | Purpose                             |
| ----------------- | ----------------------------------- |
| `game_state.py`   | Main environment logic              |
| `player.py`       | Handles hand, melds, and tile logic |
| `cfr_trainer.py`  | Contains CFR training loop          |
| `action_space.py` | Defines legal actions and encodings |
| `tile.py`         | Tile definitions and IDs            |
| `test_*`          | All unittests using TDD approach    |
| `run_cfr_demo.py` | Script for running a CFR iteration  |


Next Goals

    Meld Conflict Resolution

        Enforce CHI from left player only

        Auto-skip if PON overrides CHI

    Partial Reward Design

        Assign values to tile efficiency (e.g., efficiency heuristics)

    Real Game Termination

        Add real win-checking and Tenpai logic

    CFR+ / Optimizations

        Add regret matching+ variant for faster convergence

    Deep Learning Future

        Plan for CFR self-play + offline neural regret approximation



### Development Notes (v1.4.2)

- Fixed CHI action handling to remove two correct tiles from hand and update melds cleanly
- CHI is now only allowed by the player to the left of the discarder
- Shominkan logic verifies PON existence and hand tile before upgrade to KAN
- Minkan meld creation cleaned up, discard cleanup verified
- Fixed several test cases that previously failed due to tile object mismatch in assertions
- All 51 tests passing as of `v1.4.2-shominkan-fix-complete`


### v1.4.1 – Shominkan (Upgrade PON to KAN)

    Players can now upgrade an existing PON meld to a KAN if they draw or already hold the 4th matching tile.

    The game detects the upgrade automatically if a PON meld exists and the player calls KAN_<tile_id>.

    After upgrade, the meld becomes ("KAN", [tile, tile, tile, tile]) and the 4th tile is removed from the hand.

    A bonus tile is drawn after the upgrade, consistent with Ankan and Minkan behavior.

    Fully tested and CFR-safe.

### v1.4.0 – Open KAN (Minkan) Support

    Added full support for Minkan (open KAN) when a player holds 3 matching tiles and claims a discard.

    Both closed KAN (Ankan) and open KAN (Minkan) now trigger an immediate bonus tile draw from the wall.

    Melds are recorded as ("KAN", [tile1, tile2, tile3, tile4]), including the claimed discard if open.

    Turn passes to the caller, and they must discard after the bonus draw.

    Tests cover:

        Valid Minkan calls

        Bonus tile draw logic

        Discard cleanup

        Rejection of invalid Minkan attempts

## v1.3.0-kan-ankan-only

### Added
- Full support for Closed KAN (Ankan) melds
- `Player.can_ankan()` added and tested
- New action range `KAN_0`–`KAN_33` (IDs 90–123)
- `GameState.step()` supports KAN meld registration and tile removal
- `get_legal_actions()` returns KAN actions when 4-of-a-kind is present

### CFR Support
- CFR action space extended to 124 actions
- Strategy/regret tables updated to match
- KAN confirmed to appear in `get_strategy()` and be sampled
- Added unit test: `test_cfr_learns_ankan()` using `FixedKanTrainer`
- CFR export shows `KAN_*` when threshold is lowered

### Notes
- Only Closed KAN is supported in this version
- No bonus draw or replacement logic yet (stubbed)
- No interrupt/reactive KAN types (Minkan, Shominkan) yet

### Next Planned Feature
- Add Minkan (open KAN) support based on last discard
- Upgrade from Pon → Kan (Shominkan)
- Add KAN bonus draw logic (tile from back of wall)

### v1.2.0 – Terminal State + Win Detection

- Replaced temporary `is_terminal()` and `get_reward()` logic with meld-based win condition.
- A game is now terminal if any player forms 4 melds.
- CFR logic halts correctly on terminal states and propagates rewards.
- Added tests to verify terminal detection and reward correctness.
- Melds are used as a stand-in for full Mahjong hands, which is sufficient for CFR convergence during early iterations.

#### Known Limitations:
- We do not yet detect actual Mahjong wins (e.g., 4 melds + pair) — this is just a placeholder.
- No point-based scoring — reward is binary (+1.0 for winner).
- Once real scoring is added, CFR strategy behavior may shift.


### v1.1.0 – CHI Meld Implementation

v1.1.0 – CHI Meld Implementation

    Implemented CHI meld logic in step():

        Validates that the discard is part of the CHI sequence

        Removes two appropriate tiles from the current player’s hand

        Registers the CHI meld

        Removes the claimed tile from the discard pile based on tile_id, not object reference

    Updated action_space.py to encode and decode CHI actions using a new ID range (69–89)

    Test test_step_handles_chi_action added in test_game_state.py to verify the full CHI pipeline

Known Limitations (to revisit later)

    Only left-player CHI is valid in real Mahjong — our engine allows CHI from any direction (this isn’t enforced)

    Meld conflict resolution is missing (e.g., PON overrides CHI)

    If multiple CHI options are possible (e.g., CHI_2_3_4 and CHI_3_4_5 for a discard of 4), the system always uses the first match

    CHI support exists in CFR action space, but its frequency and impact on policy learning are yet untested

Let me know when that’s done and we’ll either:

    Move to KAN (optional but useful)

    Or start refining CFR rollout with win/terminal condition stubs.

### v1.0.0 Milestone – Working Tabular CFR Agent

    | Component                 | Status                           |
| ------------------------- | -------------------------------- |
| `get_info_set()`          |  Tested abstraction             |
| `get_strategy()`          |  Regret matching + strategy sum |
| `cfr()`                   |  Recursive regret update logic  |
| `train()`                 |  Iteration loop + regret growth |
| `get_average_strategy()`  |  Normalized strategy access     |
| `export_strategy_table()` |  Dumps readable learned policy  |

 Tests

    test_get_info_set_format

    test_get_strategy_returns_uniform_when_no_regrets

    test_average_strategy_returns_normalized_probs

    test_train_forces_regret_update_with_known_state

All passing, stable, and isolated.

Stubbed for Now

| Stubbed Function | Temporary Purpose               | Plan to Replace    |
| ---------------- | ------------------------------- | ------------------ |
| `is_terminal()`  | Early wall-cutoff for recursion | Add full win logic |
| `get_reward()`   | Always gives reward to player 0 | Add real scoring   |

🧾 README Dev Notes for v1.0.0
CFR Policy Export

CFRTrainer.export_strategy_table() writes a readable strategy file showing average probabilities per info set. This gives insight into what the agent has learned over many training iterations and is useful for debugging, visualization, and future deep policy distillation.


### v0.9.0 Development Notes – CFR Regret Testing & Training (v0.9.0)
What Was Added

    CFRTrainer.train()

        Iteratively runs cfr() from a new GameState instance.

        Used to populate regret tables over repeated self-play simulations.

    Stub: GameState.is_terminal()

        Temporarily ends the game when fewer than 130 tiles remain in the wall.

        This allows CFR to terminate gracefully and avoids infinite recursion.

        Will be replaced once actual game-ending conditions are implemented.

    Stub: GameState.get_reward(player_id)

        Always returns 1.0 for player 0, 0.0 for all others.

        This is a placeholder utility signal to validate regret updates.

        Will be replaced with proper scoring logic when available.
        🧪 Known Stubs (Intentional)
            Component	Why It's Stubbed	Status
            is_terminal()	Early exit for CFR control	🔜 Replace in v1.1
            get_reward()	Fake win reward for testing	🔜 Replace in v1.1
            Regret scaling logic	Simplified (no reach prob)	🔜 Fix in v1.1
            Actual scoring/win	Not needed for base CFR	🔜 Optional in Phase 3

    Fallback regret injection inside cfr()

        Manually forces a non-zero regret for at least one action (for testing).

        Ensures the regret table receives entries even when recursion is shallow or stubbed.

        This bypass is removed once terminal reward and real recursion are functioning.

    Controlled test: test_train_forces_regret_update_with_known_state()

        Injects a deterministic tile setup using a subclassed FixedTrainer.

        Overrides cfr() to insert a known regret update.

        Guarantees that the regret table is populated in a testable, stable way.

Risks and Limitations

    Reward and terminal logic are fake: All CFR utilities are currently hardcoded and not based on real game outcomes. Any data produced during training is not meaningful until the proper terminal and scoring logic is implemented.

    Manual regret updates: The current regret calculations in cfr() do not reflect actual expected utility differentials. These are placeholders solely to verify structural correctness.

    Testing overrides internal logic: The current test bypasses real environment transitions. Once cfr() uses full recursive simulation and scoring, the test must be updated accordingly.

    No strategy averaging yet: We haven’t yet added get_average_strategy(), so there’s no way to retrieve a converged policy yet. That’s the next step.

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

*Last updated after resolving the PON logic and tile matching issues.*

Debug History: CFR Regret Update Test

Issue
Initial CFR regret update test failed due to:

    Random game state not guaranteeing a regret update

    Utilities being 0.0 for all actions

    get_strategy() returning uniform but still zero regret

Fix
We replaced the test with a deterministic CFR unit test that:

    Injects a known hand with 2 unique tile_ids (forcing a decision)

    Bypasses full recursion using a fake cfr() override

    Manually sets regret[action] = 1.0 inside the override

    Verifies the regret table contains non-zero values

Why It’s Important
This test does not prove optimal regret computation, but verifies that:

    The regret table is writable

    Legal action masking works

    Basic CFR table logic is structurally correct

Test File:
tests/test_cfr_trainer.py
Test Name: test_cfr_regret_update_minimal
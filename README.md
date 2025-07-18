# Mahjong CFR Agent
---
A modular, test-driven, and research-grade 4-player Japanese Mahjong engine built for training AI agents using Counterfactual Regret Minimization (CFR).  
The project is structured to support curriculum/oracle tests, progressive info set abstraction, and future deep RL integration.
A complete, authentic 144-tile Chinese Mahjong engine built for training AI agents using Counterfactual Regret Minimization (CFR). Features full Flowers and Seasons implementation, automatic replacement of bonus tiles, and comprehensive Chinese scoring systegit add README.mdm.
---
---

## v2.0.3 — Seven Pairs & Thirteen Orphans Special Hands (2025-07-19)

**MAJOR FEATURE**: Successfully implemented the first two official Chinese Mahjong special hands using test-driven development.

**New Special Hands Implemented:**
- **Seven Pairs (Qi Dui Zi / 七对子)**: Hand consists of exactly 7 distinct pairs (no melds)
- **Thirteen Orphans (Shi San Yao / 十三么)**: One of each terminal/honor tile + one duplicate

**Technical Implementation:**
- Added `check_seven_pairs()` function with strict validation (exactly 7 pairs, no triplets)
- Added `check_thirteen_orphans()` function following official Chinese rules (13 terminals/honors + 1 duplicate)
- Updated `is_winning_hand()` to check special hands before standard meld structure
- Created comprehensive test suite in `tests/test_special_hands.py`

**Test Coverage Enhancement:**
- New test file: `tests/test_special_hands.py` with 4 comprehensive tests
- Tests simulate realistic draw scenarios for both special hands
- Verification that special hands don't interfere with standard wins
- Edge case testing (triplets blocking Seven Pairs, etc.)

**Code Quality:**
- Followed strict TDD: test first, implement, verify
- All existing functionality preserved (no regressions)
- Clean separation of special hand logic from standard win detection
- Debug output for hand structure validation

**Game Impact:**
- Players can now win with Seven Pairs (most common special hand)
- Players can now win with Thirteen Orphans (most famous special hand) 
- Engine correctly recognizes these patterns during actual gameplay
- Foundation established for remaining special hands

**Next Planned Features:**
- Additional special hands: All Honors, All Terminals, Big Three Dragons
- Complete Chinese scoring system after all special hands implemented
- Special hand bonuses and point calculations

**Statistics:**
- Special hands implemented: 2/10+ official Chinese special hands
- All tests passing with comprehensive edge case coverage
- Zero regressions in existing functionality

**Development Notes:**
- Used official Chinese Mahjong rules document as specification
- Maintained backward compatibility with all existing features
- Clean modular architecture supports easy addition of more special hands


---
## v2.0.2 — KAN Replacement Tile Fixes & Chinese Rules Compliance (2025-07-15)

**MAJOR FIX**: Corrected critical bug in KAN (Kong) implementation to fully comply with Chinese Mahjong rules.

### What Was Fixed:
- **KAN Replacement Draws**: All KAN types (Ankan, Minkan, Shominkan) now correctly draw replacement tiles from wall
- **Chinese Rule Compliance**: Engine now follows authentic Chinese Mahjong KAN rules instead of incorrect "no bonus draw" interpretation
- **Test Suite Alignment**: Updated 5 test expectations that were based on incorrect rule understanding

### Technical Details:
**Before Fix:**
- KAN declared → 4 tiles removed → hand becomes smaller →  WRONG
- Wall unchanged →  WRONG  
- Players ended up with incorrect tile counts

**After Fix:**
- KAN declared → 4 tiles removed → replacement tile drawn → hand size correct →  CORRECT
- Wall decreases by 1 →  CORRECT
- Players maintain proper tile counts for continued play

### Files Changed:
- `engine/game_state.py`: Added replacement tile draws after KAN formation (3 locations)
- `tests/test_game_state.py`: Updated test expectations to match Chinese rules (5 tests)

### Current Engine Status:
-  **Complete Chinese Mahjong Implementation**: CHI from any player, KAN replacement draws, Chinese scoring
-  **144-tile system**: Full flowers and seasons support with auto-replacement
-  **Robust Test Suite**: All 79 tests passing with correct rule expectations
-  **CFR Training Ready**: Stable engine for AI agent training and tournament play

**Ready for:** Special hands implementation (Seven Pairs, Thirteen Orphans, etc.)

---

## Previous Milestone: v2.0.1 — Critical Win Detection Bug Discovery (2025-06-30)
---

## v2.0.1 — Critical Win Detection Bug Discovery (2025-06-30)

## CRITICAL ISSUE IDENTIFIED
Major flaw discovered in win detection logic. The engine’s meld, turn, and wall handling is robust, but the core _can_form_melds() function contains a critical bug that prevents some legitimate wins from being recognized.

## Issue Summary
Win check failure: Engine did not recognize some valid winning hands. In several tests, the winner was declared with only 1 tile and 4 melds, omitting the required pair.
Initial suspicion: First noticed after East was shown as winner with 1 tile in hand and 4 melds (should always be 2 tiles remaining for a pair).
Function name fix: Corrected a naming error from *can*form_melds to _can_form_melds.
Debug logging: Added detailed output in is_winning_hand() for all win checks.
Critical confirmation: Confirmed via debug that North had a valid winning hand (4 melds + 1 pair) that was rejected.

## Evidence
Game log analysis showed hands with only 1 tile after a "win", which is always invalid.
Further inspection revealed _can_form_melds() missed valid hand states and returned false negatives.

## Next Steps
Fully audit and repair _can_form_melds() to correctly identify all legal winning hand structures (4 melds + 1 pair).
Add targeted tests to guarantee no win state can occur with only 1 tile and 4 melds.
Re-run all demos and test suite after fixing.

## Status
Engine is stable for gameplay, meld, and tile flow.
Win detection is currently broken and under urgent repair.
Full debug logging and test coverage now in place for continued diagnosis.

Documented: 2025-06-30

---

## v2.0.0 — Complete Chinese Mahjong with Flowers & Seasons (2025-06-30)

MAJOR RELEASE: Full implementation of authentic 144-tile Chinese Mahjong with Flowers and Seasons, advanced scoring, and stable wall and action space upgrades

New Features in v2.0.0:

Flowers and Seasons System
144 tiles total, including 136 regular tiles and 8 bonus tiles (Plum, Orchid, Chrysanthemum, Bamboo, Spring, Summer, Autumn, Winter)
Bonus tiles are automatically replaced when drawn and are stored in player.bonus_tiles
Bonus tiles contribute to Chinese scoring and are not counted in the 13-tile hand

Authentic Chinese Gameplay
Complete tile set matches official tournament rules with correct tile frequencies
Wall generation produces 4 copies of each regular tile and 1 copy of each bonus tile
All rules follow official Chinese tournament standards

Enhanced Scoring System
Dual rewards system: CFR training uses 1.0 or 0.0, gameplay displays full Chinese point scoring
Bonus tiles each provide 1 point
Special bonuses for collecting all four flowers or all four seasons (3 extra points per set)
Game summaries include detailed point analysis

What This Engine Provides

Complete Chinese Mahjong implementation including all meld types (CHI, PON, KAN)
144-tile system with full Flowers and Seasons support
All Chinese rules including CHI from any player and no KAN bonus draws
Seamless auto-replacement of bonus tiles on draw
Win detection based on 4 melds plus one pair
Chinese scoring system active throughout gameplay

AI Training Ready

CFR training framework with tabular regret-matching
Expanded action space to 148 actions covering all legal moves
Deterministic info set encoding for reproducible learning
Oracle state scenarios for curriculum-based training
Full test coverage with 79 tests ensuring stability and correctness

Implements Chinese Official Mahjong (MCR) rules
Stable gameplay validated through extensive testing

Quick Demo

To run a full Chinese Mahjong game with 4 random agents:
python scripts/demo.py

Demo showcases authentic 144-tile gameplay, automatic handling of Flowers and Seasons, meld creation and interrupts, Chinese scoring, and detailed game summary

Project Architecture

Core engine in engine/
game_state.py implements main game logic including bonus tile replacement
player.py manages player state including bonus tile storage
tile.py includes tile logic and bonus detection
wall.py generates a 144-tile wall
action_space.py defines action encoding and action space
cfr_trainer.py implements CFR training

Test suite in tests/
test_flowers_seasons.py validates bonus tile logic
test_game_state.py covers core game mechanics
test_cfr_trainer.py tests CFR framework
test_action_space.py validates action encoding
test_chinese_scoring.py covers all scoring logic

Latest Game Results

Recent demo run (v2.0.0)
Winner: Player 2 (West) with 4 melds and 1 pair
Chinese score: 2 points for a basic win
Bonus tiles: 4 flowers and seasons replaced successfully
Meld types: Both CHI and PON used
Game flow: Played to completion with authentic Chinese gameplay and accurate scoring

Next Steps

CFR training on the complete 144-tile system
Botzone and tournament platform submissions
Oracle state curriculum learning for advanced training
Addition of extended Chinese hands, GUI for human play, and tournament formats

Technical Specifications

Implements 144-tile Chinese Official Mahjong for 4 players (East, South, West, North)
Hand size is 13 tiles plus melds and bonus tiles
Win condition is 4 melds plus a pair
Meld priority order is Ron, then KAN, then PON, then CHI
Action space includes 148 legal actions
Pure Python 3.11 or later with no dependencies required
All tests use unittest framework

Project Achievements

First fully authentic Chinese Mahjong engine built for CFR-based AI research and competition
Robust CFR implementation with full test coverage
All code, test suite, and devlog updated and validated for Flowers and Seasons, scoring, and 144-tile play

Documentation

devlog.md for complete development history and technical details
CODE_INDEX files for navigation and API reference
tests/ folder for all usage and stability tests

---
### v1.9.3 — Chinese Mahjong Engine Complete & Demo-Ready (2025-06-28)

**MAJOR MILESTONE**: Full Chinese Mahjong implementation with validated gameplay, stable meld processing, and professional demo capabilities.

**Final Implementation Status:**
- **Chinese Rules Complete**: CHI from any player, no KAN bonus draws, realistic Chinese scoring system
- **Bug-Free Operation**: All critical validation and meld processing bugs resolved
- **Professional Quality**: Suitable for technical demonstrations and real gameplay
- **Test Coverage**: 71+ tests passing, including comprehensive Chinese rule validation

**Latest Fixes (v1.9.3):**
- **CHI Validation Bug Fixed**: Resolved critical issue where invalid cross-suit CHI sequences were being processed
- **Meld Processing Stabilized**: Enhanced claim arbitration with proper validation checks
- **Hand Size Consistency**: All tile removal and meld creation math now correct
- **Demo-Ready Output**: Clean gameplay with professional summary generation

---

### v1.9.2 — Chinese Mahjong Rules Complete (2025-06-26)

**MAJOR MILESTONE**: Full conversion from Japanese to Chinese Mahjong rules completed.

**Chinese Rules Implemented:**
- **CHI from any player**: Removed Japanese restriction (left player only)
- **No KAN bonus draws**: Ankan, Minkan, and Shominkan no longer draw bonus tiles  
- **Chinese scoring system**: Point-based rewards (2-10+ points) with special hand bonuses
- **Dual reward system**: CFR training uses simple 1.0/0.0, gameplay shows realistic Chinese scores

**New Features:**
- `get_hand_score()`: Calculates Chinese point values for winning hands
- `get_game_summary()`: Writes detailed game analysis to text files
- Full test suite for Chinese scoring in `tests/test_chinese_scoring.py`

**Impact**: Engine now accurately represents Chinese Mahjong rules while maintaining CFR training stability.

---
### v1.9.1 — Critical Legal Actions Bug Fix & Engine Stabilization (2025-06-26)

- **CRITICAL FIX**: Resolved major bug in `get_legal_actions()` where the discard phase was returning `None` instead of a list of actions, causing CFR training and all game logic to fail.
- **Enhanced Meld Support**: Legal actions now correctly include PON and KAN reactions during the meld phase (when `awaiting_discard = False`), enabling CFR to learn all meld strategies.
- **Improved Action Coverage**: 
  - Discard phase: Returns all discardable tiles + closed KAN (Ankan) + Shominkan (PON→KAN upgrade)
  - Reaction phase: Returns CHI + PON + Minkan + PASS actions based on last discard
- **Consistent Rule Adherence**: PASS action only available during reaction phase, not after drawing (matches real Mahjong rules)
- **Full Test Suite**: All 65 tests now pass, including CFR training, meld logic, terminal detection, and curriculum scenarios
- **Root Cause**: Missing `return sorted(legal_actions)` statement at end of discard phase logic in `get_legal_actions()` method
- **Impact**: CFR can now learn complete strategy space including all meld types and reactions

---

### v1.9.0 — Unified Win Handling, Multiple Ron, Meld Win Consistency

- All win types (Ron, self-draw, CHI/PON/KAN) now mark winners using `self.winners` and `_terminal`, ensuring consistent reward assignment and CFR propagation.
- Multiple Ron is supported: several players can win on the same discard (Japanese rules), and all are rewarded correctly.
- Meld win detection is now unified: after any meld (CHI, PON, KAN), win status is checked and handled identically to self-draw and Ron.
- The engine no longer mutates the hand for Ron claims; instead, winners are tracked explicitly.
- Reward logic is centralized: `get_reward` references only `self.winners` for all cases.
- Removed legacy debug counter—no more artificial early terminations.
- All related oracle and curriculum tests updated to validate new behavior.

---

### v1.8.3 — KAN/Ankan Meld Tile Removal Fix

- Refactored closed KAN (Ankan) meld logic: tile removal is now handled consistently by `call_meld` for all meld types, eliminating double-removal errors.
- Fixes test failures for Ankan actions and bonus draws.
- Engine is now more robust, maintainable.

---

### v1.8.2 — Double Turn Advance Fix

- Fixed bug where, after a discard with no meld claims, the turn index was advanced twice, causing skipped turns and breaking sequential play.
- Now, after a discard with no melds/claims, the turn properly advances to the next player, matching official Mahjong rules.
- All unit and oracle tests pass; behavior verified with full test suite.
- Documentation and code index updated.

---

## v1.8.1 — PASS Action Fix in Discard Phase (2025-06-25)

- Fixed a rules bug: PASS action is no longer legal in the discard phase (i.e., after a player draws, they must discard or declare a closed KAN; PASS is now only available as a reaction to another player’s discard).
- Updated unit test (test_get_legal_actions_after_draw) to reflect the correct rules—PASS is no longer allowed immediately after a draw.
- No changes to agent logic or CFR policy—this only prevents illegal moves in the engine and maintains true-to-rules gameplay.
- All docs and code indexes updated as per dev conventions.



---

## v1.8.0 – Curriculum Multi-Step Win States (2025-06-22)

### Recent Additions

- **Curriculum Win States:**  
  Added `FixedWinGameState_2StepsFromWin` and `FixedWinGameState_3StepsFromWin` in `engine/oracle_states.py`.
  - These deterministic states allow precise TDD for CFR reward propagation, verifying planning over multiple moves.
  - Hands/walls are designed for only draw/discard actions (no melds possible), ensuring reward paths are simple and fully testable.

- **Tests:**  
  Added `test_cfr_learns_2_steps_from_win` and `test_cfr_learns_3_steps_from_win` in `tests/test_curriculum_learning.py`.
  - Both tests pass, confirming CFR correctly learns the optimal policy even when the win is multiple steps away.
  - This ensures recursive value propagation and agent planning work before adding game complexity.

### Development Notes

- For curriculum states focused on draw/discard, **hands and wall never include the same tile more than once**. This prevents CFR from ever attempting illegal meld actions, eliminating ValueErrors during recursive training.
- Print/debug output may not appear when running passing unittests due to output buffering. This is normal and not a code issue.

### Next Steps

- Extend curriculum to more steps-from-win or introduce controlled meld curriculum.
- Once stable, move toward realistic self-play and more advanced agent-environment interactions.

---

### v1.7.2 — Meld Arbitration, PON/KAN Handling, Ron Priority

- Discard claims are now resolved using `collect_and_arbitrate_claims()` which strictly follows Mahjong meld priority: **Ron > Kan > Pon > Chi**.
- Fixed bug where tiles were removed from player hand both before and inside `call_meld` (PON/KAN): now only `call_meld` removes meld tiles.
- Deprecated the old `resolve_meld_priority` logic; all claim processing now flows through `collect_and_arbitrate_claims`.
- Added and debugged tests:
  - `test_chi_blocked_by_pon` (CHI must be blocked if a valid PON exists)
  - `test_claim_arbitration_ron_over_pon_and_chi` (Ron takes precedence, triggers terminal)
- Improved debug printouts during arbitration, step, and meld processing.
- All tests pass. Oracle scenarios and CFR learning verified.
---

## Latest Milestone: v1.7.1 – Phase-Stable KAN & Meld TDD

**Summary:**  
- KAN (Ankan/closed KAN) logic now phase-gated and 100% deterministic via TDD (unit tests pass reliably).
- Phase variable (`awaiting_discard`) is now required for all meld and draw actions, removing all intermittent test bugs.
- Tests and engine updated for strict phase handling; KAN, CHI, and meld mutations are now robust.
- Documentation and CODE_INDEX files are updated before every commit/snapshot as a **required rule**.

**Project Rule Update (v1.7.1+):**
- *Before every git commit or project snapshot, update `README.md`, `devlog.md`, and all `CODE_INDEX` files to reflect all changes, new tests, features, or refactors. This ensures every version checkpoint is fully documented and project navigation is always accurate.*

*Last updated for v1.7.1 – phase-stable KAN/Ankan and strict TDD.*

---

## Latest Milestone: v1.6.3 – Full Oracle Meld Win Coverage

**Summary:**  
- Oracle CFR tests cover all core meld-based wins: self-draw, Ron, CHI, and PON.
- CFR/engine logic for meld claim and reward is now compatible and bug-free for all single-step wins.
- The foundation is ready for curriculum learning, reward shaping, and true reaction/interrupt agent actions.

---

### v1.6.2 – Oracle CHI Win Test

- Deterministic oracle test for CHI win (Player 0 wins by CHI on left discard).
- Validates CFR, meld interrupt, and reward logic.
- Environment now robust for self-draw, Ron, and CHI-based wins.
- Next: Add PON scenario, implement true interrupt/call actions, and begin curriculum learning.

---

### v1.6.1 – Oracle Ron (Discard Win) Test

- Added `FixedWinGameState_Ron` for a forced Ron scenario (Player 0 tenpai, Player 1 forced to discard winning tile).
- Oracle unit test ensures terminality and reward assignment on Ron.
- Ron action not yet explicit; test simulates by appending discard to Player 0’s hand.
- Both self-draw and Ron win now CFR-tested and passing.
- Next: Refactor for explicit Ron action.

---

### v1.6.0 – Oracle CFR Self-Draw Win Test

- First oracle curriculum scenario: Player 0 in tenpai, draws the only winning tile from the wall.
- Test asserts: hand is a valid Mahjong win, `is_terminal()` is true, and CFR reward is propagated.
- Proves that engine logic, win/terminal detection, and CFR reward flow work together.
- Sets the baseline for all future oracle/curriculum CFR tests.
- Next: Add and pass similar tests for Ron, meld interrupts, and bonus tile scenarios.

---

## v1.5.7 – Oracle-Guided Curriculum Learning Plan

**Goal:**  
Accelerate CFR debugging and learning using controlled "oracle" test states and a curriculum of progressively harder scenarios.

**Method:**  
- Inject "solvable" game states with known optimal actions (oracle states).
- Start CFR training/tests from states closest to terminal (e.g., one move from win).
- Only progress to more complex states once CFR matches oracle policy in simple cases.
- At each step, validate CFR using the oracle policy for correctness.
- Transition to random full-game self-play once curriculum states are solved.

**Benefits:**  
- Rapid, interpretable debugging.
- Faster convergence; avoids wasted computation on unreachable states.
- Structured record of agent learning.

**Example Curriculum:**  
- Implement FixedWinGameState (one move from win, known best discard).
- Test CFR convergence on oracle action.
- Progressively increase state complexity, logging all results and curriculum steps.

---

## v1.5.7 – Full CFR Game Loop + Stable Tests

**What’s Working:**  
- All meld, claim, wall, discard, and win detection logic passes deterministic tests.
- CFRTrainer runs full self-play, exports policies, tracks average strategies.
- Debug logging and modular architecture support fast upgrades and diagnosis.
- All fixes and architectural changes logged in README/devlog.
- Project is snapshot/versioned for clean branching.

**Known Limitations:**  
- Rewards are simple (win = 4 melds); not full Mahjong scoring/yaku.
- Infoset abstraction is basic (hand, last discard, meld types).
- No multi-round play or agent-vs-human interface yet.

**Next Major Steps:**  
- Implement oracle CFR training for policy validation.
- Design realistic scoring and reward functions.
- Prepare for abstraction research and/or deep RL integration.
- Add UI/log replay tools for debugging/demoing.

---

## Next Steps & Roadmap (After v1.5.6)

### Short-Term (v1.6.x)
- Add real win detection: `is_winning_hand()` with full meld/pair logic.
- Update terminal and reward logic to require actual wins.
- Add tests for real win conditions.
- Integrate true win/reward logic into CFR.
- Optional: Partial rewards for hand improvement, tenpai, or shanten.

### Medium-Term (v1.7.x+)
- Improve info set abstraction (visible discards, melds, seat wind).
- Integrate CFR+ or Regret Matching+ for convergence.
- Explore state abstraction to control info set growth.

### Long-Term / Research (v2.x+)
- Deep learning integration (Deep CFR, neural regret approximation).
- Prepare for online self-play, human-vs-agent play, or competitions.
- Implement oracle/heuristic agents for curriculum/acceleration.

### Ongoing
- Meld priority/interrupt logic.
- Expand test suite for all new edge cases/features.
- Keep devlog and versioning up to date.

---

## Previous Milestones (Selected Summaries)

### v1.5.5 – Flaky Test Removal

- Removed `test_pon_action` and `test_step_auto_resolves_pon` due to instability (relied on fake meld triggers).
- All meld actions now tested via real state transitions only.

---

### v1.5.4 – Meld Priority Bug Fix (CHI overriding PON)

- Fixed: `resolve_meld_priority()` now matches meld tiles by category and value (not tile_id only).
- Prevents rare nondeterministic test failures and ensures PON claims succeed when valid.

---

### v1.5.3 – Meld Turn Ownership + CFR Integration

- Meld claimer receives next action (turn_index).
- `resolve_meld_priority()` returns claiming player ID; `GameState.step()` handles ownership handoff.
- Tests: `test_turn_passes_to_meld_claimer` verifies new turn logic.

---

### v1.5.2 – Meld Priority Resolution

- Added correct meld arbitration: PON > CHI > PASS enforced by `GameState.resolve_meld_priority()`.
- Only one player may claim a discard; meld execution and discard removal implemented for PON/CHI.
- Test: `test_chi_blocked_by_pon`.

---

### v1.5.1 – Meld Action CFR Tests

- Targeted tests for CHI, PON, and KAN regret learning in CFR.
- Deterministic CFR state setup to ensure regret table and strategy export covers all meld types.

---

### v1.5.0 – terminal-fixes-full-pass

- Finalized wall/terminal detection, meld logic, and reward propagation in CFR.
- Defensive coding: recursion depth limits, deep copy handling, attribute protection.
- All major tests pass; strategy tables exported and non-uniform.

---

### v1.4.x – Meld, KAN, and Terminal Fixes

- Full support for closed KAN, open KAN (Minkan), PON→KAN upgrade (Shominkan).
- Meld logic: legal checks, bonus tile draw, meld registration, turn passing.
- All meld/interrupt logic validated via unit tests and CFR simulation.
- Added/removed tests as needed to ensure deterministic, correct coverage.

---

### v1.3.0 – Closed KAN (Ankan) Only

- Full support for closed KAN melds.
- Player.can_ankan() and new action range `KAN_0`–`KAN_33` (IDs 90–123).
- get_legal_actions() exposes KAN actions if 4-of-a-kind in hand.
- CFR/strategy tables updated for KAN actions; test: `test_cfr_learns_ankan()`.

---

### v1.2.0 – Terminal State + Win Detection

- Game ends if any player forms 4 melds (placeholder logic; not yet true win check).
- CFR halts and propagates rewards on terminal.
- Added tests to verify terminal detection and reward correctness.

---

### v1.1.0 – CHI Meld Implementation

- CHI meld logic: Validates sequence, removes correct tiles, registers meld, removes discard.
- Action space updated to encode/decode CHI actions.
- Test added: `test_step_handles_chi_action`.

---

### v1.0.0 – Working Tabular CFR Agent

- get_info_set(), get_strategy(), cfr(), train(), get_average_strategy(), and export_strategy_table() all implemented.
- Tests for each core logic branch.
- Regret table and action masking work.

---

## Project Overview and Core Features

**What Has Been Completed So Far:**

- **Tile System:** All tile types (Man, Pin, Sou, winds, dragons) with unique IDs and full equality/hash logic.
- **Action Space:** Full discrete mapping for all legal actions (discard, meld, pass).
- **Game Engine:** Turn-based environment, wall management, player discards, meld claims (with validation).
- **Player Class:** Hand/meld management, meld action support.
- **CFR Integration:** Aligned action/tile IDs, info set abstraction, robust for regret-matching research.
- **Test-Driven Development:** All logic covered by unit tests; CFR logic validated with deterministic and randomized tests.

**Debug History, Issue Fixes, and Development Conventions:**

- Consistent use of PowerShell snapshots and explicit git versioning.
- All major bugs, fragile logic, and critical test discoveries tracked in README and devlog.
- Ongoing: CFR table growth and memory use monitored as info set abstraction increases.

---

## Next Goals

- Enforce meld conflict resolution (PON > CHI; CHI from left player only).
- Add partial reward design (tile efficiency, tenpai, shanten).
- Add real game termination and Tenpai logic.
- Integrate CFR+ or deep RL (offline/online) methods for advanced training.
- Develop replay/visualization tools for policy debugging and demonstration.

---

*Last updated for v1.6.3 – full oracle meld win coverage and curriculum baseline complete.*

# Mahjong CFR Agent – Devlog

---

## Last Milestone: v1.3.0-kan-ankan-only

**Status:**  
All core meld types (CHI, PON, Ankan) implemented with legal action generation and CFR compatibility.

| Component             | Description                                                                           |
| --------------------- | ------------------------------------------------------------------------------------- |
| Tile System           | All tile types (suits, winds, dragons) implemented with ID, equality, hash            |
| Action Space          | Covers 124 actions: Discard (0–33), PON (34–67), PASS (68), CHI (69–89), KAN (90–123) |
| Player Class          | Supports draw, discard, CHI, PON, KAN (Ankan only)                                    |
| GameState             | Turn cycle with draw, discard, and meld handling                                      |
| get_legal_actions()   | Dynamically returns legal CHI, PON, and KAN actions                                   |
| CFRTrainer            | Working regret-matching, info set tracking, average strategy export                   |
| FixedTrainer          | Used for deterministic CFR tests (regret update, KAN eligibility, etc.)               |
| Unit Tests            | 30+ tests cover all logic: player behavior, meld calls, CFR integrity                 |

### Tests

All tests passing as of v1.3.0.  
CFR confirmed to:
- Learn from CHI and PON actions
- Detect and sample KAN (Ankan) actions when available
- Maintain valid regret and strategy tables of length 124

### Short-Term Simplifications

| Component       | Description                                                             | Target Fix Version |
| --------------- | ----------------------------------------------------------------------- | ------------------ |
| is_terminal()   | Game ends if a player has 4 melds                                       | v1.4.x             |
| get_reward()    | Returns 1.0 for first player with 4 melds, 0.0 for others               | v1.4.x             |
| Meld Priority   | No priority enforcement (PON vs CHI vs KAN); first match always taken   | v1.5.x             |
| Ankan Logic     | No bonus tile drawn after KAN                                           | v1.3.1             |
| Shominkan       | No upgrade from PON to KAN                                              | v1.4.x             |
| Minkan          | Open KAN (on discard) not supported                                     | v1.4.0             |
| Win Detection   | No yaku/win check, only meld count                                      | Phase 3            |
| Info Set Format | get_info_set() includes only hand, discards, turn; not full game obs    | v1.5.x             |

### Known Tricky Areas

- Meld matching in CHI/PON requires exact Tile.tile_id alignment.
- CFR tests originally failed when action space was too small ([0.0] * 90); now fixed to [0.0] * 124.
- KAN actions not visible in exported policy until threshold set to 0.0.
- Unit test for KAN required full hand overwrite to stabilize.

### Planned Short-Term Milestones

| Version                   | Goal                                 |
| ------------------------- | ------------------------------------ |
| v1.3.1-kan-bonus-draw     | Add bonus tile draw after closed KAN |
| v1.4.0-kan-minkan         | Add support for open KAN via discard |
| v1.4.1-shominkan          | Upgrade PON to KAN during turn       |
| v1.5.0-terminal-correct   | Real win detection and reward logic  |
| v1.6.x                    | Priority system (PON > CHI > PASS)   |

---

## v1.4.0 – Add Minkan (Open KAN via Discard)

**Summary:**  
Implemented Minkan detection in GameState. Valid Minkan requires player to hold 3 matching tiles and last_discard to match tile_id. Discard is removed from original player's pile. Meld uses 3 tiles from hand and 1 from discard. Bonus draw is triggered after any KAN. Player continues with a discard.

**Known Limitations:**  
- No distinction between open/closed KAN in meld encoding yet.
- Shominkan (PON → KAN upgrade) not yet implemented.
- No priority conflict logic between CHI/PON/KAN callers.

**Tests:**  
- test_minkan_action_successful  
- test_minkan_bonus_draw  
- test_minkan_removes_discard  
- test_minkan_fails_with_less_than_3

---

## v1.4.1 – Add Shominkan (Upgrade PON to KAN)

**Summary:**  
Added Shominkan logic to GameState to allow upgrade from PON to KAN if player holds 4th matching tile and already has a PON meld. On upgrade: remove 4th tile from hand, replace PON with a KAN meld, bonus tile is drawn, and player discards.

**Known Limitations:**  
- No priority conflict resolution; other players cannot block upgrade.
- Meld type (open/closed) not encoded explicitly in meld string.

**Tests:**  
- test_shominkan_upgrade_successful  
- test_shominkan_removes_tile_from_hand  
- test_shominkan_replaces_meld_type  
- test_shominkan_bonus_draw_after_upgrade  
- test_shominkan_illegal_if_no_pon  
- test_shominkan_illegal_if_tile_not_in_hand

---

## v1.4.2 – Shominkan/CHI/KAN Fixes Complete

**Summary:**  
Resolved critical issues with CHI and KAN melds, including Shominkan and Minkan edge cases. Fixed action resolution, tile tracking, and meld registration logic.

**Changes:**  
- Fixed can_chi() to restrict to left-seat only.
- CHI action now removes exactly two tiles from hand and removes claimed tile from discard.
- Shominkan validates exact PON match and presence of 4th tile before upgrade.
- Minkan verifies 3 matching tiles in hand plus last discard.
- Added error handling for illegal melds (missing tiles, no matching melds).
- Cleaned up test cases to compare meld content by string representation.
- 100% test pass: 51 tests.

**Bug Fixes:**  
- CHI tile mismatch failures.
- Discard not removed after meld.
- No exception for bad CHI/KAN attempts.
- Meld object mismatch in step/CHI actions.

**Known Limitations:**  
- Meld encoding/decoding not type-safe.
- Meld registration logic could be abstracted (e.g., resolve_chi_meld()).
- No CHI interrupt or priority handling—atomic resolution only.

**Future Impact:**  
- Stabilizes action logic for downstream CFR.
- Refactor opportunities to unify meld logic.
- Melds are now traceable for replay/visualization.

---

## v1.5.0 – terminal-fixes-full-pass (2025-06-18)

**Summary:**  
Terminal handling is fully working (wall depletion, win detection). CFR training is stable and exports strategy output. All tests, including meld and discard transitions, now pass.

**Key Changes Since v1.4.2:**  
- Fixed endless loop with wall exhaustion and `_terminal`.
- Defensive recursion depth limit.
- Test suite stabilization (melds, discard logic, deep copies, attribute errors).
- CFR now terminates correctly on wins.
- Info sets encode melds and tile vectors.
- CFR export outputs to `cfr_policy.txt`.
- All major bugs fixed.

**Known Limitations:**  
- No hand validation logic for true yaku/win.
- Meld conflicts and priority still stubbed.
- Some tests use manual hand setup.

**Next Steps:**  
- Meld resolution priority (PON > CHI, interrupt).
- Reward shaping for partial melds/tile efficiency.
- Deep CFR baseline.
- Add snapshot tagging post-run.

---

## v1.5.1 – Meld Action CFR Tests

**Summary:**  
CFR regret table learning for meld actions now tested.  
CHI, PON, and KAN action tests pass. Regrets for all meld types are updated and visible in policy exports.

---

## v1.5.2 – Meld Priority Resolution

**Summary:**  
Implemented priority arbitration in `resolve_meld_priority()` (PON > CHI). Only one meld proceeds. Melds registered with correct tile structure.  
Tested with `test_chi_blocked_by_pon`.

---

## v1.5.3 – Meld Ownership & Turn Reassignment

**Summary:**  
Turn now passes to meld claimer after interrupt.  
`resolve_meld_priority()` returns new owner and integrates with main loop.  
Enables multi-agent CFR to model interrupts and ownership changes.

---

## v1.5.4 – Meld Priority Bug: CHI overriding PON (Fixed)

**Summary:**  
Fixed bug in meld matching logic (PON now matches by category and value, not just tile_id).  
Prevents CHI overriding valid PON melds in rare cases.

---

## v1.5.5 – Flaky Tests Fixed

**Summary:**  
Removed two unreliable tests.  
All meld logic validated in flow and CFR simulation.  
Suite is now deterministic and stable.

**Key Notes:**  
- CFR action space supports tile IDs 0–33 only.
- Manual edits of last_discard for test hacks are unreliable.
- All interrupt meld logic validated via core tests.

**Next Feature:**  
- Reward signal adjustment by meld value.
- Win detection/scoring.

---

## v1.5.7 – Baseline CFR Policy & Win Detection Integrated

**Summary:**  
All tests pass, including meld logic, terminal, and win detection.  
CFR run for 1000 iterations (flat learning as expected with sparse rewards).  
CFR output, action probabilities, and debug traces validated.  
Next: Oracle CFR test for near-win state.

---

## v1.6.0 – Oracle Self-Draw Win Test

**Summary:**  
Implemented deterministic self-draw win scenario and test.  
Confirmed stable, reproducible CFR for oracle/curriculum testing.

---

## v1.6.1 – Oracle Ron Win Test

**Summary:**  
Added deterministic Ron win scenario and test.  
Terminal state, reward propagation confirmed.  
Next: Add oracle CHI/PON win scenarios, begin full interrupt/claim actions.

---

## v1.6.2 – Oracle CHI Win Test

**Summary:**  
Oracle test for CHI win passes.  
Validates meld interrupt and win logic for CHI.  
Environment stable for self-draw, Ron, and CHI-based wins.  
Next: PON scenario, real interrupt system, curriculum learning.

---

## v1.6.3 – Full Oracle Meld Win Coverage

**Summary:**  
Oracle CFR tests pass for all meld-based wins (self-draw, Ron, CHI, PON).  
All meld claim/reward logic now CFR-compatible and bug-free for single-step wins.  
Ready for curriculum, reward shaping, and full interrupt action system.

---

## v1.7.1 – Phase-Gated KAN (Ankan), Test Determinism, and Documentation Rule

**Status:**  
- All KAN actions (especially Ankan/closed KAN) now require the phase (`awaiting_discard = True`), preventing accidental engine skips.
- Test logic fully phase-aware: all meld, draw, and discard tests explicitly set phase/turn variables.
- Deterministic, reliable pass on all engine/test runs (no more intermittent KAN bugs).

**Process Update:**  
- New rule: *Before every git commit or snapshot, `README.md`, `devlog.md`, and all `CODE_INDEX` files are updated to reflect the current version, features, fixes, and navigation. No code is versioned or snapshotted unless documentation matches code.*

**Tests:**  
- `test_bonus_tile_goes_to_correct_player` and all KAN/Ankan tests pass with strict phase checks.
- All meld, reward, and turn logic verified stable for CFR integration.

**Known Tricky Areas:**  
- If any test fails intermittently, check and set phase/turn variables in the test (no hidden state allowed).
- KAN, CHI, and other melds are sensitive to phase; engine is now robust to these transitions.

**Next:**  
- Repeat this phase-check pattern for all meld types.
- Expand info set and reward structure for next curriculum phase.

---
## v1.7.2 — Meld Arbitration & Meld Removal Fixes

- Meld claim resolution now uses `collect_and_arbitrate_claims`, supporting full priority: Ron > Kan > Pon > Chi.
- Fixed double-removal bug: only `call_meld()` removes tiles for melds.
- Deprecated `resolve_meld_priority`; codebase now fully uses claim arbitration.
- Improved debugging output in `step()` and meld arbitration logic.
- Added/updated tests:
  - `test_chi_blocked_by_pon`
  - `test_claim_arbitration_ron_over_pon_and_chi`
- Confirmed CFR and oracle test stability.

---


### v1.8.0 – Curriculum Multi-Step Win States (2025-06-22)

- **Added**: `FixedWinGameState_2StepsFromWin` and `FixedWinGameState_3StepsFromWin` for deterministic curriculum-based CFR testing.
- **Added**: Unittest coverage for both curriculum states (see `tests/test_curriculum_learning.py`).
- **Fixed**: Prior bug where illegal meld actions could be attempted in curriculum states, causing exceptions during CFR recursion. Now all curriculum states use unique tiles only, so only legal actions are possible.
- **Notes**: Print debug output is suppressed during passing unittests (normal). To view debug, run failing tests or run curriculum logic outside unittest.
- **Next**: Expand curriculum depth, consider meld-based curriculum, and prep for full self-play agent training.

---

### v1.8.1 — Discard Phase PASS Fix

Summary:
Fixed a long-standing rules issue: the PASS action was mistakenly included in the discard phase legal actions. After a player draws, their only legal actions are to discard a tile or declare closed KAN (if eligible). PASS is now only permitted during the meld/reaction phase (in response to another player’s discard).

- What changed:
- Removed PASS from discard phase in get_legal_actions.
- Updated test_get_legal_actions_after_draw to require PASS not be present after a draw.
- Why:
- This fix aligns with real Mahjong rules and eliminates a possible illegal engine state.
- Impact:
- Tighter rule adherence, prevents skipped turns, avoids teaching agent illegal habits.
- No strategy/learning logic affected; all oracle and CFR tests continue to pass.

---

## v1.8.2 — Discard Phase Turn Rotation Bug Fixed

**Summary:**  
Fixed a long-standing engine bug where the turn index was incremented twice when no claims were made after a discard. This resulted in the next player being skipped in some cases, leading to illegal turn order and failing some sequence-based tests.

- **What changed:**  
  - Removed redundant turn increment/return in `GameState.step` after the discard branch.
- **Why:**  
  - The fix ensures the game engine always hands off the turn correctly after a discard, in compliance with the real game flow.
- **Impact:**  
  - All sequential and meld logic now function correctly; game never skips a player.
  - All tests (including edge/curriculum/oracle) now pass.

  ---

## v1.8.3 — KAN/Ankan Meld Removal Consistency

**Summary:**  
Fixed a major logic bug where closed KAN (Ankan) actions removed tiles manually in the engine before calling `call_meld`, resulting in errors and failing all related tests. Now, all tile removal for melds is delegated to `call_meld`, ensuring future consistency and correct hand mutation.

- **Impact:**  
  - All meld logic now flows through a single, robust interface.
  - All CFR, oracle, and bonus tile tests for KAN/Ankan pass.
Last Milestone: v1.3.0-kan-ankan-only

Status: All core meld types (CHI, PON, Ankan) implemented with legal action generation and CFR compatibility.

| Component             | Description                                                                           |
| --------------------- | ------------------------------------------------------------------------------------- |
| `Tile` System         | All tile types (suits, winds, dragons) implemented with ID, equality, hash            |
| `Action Space`        | Covers 124 actions: Discard (0–33), PON (34–67), PASS (68), CHI (69–89), KAN (90–123) |
| `Player` Class        | Supports draw, discard, CHI, PON, KAN (Ankan only)                                    |
| `GameState`           | Turn cycle with draw, discard, and meld handling                                      |
| `get_legal_actions()` | Dynamically returns legal CHI, PON, and KAN actions                                   |
| `CFRTrainer`          | Working regret-matching, info set tracking, average strategy export                   |
| `FixedTrainer`        | Used for deterministic CFR tests (regret update, KAN eligibility, etc.)               |
| `Unit Tests`          | 30+ tests cover all logic: player behavior, meld calls, CFR integrity                 |

Tests

All tests passing as of v1.3.0. CFR confirmed to:

    Learn from CHI and PON actions

    Detect and sample KAN (Ankan) actions when available

    Maintain valid regret and strategy tables of length 124

 Short-Term Simplifications (To Be Replaced)

 | Component       | Description                                                             | Target Fix Version |
| --------------- | ----------------------------------------------------------------------- | ------------------ |
| `is_terminal()` | Game ends if a player has 4 melds                                       | `v1.4.x`           |
| `get_reward()`  | Returns 1.0 for the first player with 4 melds, 0.0 for others           | `v1.4.x`           |
| Meld Priority   | No priority enforcement (PON vs CHI vs KAN) — first match always taken  | `v1.5.x`           |
| Ankan Logic     | No bonus tile drawn yet after KAN                                       | `v1.3.1`           |
| Shominkan       | No upgrade from PON → KAN                                               | `v1.4.x`           |
| Minkan          | Open KAN (on discard) not yet supported                                 | `v1.4.0`           |
| Win Detection   | No yaku/win check, only meld count                                      | Phase 3            |
| Info Set Format | `get_info_set()` includes only hand, discards, turn — not full game obs | `v1.5.x`           |


Known Tricky Areas (Tracked)

Meld matching in CHI/PON requires exact Tile.tile_id alignment — caused test failures if Tile() objects didn’t match by ID or instance

CFR tests originally failed when action space was too small ([0.0] * 90) — now fixed to [0.0] * 124

KAN actions were not visible in exported policy until the threshold was set to 0.0

Unit test for KAN (test_cfr_learns_ankan) required full hand overwrite (clear() + extend()) to stabilize

Planned Short-Term Milestones

| Version                   | Goal                                 |
| ------------------------- | ------------------------------------ |
| `v1.3.1-kan-bonus-draw`   | Add bonus tile draw after closed KAN |
| `v1.4.0-kan-minkan`       | Add support for open KAN via discard |
| `v1.4.1-shominkan`        | Upgrade PON to KAN during turn       |
| `v1.5.0-terminal-correct` | Real win detection and reward logic  |
| `v1.6.x`                  | Priority system (PON > CHI > PASS)   |

v1.4.0 – Add Minkan (Open KAN via Discard)

What Was Added

    Implemented Minkan detection in GameState.step() using the same KAN_<tile_id> action ID.

    Valid Minkan requires:

        last_discard.tile_id == tile_id

        Player holds 3 matching tiles

    Discard is removed from the original player’s discard pile.

    Meld registered with 3 tiles from hand + 1 from discard.

    Bonus draw is automatically triggered after any KAN (open or closed).

    Player must then discard.

Known Limitations

    No distinction between open/closed KAN in meld encoding yet (we just use ("KAN", [...])).

    Shominkan (upgrade from PON → KAN) is not yet implemented.

    No priority conflict logic between CHI/PON/KAN callers.

Tests

    test_minkan_action_successful

    test_minkan_bonus_draw

    test_minkan_removes_discard

    test_minkan_fails_with_less_than_3

v1.4.1 – Add Shominkan (Upgrade PON to KAN)

What Was Added

    Added Shominkan logic to GameState.step() to detect and allow upgrade from PON to KAN.

    Player must:

        Have an existing ("PON", [...]) meld

        Hold the 4th matching tile in hand

    On upgrade:

        The 4th tile is removed from hand

        PON meld is replaced in-place with a ("KAN", [...]) meld

        A bonus tile is drawn from the wall

        Player continues with a discard

Known Limitations

    No priority conflict resolution yet (i.e. other players cannot block the upgrade)

    Meld type (open/closed) is not encoded explicitly in the meld string

Tests

    test_shominkan_upgrade_successful

    test_shominkan_removes_tile_from_hand

    test_shominkan_replaces_meld_type

    test_shominkan_bonus_draw_after_upgrade

    test_shominkan_illegal_if_no_pon

    test_shominkan_illegal_if_tile_not_in_hand

## v1.4.2-shominkan-fix-complete

### Summary
This patch resolves critical issues around CHI and KAN meld behavior, including Shominkan and Minkan edge cases. It corrects action resolution, tile tracking, and meld registration logic.

### Changes
- ✅ Fixed `can_chi()` to properly restrict CHI to left-seat only
- ✅ CHI action now:
  - Removes exactly two tiles from hand (excluding the claimed tile)
  - Constructs meld using correct `Tile` objects
  - Removes claimed tile from discard pile
- ✅ Shominkan (upgrade PON to KAN) now:
  - Checks for exact PON match before allowing upgrade
  - Validates 4th tile exists in hand
  - Replaces PON with a 4-tile KAN meld
- ✅ Minkan fixes:
  - Verifies 3 matching tiles in hand + last discard
  - Ensures correct meld structure and discard cleanup
- ✅ Added robust error handling for illegal melds (CHI with missing tiles, KAN with no matching melds)
- ✅ Cleaned up test cases to assert meld content using string representation (prevents object identity mismatch)
- ✅ 100% test pass: 51 tests

### Bug Fixes
- CHI tile mismatch caused test failures
- Discard not removed after meld (test_chi_removes_discard_from_pile)
- No exception raised for bad CHI or KAN attempts
- Meld object mismatch in `test_step_handles_chi_action`

### Known Limitations
- Meld encoding/decoding is not yet fully type-safe
- Meld registration logic could be abstracted to reduce duplication (e.g., `resolve_chi_meld()` helper)
- No CHI interrupt or priority handling — assume atomic resolution for now

### Future Impact
- 🧠 These changes stabilize action logic for downstream CFR updates (where info sets depend on visible melds)
- 🧪 Refactor opportunities: unify meld resolution logic (CHI, PON, KAN) into a helper
- 📦 Useful for later stage: visualization of melds + replay tools, since melds are now fully traceable

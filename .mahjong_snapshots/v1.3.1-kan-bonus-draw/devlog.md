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

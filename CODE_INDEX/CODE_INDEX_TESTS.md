## tests/fixed_meld_state.py

**Updates:** 
- Updated/rewrote: test_game_state.py — rewrote `test_chi_blocked_by_pon` to validate CHI is blocked by higher-priority PON; debugged.
- Added: test_claim_arbitration_ron_over_pon_and_chi
- Confirmed: test_oracle_scenarios.py — Ron win now correctly sets terminal and rewards.


---

**Purpose:**  
Defines a fixed, custom test game state with a known meld/discard situation for targeted CFR testing and debugging. Also includes a trainer subclass for rapid experiments on this fixed scenario.

---

### Classes:

- `FixedMeldGameState` (inherits from `GameState`)
    - **Desc:**  
      Sets up a deterministic state where Player 0 (South) has a hand ready for a CHI on a specific tile (Man 3, just discarded by North).
    - **Setup:**
        - Player 0: Custom hand with tiles enabling CHI on Man 3 (e.g., has Man 4 and Man 5).
        - Players 1–3: Empty hands.
        - Last discard: Man 3 by North.
        - Turn: South, not awaiting discard (so ready for meld claim).
    - **Use:**  
      For fine-grained CFR/meld tests, especially CHI logic and claim arbitration.

- `FixedMeldTrainer` (inherits from `CFRTrainer`)
    - **train(self, iterations=1, player_id=0):**
        - Runs CFR training loop using `FixedMeldGameState` as the root state.
        - **Purpose:**  
          Allows quick, repeated training/tests on the same meld state for debugging or curriculum steps.

---

**Notes:**
- Used to isolate and debug meld/call behavior (especially CHI) outside of full random games.
- Can be adapted for other fixed-state CFR/engine test cases.
- A prototype/example for future curriculum and oracle test states.


------------------------------
## tests/test_action_space.py

**Purpose:**  
Unit tests for the Mahjong action space definitions. Ensures all action encoding/decoding logic, action IDs, and helper functions in `engine/action_space.py` behave as expected.

---

### Class: `TestActionSpace` (inherits from `unittest.TestCase`)

- `test_discard_action_ids(self)`
    - Checks correct range and length for discard actions (0–33).

- `test_pass_action_exists(self)`
    - Verifies PASS action ID is present and mapped correctly in both ID-to-name and name-to-ID.

- `test_pon_action_ids(self)`
    - Checks PON action IDs (34–67), mapping, and naming.

- `test_chi_action_ids(self)`
    - Checks all CHI action IDs, their string names, and mappings for each suit and sequence.

- `test_encode_decode_chi(self)`
    - Verifies that encoding/decoding of CHI melds is correct for legal sequences; checks that invalid melds raise errors.

- `test_kan_action_ids(self)`
    - Checks KAN action IDs (90–123), mapping, and naming.

---

**Notes:**
- Guarantees that all action constants, mappings, and CHI encoding logic remain valid.
- Will catch changes or regressions in action space design immediately.
- Essential for long-term maintenance of the action space contract between agent, environment, and CFR.

------------------------------

## tests/test_cfr_debug.py

**Purpose:**  
Debug and smoke test for CFRTrainer’s core recursion and table-building, using a trivial game state that always terminates after one step. Used to verify that the CFR loop and strategy/utility extraction work in the simplest possible case.

---

### Class: `TestCFRDebug` (inherits from `unittest.TestCase`)

- `test_cfr_runs_to_terminal(self)`
    - **Sets up:**  
      - `FixedGameState` (subclass of GameState): `step()` always sets `_terminal = True` immediately.
      - `FixedTrainer` (subclass of CFRTrainer): overrides `clone_state` to use `copy.deepcopy`.
    - **Tests:**
      - Runs CFR from this trivial game state.
      - Asserts that the strategy table is populated and the utility returned is a float.
    - **Purpose:**  
      - Quick regression check for CFR’s ability to handle terminal states and minimal info sets.

---

**Notes:**
- Used mainly for rapid development and CFR loop validation.
- Useful for catching table/indexing bugs, not for full-game or realistic agent behavior.


------------------------------

## tests/test_cfr_trainer.py

**Purpose:**  
Unit tests for `CFRTrainer` regret updates, strategy computation, and meld handling (CHI, PON, KAN). Uses both real and fixed-game scenarios to validate core CFR loop logic and regret matching.

---

### Classes:

- `FixedTrainerWithCHIRegret(CFRTrainer)`
    - Custom `cfr` method: Forces regret update for a specific CHI action in test states.

- `FixedTrainerWithPONRegret(CFRTrainer)`
    - Custom `cfr` method: Forces regret update for a specific PON action in test states.

- `TestCFRTrainer(unittest.TestCase)`
    - `test_get_strategy_returns_uniform_when_no_regrets(self)`
        - Verifies that uninitialized info sets return uniform probabilities over legal actions.
    - `test_cfr_regret_update_minimal(self)`
        - Tests regret table is updated after a minimal fake CFR run on a controlled GameState.
    - `test_train_forces_regret_update_with_known_state(self)`
        - Tests that running `.train()` results in regret table mutation with a fixed player state.
    - `test_cfr_learns_ankan(self)`
        - Ensures CFR can learn/analyze ANKAN (closed KAN) moves.
    - `test_cfr_learns_chi(self)`
        - Ensures CHI action regret is updated in a fixed state with custom CFR logic.
    - `test_cfr_learns_pon(self)`
        - Ensures PON action regret is updated in a fixed state with custom CFR logic.

---

**Notes:**
- Relies on controlled or custom game states for deterministic tests.
- Essential for regression testing any change to the CFRTrainer, action space, or meld/claim logic.
- Ensures CFR can learn/track regrets for all major action types (discard, CHI, PON, KAN).


------------------------------

## tests/test_game_state.py

**Purpose:**  
Comprehensive unit tests for all major features of the `GameState` environment. Covers initial state, turn logic, drawing, discarding, meld claims (CHI/PON/KAN), meld priority, legal actions, info sets, bonus tile rules, terminal and win conditions, and reward calculation.

---

### Class: `TestGameState` (inherits from `unittest.TestCase`)

- **Setup and Player/Seat:**
    - `test_initial_state` — Checks correct number of players, hand sizes, wall size, and starting turn.
    - `test_get_current_player` — Confirms correct player at turn index.
    - `seat_index` — Utility for seat order.

- **Step/Turn Logic:**
    - `test_step_discard` — Draw, discard, and post-discard checks.
    - `test_draw_then_discard` — Sequence of draw then discard with checks.
    - `test_pass_action` — PASS handling: turn advance, no discard, hand count.

- **Legal Actions:**
    - `test_get_legal_actions_after_draw` — Legal discard actions after draw.
    - `test_get_info_set_format` — Checks info set contains expected fields.

- **Discard and Meld Tracking:**
    - `test_last_discard_tracking` — Discard tracking by player/turn.
    - `test_can_chi_detects_valid_melds` — CHI detection on discard.
    - `test_step_handles_chi_action` — End-to-end CHI meld action.

- **Win, Reward, and Terminal Logic:**
    - `test_terminal_win_check`, `test_reward_logic_basic` — Simulate winning hands and validate terminal/reward states.

- **CHI/PON/KAN Special Cases:**
    - `test_chi_blocked_by_pon` — Ensures meld priority (PON > CHI).
    - `test_step_auto_resolves_pon` — (DISABLED) Direct PON action.
    - `test_turn_passes_to_meld_claimer` — Turn rotation after meld claim.

- **CHI Legality and Removal:**
    - `test_chi_only_from_left_seat`, `test_chi_fails_from_wrong_seat` — Directionality and legality for CHI.
    - `test_chi_removes_two_tiles_from_hand`, `test_chi_removes_discard_from_pile` — Hand and discard mutations.
    - `test_chi_turn_passes_to_caller`, `test_illegal_chi_action_raises` — Turn and error handling.

- **KAN and Bonus Tile Tests:**
    - `test_ankan_action`, `test_bonus_draw_after_ankan`, `test_wall_decreases_after_bonus_draw`, `test_bonus_tile_goes_to_correct_player` — ANKAN (closed KAN) actions and post-KAN draws.
    - `test_minkan_action_successful`, `test_minkan_bonus_draw`, `test_minkan_removes_discard` — Minkan (open KAN on discard) behavior.
    - `test_minkan_fails_with_less_than_3` — KAN with insufficient tiles (should fail).
    - `test_shominkan_upgrade_successful`, `test_shominkan_removes_tile_from_hand`, `test_shominkan_replaces_meld_type`, `test_shominkan_bonus_draw_after_upgrade` — Shominkan (PON upgraded to KAN) behavior.
    - `test_shominkan_illegal_if_no_pon`, `test_shominkan_illegal_if_tile_not_in_hand` — Illegal Shominkan attempts.

---

**Notes:**
- Tests use both full games and controlled setups for edge-case validation.
- Covers all core engine transitions, meld/arbitration logic, and info set consistency.
- Serves as the primary regression suite for any engine refactoring.


------------------------------

## tests/test_oracle_scenarios.py

**Purpose:**  
Unit tests using oracle (fixed) game states to verify that CFRTrainer and the engine correctly recognize and reward all key win types: self-draw (tsumo), Ron (discard win), CHI, and PON. Ensures CFR, meld logic, and reward propagation work in deterministic, minimal states.

---

### Classes:

- `TestOracleSelfDraw`
    - `test_cfr_learns_to_draw_win(self)`
        - Simulates a win by self-draw (tsumo) using `FixedWinGameState_SelfDraw`.
        - Checks terminal state, reward, and CFR terminal utility.

- `TestOracleRon`
    - `test_cfr_learns_to_ron_win(self)`
        - Simulates a win by Ron (discard win) using `FixedWinGameState_Ron`.
        - Simulates discard and manual win claim, checks terminal state and reward logic, and verifies CFR reward.

- `TestOracleCHI`
    - `test_cfr_learns_to_chi_win(self)`
        - Simulates a win by CHI claim (sequence meld) using `FixedWinGameState_CHI`.
        - Checks that after claiming CHI, player has a winning hand, terminal state, and correct reward.

- `TestOraclePON`
    - `test_cfr_learns_to_pon_win(self)`
        - Simulates a win by PON claim (triplet meld) using `FixedWinGameState_PON`.
        - Checks terminal state and reward after claiming PON.

---

**Notes:**
- Each test steps through only the necessary moves to trigger a win.
- Tests are deterministic and used to guarantee engine/CFR correctness and reward logic for each win type.
- Essential for debugging new meld logic, CFR recursion, and win/terminal propagation.


------------------------------

## tests/test_player.py

**Purpose:**  
Unit tests for the `Player` class. Ensures correct handling of hand operations, meld detection and declaration, and legality checks for PON, CHI, and ANKAN.

---

### Class: `TestPlayer` (inherits from `unittest.TestCase`)

- `test_player_initialization`
    - Verifies that a new player is initialized with correct seat, empty hand, and no melds.
- `test_draw_tile`
    - Checks that drawing a tile adds it to the player's hand with correct attributes.
- `test_discard_tile`
    - Ensures discarding a tile removes it from hand and returns the tile.
- `test_can_pon`
    - Tests PON eligibility based on tile count in hand.
- `test_can_chi`
    - Tests CHI eligibility given hand and discard seat direction; only valid from the left.
- `test_call_meld`
    - Declares a PON meld and verifies hand/meld state mutation.
- `test_can_ankan`
    - Checks ANKAN (concealed KAN) eligibility for having four identical tiles.

---

**Notes:**
- Catches regressions in all hand/meld logic.
- Ensures seat/direction logic for CHI is correct.
- Used to verify hand mutation and meld construction logic

------------------------------

## tests/test_tile.py

**Purpose:**  
Simple script to instantiate and print example `Tile` objects of every category. Used for visual inspection and debugging of `Tile` string representations.

---

### Main Flow:

- **Creates** instances of `Tile` for Man, Pin, Sou, Wind, and Dragon categories with example values and IDs.
- **Prints** each tile to the console to verify `__str__` and construction.

---

**Notes:**
- Not a true unit test (no assertions); acts as a manual/visual check for Tile object correctness.
- Can be extended with assertions to become a proper `unittest.TestCase`.

------------------------------

## tests/test_wall.py

**Purpose:**  
Unit tests for Mahjong wall generation, ensuring correct tile count and correct number of each unique tile in the wall.

---

### Class: `TestWall` (inherits from `unittest.TestCase`)

- `test_wall_tile_count`
    - Asserts that the generated wall contains 136 tiles (no flowers/seasons).

- `test_wall_contains_unique_tile_types`
    - Verifies that every unique tile type (category, value, tile_id) appears exactly 4 times in the wall.

---

**Notes:**
- Guarantees that wall generation follows official Mahjong rules.
- Prevents duplicate or missing tile types due to code bugs.
- Part of the core regression suite for stable tile dealing and game setup.

------------------------------

## tests/test_win_detection.py

**Purpose:**  
Unit tests for the win detection logic (`is_winning_hand`). Ensures basic hands with correct melds and a pair are detected as wins, while incorrect hands are not.

---

### Class: `TestWinDetection` (inherits from `unittest.TestCase`)

- `test_basic_win`
    - Tests a valid hand with four sequences and a pair.
    - Asserts `is_winning_hand` returns `True`.

- `test_not_win`
    - Tests an invalid hand (not enough melds, no pair).
    - Asserts `is_winning_hand` returns `False`.

- `test_win_with_pongs`
    - Tests a valid hand of four pongs and a pair.
    - Asserts `is_winning_hand` returns `True`.

---

**Notes:**
- Covers both sequence and triplet-based (pong) winning hands.
- Ensures win check logic is robust to hand composition.
- Useful for regression after changes to meld or win logic.

------------------------------




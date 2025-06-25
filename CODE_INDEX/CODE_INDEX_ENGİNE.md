## engine/action_space.py


*Updates:** 
- Updated: game_state.py — replaced `resolve_meld_priority` with `collect_and_arbitrate_claims`, claim logic now enforces correct priority for melds and Ron.
- Updated: player.py — now `call_meld` handles all meld tile removals, fixes double-removal bug.
- v1.8.1: Remove PASS from discard phase legal actions, update test and documentation for rule accuracy
- Updated v1.8.2 : game_state.py — Fixed bug in discard phase where the turn would advance twice if no claims were made. Now, after a discard with no meld claims, the turn passes only once to the next player.

---


**Purpose:**  
Defines the action space for the Mahjong engine. Handles encoding, decoding, and lookup of all possible actions (discard, PON, KAN, CHI, PASS), including their unique action IDs and human-readable names. Central utility for agent, environment, and CFR logic.


### Contents:

- **Constants:**
    - `NUM_TILE_TYPES` — Number of unique tile types (34).
    - `DISCARD_ACTIONS` — List of discard action IDs (0–33).
    - `PON_ACTIONS` — List of PON action IDs (34–67).
    - `KAN_ACTIONS` — List of KAN action IDs (90–123).
    - `CHI_ACTIONS` — List of CHI action IDs (69–89).
    - `PASS` — Action ID for passing (68).
    - `ALL_ACTIONS` — List of all action IDs.

- **Mappings:**
    - `ACTION_ID_TO_NAME` — Dict: action ID → action name string (e.g., "DISCARD_3", "CHI_MAN_2").
    - `ACTION_NAME_TO_ID` — Dict: action name string → action ID.

---

### Functions:

- `get_all_discard_actions()`
    - **Returns:** List[int]
    - **Desc:** All discard action IDs.
- `get_all_pon_actions()`
    - **Returns:** List[int]
    - **Desc:** All PON meld action IDs.
- `get_all_kan_actions()`
    - **Returns:** List[int]
    - **Desc:** All KAN meld action IDs.
- `get_all_chi_actions()`
    - **Returns:** List[int]
    - **Desc:** All CHI meld action IDs.
- `get_all_actions()`
    - **Returns:** List[int]
    - **Desc:** All valid action IDs.

- `encode_chi(meld: List[int]) -> int`
    - **Input:** Meld as sorted tile IDs, e.g., [3,4,5].
    - **Output:** CHI action ID.
    - **Desc:** Converts meld to unique CHI action ID.

- `decode_chi(action_id: int) -> List[int]`
    - **Input:** CHI action ID.
    - **Output:** List of three tile IDs.
    - **Desc:** Converts CHI action ID back to original meld.

- `tile_id_from_action(action_id: int) -> int`
    - **Input:** Action ID.
    - **Output:** Tile ID related to action (if any).
    - **Desc:** Extracts tile_id for tile-based actions (discard/meld).

---

**Notes:**  
- Centralizes all action encoding/decoding logic.
- Used throughout environment, player, and CFR code.
- CHI actions are the most complex due to sequence and suit logic.

------------------------------


## engine/cfr_trainer.py

**Purpose:**  
Implements Counterfactual Regret Minimization (CFR) for policy learning in the Mahjong environment. Handles all regret tracking, recursive traversal, policy extraction, and exporting learned strategies.

---

### Contents:

- **Classes:**
    - `CFRTrainer`
        - `__init__(self)`
            - **Initializes** regret and strategy tables for all info sets.
        - `get_strategy(self, info_set, legal_actions)`
            - **Inputs:** `info_set` (str), `legal_actions` (List[int])
            - **Returns:** List[float] (probabilities for each action)
            - **Desc:** Computes current strategy for an info set using regret-matching; tracks strategy sum for averaging.
        - `cfr(self, state, reach_probs, player_id, depth=0)`
            - **Inputs:** `state` (GameState), `reach_probs` (List[float]), `player_id` (int), `depth` (int)
            - **Returns:** float (expected utility)
            - **Desc:** Main recursive CFR function—traverses game tree, updates regrets, propagates values.
        - `clone_state(self, state)`
            - **Inputs:** `state` (GameState)
            - **Returns:** Deep copy of `state`
            - **Desc:** Creates a new independent copy for recursion.
        - `train(self, iterations, player_id=0)`
            - **Inputs:** `iterations` (int), `player_id` (int)
            - **Desc:** Runs CFR for N iterations from new games, exporting learned policy at end.
        - `get_average_strategy(self, info_set, legal_actions)`
            - **Inputs:** `info_set` (str), `legal_actions` (List[int])
            - **Returns:** List[float] (normalized average strategy)
            - **Desc:** Computes average policy over all training episodes for a given info set.
        - `export_strategy_table(self, filename="strategy_table.txt", threshold=0.01)`
            - **Inputs:** `filename` (str), `threshold` (float)
            - **Desc:** Writes average strategies for all info sets to a file, filtering actions by probability.
        - `test_average_strategy_returns_normalized_probs(self)`
            - **Desc:** Test method for internal validation (not used in normal runs).

---

**Notes:**  
- `CFRTrainer` is the core of policy learning and value propagation; all agent learning is managed here.
- `MAX_DEPTH` limits recursion to prevent stack overflow.
- Regret/strategy tables are keyed by deterministic info set strings (see GameState).
- Debug prints for KAN actions and recursion depth to help with troubleshooting.
- Used by top-level scripts (e.g., run_cfr_demo.py) and oracle curriculum tests.

------------------------------


## engine/game_state.py

**Purpose:**  
Central environment and game loop for Mahjong. Manages wall, players, turns, discards, meld/claim logic, legal actions, state transitions, and win/terminal detection.

---

### Contents:

- **Classes:**
    - `GameState`
        - `__init__(self)`
            - **Initializes:** Wall, four Players, discards, deals starting hands, sets turn and phase.
        - `seat_index(self, seat)`
            - **Input:** Seat name ("East", ...)
            - **Output:** Integer index (0–3)
            - **Desc:** Converts seat to index.
        - `id_to_tile_name(self, tile_id)`
            - **Input:** Tile ID (int)
            - **Output:** Human-readable tile name.
        - `get_current_player(self)`
            - **Returns:** Player object for current turn.
        - `step(self, action_id=None)`
            - **Input:** Action ID (int)
            - **Desc:** Advances state by one action; handles draw, discard, meld calls, meld interrupts, KAN/CHI/PON logic, pass, etc.
        - `get_legal_actions(self)`
            - **Returns:** List of legal action IDs for current player/phase.
            - **Desc:** Handles detection of all meld, KAN, CHI, PON, discard, and pass possibilities.
        - `get_info_set(self)`
            - **Returns:** String encoding current player seat, hand, last discard, discarder, meld types; used as info set key for CFR.
        - `can_chi(self, tile)`
            - **Input:** Tile object (discard)
            - **Returns:** List of legal CHI melds available to current player.
        - `is_terminal(self)`
            - **Returns:** True if wall empty or any player has a valid winning hand (4 melds + pair).
            - **Handles:** Manual override with `_terminal` flag for forced termination.
        - `get_reward(self, player_id)`
            - **Input:** Player index.
            - **Returns:** 1.0 for winner, 0.0 for others.
        - `resolve_meld_priority(self, tile)`
            - **Input:** Tile object (most recent discard).
            - **Returns:** Player index who claims meld (PON > CHI > PASS) or None.
            - **Desc:** Meld arbitration after each discard.
- **Functions:**
    - `is_winning_hand(hand_tiles)`
        - **Input:** List of 14 Tile objects (hand + melds).
        - **Returns:** True if hand is 4 melds + 1 pair (closed hand; no yaku/honor/yaku check).
    - `_can_form_melds(tiles)`
        - **Input:** List of Tile objects.
        - **Returns:** True if the tiles can be decomposed into legal melds (recursive helper for win check).

---

**Notes:**  
- All game transitions (draw, discard, melds, interrupts, claims, win check) are implemented here.
- Designed for deterministic CFR and TDD—every legal action can be enumerated.
- Meld arbitration logic ensures only one player claims a discard (priority: PON > CHI > PASS).
- Hand/win check logic only supports basic win structure for now (4 melds + pair).

---

**Specials:**  
- `step()` function handles *all* action types, phase transitions, and meld interrupts in one place.
- Info set logic encodes only observable features (no hidden info leakage).
- Helper functions flatten melds and hand for win checking.

------------------------------

## engine/oracle_states.py

**Purpose:**  
Defines custom fixed (oracle) game states for deterministic CFR testing and curriculum learning. Each state is set up so a win is possible in a controlled way (e.g., self-draw, Ron, CHI, or PON win).

---

### Contents:

- **Classes (all inherit from GameState):**

    - `FixedWinGameState_SelfDraw`
        - **Desc:** Player 0 (East) has a 13-tile hand needing only one more (Pin 1) for a win; wall contains the winning tile. All other hands empty. Next action is Player 0 drawing the win tile.
        - **Usage:** Oracle CFR test for self-draw/tsumo win.
    - `FixedWinGameState_Ron`
        - **Desc:** Player 0 (East) needs one tile for a win. Player 1 (South) holds only that winning tile and must discard it. Wall is empty; after the discard, Player 0 can win by Ron.
        - **Usage:** Oracle CFR test for Ron/discard win.
    - `FixedWinGameState_CHI`
        - **Desc:** Player 0 (South) can win by CHI if Player 3 (East) discards Man 3. Both hands set up for this; wall and other hands empty. Next action is Player 3 discarding Man 3.
        - **Usage:** Oracle CFR test for CHI win on interrupt.
    - `FixedWinGameState_PON`
        - **Desc:** Player 0 (South) needs to PON to win; holds two Man 3, Player 2 (West) discards the third. Wall and other hands empty. Next action is Player 2 discarding Man 3.
        - **Usage:** Oracle CFR test for PON win on interrupt.

---

**Notes:**  
- Each class sets up players’ hands, wall, discards, and turn/phase so only one or two actions are needed for a win.
- Used to verify engine, reward, and CFR learning logic in isolation.
- Essential for curriculum and regression testing.


------------------------------

## engine/game_state.py

**Purpose:**  
Main game environment and turn logic for Mahjong. Controls wall generation, dealing, player hands, turn rotation, meld/claim handling, action legality, meld priority, state transitions, info set encoding, and win/reward detection.

---

### Contents:

- **Classes:**
    - `GameState`
        - `__init__(self)`
            - Initializes wall, player objects, discards, deals 13 tiles to each player, sets turn and phase.
        - `seat_index(self, seat)`
            - **Input:** Seat name ("East", "South", etc.)
            - **Output:** Integer index (0-3).
            - Converts seat name to player index.
        - `id_to_tile_name(self, tile_id)`
            - **Input:** Tile ID (int)
            - **Output:** Human-readable tile name (e.g., "Man 1", "Pin 5").
        - `get_current_player(self)`
            - **Returns:** Player object for current turn.
        - `step(self, action_id=None)`
            - **Input:** Action ID (int, or None for draw phase)
            - **Desc:** Advances state by one action; handles draw, discard, PASS, meld claims (CHI, PON, KAN), meld interrupts, meld priority, win detection, and state transitions.
        - `get_legal_actions(self)`
            - **Returns:** List of legal action IDs for the current player and phase.
            - Includes discards, PASS, and all eligible melds.
        - `get_info_set(self)`
            - **Returns:** Deterministic info set string (player, hand, last discard, discarder, melds) for CFR policy and regret tables.
        - `can_chi(self, tile)`
            - **Input:** Tile (discarded)
            - **Returns:** List of valid CHI melds available to current player on this tile (if allowed by rules/seat).
        - `is_terminal(self)`
            - **Returns:** True if game is over (win or wall empty); supports forced termination override.
        - `get_reward(self, player_id)`
            - **Input:** Player index (int)
            - **Returns:** 1.0 if that player has a winning hand; 0.0 otherwise.
        - `resolve_meld_priority(self, tile)`
            - **Input:** Tile (last discard)
            - **Returns:** Player index of meld claimer, or None.
            - Enforces meld priority (PON > CHI > PASS) and performs meld mutation for winner.
- **Functions:**
    - `is_winning_hand(hand_tiles)`
        - **Input:** List of 14 Tile objects (flattened hand+melds).
        - **Returns:** True if hand is 4 melds + 1 pair (no yaku/honor check).
        - **Desc:** Used for all win/terminal checks.
    - `_can_form_melds(tiles)`
        - **Input:** List of Tile objects.
        - **Returns:** True if the tiles can be recursively decomposed into legal melds (helper for win detection).

---

**Notes:**  
- `step()` centralizes all turn progression, action handling, meld calls, and meld interrupt logic.
- Meld arbitration/priority is managed by `resolve_meld_priority()`.
- Info set encoding is designed for CFR: string includes only observable, non-hidden state.
- Win detection is "structure only": 4 melds + 1 pair; yaku and full scoring can be added later.
- Designed for testability and deterministic CFR training.

---

------------------------------

## engine/oracle_states.py

**Purpose:**  
Contains deterministic "oracle" test states for unit testing and CFR curriculum, each set up so a specific player can win in a known way. Used to prove engine correctness for all win scenarios.

---

### Classes:

- `FixedWinGameState_SelfDraw`
    - **Desc:** Player 0 is one tile from a self-draw (tsumo) win; wall contains the winning tile; other players' hands empty.
    - **Use:** Oracle test for self-draw win logic and CFR terminal reward.

- `FixedWinGameState_Ron`
    - **Desc:** Player 0 is one tile from winning, Player 1 holds and must discard the winning tile; wall empty. Player 0 wins by Ron on Player 1's discard.
    - **Use:** Oracle test for Ron (discard win) logic and terminal detection.

- `FixedWinGameState_CHI`
    - **Desc:** Player 0 can win by claiming CHI on Player 3's discard (e.g., Player 0 has 1-2, Player 3 discards 3). Wall and other hands empty.
    - **Use:** Oracle test for meld-interrupt win (CHI claim).

- `FixedWinGameState_PON`
    - **Desc:** Player 0 has two of a kind, Player 2 will discard the third for a PON win; wall and other hands empty.
    - **Use:** Oracle test for meld-interrupt win (PON claim).

---

**Notes:**
- Every class is a `GameState` subclass with a deterministic, winnable state for rapid CFR and logic testing.
- No random elements, and all external state (wall, discards, melds) is set for reproducibility.
- Critical for TDD and regression in engine and CFR learning.

------------------------------

## engine/player.py

**Purpose:**  
Defines the Player object, including hand, meld logic, meld declaration, draw/discard operations, and legal meld detection (PON, CHI, ANKAN). Used throughout GameState and CFR for all player actions.

---

### Class: `Player`

- `__init__(self, seat)`
    - **Inputs:** Seat ("East", "South", etc.)
    - **Initializes:** Hand (list of Tile), melds (list of tuples).
- `draw_tile(self, tile)`
    - **Adds** a tile to the player's hand.
- `discard_tile(self, tile)`
    - **Removes** tile from hand and returns it; raises if not present.
- `can_pon(self, tile)`
    - **Returns:** True if player can PON (has two matching tiles in hand).
- `can_chi(self, tile, source_seat)`
    - **Returns:** True if player can CHI the tile from the specified seat (must be from right).
    - **Checks:** Suit, possible sequence, and seat order.
- `call_meld(self, meld_type, tiles, include_discard=False)`
    - **Inputs:** Meld type (str), list of Tiles, whether to include discarded tile.
    - **Removes** necessary tiles from hand and appends meld; updates melds list.
    - **Debugs:** Prints meld and hand mutation steps.
- `can_ankan(self, tile)`
    - **Returns:** True if player has all four of this tile (for concealed KAN).
- `clone(self)`
    - **Returns:** Deep copy of player (hand and melds).

---

**Notes:**
- Meld call methods handle both mutation of the hand and tracking in melds list.
- All meld legality checks are centralized (CHI seat rule, ANKAN, etc.).
- `clone()` is essential for CFR branching and state copy.
- Used by GameState, CFRTrainer, and oracle state setup.


------------------------------

## engine/tile.py

**Purpose:**  
Defines the `Tile` object, the fundamental unit for all tile operations in Mahjong (hands, melds, wall, discards). Ensures each tile can be compared, hashed, and displayed consistently.

---

### Class: `Tile`

- `__init__(self, category, value, tile_id)`
    - **Inputs:** 
        - `category` (str): "Man", "Pin", "Sou", "Wind", "Dragon"
        - `value` (int or str): Number (1–9) or honor name ("East", etc.)
        - `tile_id` (int): Unique integer for tile type (usually 0–33 for 1 of each type, may go higher for all instances)
    - **Sets:** Attributes for category, value, and unique ID.

- `__str__(self)`
    - **Returns:** Human-readable string, e.g. `"Man 1"`.

- `__repr__(self)`
    - **Returns:** Same as `__str__`, for debugging/printing.

- `__eq__(self, other)`
    - **Checks:** Equality by `tile_id` (used for melds, discards, etc.).

- `__hash__(self)`
    - **Enables:** Use of `Tile` objects as dictionary keys, set elements (critical for counting, win-checks).

---

**Notes:**
- All comparison, display, and hashing is by `tile_id` for determinism and efficiency.
- Used throughout engine for hand, meld, discard, wall, and all state comparisons.
- Ensures tiles can be reliably used as elements in sets, counters, and info sets.


------------------------------

## engine/wall.py

**Purpose:**  
Generates the Mahjong wall (the shuffled draw pile of all tiles used in the game). Handles creation and shuffling of all tile objects (suits, winds, dragons).

---

### Functions:

- `generate_wall()`
    - **Returns:** List of 136 Tile objects (4 of each standard tile type: 34 types x 4).
    - **How:** 
        - Adds all Man, Pin, Sou tiles (1–9 of each suit, 4 of each).
        - Adds all Winds ("East", "South", "West", "North", 4 of each).
        - Adds all Dragons ("Red", "Green", "White", 4 of each).
        - Shuffles the full tile list randomly.
    - **Notes:** 
        - Flowers/Seasons are skipped (not used).
        - Used in GameState for game initialization and dealing.

---

**Notes:**
- Ensures a correct, randomized wall every game.
- Tile IDs are deterministic and unique per tile type.
- `Tile` class is used for all tile creation (see engine/tile.py).

------------------------------


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

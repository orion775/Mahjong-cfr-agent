## scripts/run_cfr_demo.py

**Purpose:**  
Demo and entry-point script for training the Mahjong CFR agent. Runs training, exports the learned policy, and prints sample strategies. Used for development verification and quick policy inspection.

---

### Main Script Flow:

- **Imports and Setup:**
    - Adds parent directory to `sys.path` to enable engine imports.
    - Imports `CFRTrainer` from `engine.cfr_trainer`.

- **Training:**
    - Instantiates `CFRTrainer`.
    - Runs `trainer.train(iterations=1000, player_id=0)` to train the agent for 1000 iterations as Player 0.

- **Exporting & Inspection:**
    - Exports the full strategy table to `cfr_policy.txt` (no probability threshold).
    - Prints out sample learned strategies for info sets where any action has >5% probability (stops after 3 info sets for brevity).

---

**Notes:**
- Intended for use from the command line as a quick experiment.
- Can be adapted to run for more iterations or to print all info sets.
- Useful for verifying that CFR training is stable, policies are non-uniform, and strategies are being learned as expected.

------------------------------
## tests/fixed_meld_state.py

**Purpose:**  
Defines a fixed, custom test game state with a known meld/discard situation for targeted CFR testing and debugging. Also includes a trainer subclass for rapid experiments on this fixed scenario.
# scripts/train_cfr_debug.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.cfr_trainer import CFRTrainer

def train_with_debug_output():
    trainer = CFRTrainer()  # No max_depth passed here

    iterations = 1
    print(f"Starting CFR training for {iterations} iterations...\n")

    for i in range(1, iterations + 1):
        trainer.train(iterations=1, player_id=0)

        if i % 10 == 0:
            print(f"{i} games completed")

    # Optional: export learned strategy (can be skipped if not needed)
    trainer.export_strategy_table("debug_strategy_table.txt", threshold=0.01)
    print("\n✅ Strategy table exported to debug_strategy_table.txt")

if __name__ == "__main__":
    train_with_debug_output()

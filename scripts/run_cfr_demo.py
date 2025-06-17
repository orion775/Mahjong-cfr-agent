import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine.cfr_trainer import CFRTrainer

trainer = CFRTrainer()
trainer.train(iterations=10000, player_id=0)

# Export full strategy to file
trainer.export_strategy_table("cfr_policy.txt", threshold=0.0)

# Print top strategies in memory
print("\nSample learned strategies (threshold > 5%):")
for info_set, strategy_sum in trainer.strategy_table.items():
    legal_actions = [a for a, p in enumerate(strategy_sum) if p > 0]
    avg = trainer.get_average_strategy(info_set, legal_actions)

    print(f"{info_set}")
    for a, p in enumerate(avg):
        if p > 0.05:
            print(f"  Action {a}: {p:.2f}")
    print()

    # Stop after showing 3 info sets
    if sum(1 for _ in trainer.strategy_table) > 3:
        break
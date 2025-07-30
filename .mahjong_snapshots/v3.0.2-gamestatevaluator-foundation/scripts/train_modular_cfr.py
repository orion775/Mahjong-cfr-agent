# scripts/train_modular_cfr.py

from engine.modular_cfr_trainer import ModularCFRTrainer
from engine.game_state import GameState

if __name__ == "__main__":
    # Create the modular CFR trainer, using default reward/info set
    trainer = ModularCFRTrainer(
        game_state_cls=GameState
        # No need to set reward_fn, info_set_fn, or clone_fn unless you want to override defaults
    )

    # Train for 100 self-play games (iterations)
    trainer.train(iterations=1, verbose=True)

    # Export the learned policy for inspection
    trainer.export_policy("cfr_policy.txt")

    print("Training complete. Policy saved to cfr_policy.txt")
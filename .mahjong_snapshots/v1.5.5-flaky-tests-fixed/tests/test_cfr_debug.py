import unittest
from engine.cfr_trainer import CFRTrainer
from engine.game_state import GameState
import copy

class TestCFRDebug(unittest.TestCase):
    def test_cfr_runs_to_terminal(self):
        class FixedGameState(GameState):
            def __init__(self):
                super().__init__()
                self._terminal = False

            def step(self, action=None):
                self._terminal = True  # Terminal immediately

        class FixedTrainer(CFRTrainer):
            def clone_state(self, state):
                return copy.deepcopy(state)

        state = FixedGameState()
        trainer = FixedTrainer()

        reach_probs = [1.0] * 4
        utility = trainer.cfr(state, reach_probs, player_id=0, depth=0)

        self.assertTrue(len(trainer.strategy_table) > 0)
        self.assertIsInstance(utility, float)

if __name__ == "__main__":
    unittest.main()
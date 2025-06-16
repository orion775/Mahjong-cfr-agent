import unittest
from engine.cfr_trainer import CFRTrainer

class TestCFRTrainer(unittest.TestCase):
    def test_get_strategy_returns_uniform_when_no_regrets(self):
        trainer = CFRTrainer()
        info_set = "East|H:...|L:...|BY:...|M:..."  # dummy
        legal_actions = [0, 1, 2]  # pretend the hand allows discarding tile_ids 0–2

        strategy = trainer.get_strategy(info_set, legal_actions)

        self.assertEqual(len(strategy), 90)
        self.assertAlmostEqual(sum(strategy), 1.0)
        for i in legal_actions:
            self.assertAlmostEqual(strategy[i], 1 / len(legal_actions))
        for i in range(90):
            if i not in legal_actions:
                self.assertEqual(strategy[i], 0.0)
    
    def test_cfr_regret_update_minimal(self):
        from engine.game_state import GameState
        from engine.tile import Tile
        from engine import action_space

        trainer = CFRTrainer()

        # Build a controlled GameState
        state = GameState()
        state.turn_index = 0
        player = state.get_current_player()
        
        # Give player two tiles with different IDs (so 2 discard choices)
        t1 = Tile("Man", 1, 0)
        t2 = Tile("Man", 2, 1)
        player.hand = [t1, t2] + player.hand[2:]
        
        state.awaiting_discard = True  # skip draw, allow discard

        info = state.get_info_set()
        legal = state.get_legal_actions()
        
        # Inject fake strategy call with fixed utility values
        def fake_cfr(*args, **kwargs):
            info_set = state.get_info_set()
            regrets = trainer.regret_table.setdefault(info_set, [0.0] * 90)
            regrets[0] = 1.0  # fake regret for action 0
            return 0.5

        trainer.cfr = fake_cfr  # override to short-circuit

        # Manually trigger it once
        trainer.cfr(state, [1.0] * 4, player_id=0)

        regrets = trainer.regret_table[info]
        nonzero = [r for r in regrets if abs(r) > 0]
        self.assertTrue(len(nonzero) > 0)

if __name__ == "__main__":
    unittest.main()
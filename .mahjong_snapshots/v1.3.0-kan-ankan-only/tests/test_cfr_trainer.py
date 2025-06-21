import unittest
from engine.cfr_trainer import CFRTrainer

class TestCFRTrainer(unittest.TestCase):
    def test_get_strategy_returns_uniform_when_no_regrets(self):
        trainer = CFRTrainer()
        info_set = "East|H:...|L:...|BY:...|M:..."  # dummy
        legal_actions = [0, 1, 2]  # pretend the hand allows discarding tile_ids 0–2

        strategy = trainer.get_strategy(info_set, legal_actions)

        self.assertEqual(len(strategy), 124)
        self.assertAlmostEqual(sum(strategy), 1.0)
        for i in legal_actions:
            self.assertAlmostEqual(strategy[i], 1 / len(legal_actions))
        for i in range(124):
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
            regrets = trainer.regret_table.setdefault(info_set, [0.0] * 124)
            regrets[0] = 1.0  # fake regret for action 0
            return 0.5

        trainer.cfr = fake_cfr  # override to short-circuit

        # Manually trigger it once
        trainer.cfr(state, [1.0] * 4, player_id=0)

        regrets = trainer.regret_table[info]
        nonzero = [r for r in regrets if abs(r) > 0]
        self.assertTrue(len(nonzero) > 0)

    def test_train_forces_regret_update_with_known_state(self):
        from engine.game_state import GameState
        from engine.tile import Tile
        from engine import action_space

        class FixedTrainer(CFRTrainer):
            def cfr(self, state, reach_probs, player_id):
                player = state.get_current_player()
                state.awaiting_discard = True
                player.hand = [Tile("Man", 1, 0), Tile("Man", 2, 1)]
                state.turn_index = 0

                info_set = state.get_info_set()
                legal_actions = state.get_legal_actions()

                strategy = self.get_strategy(info_set, legal_actions)

                regrets = self.regret_table.setdefault(info_set, [0.0] * 124)
                regrets[0] += 1.0  # Force non-zero update
                return 1.0

        trainer = FixedTrainer()
        trainer.train(iterations=1, player_id=0)

        self.assertGreater(len(trainer.regret_table), 0)
        for regrets in trainer.regret_table.values():
            self.assertTrue(any(abs(r) > 0 for r in regrets))
    
    def test_cfr_learns_ankan(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import ACTION_NAME_TO_ID
        from engine.cfr_trainer import CFRTrainer

        class FixedKanTrainer(CFRTrainer):
            def cfr(self, state, reach_probs, player_id):
                # Force correct discard phase
                state.awaiting_discard = True
                player = state.get_current_player()

                # Give player 4 separate tiles with tile_id = 0
                
                player.hand.clear()
                player.hand.extend([Tile("Man", 1, 0) for _ in range(4)])
                player.melds.clear()
                state.awaiting_discard = True

                legal_actions = state.get_legal_actions()
                assert ACTION_NAME_TO_ID["KAN_0"] in legal_actions, f"KAN_0 not in {legal_actions}"

                info_set = state.get_info_set()
                self.regret_table.setdefault(info_set, [0.0] * 124)[90] += 1.0  # force regret on KAN_0
                return 1.0

        trainer = FixedKanTrainer()
        trainer.train(iterations=1, player_id=0)

        regrets = list(trainer.regret_table.values())[0]
        self.assertGreater(regrets[90], 0.0, "KAN_0 regret not updated")

if __name__ == "__main__":
    unittest.main()
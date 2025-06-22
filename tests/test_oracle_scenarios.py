#tests\test_oracle_scenarios.py


import unittest
from engine.cfr_trainer import CFRTrainer
from engine.oracle_states import FixedWinGameState_SelfDraw
from engine.oracle_states import FixedWinGameState_Ron
from engine.oracle_states import FixedWinGameState_CHI
from engine.oracle_states import FixedWinGameState_PON
from engine import action_space

class TestOracleSelfDraw(unittest.TestCase):
    def test_cfr_learns_to_draw_win(self):
        trainer = CFRTrainer()
        state = FixedWinGameState_SelfDraw()

        # Before drawing, state should NOT be terminal
        self.assertFalse(state.is_terminal(), "State should not be terminal before the draw.")

        # --- Step the state: Player 0 draws the winning tile ---
        state.step()  # Simulates Player 0 drawing
        print("Player 0 hand:", [str(t) for t in state.players[0].hand])
        print("Player 0 melds:", state.players[0].melds)
        print("Hand length:", len(state.players[0].hand))
        print("is_terminal():", state.is_terminal())

        # Now the state should be terminal and Player 0 should have won
        self.assertTrue(state.is_terminal(), "State should be terminal after drawing the winning tile.")

        # Check the reward logic directly
        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning self-draw.")

        # Optionally: Check CFR directly on terminal state
        utility = trainer.cfr(state, [1.0]*4, player_id=0)
        self.assertEqual(utility, 1.0, "CFR should immediately return win reward from terminal state.")


class TestOracleRon(unittest.TestCase):
    def test_cfr_learns_to_ron_win(self):
        from engine.cfr_trainer import CFRTrainer
        from engine.game_state import GameState
        from engine.tile import Tile

        trainer = CFRTrainer()
        state = GameState()

        # Setup: clear hands and melds
        for p in state.players:
            p.hand.clear()
            p.melds.clear()

        # Player 1 discards Pin 1
        state.players[1].hand.append(Tile("Pin", 1, 9))

        # Player 0: 13-tile tenpai (ready) hand, needs Pin 1 for win
        state.players[0].hand.extend([
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            Tile("Man", 2, 1), Tile("Man", 2, 1), Tile("Man", 2, 1),
            Tile("Man", 3, 2), Tile("Man", 3, 2), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 4, 3), Tile("Man", 4, 3),
            Tile("Pin", 1, 9)
        ])

        state.turn_index = 1
        state.awaiting_discard = True

        discard_tile = state.players[1].hand[0]
        state.step(discard_tile.tile_id)

        print("Player 0 hand (after Ron):", [str(t) for t in state.players[0].hand])
        print("Hand length (after Ron):", len(state.players[0].hand))
        print("is_terminal() (after Ron):", state.is_terminal())
        print("DEBUG: _terminal =", getattr(state, "_terminal", None))

        self.assertTrue(state.is_terminal(), "State should be terminal after Player 0 claims Ron.")
        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning on discard (Ron).")

        utility = trainer.cfr(state, [1.0]*4, player_id=0)
        self.assertEqual(utility, 1.0, "CFR should immediately return win reward from Ron terminal state.")
    

class TestOracleCHI(unittest.TestCase):
    def test_cfr_learns_to_chi_win(self):
        trainer = CFRTrainer()
        state = FixedWinGameState_CHI()

        # Step 1: Player 3 discards Man 3
        discard_tile = state.players[3].hand[0]
        state.step(discard_tile.tile_id)

        # Step 2: Player 0 (South) can now claim CHI
        player0 = state.players[0]
        # Find the correct CHI action for [Man 1, Man 2, Man 3]
        chi_action = action_space.encode_chi([0, 1, 2])

        # Step: Player 0 claims CHI
        state.step(chi_action)

        # After CHI, player0 should have 14 tiles and a meld, which should be a win
        print("Player 0 hand (after CHI):", [str(t) for t in player0.hand])
        print("Player 0 melds:", player0.melds)
        print("is_terminal() (after CHI):", state.is_terminal())

        self.assertTrue(state.is_terminal(), "State should be terminal after Player 0 wins by CHI.")
        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning by CHI.")



class TestOraclePON(unittest.TestCase):
    def test_cfr_learns_to_pon_win(self):
        trainer = CFRTrainer()
        state = FixedWinGameState_PON()

        # Step 1: Player 2 discards Man 3
        discard_tile = state.players[2].hand[0]
        state.step(discard_tile.tile_id)

        # Step 2: Player 0 (South) can now claim PON
        pon_action = action_space.ACTION_NAME_TO_ID["PON_2"]  # PON on Man 3

        state.step(pon_action)

        player0 = state.players[0]
        print("Player 0 hand (after PON):", [str(t) for t in player0.hand])
        print("Player 0 melds:", player0.melds)
        print("is_terminal() (after PON):", state.is_terminal())

        self.assertTrue(state.is_terminal(), "State should be terminal after Player 0 wins by PON.")
        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning by PON.")




if __name__ == '__main__':
    unittest.main()
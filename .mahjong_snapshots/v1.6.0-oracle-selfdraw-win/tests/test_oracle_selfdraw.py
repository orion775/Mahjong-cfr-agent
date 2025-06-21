import unittest
from engine.cfr_trainer import CFRTrainer
from engine.oracle_states import FixedWinGameState_SelfDraw

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

if __name__ == '__main__':
    unittest.main()
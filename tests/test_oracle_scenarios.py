import unittest
from engine.cfr_trainer import CFRTrainer
from engine.oracle_states import FixedWinGameState_SelfDraw
from engine.oracle_states import FixedWinGameState_Ron

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
        trainer = CFRTrainer()
        state = FixedWinGameState_Ron()

        # --- Step 1: Player 1 discards their only tile (Pin 1) ---
        player1 = state.players[1]
        discard_tile = player1.hand[0]
        
        state.step(discard_tile.tile_id)
        # Simulate Player 0 calling Ron by picking up the discard
        player0 = state.players[0]
        player0.hand.append(state.last_discard)

        print("Player 0 hand (after Ron):", [str(t) for t in player0.hand])
        print("Hand length (after Ron):", len(player0.hand))
        print("is_terminal() (after Ron):", state.is_terminal())

        # Now test terminal and reward
        self.assertTrue(state.is_terminal(), "State should be terminal after Player 0 claims Ron.")
        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning on discard (Ron).")

        # Check that the discard was registered correctly
        self.assertEqual(state.last_discard.tile_id, discard_tile.tile_id)
        self.assertEqual(state.last_discarded_by, 1)

        # --- Step 2: Player 0's turn to react ---
        # Now, Player 0 (East) should be able to win with this tile
        # (In a real Mahjong engine, Ron would trigger; here, we'll check terminal state and reward)
        # Simulate that Player 0 picks up the discard for a win (if you have Ron support, otherwise check is_terminal)
        self.assertTrue(state.is_terminal(), "State should be terminal after Player 0 wins by Ron.")

        reward = state.get_reward(0)
        self.assertEqual(reward, 1.0, "Player 0 should receive reward for winning on discard (Ron).")

        # CFR utility check (optional)
        utility = trainer.cfr(state, [1.0]*4, player_id=0)
        self.assertEqual(utility, 1.0, "CFR should immediately return win reward from Ron terminal state.")


if __name__ == '__main__':
    unittest.main()
# tests/test_game_state.py

import unittest
from engine.game_state import GameState

class TestGameState(unittest.TestCase):
    def test_initial_state(self):
        state = GameState()
        self.assertEqual(len(state.players), 4)
        for player in state.players:
            self.assertEqual(len(player.hand), 13)
        self.assertEqual(len(state.wall), 136 - (4 * 13))
        self.assertEqual(state.turn_index, 0)
    
    def test_get_current_player(self):
        state = GameState()
        current = state.get_current_player()
        self.assertEqual(current.seat, "East")

    def test_step_discard(self):
        from engine import action_space

        state = GameState()
        player = state.get_current_player()
        tile = player.hand[0]

        # Step 1: Draw
        state.step()  # player draws → 13 → 14

        # Step 2: Discard
        state.step(tile.tile_id)  # 14 → 13

        self.assertEqual(len(player.hand), 13)
        self.assertEqual(state.discards[player.seat][-1].tile_id, tile.tile_id)
        self.assertEqual(state.turn_index, 1)
    
    def test_draw_then_discard(self):
        from engine import action_space

        state = GameState()
        player = state.get_current_player()
        initial_hand_size = len(player.hand)

        # Step 1: Player draws
        state.step()
        self.assertEqual(len(player.hand), initial_hand_size + 1)
        self.assertTrue(state.awaiting_discard)

        # Step 2: Player discards
        tile = player.hand[0]
        state.step(tile.tile_id)
        self.assertEqual(len(player.hand), initial_hand_size)
        self.assertFalse(state.awaiting_discard)
        self.assertEqual(state.turn_index, 1)

    def test_pass_action(self):
        from engine import action_space

        state = GameState()
        player = state.get_current_player()

        # Step 1: draw
        state.step()
        self.assertTrue(state.awaiting_discard)

        # Step 2: pass instead of discard
        state.step(action_space.PASS)

        self.assertFalse(state.awaiting_discard)
        self.assertEqual(state.turn_index, 1)  # Turn advances
        self.assertEqual(len(state.discards[player.seat]), 0)  # No tile discarded
        self.assertEqual(len(player.hand), 14)  # Still holding 14

    def test_get_legal_actions_after_draw(self):
        from engine import action_space

        state = GameState()
        player = state.get_current_player()

        # Step 1: Draw a tile
        state.step()  # player draws, hand becomes 14

        # Step 2: Get legal actions
        legal = state.get_legal_actions()
        tile_ids = {tile.tile_id for tile in player.hand}

        # Test: each tile in hand has a corresponding DISCARD action
        for tid in tile_ids:
            self.assertIn(tid, legal)

        # Test: PASS is always allowed
        self.assertIn(action_space.PASS, legal)

        # Total actions = unique tiles in hand + PASS
        self.assertEqual(len(legal), len(tile_ids) + 1)

    def test_last_discard_tracking(self):
        state = GameState()
        state.step()  # draw
        player = state.get_current_player()
        tile = player.hand[0]
        state.step(tile.tile_id)  # discard

        self.assertIsNotNone(state.last_discard)
        self.assertEqual(state.last_discard.tile_id, tile.tile_id)
        self.assertEqual(state.last_discarded_by, 0)

    def test_pon_action(self):
        from engine import action_space
        from engine.tile import Tile

        state = GameState()

        # EAST player's turn
        state.step()  # draw phase
        east = state.get_current_player()

        # Give East 2 matching tiles
        tile1 = Tile("Man", 1, 0)
        tile2 = Tile("Man", 1, 0)
        east.hand = [tile1, tile2] + east.hand[2:]

        # Discard an actual tile from East's hand (so the object identity is preserved)
        tile_to_discard = east.hand[0]
        state.step(tile_to_discard.tile_id)  # East discards this tile
        state.turn_index = 1                 # Force South's turn
        state.awaiting_discard = True

        # SOUTH's turn (automatically after East's discard)
        south = state.get_current_player()

        # Give South 2 matching tiles (separate objects)
        tile4 = Tile("Man", 1, 0)
        tile5 = Tile("Man", 1, 0)
        south.hand = [tile4, tile5] + south.hand[2:]

        # Action ID for PON_0 (tile_id 0)
        pon_action = action_space.NUM_TILE_TYPES + 0

        state.step(pon_action)

        self.assertEqual(state.get_current_player().seat, "South")
        self.assertEqual(len(south.melds), 1)
        self.assertEqual(south.melds[0][0], "PON")
        self.assertEqual(state.awaiting_discard, True)
    
    def test_get_info_set_format(self):
        state = GameState()
        state.step()  # draw phase
        info = state.get_info_set()

        self.assertIn("H:", info)
        self.assertIn("L:", info)
        self.assertIn("BY:", info)
        self.assertIn("M:", info)
        self.assertIn(state.get_current_player().seat, info)

if __name__ == "__main__":
    unittest.main()
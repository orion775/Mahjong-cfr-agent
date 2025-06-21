# tests/test_game_state.py

import unittest
from engine.game_state import GameState

class TestGameState(unittest.TestCase):
    def seat_index(self, seat):
        return ["East", "South", "West", "North"].index(seat)
    
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
    
    def test_can_chi_detects_valid_melds(self):
        from engine.tile import Tile

        state = GameState()

        # Simulate a discard from West to South (valid CHI direction)
        state.turn_index = 3  # West
        state.step()  # West draws
        discard_tile = Tile("Man", 3, 2)  # ID = 2 (Man 3)
        state.last_discard = discard_tile
        state.last_discarded_by = 3  # West

        # South's turn
        state.turn_index = 0  # South

        # Give South a hand that can form a CHI with Man 3
        state.players[0].hand = [
            Tile("Man", 1, 0),  # ID 0
            Tile("Man", 2, 1),  # ID 1
            Tile("Man", 4, 3),  # ID 3
            Tile("Man", 5, 4),  # ID 4
        ] + state.players[0].hand[4:]

        result = state.can_chi(discard_tile)
        expected = [[0, 1, 2], [1, 2, 3], [2, 3, 4]]  # depending on the tile IDs

        self.assertTrue(any(result))  # At least one meld returned
        flat = [tuple(m) for m in result]
        self.assertIn((1, 2, 3), flat)  # (Man 2, 3, 4)

    def test_step_handles_chi_action(self):
        from engine.tile import Tile
        from engine import action_space

        state = GameState()
        from engine.tile import Tile

        east = state.players[0]
        east.hand = [
            Tile("Man", 2, 1), Tile("Man", 3, 2), Tile("Man", 4, 3),
            Tile("Sou", 9, 26), Tile("Pin", 9, 17)
]

        # Simulate West's discard of Man 3 (tile_id=2)
        discard_tile = Tile("Man", 3, 2)
        state.last_discard = discard_tile
        state.last_discarded_by = 3
        state.discards["North"].append(discard_tile)
        state.awaiting_discard = True
        
        # Set turn to South (next player after West)
        state.turn_index = 0  # South
        player = state.get_current_player()

        # Give South a hand that completes CHI with Man 2 (1) and Man 4 (3)
        player.hand = [Tile("Man", 2, 1), Tile("Man", 4, 3)] + player.hand[2:]

        # Verify everything lines up
        assert discard_tile.tile_id == 2  # Man 3
        chi_action = action_space.encode_chi([1, 2, 3])  # [Man 2, Man 3, Man 4]

        # Take CHI action
        print("[DEBUG] chi_action =", chi_action)
        print("[DEBUG] action_space.CHI_ACTIONS =", action_space.CHI_ACTIONS)
        print("[DEBUG TEST] player.melds =", player.melds)
        state.awaiting_discard = True
        state.step(chi_action)
        print("[DEBUG TEST] player.melds =", player.melds)

        # Check meld added
        self.assertIn(
            ("CHI", ["Man 2", "Man 3", "Man 4"]),
            [("CHI", [str(t) for t in meld[1]]) for meld in player.melds]
    )
        print("[DEBUG TEST] player.melds =", player.melds)
        

        # Check discard removed by tile_id
        self.assertFalse(any(t.tile_id == 2 for t in state.discards["West"]))

        # Check removed from hand
        hand_ids = [t.tile_id for t in player.hand]

        # Player must now discard
        self.assertTrue(state.awaiting_discard)
    
    def test_terminal_win_check(self):
        state = GameState()
        player = state.players[0]

        # Simulate winning by creating 4 melds
        for _ in range(4):
            player.melds.append(("PON", ["Man 1", "Man 1", "Man 1"]))

        self.assertTrue(state.is_terminal())
        self.assertEqual(state.get_reward(0), 1.0)

        for pid in range(1, 4):
            self.assertEqual(state.get_reward(pid), 0.0)
    
    def test_ankan_action(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()

        # Force hand to contain only 4 of the same tile
        player.hand.clear()
        player.hand.extend([Tile("Man", 1, 0) for _ in range(4)])

        state.awaiting_discard = True
        kan_action = action_space.ACTION_NAME_TO_ID["KAN_0"]
        state.step(kan_action)

        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "KAN")
        self.assertEqual(len(player.melds[0][1]), 4)
        self.assertTrue(state.awaiting_discard)

        
    def test_bonus_draw_after_ankan(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()

        # Give player 4 matching tiles (e.g., tile_id = 0)
        player.hand.clear()
        tile = Tile("Man", 1, 0)
        player.hand.extend([tile] * 4)
        hand_size_before = len(player.hand)
        wall_size_before = len(state.wall)

        kan_action = action_space.ACTION_NAME_TO_ID["KAN_0"]
        state.awaiting_discard = True  # simulate discard phase
        state.step(kan_action)

        self.assertEqual(len(player.hand), hand_size_before - 4 + 1)  # -4 tiles + 1 bonus draw
        self.assertTrue(state.awaiting_discard)

    def test_wall_decreases_after_bonus_draw(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()

        player.hand.clear()
        tile = Tile("Man", 1, 0)
        player.hand.extend([tile] * 4)

        state.awaiting_discard = True
        wall_before = len(state.wall)
        kan_action = action_space.ACTION_NAME_TO_ID["KAN_0"]
        state.step(kan_action)
        wall_after = len(state.wall)

        self.assertEqual(wall_after, wall_before - 1)

    def test_bonus_tile_goes_to_correct_player(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()

        player.hand.clear()
        tile = Tile("Man", 1, 0)
        player.hand.extend([tile] * 4)

        state.awaiting_discard = True
        kan_action = action_space.ACTION_NAME_TO_ID["KAN_0"]
        state.step(kan_action)

        # Verify the hand contains 1 tile not matching the KAN tile_id (bonus draw)
        kan_tile_ids = [t.tile_id for t in player.hand if t.tile_id == 0]
        self.assertLess(len(kan_tile_ids), len(player.hand))  # At least 1 bonus tile differs
    
    def test_minkan_action_successful(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()

        # Force turn order and discard state
        state.turn_index = 3  # West
        state.step()  # West draws
        discard_tile = Tile("Pin", 2, 10)
        state.last_discard = discard_tile
        state.last_discarded_by = 3
        state.discards["North"].append(discard_tile)

        # Player South holds 3× tile_id = 10
        state.turn_index = 0
        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Pin", 2, 10) for _ in range(3)])

        state.awaiting_discard = True
        kan_action = action_space.ACTION_NAME_TO_ID["KAN_10"]

        state.step(kan_action)

        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "KAN")
        self.assertEqual(len(player.melds[0][1]), 4)
        self.assertTrue(state.awaiting_discard)

    def test_minkan_bonus_draw(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        discard_tile = Tile("Sou", 5, 22)

        state.last_discard = discard_tile
        state.last_discarded_by = 3
        state.discards["North"].append(discard_tile)
        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Sou", 5, 22) for _ in range(3)])

        wall_before = len(state.wall)
        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_22"])

        self.assertEqual(len(state.wall), wall_before - 1)
        self.assertEqual(len(player.hand), 0 + 1)  # -3 + 1 = 1

    def test_minkan_removes_discard(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        discard_tile = Tile("Man", 8, 7)
        state.last_discard = discard_tile
        state.last_discarded_by = 2
        state.discards["West"].append(discard_tile)

        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Man", 8, 7) for _ in range(3)])

        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_7"])

        discards = state.discards["West"]
        self.assertFalse(any(t.tile_id == 7 for t in discards))
        self.assertIsNone(state.last_discard)
        self.assertIsNone(state.last_discarded_by)

    def test_minkan_fails_with_less_than_3(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        discard_tile = Tile("Dragon", "Red", 31)
        state.last_discard = discard_tile
        state.last_discarded_by = 1
        state.discards["South"].append(discard_tile)

        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31)])  # only 2

        state.awaiting_discard = True
        with self.assertRaises(ValueError):
            state.step(action_space.ACTION_NAME_TO_ID["KAN_31"])

    def test_shominkan_upgrade_successful(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()

        # Set up an existing PON meld for tile_id = 4
        tile = Tile("Man", 5, 4)
        pon_meld = ("PON", [tile, tile, tile])
        player.melds = [pon_meld]

        # Add 4th tile to hand
        player.hand.clear()
        player.hand.append(Tile("Man", 5, 4))

        # Simulate discard phase
        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_4"])

        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "KAN")
        self.assertEqual(len(player.melds[0][1]), 4)
        self.assertTrue(state.awaiting_discard)

    def test_shominkan_removes_tile_from_hand(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()
        tile = Tile("Sou", 3, 20)

        player.melds = [("PON", [tile, tile, tile])]
        player.hand.clear()
        player.hand.append(Tile("Sou", 3, 20))

        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_20"])

        self.assertNotIn(tile, player.hand)

    def test_shominkan_replaces_meld_type(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()
        tile = Tile("Pin", 9, 17)

        player.melds = [("PON", [tile, tile, tile])]
        player.hand.clear()
        player.hand.append(Tile("Pin", 9, 17))

        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_17"])

        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "KAN")

    def test_shominkan_bonus_draw_after_upgrade(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()
        tile = Tile("Wind", "East", 27)

        player.melds = [("PON", [tile, tile, tile])]
        player.hand.clear()
        player.hand.append(Tile("Wind", "East", 27))

        wall_before = len(state.wall)
        state.awaiting_discard = True
        state.step(action_space.ACTION_NAME_TO_ID["KAN_27"])
        self.assertEqual(len(state.wall), wall_before - 1)

    def test_shominkan_illegal_if_no_pon(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()
        player.melds = [("PON", [Tile("Man", 5, 4)] * 3)]  # wrong PON
        player.hand.clear()
        player.hand.extend([Tile("Man", 6, 5)] * 4)

        state.awaiting_discard = True
        with self.assertRaises(ValueError):
            state.step(action_space.ACTION_NAME_TO_ID["KAN_5"])

    def test_shominkan_illegal_if_tile_not_in_hand(self):
        from engine.tile import Tile
        from engine import action_space
        from engine.game_state import GameState

        state = GameState()
        player = state.get_current_player()
        tile = Tile("Dragon", "Green", 32)

        player.melds = [("PON", [tile, tile, tile])]
        player.hand.clear()  # no 4th tile in hand

        state.awaiting_discard = True
        with self.assertRaises(ValueError):
            state.step(action_space.ACTION_NAME_TO_ID["KAN_32"])
    
    def test_chi_only_from_left_seat(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import encode_chi

        state = GameState()

        # Set discard info: East discards Man 3 (tile_id=2)
        state.last_discard = Tile("Man", 3, 2)
        state.last_discarded_by = 0  # East

        # South is to the left of East
        state.turn_index = 1
        state.awaiting_discard = False  # must be false for meld reaction

        # Setup South’s hand with Man 2 (tile_id=1), Man 4 (tile_id=3)
        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([
            Tile("Man", 2, 1),
            Tile("Man", 4, 3)
        ])
        print("DEBUG: Discarder =", state.players[state.last_discarded_by].seat)
        print("DEBUG: Current player =", state.get_current_player().seat)
        print("DEBUG: awaiting_discard =", state.awaiting_discard)
        print("DEBUG: can_chi() =", state.can_chi(state.last_discard))

        action_id = encode_chi([1, 2, 3])  # CHI Man 2,3,4 (tile_ids)

        legal_actions = state.get_legal_actions()

        self.assertIn(action_id, legal_actions, f"Expected CHI action {action_id} in legal_actions={legal_actions}")

    def test_chi_fails_from_wrong_seat(self):
        from engine.tile import Tile
        from engine.action_space import encode_chi
        from engine.game_state import GameState

        state = GameState()
        tile = Tile("Sou", 6, 23)  # Discarded tile

        # Discarder is West (index 2)
        state.last_discarded_by = 2
        state.players[2].seat = "West"

        # Current player is East (index 0)
        state.turn_index = 0
        state.players[0].seat = "East"

        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([
            Tile("Sou", 5, 22),
            Tile("Sou", 7, 24),
        ])

        state.last_discard = tile
        state.discards["West"].append(tile)

        action_id = encode_chi([22, 23, 24])
        legal_actions = state.get_legal_actions()

        print("[DEBUG] Legal actions:", legal_actions)
        print("[DEBUG] Trying to assert action_id:", action_id)
        self.assertNotIn(action_id, legal_actions)

    def test_chi_removes_two_tiles_from_hand(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import encode_chi

        state = GameState()

        state.turn_index = 1  # South
        state.last_discard = Tile("Pin", 3, 11)
        state.last_discarded_by = 0  # East
        player = state.get_current_player()

        player.hand.clear()
        player.hand.extend([Tile("Pin", 2, 10), Tile("Pin", 4, 12)])

        action_id = encode_chi([10, 11, 12])
        state.awaiting_discard = True
        state.step(action_id)

        self.assertEqual(len(player.hand), 0)
        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "CHI")

    def test_chi_removes_discard_from_pile(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import encode_chi

        state = GameState()
        state.last_discarded_by = 0  # East
        state.turn_index = 1  # South
        tile = Tile("Man", 6, 5)
        state.last_discard = tile
        state.discards["East"].append(tile)

        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Man", 5, 4), Tile("Man", 7, 6)])

        action_id = encode_chi([4, 5, 6])
        state.awaiting_discard = True

        # Store discard seat before we step (since it's cleared inside step)
        discard_seat = state.players[state.last_discarded_by].seat

        state.step(action_id)

        self.assertFalse(any(t.tile_id == tile.tile_id for t in state.discards[discard_seat]))
        self.assertIsNone(state.last_discard)
        self.assertIsNone(state.last_discarded_by)

    def test_chi_turn_passes_to_caller(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import encode_chi

        state = GameState()
        state.last_discarded_by = 3  # North
        state.turn_index = 0  # East
        tile = Tile("Sou", 4, 21)
        state.last_discard = tile
        state.discards["North"].append(tile)

        player = state.get_current_player()
        player.hand.clear()
        player.hand.extend([Tile("Sou", 3, 20), Tile("Sou", 5, 22)])

        action_id = encode_chi([20, 21, 22])
        state.awaiting_discard = False
        state.step(action_id)

        self.assertEqual(state.turn_index, 0)  # caller keeps the turn
        self.assertTrue(state.awaiting_discard)

    def test_illegal_chi_action_raises(self):
        from engine.tile import Tile
        from engine.game_state import GameState
        from engine.action_space import encode_chi

        state = GameState()
        state.turn_index = 1
        state.last_discarded_by = 0
        tile = Tile("Man", 4, 3)
        state.last_discard = tile
        state.discards["East"].append(tile)

        player = state.get_current_player()
        player.hand.clear()
        player.hand.append(Tile("Man", 2, 1))  # missing one tile for CHI

        action_id = encode_chi([1, 2, 3])  # invalid chi: [1,2,3] but missing 2

        state.awaiting_discard = True
        with self.assertRaises(ValueError):
            state.step(action_id)
    
    def test_reward_logic_basic(self):
        state = GameState()
        player = state.players[0]

        # Simulate 4 melds for player 0
        for _ in range(4):
            player.melds.append(("PON", ["Man 1", "Man 1", "Man 1"]))

        self.assertTrue(state.is_terminal())
        self.assertEqual(state.get_reward(0), 1.0)
        self.assertEqual(state.get_reward(1), 0.0)
        self.assertEqual(state.get_reward(2), 0.0)
        self.assertEqual(state.get_reward(3), 0.0)

        

if __name__ == "__main__":
    unittest.main()
# tests/test_player.py

import unittest
from engine.player import Player

class TestPlayer(unittest.TestCase):
    def test_player_initialization(self):
        player = Player("East")
        self.assertEqual(player.seat, "East")
        self.assertEqual(player.hand, [])
        self.assertEqual(player.melds, [])
    
    def test_draw_tile(self):
        from engine.tile import Tile
        player = Player("South")
        tile = Tile("Man", 3, 2)
        player.draw_tile(tile)
        self.assertIn(tile, player.hand)
        self.assertEqual(len(player.hand), 1)
        self.assertEqual(player.hand[0].category, "Man")
        self.assertEqual(player.hand[0].value, 3)

    def test_discard_tile(self):
        from engine.tile import Tile
        player = Player("West")
        tile = Tile("Pin", 6, 14)
        player.draw_tile(tile)
        discarded = player.discard_tile(tile)
        self.assertEqual(discarded, tile)
        self.assertNotIn(tile, player.hand)
        self.assertEqual(len(player.hand), 0)
    
    def test_can_pon(self):
        from engine.tile import Tile
        player = Player("North")
        tile = Tile("Sou", 7, 24)
        player.draw_tile(tile)
        player.draw_tile(tile)
        self.assertTrue(player.can_pon(tile))
        player.draw_tile(Tile("Sou", 1, 18))  # unrelated tile
        player.discard_tile(tile)
        self.assertFalse(player.can_pon(tile))  # only one copy left
    
    def test_can_chi(self):
        from engine.player import Player
        from engine.tile import Tile
        # Setup Player South
        player = Player(seat="South")
        player.hand = [
            Tile("Man", 2, 0),
            Tile("Man", 4, 2),
            Tile("Sou", 9, 33)
        ]
        tile3 = Tile("Man", 3, 1)  # the discard
        # Chinese rules: Valid CHI from any seat (just check tile compatibility)
        self.assertTrue(player.can_chi(tile3, "East"))
        self.assertTrue(player.can_chi(tile3, "West"))
        self.assertTrue(player.can_chi(tile3, "North"))
        # Still invalid from own seat (but this is handled in game_state logic)
        # Here we just test that the tile sequence is valid regardless of seat
        self.assertTrue(player.can_chi(tile3, "South"))

    def test_call_meld(self):
        from engine.tile import Tile
        tile = Tile("Pin", 2, 10)
        player = Player("South")

        # Draw two matching tiles
        player.draw_tile(tile)
        player.draw_tile(tile)

        # Declare Pon using those two tiles
        player.call_meld("PON", [tile, tile])

        self.assertEqual(len(player.hand), 0)
        self.assertEqual(len(player.melds), 1)
        self.assertEqual(player.melds[0][0], "PON")
        self.assertEqual(player.melds[0][1], [tile, tile])

    def test_can_ankan(self):
        from engine.tile import Tile
        player = Player("East")

        # Give player four identical tiles (e.g. 4× Man 1)
        tile = Tile("Man", 1, 0)
        for _ in range(4):
            player.draw_tile(tile)

        self.assertTrue(player.can_ankan(tile))

        # Remove one tile — should fail
        player.discard_tile(tile)
        self.assertFalse(player.can_ankan(tile))


if __name__ == '__main__':
    unittest.main()
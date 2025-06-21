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
        from engine.tile import Tile
        player = Player("East")
        tile3 = Tile("Man", 3, 2)
        tile4 = Tile("Man", 4, 3)
        tile5 = Tile("Man", 5, 4)

        player.draw_tile(tile3)
        player.draw_tile(tile5)

        # Legal Chi from left
        self.assertTrue(player.can_chi(tile4, "South"))  # South is left of East

        # Illegal Chi from non-left seat
        self.assertFalse(player.can_chi(tile4, "North"))

        # Illegal Chi if one tile is missing
        player.discard_tile(tile3)
        self.assertFalse(player.can_chi(tile4, "South"))

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
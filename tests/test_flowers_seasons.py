import unittest
from engine.tile import Tile

class TestFlowersSeasons(unittest.TestCase):
    
    def test_regular_tiles_not_bonus(self):
        """Test that regular tiles return False for is_bonus_tile"""
        regular_tiles = [
            Tile("Man", 1, 0),
            Tile("Pin", 5, 13),
            Tile("Sou", 9, 26),
            Tile("Wind", "East", 27),
            Tile("Dragon", "Red", 31)
        ]
        
        for tile in regular_tiles:
            self.assertFalse(tile.is_bonus_tile(), 
                           f"{tile} should not be a bonus tile")
    
    def test_flower_tiles_are_bonus(self):
        """Test that Flower tiles return True for is_bonus_tile"""
        flower_tiles = [
            Tile("Flower", "Plum", 34),
            Tile("Flower", "Orchid", 35),
            Tile("Flower", "Chrysanthemum", 36),
            Tile("Flower", "Bamboo", 37)
        ]
        
        for tile in flower_tiles:
            self.assertTrue(tile.is_bonus_tile(),
                          f"{tile} should be a bonus tile")
    
    def test_season_tiles_are_bonus(self):
        """Test that Season tiles return True for is_bonus_tile"""
        season_tiles = [
            Tile("Season", "Spring", 38),
            Tile("Season", "Summer", 39),
            Tile("Season", "Autumn", 40),
            Tile("Season", "Winter", 41)
        ]
        
        for tile in season_tiles:
            self.assertTrue(tile.is_bonus_tile(),
                          f"{tile} should be a bonus tile")
            
    def test_wall_contains_144_tiles_with_bonus(self):
        """Test that generate_wall() now produces 144 tiles including 8 bonus tiles"""
        from engine.wall import generate_wall
        
        wall = generate_wall()
        
        # Total should be 144 (136 regular + 8 bonus)
        self.assertEqual(len(wall), 144)
        
        # Count bonus tiles
        bonus_tiles = [t for t in wall if t.is_bonus_tile()]
        self.assertEqual(len(bonus_tiles), 8)
        
        # Count flowers and seasons specifically
        flowers = [t for t in wall if t.category == "Flower"]
        seasons = [t for t in wall if t.category == "Season"]
        self.assertEqual(len(flowers), 4)
        self.assertEqual(len(seasons), 4)
        
        # Verify specific flower/season names exist
        flower_names = {t.value for t in flowers}
        season_names = {t.value for t in seasons}
        
        expected_flowers = {"Plum", "Orchid", "Chrysanthemum", "Bamboo"}
        expected_seasons = {"Spring", "Summer", "Autumn", "Winter"}
        
        self.assertEqual(flower_names, expected_flowers)
        self.assertEqual(season_names, expected_seasons)

    def test_player_bonus_tile_storage(self):
        """Test that players can store bonus tiles separately from hand"""
        from engine.player import Player
        from engine.tile import Tile
        
        player = Player("East")
        
        # Initially no bonus tiles
        self.assertEqual(len(player.bonus_tiles), 0)
        
        # Add a flower tile
        flower = Tile("Flower", "Plum", 34)
        result = player.add_bonus_tile(flower)
        
        self.assertTrue(result)
        self.assertEqual(len(player.bonus_tiles), 1)
        self.assertEqual(player.bonus_tiles[0], flower)
        self.assertEqual(len(player.hand), 0)  # Should not affect hand
        
        # Add a season tile
        season = Tile("Season", "Spring", 38)
        result = player.add_bonus_tile(season)
        
        self.assertTrue(result)
        self.assertEqual(len(player.bonus_tiles), 2)
        
        # Try to add regular tile (should fail)
        regular = Tile("Man", 1, 0)
        result = player.add_bonus_tile(regular)
        
        self.assertFalse(result)
        self.assertEqual(len(player.bonus_tiles), 2)  # Should stay same

    
    def test_auto_replacement_mechanism(self):
        """Test that drawing a bonus tile triggers automatic replacement"""
        from engine.game_state import GameState
        from engine.tile import Tile
        
        state = GameState()
        player = state.get_current_player()
        
        # Force a flower tile to be on top of wall
        flower_tile = Tile("Flower", "Plum", 34)
        regular_tile = Tile("Man", 1, 0)
        
        # Clear wall and add our test tiles
        state.wall = [regular_tile, flower_tile]  # flower on top (last item = top)
        
        hand_size_before = len(player.hand)
        bonus_before = len(player.bonus_tiles)
        wall_size_before = len(state.wall)
        
        # Draw phase - should get flower + auto-replacement
        state.step()
        
        # Check results
        self.assertEqual(len(player.hand), hand_size_before + 1, "Hand should grow by 1 (replacement tile)")
        self.assertEqual(len(player.bonus_tiles), bonus_before + 1, "Should have 1 bonus tile")
        self.assertEqual(len(state.wall), wall_size_before - 2, "Wall should lose 2 tiles (flower + replacement)")
        self.assertEqual(player.bonus_tiles[-1].category, "Flower", "Bonus tile should be the flower")

    def test_action_space_updated_for_bonus_tiles(self):
        """Test that action space constants account for bonus tiles"""
        from engine import action_space
        
        # Should now be 42 tile types (34 regular + 8 bonus)
        self.assertEqual(action_space.NUM_TILE_TYPES, 42)
        
        # Discard actions should cover all tile types
        self.assertEqual(len(action_space.DISCARD_ACTIONS), 42)
        self.assertEqual(action_space.DISCARD_ACTIONS[-1], 41)  # Last discard action

    def test_bonus_tile_scoring(self):
        """Test that flowers/seasons add to Chinese scoring"""
        from engine.game_state import GameState
        from engine.tile import Tile
        
        state = GameState()
        player = state.players[0]
        
        # Set up a basic winning hand (4 sequences + pair)
        player.hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),  # seq 1
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),  # seq 2
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11), # seq 3
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14), # seq 4
            Tile("Sou", 1, 18), Tile("Sou", 1, 19)  # pair
        ]
        
        # Add some bonus tiles
        player.bonus_tiles = [
            Tile("Flower", "Plum", 34),
            Tile("Season", "Spring", 38)
        ]
        
        # Force this to be a winning hand for scoring
        state.winners = [0]
        
        score = state.get_hand_score(player)
        
        # Should get base score (2) + 2 bonus tiles (2) = at least 4
        self.assertGreaterEqual(score, 4, "Should get points for bonus tiles")

if __name__ == '__main__':
    unittest.main()
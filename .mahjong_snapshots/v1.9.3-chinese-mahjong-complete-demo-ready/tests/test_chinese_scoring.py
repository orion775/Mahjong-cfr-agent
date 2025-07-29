# tests/test_chinese_scoring.py

import unittest
import os
from engine.game_state import GameState
from engine.tile import Tile

class TestChineseScoring(unittest.TestCase):
    
    def test_basic_win_score(self):
        """Test that any basic win gets minimum 2 points"""
        state = GameState()
        player = state.players[0]
        
        # Clear and set up basic winning hand
        player.hand.clear()
        player.melds.clear()
        
        # 4 sequences + pair (basic win)
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),
            Tile("Sou", 1, 18), Tile("Sou", 1, 19)  # pair
        ])
        
        score = state.get_hand_score(player)
        self.assertGreaterEqual(score, 2, "Basic win should score at least 2 points")
    
    def test_all_one_suit_bonus(self):
        """Test that all-one-suit hands get +6 bonus"""
        state = GameState()
        player = state.players[0]
        
        player.hand.clear()
        player.melds.clear()
        
        # All Man tiles (清一色)
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Man", 9, 8),
            Tile("Man", 1, 3), Tile("Man", 2, 4), Tile("Man", 3, 5),
            Tile("Man", 5, 4), Tile("Man", 5, 4)  # pair
        ])
        
        score = state.get_hand_score(player)
        self.assertGreaterEqual(score, 8, "All-one-suit should score 2+6=8+ points")
    
    def test_kan_bonus_scoring(self):
        """Test that KAN melds add +2 points each"""
        state = GameState()
        player = state.players[0]
        
        player.hand.clear() 
        player.melds.clear()
        
        # Use the exact same winning hand from test_basic_win_score
        # but replace one sequence with a KAN meld
        
        # 3 sequences + 1 pair = 3*3 + 2 = 11 tiles in hand
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),        # sequence 1
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),      # sequence 2  
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),     # sequence 3
            Tile("Sou", 1, 18), Tile("Sou", 1, 19)                          # pair
        ])
        
        # Add 1 KAN meld (4 tiles) 
        # Total: 11 (hand) + 4 (KAN) = 15 tiles (still wrong!)
        
        # Correct approach: 2 sequences + 1 pair in hand = 9 tiles
        # + 1 KAN meld = 4 tiles  
        # Total = 13 tiles (need 1 more)
        
        # Final correct: 2 sequences + 1 pair + 1 triplet in hand = 12 tiles
        # Then move the triplet to KAN meld = 12 - 3 + 4 = 13 tiles (still need 1)
        
        # Actually simplest: Just use 14 tiles that form a valid win
        player.hand = [
            # This is a known working 14-tile hand from another test
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5), 
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),
            Tile("Sou", 1, 18), Tile("Sou", 1, 19)
        ]
        
        # Add a KAN meld (this makes it 18 tiles total, but let's see if scoring works)
        kan_tiles = [Tile("Man", 9, 8)] * 4  # Different tile not in hand
        player.melds.append(("KAN", kan_tiles))
        
        # Manually override the win check for this test
        original_check = state.check_player_win
        state.check_player_win = lambda p: p == player
        
        score = state.get_hand_score(player)
        
        # Restore original check
        state.check_player_win = original_check
        
        print(f"Score with KAN override: {score}")
        
        # Base (2) + 1 KAN meld (2) = 4 minimum
        self.assertGreaterEqual(score, 4, "1 KAN meld should add 2 points")
    
    def test_no_win_zero_score(self):
        """Test that non-winning hands score 0"""
        state = GameState()
        player = state.players[0]
        
        player.hand.clear()
        player.melds.clear()
        
        # Incomplete hand (not a win)
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Pin", 1, 9), Tile("Pin", 2, 10)  # Only 5 tiles, not a win
        ])
        
        score = state.get_hand_score(player)
        self.assertEqual(score, 0, "Non-winning hand should score 0")
    
    def test_game_summary_file_creation(self):
        """Test that get_game_summary creates a readable text file"""
        state = GameState()
        player = state.players[0]
        
        # Set up a win scenario
        player.hand.clear()
        player.melds.clear()
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),
            Tile("Sou", 1, 18), Tile("Sou", 1, 19)
        ])
        
        # Force terminal and winner
        state._terminal = True
        state.winners = [0]
        
        # Generate summary
        test_filename = "test_game_summary.txt"
        state.get_game_summary(test_filename)
        
        # Check file was created and has content
        self.assertTrue(os.path.exists(test_filename), "Summary file should be created")
        
        with open(test_filename, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("MAHJONG GAME SUMMARY", content)
            self.assertIn("PLAYER 0: East", content)
            self.assertIn("Chinese Score:", content)
            self.assertIn("CFR Reward:", content)
        
        # Clean up
        os.remove(test_filename)
    
    def test_cfr_reward_vs_chinese_score_separation(self):
        """Test that CFR rewards stay simple while Chinese scores are detailed"""
        state = GameState()
        player = state.players[0]
        
        # Set up high-scoring Chinese hand
        player.hand.clear()
        player.melds.clear()
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # All same suit
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8),  # + terminals
            Tile("Man", 3, 2), Tile("Man", 4, 3), Tile("Man", 5, 4),
            Tile("Man", 6, 5), Tile("Man", 7, 6), Tile("Man", 8, 7),
            Tile("Man", 2, 1), Tile("Man", 2, 1)  # pair
        ])
        
        # Force winner
        state.winners = [0]
        
        chinese_score = state.get_hand_score(player)
        cfr_reward = state.get_reward(0)
        
        # Chinese score should be high (all one suit + other bonuses)
        self.assertGreater(chinese_score, 6, "High-value Chinese hand should score >6")
        
        # CFR reward should stay simple
        self.assertEqual(cfr_reward, 1.0, "CFR reward should remain 1.0 for any win")

if __name__ == '__main__':
    unittest.main()
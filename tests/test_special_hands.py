# tests/test_special_hands.py

import unittest
from engine.tile import Tile
from engine.game_state import GameState, is_winning_hand, check_seven_pairs, check_thirteen_orphans

class TestSpecialHands(unittest.TestCase):
    
    def test_seven_pairs_win_on_draw(self):
        """Test Seven Pairs win by drawing the final tile"""
        state = GameState()
        player = state.players[0]  # East player
        
        # Clear the player's hand and set up 6 pairs + 1 single tile
        player.hand.clear()
        player.melds.clear()
        
        # 6 complete pairs
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 1, 0),    # Pair 1: Man 1
            Tile("Man", 2, 1), Tile("Man", 2, 1),    # Pair 2: Man 2  
            Tile("Pin", 1, 9), Tile("Pin", 1, 9),    # Pair 3: Pin 1
            Tile("Pin", 2, 10), Tile("Pin", 2, 10),  # Pair 4: Pin 2
            Tile("Sou", 1, 18), Tile("Sou", 1, 18),  # Pair 5: Sou 1
            Tile("Wind", "East", 27), Tile("Wind", "East", 27),  # Pair 6: East
            Tile("Dragon", "Red", 33)  # Single Red Dragon (needs pair)
        ])
        
        # Verify starting state
        self.assertEqual(len(player.hand), 13, "Player should have 13 tiles before draw")
        self.assertFalse(is_winning_hand(player.hand), "Should not be winning with 13 tiles")
        
        # Set up wall with the winning tile (second Red Dragon)
        state.wall.clear()
        winning_tile = Tile("Dragon", "Red", 33)
        state.wall.append(winning_tile)
        
        # Set up game state for draw
        state.turn_index = 0  # East's turn
        state.awaiting_discard = False  # Ready to draw
        
        # Draw the winning tile
        state.step()  # This should draw the winning tile
        
        # Verify the draw
        self.assertEqual(len(player.hand), 14, "Player should have 14 tiles after draw")
        
        # Count Red Dragons in hand (should be 2 now)
        red_dragons = [t for t in player.hand if t.category == "Dragon" and t.value == "Red"]
        self.assertEqual(len(red_dragons), 2, "Should have 2 Red Dragons after draw")
        
        # Test Seven Pairs win detection (should succeed now)
        result = is_winning_hand(player.hand)
        self.assertTrue(result, "Seven Pairs should be recognized as a winning hand")
        
        # Verify we have exactly 7 different tile types (all pairs)
        from collections import Counter
        counts = Counter((t.category, t.value) for t in player.hand)
        self.assertEqual(len(counts), 7, "Should have exactly 7 different tile types")
        
        # Verify all tiles appear exactly twice
        for count in counts.values():
            self.assertEqual(count, 2, f"All tiles should appear exactly twice, got counts: {dict(counts)}")
        
        print(f"DEBUG: Seven Pairs hand: {[(t.category, t.value) for t in player.hand]}")
        print(f"DEBUG: Tile counts: {dict(counts)}")
    
    def test_seven_pairs_with_triplet_fails(self):
        """Test that a hand with a triplet is not Seven Pairs"""
        state = GameState()
        player = state.players[0]
        player.hand.clear()
        
        # Hand with triplet: 5 pairs + 1 triplet + 1 single = 14 tiles
        player.hand.extend([
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Triplet (3 tiles)
            Tile("Man", 2, 1), Tile("Man", 2, 1),    # Pair (2 tiles)
            Tile("Pin", 1, 9), Tile("Pin", 1, 9),    # Pair (2 tiles)
            Tile("Pin", 2, 10), Tile("Pin", 2, 10),  # Pair (2 tiles)
            Tile("Sou", 1, 18), Tile("Sou", 1, 18),  # Pair (2 tiles)
            Tile("Wind", "East", 27), Tile("Wind", "East", 27),  # Pair (2 tiles)
            Tile("Dragon", "Red", 33),  # Single (1 tile)
            # Total: 3 + 2 + 2 + 2 + 2 + 2 + 1 = 14 tiles
        ])
        
        self.assertEqual(len(player.hand), 14, "Should have 14 tiles")
        
        # This should NOT be Seven Pairs (has triplet)
        self.assertFalse(check_seven_pairs(player.hand), "Should not be Seven Pairs due to triplet")
        
        # This should also NOT be a standard win (incomplete structure)
        self.assertFalse(is_winning_hand(player.hand), "Should not be any kind of win")

    def test_standard_win_still_works(self):
        """Test that standard 4 melds + 1 pair still works after Seven Pairs addition"""
        state = GameState()
        player = state.players[0]
        player.hand.clear()
        
        # Standard winning hand: 4 sequences + 1 pair
        player.hand.extend([
            # Sequence 1: Man 1-2-3
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            # Sequence 2: Man 4-5-6  
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            # Sequence 3: Pin 1-2-3
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
            # Sequence 4: Pin 4-5-6
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),
            # Pair: Sou 1
            Tile("Sou", 1, 18), Tile("Sou", 1, 18)
        ])
        
        self.assertEqual(len(player.hand), 14, "Should have 14 tiles")
        
        # This should NOT be Seven Pairs (has sequences)
        self.assertFalse(check_seven_pairs(player.hand), "Should not be Seven Pairs (has sequences)")
        
        # This SHOULD be a standard win
        self.assertTrue(is_winning_hand(player.hand), "Should be a standard winning hand")
        
        print(f"DEBUG: Standard win hand structure verified")

    def test_thirteen_orphans_win_on_draw(self):
        """Test Thirteen Orphans win by drawing the final tile"""
        state = GameState()
        player = state.players[0]  # East player
        
        # Clear the player's hand
        player.hand.clear()
        player.melds.clear()
        
        # Set up 12 different terminals/honors + 1 duplicate (13 tiles)
        # Terminals: 1M, 9M, 1P, 9P, 1S, 9S (6 tiles)
        # Honors: East, South, West, North, Red, Green, White (7 tiles)
        # Total: 13 different types, need 1 duplicate for win
        player.hand.extend([
            # Terminals (1s and 9s)
            Tile("Man", 1, 0),     # 1 Man
            Tile("Man", 9, 8),     # 9 Man  
            Tile("Pin", 1, 9),     # 1 Pin
            Tile("Pin", 9, 17),    # 9 Pin
            Tile("Sou", 1, 18),    # 1 Sou
            Tile("Sou", 9, 26),    # 9 Sou
            # All Winds
            Tile("Wind", "East", 27),   # East
            Tile("Wind", "South", 28),  # South  
            Tile("Wind", "West", 29),   # West
            Tile("Wind", "North", 30),  # North
            # All Dragons  
            Tile("Dragon", "Red", 33),    # Red Dragon
            Tile("Dragon", "Green", 32),  # Green Dragon
            Tile("Dragon", "White", 31),  # White Dragon
            # Missing: Need 1 duplicate of any of the above 13 types
        ])
        
        # Verify starting state
        self.assertEqual(len(player.hand), 13, "Player should have 13 tiles before draw")
        self.assertFalse(is_winning_hand(player.hand), "Should not be winning with 13 tiles")
        
        # Set up wall with winning tile (duplicate of any terminal/honor)
        # Let's use another East Wind as the winning tile
        state.wall.clear()
        winning_tile = Tile("Wind", "East", 27)  # Duplicate East Wind
        state.wall.append(winning_tile)
        
        # Set up game state for draw
        state.turn_index = 0  # East's turn
        state.awaiting_discard = False  # Ready to draw
        
        # Draw the winning tile
        state.step()  # This should draw the winning tile
        
        # Verify the draw
        self.assertEqual(len(player.hand), 14, "Player should have 14 tiles after draw")
        
        # Count East Winds in hand (should be 2 now)
        east_winds = [t for t in player.hand if t.category == "Wind" and t.value == "East"]
        self.assertEqual(len(east_winds), 2, "Should have 2 East Winds after draw")
        
        # Test Thirteen Orphans win detection (should succeed now)
        result = is_winning_hand(player.hand)
        self.assertTrue(result, "Thirteen Orphans should be recognized as a winning hand")
        
        # Verify we have exactly 13 different terminal/honor types + 1 duplicate
        from collections import Counter
        counts = Counter((t.category, t.value) for t in player.hand)
        
        # Should have 13 different types (12 singles + 1 pair)
        self.assertEqual(len(counts), 13, "Should have exactly 13 different tile types")
        
        # Should have exactly one pair (count = 2) and twelve singles (count = 1)
        count_values = list(counts.values())
        self.assertEqual(count_values.count(2), 1, "Should have exactly 1 pair")
        self.assertEqual(count_values.count(1), 12, "Should have exactly 12 singles")
        
        print(f"DEBUG: Thirteen Orphans hand: {[(t.category, t.value) for t in player.hand]}")
        print(f"DEBUG: Tile counts: {dict(counts)}")

if __name__ == '__main__':
    unittest.main()
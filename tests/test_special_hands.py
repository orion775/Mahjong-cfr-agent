# tests/test_special_hands.py

import unittest
from engine.tile import Tile
from engine.game_state import GameState, is_winning_hand, _can_form_melds
from engine.special_hands import check_seven_pairs, check_thirteen_orphans, check_all_honors, check_all_terminals

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

    def test_all_honors_valid_hand(self):
        """Test that check_all_honors() correctly identifies pure honor hands"""
        hand = [
            # East wind triplet
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            # South wind triplet  
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            # West wind triplet
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            # Red dragon triplet
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31),
            # White dragon pair
            Tile("Dragon", "White", 33), Tile("Dragon", "White", 33)
        ]
        
        print(f"All Honors test hand: {[(t.category, t.value) for t in hand]}")
        # Test the specific All Honors function (this WILL fail until we implement it)
        result = check_all_honors(hand)
        print(f"check_all_honors result: {result}")
        self.assertTrue(result, "Pure honor hand should be All Honors")

    def test_all_honors_mixed_with_suits_invalid(self):
        """Test that check_all_honors() rejects hands with suit tiles"""
        hand = [
            # Honor tiles
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31),
            # Mixed with suit tiles - should not be All Honors
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Pin", 5, 13), Tile("Pin", 5, 13), Tile("Pin", 5, 13),
            # Pair
            Tile("Sou", 9, 26), Tile("Sou", 9, 26)
        ]
        
        print(f"Mixed hand test: {[(t.category, t.value) for t in hand]}")
        # This should be False for All Honors (even if it's a winning hand)
        result = check_all_honors(hand)
        print(f"check_all_honors result: {result}")
        self.assertFalse(result, "Mixed hand should not be All Honors")
        
    def test_all_terminals_valid_hand(self):
        """Test that check_all_terminals() correctly identifies hands with only 1s and 9s"""
        hand = [
            # Man 1 triplet
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            # Man 9 triplet
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8),
            # Pin 1 triplet
            Tile("Pin", 1, 9), Tile("Pin", 1, 9), Tile("Pin", 1, 9),
            # Sou 9 triplet
            Tile("Sou", 9, 26), Tile("Sou", 9, 26), Tile("Sou", 9, 26),
            # Pin 9 pair
            Tile("Pin", 9, 17), Tile("Pin", 9, 17)
        ]
        
        print(f"All Terminals test hand: {[(t.category, t.value) for t in hand]}")
        result = check_all_terminals(hand)
        print(f"check_all_terminals result: {result}")
        self.assertTrue(result, "Pure terminals hand should be All Terminals")
    
    def test_all_terminals_mixed_with_middle_tiles_invalid(self):
        """Test that check_all_terminals() rejects hands with middle tiles (2-8)"""
        hand = [
            # Valid terminals
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8),
            # Mixed with middle tiles - should not be All Terminals
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
            Tile("Sou", 5, 22), Tile("Sou", 5, 22), Tile("Sou", 5, 22),
            # Pair
            Tile("Sou", 9, 26), Tile("Sou", 9, 26)
        ]
        
        print(f"Mixed terminals test: {[(t.category, t.value) for t in hand]}")
        result = check_all_terminals(hand)
        print(f"check_all_terminals result: {result}")
        self.assertFalse(result, "Hand with middle tiles should not be All Terminals")
    
    def test_all_one_suit_man_valid(self):
        """Test valid All One Suit hand with Man tiles only"""
        from engine.special_hands import check_all_one_suit
        
        # All Man tiles: sequences and triplets
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Triplet
            Tile("Man", 2, 1), Tile("Man", 3, 2), Tile("Man", 4, 3),  # Sequence  
            Tile("Man", 5, 4), Tile("Man", 6, 5), Tile("Man", 7, 6),  # Sequence
            Tile("Man", 8, 7), Tile("Man", 8, 7), Tile("Man", 8, 7),  # Triplet
            Tile("Man", 9, 8), Tile("Man", 9, 8)                      # Pair
        ]
        
        self.assertTrue(check_all_one_suit(hand))
    def test_all_one_suit_mixed_suits_invalid(self):
        """Test that mixed suits invalidate All One Suit"""
        from engine.special_hands import check_all_one_suit
        
        # Mix of Man and Pin tiles
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),  # Different suit!
            Tile("Man", 5, 4), Tile("Man", 6, 5), Tile("Man", 7, 6),
            Tile("Man", 8, 7), Tile("Man", 8, 7), Tile("Man", 8, 7),
            Tile("Man", 9, 8), Tile("Man", 9, 8)
        ]
        
        self.assertFalse(check_all_one_suit(hand))
    
    def test_all_one_suit_integrated_win_detection(self):
        """Test that All One Suit hands are detected as wins by main win function"""
        from engine.game_state import is_winning_hand
        
        # All Pin tiles forming valid hand structure
        hand = [
            Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),   # Sequence
            Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),  # Sequence
            Tile("Pin", 7, 15), Tile("Pin", 8, 16), Tile("Pin", 9, 17),  # Sequence
            Tile("Pin", 1, 9), Tile("Pin", 1, 9), Tile("Pin", 1, 9),     # Triplet
            Tile("Pin", 2, 10), Tile("Pin", 2, 10)                       # Pair
        ]
        
        self.assertTrue(is_winning_hand(hand))
    
    def test_big_three_dragons_valid(self):
        """Test valid Big Three Dragons hand"""
        from engine.special_hands import check_big_three_dragons
        
        # Three dragon triplets + one sequence + one pair
        hand = [
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31),       # Red triplet
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), # Green triplet  
            Tile("Dragon", "White", 33), Tile("Dragon", "White", 33), Tile("Dragon", "White", 33), # White triplet
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),                              # Sequence
            Tile("Pin", 5, 13), Tile("Pin", 5, 13)                                                 # Pair
        ]
        
        self.assertTrue(check_big_three_dragons(hand))
    
    def test_big_three_dragons_missing_dragon_invalid(self):
        """Test that missing a dragon triplet invalidates Big Three Dragons"""
        from engine.special_hands import check_big_three_dragons
        
        # Only Red and Green dragon triplets, missing White dragon triplet
        hand = [
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31),       # Red triplet
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), # Green triplet
            Tile("Dragon", "White", 33), Tile("Dragon", "White", 33),                              # Only 2 White (not triplet)
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),                              # Sequence
            Tile("Pin", 5, 13), Tile("Pin", 6, 14), Tile("Pin", 7, 15)                            # Another sequence
        ]
        
        self.assertFalse(check_big_three_dragons(hand))
    
    def test_big_three_dragons_integrated_win_detection(self):
        """Test that Big Three Dragons hands are detected as wins by main win function"""
        from engine.game_state import is_winning_hand
        
        # Big Three Dragons - exactly 14 tiles
        hand = [
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31),       # Red triplet (3)
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), # Green triplet (3) 
            Tile("Dragon", "White", 33), Tile("Dragon", "White", 33), Tile("Dragon", "White", 33), # White triplet (3)
            Tile("Sou", 7, 24), Tile("Sou", 8, 25), Tile("Sou", 9, 26),                           # Sequence (3)
            Tile("Wind", "East", 27), Tile("Wind", "East", 27)                                     # Pair (2)
        ]  # Total: 3+3+3+3+2 = 14 tiles
        
        self.assertTrue(is_winning_hand(hand))
    
    def test_little_four_winds_valid(self):
        """Test valid Little Four Winds hand"""
        from engine.special_hands import check_little_four_winds
        
        # Three wind triplets + one wind pair + one other meld - exactly 14 tiles
        hand = [
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),     # East triplet (3)
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28), # South triplet (3)
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),    # West triplet (3)
            Tile("Wind", "North", 30), Tile("Wind", "North", 30),                            # North pair (2)
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2)                         # Sequence (3)
        ]  # Total: 3+3+3+2+3 = 14 tiles
        
        self.assertTrue(check_little_four_winds(hand))
    
    def test_little_four_winds_missing_wind_invalid(self):
        """Test that missing a wind type invalidates Little Four Winds"""
        from engine.special_hands import check_little_four_winds
        
        # Only 3 wind types (missing North), not Little Four Winds
        hand = [
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),     # East triplet
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28), # South triplet
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),    # West triplet
            # Missing North wind entirely
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),                        # Sequence
            Tile("Pin", 5, 13), Tile("Pin", 5, 13)                                          # Pair
        ]
        
        self.assertFalse(check_little_four_winds(hand))
    
    def test_little_four_winds_integrated_win_detection(self):
        """Test that Little Four Winds hands are detected as wins by main win function"""
        from engine.game_state import is_winning_hand
        
        # Little Four Winds with different meld structure - exactly 14 tiles
        hand = [
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),     # East triplet (3)
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28), # South triplet (3)
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),    # West triplet (3)
            Tile("Wind", "North", 30), Tile("Wind", "North", 30),                            # North pair (2)
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31)  # Red triplet (3)
        ]  # Total: 3+3+3+2+3 = 14 tiles
        
        self.assertTrue(is_winning_hand(hand))


if __name__ == '__main__':
    unittest.main()
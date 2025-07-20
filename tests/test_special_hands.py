# tests/test_special_hands.py

import unittest
from engine.tile import Tile
from engine.game_state import GameState, is_winning_hand
from engine.special_hands import (
    check_seven_pairs, check_thirteen_orphans, check_all_honors, 
    check_all_terminals, is_big_four_winds, _can_form_melds, check_all_green
    ,check_nine_gates
)

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

    def test_big_four_winds_valid(self):
        """Test valid Big Four Winds hand"""
        hand = [
            # East triplet
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            # South triplet  
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            # West triplet
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            # North triplet
            Tile("Wind", "North", 30), Tile("Wind", "North", 30), Tile("Wind", "North", 30),
            # Any pair (e.g., Red Dragon)
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31)
        ]
        
        self.assertTrue(is_big_four_winds(hand))

    def test_big_four_winds_with_kans(self):
        """Test Big Four Winds with some KANs (quads)"""
        hand = [
            # East quad
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), 
            Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            # South triplet
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            # West triplet
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            # North triplet  
            Tile("Wind", "North", 30), Tile("Wind", "North", 30), Tile("Wind", "North", 30),
            # Pair (Man 1)
            Tile("Man", 1, 0), Tile("Man", 1, 0)
        ]
        
        self.assertTrue(is_big_four_winds(hand))

    def test_big_four_winds_invalid_missing_wind(self):
        """Test invalid Big Four Winds - missing one wind"""
        hand = [
            # East triplet
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            # South triplet
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            # West triplet  
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            # Missing North, have other tiles instead
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            # Pair
            Tile("Dragon", "Red", 31), Tile("Dragon", "Red", 31)
        ]
        
        self.assertFalse(is_big_four_winds(hand))

    def test_big_four_winds_invalid_wind_pair(self):
        """Test invalid Big Four Winds - has wind pair instead of triplet"""
        hand = [
            # East triplet
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            # South triplet
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            # West triplet
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            # North pair (should be triplet)
            Tile("Wind", "North", 30), Tile("Wind", "North", 30),
            # Fill with other tiles
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 2, 1)
        ]
        
        self.assertFalse(is_big_four_winds(hand))

    def test_big_four_winds_integration_with_game_state(self):
        """Test Big Four Winds detection integrated with game state"""
        from engine.game_state import is_winning_hand
        
        hand = [
            # Four wind triplets
            Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
            Tile("Wind", "South", 28), Tile("Wind", "South", 28), Tile("Wind", "South", 28),
            Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29),
            Tile("Wind", "North", 30), Tile("Wind", "North", 30), Tile("Wind", "North", 30),
            # Pair
            Tile("Dragon", "White", 33), Tile("Dragon", "White", 33)
        ]
        
        self.assertTrue(is_winning_hand(hand))

    def test_all_green_valid(self):
        """Test valid All Green hand"""
        hand = [
            # Green bamboos: 2,3,4,6,8
            Tile("Sou", 2, 19), Tile("Sou", 2, 19), Tile("Sou", 2, 19),  # 2 Bamboo triplet
            Tile("Sou", 3, 20), Tile("Sou", 3, 20), Tile("Sou", 3, 20),  # 3 Bamboo triplet
            Tile("Sou", 4, 21), Tile("Sou", 4, 21), Tile("Sou", 4, 21),  # 4 Bamboo triplet
            Tile("Sou", 6, 23), Tile("Sou", 6, 23), Tile("Sou", 6, 23),  # 6 Bamboo triplet
            # Green Dragon pair
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32)
        ]
        
        self.assertTrue(check_all_green(hand))

    def test_all_green_with_sequences(self):
        """Test All Green with sequences (chows)"""
        hand = [
            # Green sequences
            Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),  # 2-3-4 sequence
            Tile("Sou", 3, 20), Tile("Sou", 4, 21), Tile("Sou", 6, 23),  # 3-4-6 is invalid sequence
            Tile("Sou", 6, 23), Tile("Sou", 8, 25), Tile("Sou", 2, 19),  # Non-consecutive
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32),
            # Pair
            Tile("Sou", 4, 21), Tile("Sou", 4, 21)
        ]
        
        self.assertTrue(check_all_green(hand))

    def test_all_green_invalid_wrong_bamboo(self):
        """Test invalid All Green - contains non-green bamboo"""
        hand = [
            # Contains 5 Bamboo (not green)
            Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),
            Tile("Sou", 5, 22), Tile("Sou", 6, 23), Tile("Sou", 8, 25),  # 5 is not green!
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32),
            Tile("Sou", 2, 19), Tile("Sou", 2, 19), Tile("Sou", 3, 20),
            Tile("Sou", 4, 21), Tile("Sou", 6, 23)
        ]
        
        self.assertFalse(check_all_green(hand))

    def test_all_green_invalid_other_suit(self):
        """Test invalid All Green - contains non-bamboo tiles"""
        hand = [
            # Contains Man tiles (not green)
            Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),  # Not green!
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32),
            Tile("Sou", 6, 23), Tile("Sou", 6, 23), Tile("Sou", 8, 25),
            Tile("Sou", 8, 25), Tile("Sou", 2, 19)
        ]
        
        self.assertFalse(check_all_green(hand))

    def test_all_green_integration_with_game_state(self):
        """Test All Green detection integrated with game state"""
        from engine.game_state import is_winning_hand
        
        hand = [
            # All green tiles
            Tile("Sou", 2, 19), Tile("Sou", 2, 19), Tile("Sou", 2, 19),
            Tile("Sou", 3, 20), Tile("Sou", 3, 20), Tile("Sou", 3, 20),
            Tile("Sou", 4, 21), Tile("Sou", 4, 21), Tile("Sou", 4, 21),
            Tile("Sou", 6, 23), Tile("Sou", 6, 23), Tile("Sou", 6, 23),
            Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32)
        ]
        
        self.assertTrue(is_winning_hand(hand))

    def test_nine_gates_valid_man_suit(self):
        """Test valid Nine Gates in Man suit"""
        hand = [
            # Pattern: 1112345678999 + extra 5
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Three 1s
            Tile("Man", 2, 1),                                        # One 2
            Tile("Man", 3, 2),                                        # One 3
            Tile("Man", 4, 3),                                        # One 4
            Tile("Man", 5, 4),                                        # One 5
            Tile("Man", 6, 5),                                        # One 6
            Tile("Man", 7, 6),                                        # One 7
            Tile("Man", 8, 7),                                        # One 8
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8), # Three 9s
            Tile("Man", 5, 4)                                         # Extra 5 (14th tile)
        ]
        
        self.assertTrue(check_nine_gates(hand))

    def test_nine_gates_valid_pin_suit(self):
        """Test valid Nine Gates in Pin suit"""
        hand = [
            # Pattern: 1112345678999 + extra 1
            Tile("Pin", 1, 9), Tile("Pin", 1, 9), Tile("Pin", 1, 9),   # Three 1s
            Tile("Pin", 2, 10),                                         # One 2
            Tile("Pin", 3, 11),                                         # One 3
            Tile("Pin", 4, 12),                                         # One 4
            Tile("Pin", 5, 13),                                         # One 5
            Tile("Pin", 6, 14),                                         # One 6
            Tile("Pin", 7, 15),                                         # One 7
            Tile("Pin", 8, 16),                                         # One 8
            Tile("Pin", 9, 17), Tile("Pin", 9, 17), Tile("Pin", 9, 17), # Three 9s
            Tile("Pin", 1, 9)                                           # Extra 1 (14th tile)
        ]
        
        self.assertTrue(check_nine_gates(hand))

    def test_nine_gates_invalid_mixed_suits(self):
        """Test invalid Nine Gates - mixed suits"""
        hand = [
            # Mixed Man and Pin (not pure suit)
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            Tile("Man", 2, 1), Tile("Man", 3, 2), Tile("Man", 4, 3),
            Tile("Pin", 5, 13), Tile("Pin", 6, 14), Tile("Pin", 7, 15),  # Wrong suit!
            Tile("Man", 8, 7),
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8),
            Tile("Man", 5, 4)
        ]
        
        self.assertFalse(check_nine_gates(hand))

    def test_nine_gates_invalid_wrong_pattern(self):
        """Test invalid Nine Gates - wrong tile pattern"""
        hand = [
            # Wrong pattern: 1122345678999 (two 1s, two 2s instead of three 1s, one 2)
            Tile("Sou", 1, 18), Tile("Sou", 1, 18),                    # Only two 1s
            Tile("Sou", 2, 19), Tile("Sou", 2, 19),                    # Two 2s
            Tile("Sou", 3, 20), Tile("Sou", 4, 21), Tile("Sou", 5, 22),
            Tile("Sou", 6, 23), Tile("Sou", 7, 24), Tile("Sou", 8, 25),
            Tile("Sou", 9, 26), Tile("Sou", 9, 26), Tile("Sou", 9, 26),
            Tile("Sou", 5, 22)
        ]
        
        self.assertFalse(check_nine_gates(hand))

    def test_nine_gates_invalid_honors(self):
        """Test invalid Nine Gates - contains honor tiles"""
        hand = [
            # Contains Wind tile (honor) - not allowed
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
            Tile("Man", 2, 1), Tile("Man", 3, 2), Tile("Man", 4, 3),
            Tile("Man", 5, 4), Tile("Man", 6, 5), Tile("Man", 7, 6),
            Tile("Wind", "East", 27),                                   # Honor tile!
            Tile("Man", 9, 8), Tile("Man", 9, 8), Tile("Man", 9, 8),
            Tile("Man", 5, 4)
        ]
        
        self.assertFalse(check_nine_gates(hand))

    def test_nine_gates_integration_with_game_state(self):
        """Test Nine Gates detection integrated with game state"""
        from engine.game_state import is_winning_hand
        
        hand = [
            # Perfect Nine Gates pattern
            Tile("Sou", 1, 18), Tile("Sou", 1, 18), Tile("Sou", 1, 18),
            Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),
            Tile("Sou", 5, 22), Tile("Sou", 6, 23), Tile("Sou", 7, 24),
            Tile("Sou", 8, 25),
            Tile("Sou", 9, 26), Tile("Sou", 9, 26), Tile("Sou", 9, 26),
            Tile("Sou", 9, 26)  # Extra 9 as 14th tile
        ]
        
        self.assertTrue(is_winning_hand(hand))


if __name__ == '__main__':
    unittest.main()
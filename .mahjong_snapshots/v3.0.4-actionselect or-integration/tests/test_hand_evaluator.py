# tests/test_hand_evaluator.py

import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cfr_modules.hand_evaluator import HandEvaluator
from engine.tile import Tile

class TestHandEvaluator(unittest.TestCase):
    
    def setUp(self):
        self.evaluator = HandEvaluator()
    
    def test_count_triplet_potential_empty_hand(self):
        """Test with empty hand should return 0."""
        result = self.evaluator.count_triplet_potential([])
        self.assertEqual(result, 0)
        print("✓ Empty hand test passed")
    
    def test_count_triplet_potential_no_pairs(self):
        """Test hand with no pairs (all singles) should return 0."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6)
        ]
        result = self.evaluator.count_triplet_potential(hand)
        self.assertEqual(result, 0)
        print("✓ No pairs test passed")
    
    def test_count_triplet_potential_one_pair(self):
        """Test hand with exactly one pair should return 1."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0),  # One pair
            Tile("Man", 2, 1), Tile("Man", 3, 2), Tile("Man", 4, 3)
        ]
        result = self.evaluator.count_triplet_potential(hand)
        self.assertEqual(result, 1)
        print("✓ One pair test passed")
    
    def test_count_triplet_potential_multiple_pairs(self):
        """Test hand with multiple pairs should count all of them."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0),      # Pair 1
            Tile("Man", 3, 2), Tile("Man", 3, 2),      # Pair 2  
            Tile("Wind", "East", 27), Tile("Wind", "East", 27),  # Pair 3
            Tile("Man", 2, 1)  # Single
        ]
        result = self.evaluator.count_triplet_potential(hand)
        self.assertEqual(result, 3)
        print("✓ Multiple pairs test passed")
    
    def test_count_triplet_potential_with_triplets(self):
        """Test that existing triplets (3-of-a-kind) are not counted as pairs."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Triplet (not pair)
            Tile("Man", 2, 1), Tile("Man", 2, 1),  # Pair
            Tile("Man", 3, 2)
        ]
        result = self.evaluator.count_triplet_potential(hand)
        self.assertEqual(result, 1)  # Only the pair of 2m counts
        print("✓ Triplet exclusion test passed")

    def test_count_sequence_potential_basic(self):
        """Test hand with clear sequence potential should count correctly."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1),  # 1m-2m sequence potential
            Tile("Pin", 7, 15), Tile("Pin", 8, 16),  # 7p-8p sequence potential
            Tile("Wind", "East", 27)  # Honor tile (no sequence potential)
        ]
        result = self.evaluator.count_sequence_potential(hand)
        self.assertEqual(result, 4)  # All 4 suited tiles have sequence potential
        print("✓ Basic sequence potential test passed")
    
    def test_count_sequence_potential_no_wraparound(self):
        """Test that 8-9 with 1 does NOT count as sequence potential (no wraparound)."""
        hand = [
            Tile("Sou", 8, 25), Tile("Sou", 9, 26),  # 8s-9s
            Tile("Sou", 1, 18)  # 1s (should NOT connect with 8s-9s)
        ]
        result = self.evaluator.count_sequence_potential(hand)
        self.assertEqual(result, 2)  # Only 8s-9s count, 1s is isolated
        print("✓ No wraparound test passed")
    
    def test_count_pairs_mixed_hand(self):
        """Test counting pairs in hand with singles, pairs, and triplets."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0),  # Pair (count this)
            Tile("Man", 2, 1), Tile("Man", 2, 1), Tile("Man", 2, 1),  # Triplet (don't count)
            Tile("Pin", 5, 13), Tile("Pin", 5, 13),  # Pair (count this)
            Tile("Wind", "East", 27)  # Single (don't count)
        ]
        result = self.evaluator.count_pairs(hand)
        self.assertEqual(result, 2)  # Only 1m and 5p pairs count
        print("✓ Mixed hand pairs test passed")
    
    def test_count_complete_melds_triplet_and_sequence(self):
        """Test counting complete melds with both triplets and sequences."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Triplet
            Tile("Pin", 5, 13), Tile("Pin", 6, 14), Tile("Pin", 7, 15),  # Sequence
            Tile("Sou", 8, 25), Tile("Wind", "East", 27)  # Singles (no melds)
        ]
        result = self.evaluator.count_complete_melds(hand)
        self.assertEqual(result, 2)  # 1 triplet + 1 sequence = 2 melds
        print("✓ Complete melds test passed")

    def test_count_isolated_tiles_mixed_connections(self):
        """Test counting isolated tiles with various connection types."""
        hand = [
            Tile("Man", 1, 0), Tile("Man", 1, 0),  # Paired (not isolated)
            Tile("Man", 3, 2), Tile("Man", 4, 3),  # Sequence potential (not isolated)
            Tile("Pin", 9, 17),  # Isolated (no connections)
            Tile("Wind", "East", 27),  # Isolated (honor tile, single)
            Tile("Dragon", "Red", 33)  # Isolated (honor tile, single)
        ]
        result = self.evaluator.count_isolated_tiles(hand)
        self.assertEqual(result, 3)  # 9p, East, Red are isolated
        print("✓ Isolated tiles test passed")
if __name__ == "__main__":
    unittest.main()
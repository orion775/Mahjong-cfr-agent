# tests/test_game_state_evaluator.py

"""
Test Suite for GameStateEvaluator Module

Comprehensive testing for all GameStateEvaluator functions using TDD approach.
Tests verify numerical accuracy and edge case handling for visible game state analysis.

Testing Philosophy:
- Test one function at a time with immediate validation
- Cover normal cases, edge cases, and error conditions
- Use controlled test data with known expected outcomes
- Validate both structure and correctness of returned values
"""

import unittest
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cfr_modules.game_state_evaluator import count_dead_tiles, count_available_tiles, get_left_opponent_discards, calculate_tile_likelihood,estimate_meld_completion_risk,analyze_discard_patterns,count_suit_concentration,measure_honor_vs_suited_ratio
from engine.tile import Tile


class TestCountDeadTiles(unittest.TestCase):
    """Test suite for count_dead_tiles() function"""
    
    def test_count_dead_tiles_basic_functionality(self):
        """Test basic dead tile counting functionality"""
        man_1_tiles = [Tile("Man", 1, 0), Tile("Man", 1, 0)]
        discards = {
            "East": [man_1_tiles[0]],
            "South": [man_1_tiles[1]],
            "West": [],
            "North": []
        }
        
        result = count_dead_tiles(0, discards)  # Man 1 tile_id = 0
        self.assertEqual(result, 2, "Should count 2 discarded Man 1 tiles")
    
    def test_count_dead_tiles_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid discards type
        with self.assertRaises(TypeError):
            count_dead_tiles(0, "not_a_dict")
        
        # Test invalid tile_type
        with self.assertRaises(ValueError):
            count_dead_tiles(-1, {"East": [], "South": [], "West": [], "North": []})


class TestCountAvailableTiles(unittest.TestCase):
    """Test suite for count_available_tiles() function"""
    
    def test_count_available_tiles_basic_functionality(self):
        """Test basic available tile counting"""
        man_1_tiles = [Tile("Man", 1, 0), Tile("Man", 1, 0)]
        discards = {"East": [man_1_tiles[0]], "South": [], "West": [], "North": []}
        visible_melds = [[man_1_tiles[1], Tile("Man", 2, 1), Tile("Man", 3, 2)]]  # 1 Man 1 in meld
        
        result = count_available_tiles(0, discards, visible_melds)
        self.assertEqual(result, 2, "Should have 2 available: 4 - 1 discarded - 1 in meld")
    
    def test_count_available_tiles_error_handling(self):
        """Test error handling for invalid inputs"""
        discards = {"East": [], "South": [], "West": [], "North": []}
        
        # Test invalid visible_melds type
        with self.assertRaises(TypeError):
            count_available_tiles(0, discards, "not_a_list")
        
        # Test invalid tile_type
        with self.assertRaises(ValueError):
            count_available_tiles(-1, discards, [])


class TestGetLeftOpponentDiscards(unittest.TestCase):
    """Test suite for get_left_opponent_discards() function"""
    
    def test_get_left_opponent_discards_basic_functionality(self):
        """Test correct left opponent identification"""
        sample_discards = {
            "East": [Tile("Man", 1, 0), Tile("Pin", 5, 13)],
            "South": [Tile("Dragon", "Red", 31)],
            "West": [Tile("Wind", "North", 30)],
            "North": [Tile("Man", 9, 8)]
        }
        
        # Test clockwise order: East's left is North, South's left is East
        self.assertEqual(get_left_opponent_discards("East", sample_discards), 
                        sample_discards["North"], "East's left should be North")
        self.assertEqual(get_left_opponent_discards("South", sample_discards), 
                        sample_discards["East"], "South's left should be East")
    
    def test_get_left_opponent_discards_error_handling(self):
        """Test error handling for invalid inputs"""
        sample_discards = {"East": [], "South": [], "West": [], "North": []}
        
        # Test invalid seat
        with self.assertRaises(ValueError):
            get_left_opponent_discards("InvalidSeat", sample_discards)
        
        # Test invalid discards type
        with self.assertRaises(TypeError):
            get_left_opponent_discards("East", "not_a_dict")


class TestCalculateTileLikelihood(unittest.TestCase):
    """Test suite for calculate_tile_likelihood() function"""
    
    def test_calculate_tile_likelihood_basic_functionality(self):
        """Test basic tile likelihood calculation"""
        opponent_discards = [
            Tile("Man", 1, 0),      # 1 Man 1 discarded
            Tile("Pin", 5, 13),     # Other tiles
            Tile("Dragon", "Red", 31)
        ]
        
        # 1 Man 1 discarded, so 3 remaining out of 4 = 0.75 likelihood
        result = calculate_tile_likelihood(0, opponent_discards)  # Man 1
        self.assertEqual(result, 0.75, "Should be 0.75: (4-1)/4 = 3/4")
        
        # No Pin 2 discarded, so 4 remaining out of 4 = 1.0 likelihood  
        result = calculate_tile_likelihood(10, opponent_discards)  # Pin 2
        self.assertEqual(result, 1.0, "Should be 1.0: (4-0)/4 = 4/4")
    
    def test_calculate_tile_likelihood_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid tile_type
        with self.assertRaises(ValueError):
            calculate_tile_likelihood(-1, [])
        
        # Test invalid opponent_discards type
        with self.assertRaises(TypeError):
            calculate_tile_likelihood(0, "not_a_list")

    
class TestEstimateMeldCompletionRisk(unittest.TestCase):
    """Test suite for estimate_meld_completion_risk() function"""
    
    def test_estimate_meld_completion_risk_basic_functionality(self):
        """Test basic risk calculation"""
        tile_candidates = [0, 13]  # Man 1, Pin 5
        opponent_patterns = {
            "East": {"recent_discards": [Tile("Man", 1, 0)]},  # Same as candidate 0
            "South": {"recent_discards": [Tile("Pin", 4, 12)]}  # Sequential to candidate 13
        }
        
        result = estimate_meld_completion_risk(tile_candidates, opponent_patterns)
        
        self.assertIn(0, result, "Should have risk score for tile 0")
        self.assertIn(13, result, "Should have risk score for tile 13")
        self.assertTrue(0.0 <= result[0] <= 1.0, "Risk scores should be 0.0-1.0")
    
    def test_estimate_meld_completion_risk_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid tile_candidates type
        with self.assertRaises(TypeError):
            estimate_meld_completion_risk("not_a_list", {})
        
        # Test invalid opponent_patterns type  
        with self.assertRaises(TypeError):
            estimate_meld_completion_risk([0], "not_a_dict")
class TestAnalyzeDiscardPatterns(unittest.TestCase):
    """Test suite for analyze_discard_patterns() function"""
    
    def test_analyze_discard_patterns_basic_functionality(self):
        """Test basic pattern analysis"""
        opponent_discards = [
            Tile("Man", 1, 0),      # Terminal
            Tile("Man", 5, 4),      # Man suit
            Tile("Pin", 9, 17),     # Terminal  
            Tile("Wind", "East", 27)  # Honor
        ]
        
        result = analyze_discard_patterns(opponent_discards)
        
        self.assertEqual(result["total_discards"], 4)
        self.assertEqual(result["suit_distribution"]["Man"], 2)
        self.assertEqual(result["honor_count"], 1)
        self.assertEqual(result["terminal_count"], 2)
        self.assertIn(result["recent_focus"], ["Man", "Pin", "None"])
    
    def test_analyze_discard_patterns_error_handling(self):
        """Test error handling and empty input"""
        # Test invalid input type
        with self.assertRaises(TypeError):
            analyze_discard_patterns("not_a_list")
        
        # Test empty list
        result = analyze_discard_patterns([])
        self.assertEqual(result["total_discards"], 0)
        self.assertEqual(result["recent_focus"], "None")

class TestCountSuitConcentration(unittest.TestCase):
    """Test suite for count_suit_concentration() function"""
    
    def test_count_suit_concentration_basic_functionality(self):
        """Test basic suit concentration calculation"""
        opponent_discards = [
            Tile("Man", 1, 0),      # Man suit
            Tile("Man", 5, 4),      # Man suit  
            Tile("Pin", 3, 11),     # Pin suit
            Tile("Wind", "East", 27)  # Honor (ignored for suit analysis)
        ]
        
        result = count_suit_concentration(opponent_discards)
        
        # Should have lower Man concentration (more discards) and higher Pin/Sou
        self.assertTrue(0.0 <= result["Man"] <= 1.0)
        self.assertTrue(0.0 <= result["Pin"] <= 1.0)
        self.assertIn(result["concentration_suit"], ["Man", "Pin", "Sou", "None"])
        self.assertEqual(result["max_concentration"], max(result["Man"], result["Pin"], result["Sou"]))
    
    def test_count_suit_concentration_error_handling(self):
        """Test error handling and edge cases"""
        # Test invalid input type
        with self.assertRaises(TypeError):
            count_suit_concentration("not_a_list")
        
        # Test empty list
        result = count_suit_concentration([])
        self.assertEqual(result["max_concentration"], 0.0)
        self.assertEqual(result["concentration_suit"], "None")

class TestMeasureHonorVsSuitedRatio(unittest.TestCase):
    """Test suite for measure_honor_vs_suited_ratio() function"""
    
    def test_measure_honor_vs_suited_ratio_basic_functionality(self):
        """Test basic honor vs suited ratio calculation"""
        opponent_discards = [
            Tile("Wind", "East", 27),     # Honor
            Tile("Dragon", "Red", 31),    # Honor
            Tile("Man", 1, 0),            # Suited
            Tile("Pin", 5, 13)            # Suited
        ]
        
        result = measure_honor_vs_suited_ratio(opponent_discards)
        
        self.assertEqual(result["honor_discards"], 2)
        self.assertEqual(result["suited_discards"], 2)
        self.assertEqual(result["total_analyzed"], 4)
        self.assertEqual(result["honor_ratio"], 0.5)
        self.assertEqual(result["suited_ratio"], 0.5)
        self.assertEqual(result["composition"], "Balanced")
    
    def test_measure_honor_vs_suited_ratio_error_handling(self):
        """Test error handling and edge cases"""
        # Test invalid input type
        with self.assertRaises(TypeError):
            measure_honor_vs_suited_ratio("not_a_list")
        
        # Test empty list
        result = measure_honor_vs_suited_ratio([])
        self.assertEqual(result["composition"], "No_Data")
        self.assertEqual(result["total_analyzed"], 0)

if __name__ == '__main__':
    print("Running GameStateEvaluator Tests...")
    print("=" * 50)
    
    # Run all test classes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCountDeadTiles))
    suite.addTests(loader.loadTestsFromTestCase(TestCountAvailableTiles))
    suite.addTests(loader.loadTestsFromTestCase(TestGetLeftOpponentDiscards))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculateTileLikelihood))
    suite.addTests(loader.loadTestsFromTestCase(TestEstimateMeldCompletionRisk))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyzeDiscardPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestCountSuitConcentration))
    suite.addTests(loader.loadTestsFromTestCase(TestMeasureHonorVsSuitedRatio))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All GameStateEvaluator tests PASSED!")
        print("Ready to implement next function.")
    else:
        print("❌ Some tests FAILED. Fix implementation before proceeding.")
    
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")  

    
# tests/test_action_selector.py

"""
Test Suite for ActionSelector Module

Comprehensive testing for ActionSelector functions using TDD approach.
Tests verify integration of HandEvaluator and GameStateEvaluator outputs
and validate utility score calculations for CFR learning.

Testing Philosophy:
- Test one function at a time with immediate validation
- Cover normal cases, edge cases, and error conditions  
- Validate both structure and correctness of utility scores
- Ensure proper integration of HandEvaluator + GameStateEvaluator
"""

import unittest
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from cfr_modules.action_selector import evaluate_discard_options, select_optimal_discard, assess_meld_opportunity, combine_hand_and_state_analysis, generate_action_recommendations, calculate_action_utilities
from engine.tile import Tile


class TestEvaluateDiscardOptions(unittest.TestCase):
    """Test suite for evaluate_discard_options() function"""
    
    def test_evaluate_discard_options_basic_functionality(self):
        """Test basic discard evaluation with multiple options"""
        # Create test hand with variety of tiles
        hand = [
            Tile("Man", 1, 0),     # Isolated tile - should score higher for discard
            Tile("Man", 2, 1),     # Part of potential sequence
            Tile("Man", 3, 2),     # Part of potential sequence  
            Tile("Pin", 5, 13),    # Another tile
            Tile("Pin", 5, 14),    # Pair - potential triplet
            Tile("Wind", "East", 27)  # Honor tile
        ]
        
        # Create discard actions for first 3 tiles
        available_actions = [
            {"type": "discard", "tile": hand[0]},  # Man 1 - isolated
            {"type": "discard", "tile": hand[1]},  # Man 2 - sequence potential
            {"type": "discard", "tile": hand[2]}   # Man 3 - sequence potential
        ]
        
        # Create game state with some discards
        game_state = {
            "discards": {
                "East": [Tile("Man", 1, 0)],      # One Man 1 already discarded
                "South": [Tile("Pin", 9, 17)],    # Other discards
                "West": [],
                "North": []
            },
            "visible_melds": {
                "East": [], "South": [], "West": [], "North": []
            },
            "current_seat": "East"
        }
        
        result = evaluate_discard_options(hand, available_actions, game_state)
        
        # Validate structure
        self.assertIsInstance(result, dict, "Should return dictionary")
        self.assertEqual(len(result), 3, "Should have 3 utility scores")
        
        # Validate score ranges
        for action_index, score in result.items():
            self.assertIn(action_index, [0, 1, 2], "Action index should match input")
            self.assertTrue(0.0 <= score <= 1.0, f"Score {score} should be in [0.0, 1.0]")
        
        # Isolated tile (Man 1) should generally score higher for discard
        # since it has less meld potential and one copy is already discarded
        isolated_score = result[0]
        sequence_scores = [result[1], result[2]]
        
        # Isolated tile should have higher discard utility than at least one sequence tile
        self.assertTrue(
            isolated_score >= min(sequence_scores),
            f"Isolated tile score {isolated_score} should be >= min sequence score {min(sequence_scores)}"
        )
    
    def test_evaluate_discard_options_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_hand = [Tile("Man", 1, 0)]
        valid_actions = [{"type": "discard", "tile": Tile("Man", 1, 0)}]
        valid_game_state = {
            "discards": {"East": [], "South": [], "West": [], "North": []},
            "visible_melds": {"East": [], "South": [], "West": [], "North": []},
            "current_seat": "East"
        }
        
        # Test invalid hand type
        with self.assertRaises(TypeError):
            evaluate_discard_options("not_a_list", valid_actions, valid_game_state)
        
        # Test invalid available_actions type
        with self.assertRaises(TypeError):
            evaluate_discard_options(valid_hand, "not_a_list", valid_game_state)
            
        # Test invalid game_state type
        with self.assertRaises(TypeError):
            evaluate_discard_options(valid_hand, valid_actions, "not_a_dict")
        
        # Test missing required keys in game_state
        incomplete_game_state = {"discards": {}}  # Missing visible_melds, current_seat
        with self.assertRaises(KeyError):
            evaluate_discard_options(valid_hand, valid_actions, incomplete_game_state)
        
        # Test empty actions (should return empty dict, not error)
        empty_actions = []
        result = evaluate_discard_options(valid_hand, empty_actions, valid_game_state)
        self.assertEqual(result, {}, "Empty actions should return empty dict")
        
        # Test non-discard actions (should return empty dict)
        non_discard_actions = [{"type": "chi", "tiles": []}]
        result = evaluate_discard_options(valid_hand, non_discard_actions, valid_game_state)
        self.assertEqual(result, {}, "Non-discard actions should return empty dict")


class TestSelectOptimalDiscard(unittest.TestCase):
    """Test suite for select_optimal_discard() function"""
    
    def test_select_optimal_discard_basic_functionality(self):
        """Test basic optimal discard selection"""
        # Create test hand
        hand = [
            Tile("Man", 1, 0),     # Isolated tile - should be optimal discard
            Tile("Man", 2, 1),     # Part of sequence
            Tile("Man", 3, 2),     # Part of sequence
            Tile("Pin", 5, 13),    # Another tile
        ]
        
        # Create game state metrics with available actions
        game_state_metrics = {
            "discards": {
                "East": [Tile("Man", 1, 0)],  # Man 1 already discarded (safer)
                "South": [], "West": [], "North": []
            },
            "visible_melds": {
                "East": [], "South": [], "West": [], "North": []
            },
            "current_seat": "East",
            "available_actions": [
                {"type": "discard", "tile": hand[0]},  # Man 1 - isolated
                {"type": "discard", "tile": hand[1]},  # Man 2 - sequence
                {"type": "discard", "tile": hand[3]},  # Pin 5 - isolated
            ]
        }
        
        result = select_optimal_discard(hand, game_state_metrics)
        
        # Validate structure
        self.assertIsInstance(result, dict, "Should return action dictionary")
        self.assertEqual(result["type"], "discard", "Should be discard action")
        self.assertIn("tile", result, "Should contain tile")
        self.assertIn("utility_score", result, "Should contain utility score")
        
        # Validate utility score range
        self.assertTrue(0.0 <= result["utility_score"] <= 1.0, 
                       "Utility score should be in [0.0, 1.0]")
        
        # The selected tile should be one of the available options
        selected_tile = result["tile"]
        available_tiles = [action["tile"] for action in game_state_metrics["available_actions"]]
        self.assertIn(selected_tile, available_tiles, "Selected tile should be from available actions")
    
    def test_select_optimal_discard_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_hand = [Tile("Man", 1, 0)]
        valid_metrics = {
            "discards": {"East": [], "South": [], "West": [], "North": []},
            "visible_melds": {"East": [], "South": [], "West": [], "North": []},
            "current_seat": "East",
            "available_actions": [{"type": "discard", "tile": Tile("Man", 1, 0)}]
        }
        
        # Test invalid hand type
        with self.assertRaises(TypeError):
            select_optimal_discard("not_a_list", valid_metrics)
        
        # Test invalid game_state_metrics type
        with self.assertRaises(TypeError):
            select_optimal_discard(valid_hand, "not_a_dict")
        
        # Test missing required keys
        incomplete_metrics = {"discards": {}}  # Missing other keys
        with self.assertRaises(KeyError):
            select_optimal_discard(valid_hand, incomplete_metrics)
        
        # Test no available actions (should return None, not error)
        no_actions_metrics = valid_metrics.copy()
        no_actions_metrics["available_actions"] = []
        result = select_optimal_discard(valid_hand, no_actions_metrics)
        self.assertIsNone(result, "No available actions should return None")
        
        # Test non-discard actions only (should return None)
        non_discard_metrics = valid_metrics.copy()
        non_discard_metrics["available_actions"] = [{"type": "chi", "tiles": []}]
        result = select_optimal_discard(valid_hand, non_discard_metrics)
        self.assertIsNone(result, "Non-discard actions should return None")


class TestAssessMeldOpportunity(unittest.TestCase):
    """Test suite for assess_meld_opportunity() function"""
    
    def test_assess_meld_opportunity_chi_basic_functionality(self):
        """Test basic CHI meld assessment"""
        # Create test hand that would benefit from CHI
        current_hand = [
            Tile("Man", 2, 1),     # Part of CHI sequence 1-2-3
            Tile("Man", 3, 2),     # Part of CHI sequence 1-2-3
            Tile("Pin", 5, 13),    # Unrelated tile
            Tile("Pin", 5, 14),    # Pair
            Tile("Wind", "East", 27)  # Honor tile
        ]
        
        # CHI action claiming Man 1 to complete 1-2-3 sequence
        meld_action = {
            "type": "chi",
            "tiles": [0, 1, 2],  # Man 1, Man 2, Man 3 tile IDs
            "claimed_tile": 0    # Man 1 from discard
        }
        
        game_state = {
            "current_hand": current_hand,
            "discards": {"East": [], "South": [], "West": [], "North": []},
            "visible_melds": {"East": [], "South": [], "West": [], "North": []},
            "current_seat": "East",
            "last_discard": Tile("Man", 1, 0)
        }
        
        result = assess_meld_opportunity(meld_action, game_state)
        
        # Validate structure
        self.assertIsInstance(result, dict, "Should return assessment dictionary")
        required_keys = ["utility_score", "hand_improvement", "strategic_value", "risk_factors"]
        for key in required_keys:
            self.assertIn(key, result, f"Should contain {key}")
        
        # Validate score ranges
        self.assertTrue(0.0 <= result["utility_score"] <= 1.0, 
                       "Utility score should be in [0.0, 1.0]")
        self.assertTrue(-1.0 <= result["hand_improvement"] <= 1.0,
                       "Hand improvement should be reasonable range")
        
        # CHI should have positive strategic value (sequence formation)
        self.assertGreater(result["strategic_value"], 0.5, 
                          "CHI should have above-average strategic value")
        
        # Risk factors should be present
        self.assertIn("exposure", result["risk_factors"])
        self.assertIn("efficiency", result["risk_factors"])
    
    def test_assess_meld_opportunity_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_meld_action = {
            "type": "pon",
            "tiles": [13, 14, 15],
            "claimed_tile": 15
        }
        valid_game_state = {
            "current_hand": [Tile("Pin", 5, 13), Tile("Pin", 5, 14)],
            "discards": {"East": [], "South": [], "West": [], "North": []},
            "visible_melds": {"East": [], "South": [], "West": [], "North": []},
            "current_seat": "East"
        }
        
        # Test invalid meld_action type
        with self.assertRaises(TypeError):
            assess_meld_opportunity("not_a_dict", valid_game_state)
        
        # Test invalid game_state type
        with self.assertRaises(TypeError):
            assess_meld_opportunity(valid_meld_action, "not_a_dict")
        
        # Test missing required keys in meld_action
        incomplete_meld = {"type": "chi"}  # Missing tiles
        with self.assertRaises(KeyError):
            assess_meld_opportunity(incomplete_meld, valid_game_state)
        
        # Test missing required keys in game_state
        incomplete_state = {"current_hand": []}  # Missing other keys
        with self.assertRaises(KeyError):
            assess_meld_opportunity(valid_meld_action, incomplete_state)
        
        # Test invalid meld type
        invalid_meld = {"type": "invalid_meld", "tiles": [1, 2, 3]}
        with self.assertRaises(ValueError):
            assess_meld_opportunity(invalid_meld, valid_game_state)
        
        # Test KAN meld (should work without error)
        kan_meld = {"type": "kan", "tiles": [13, 14, 15, 16]}
        result = assess_meld_opportunity(kan_meld, valid_game_state)
        self.assertIsInstance(result, dict)
        # KAN should have high strategic value due to replacement tile
        self.assertGreater(result["strategic_value"], 0.8, 
                          "KAN should have high strategic value")


class TestCombineHandAndStateAnalysis(unittest.TestCase):
    """Test suite for combine_hand_and_state_analysis() function"""
    
    def test_combine_hand_and_state_analysis_basic_functionality(self):
        """Test basic combination of hand and state metrics"""
        # Create comprehensive hand metrics
        hand_metrics = {
            "triplet_potential": 2,     # 2 near-triplets
            "sequence_potential": 3,    # 3 near-sequences
            "pairs_count": 1,           # 1 pair
            "complete_melds": 1,        # 1 completed meld
            "isolated_tiles": 3         # 3 isolated tiles
        }
        
        # Create state metrics with multiple components
        state_metrics = {
            "opponent_patterns": {
                "recent_focus": "Mixed",
                "total_discards": 8
            },
            "tile_safety": {
                0: 0.8,   # Man 1 quite safe
                1: 0.6,   # Man 2 moderate safety
                13: 0.9   # Pin 5 very safe
            },
            "availability_scores": {
                0: 0.75,  # Man 1 availability
                1: 0.5,   # Man 2 availability
                13: 0.25  # Pin 5 availability
            },
            "risk_assessments": {
                "meld_completion_risk": 0.3
            }
        }
        
        result = combine_hand_and_state_analysis(hand_metrics, state_metrics)
        
        # Validate structure
        self.assertIsInstance(result, dict, "Should return analysis dictionary")
        required_keys = ["hand_strength", "positional_advantage", "decision_priorities", "combined_score"]
        for key in required_keys:
            self.assertIn(key, result, f"Should contain {key}")
        
        # Validate score ranges
        self.assertTrue(0.0 <= result["hand_strength"] <= 1.0,
                       "Hand strength should be in [0.0, 1.0]")
        self.assertTrue(0.0 <= result["positional_advantage"] <= 1.0,
                       "Positional advantage should be in [0.0, 1.0]")
        self.assertTrue(0.0 <= result["combined_score"] <= 1.0,
                       "Combined score should be in [0.0, 1.0]")
        
        # Validate decision priorities structure
        priorities = result["decision_priorities"]
        self.assertIn("safety", priorities)
        self.assertIn("efficiency", priorities)
        self.assertIn("aggression", priorities)
        self.assertIn("defense", priorities)
        
        # Safety + efficiency should sum to 1.0
        self.assertAlmostEqual(priorities["safety"] + priorities["efficiency"], 1.0, places=5)
        # Aggression + defense should sum to 1.0
        self.assertAlmostEqual(priorities["aggression"] + priorities["defense"], 1.0, places=5)
        
        # Hand with some isolated tiles should not have maximum strength
        self.assertLess(result["hand_strength"], 0.9, 
                       "Hand with isolated tiles should not have max strength")
    
    def test_combine_hand_and_state_analysis_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_hand_metrics = {
            "triplet_potential": 1, "sequence_potential": 2, "pairs_count": 0,
            "complete_melds": 0, "isolated_tiles": 4
        }
        valid_state_metrics = {
            "opponent_patterns": {"recent_focus": "Man"},
            "tile_safety": {0: 0.5, 1: 0.7}
        }
        
        # Test invalid hand_metrics type
        with self.assertRaises(TypeError):
            combine_hand_and_state_analysis("not_a_dict", valid_state_metrics)
        
        # Test invalid state_metrics type
        with self.assertRaises(TypeError):
            combine_hand_and_state_analysis(valid_hand_metrics, "not_a_dict")
        
        # Test missing required keys in hand_metrics
        incomplete_hand = {"triplet_potential": 1}  # Missing other keys
        with self.assertRaises(KeyError):
            combine_hand_and_state_analysis(incomplete_hand, valid_state_metrics)
        
        # Test empty state_metrics (should fail - needs at least one component)
        empty_state = {}
        with self.assertRaises(KeyError):
            combine_hand_and_state_analysis(valid_hand_metrics, empty_state)
        
        # Test state_metrics with only one valid component (should work)
        minimal_state = {"tile_safety": {0: 0.5}}
        result = combine_hand_and_state_analysis(valid_hand_metrics, minimal_state)
        self.assertIsInstance(result, dict)
        self.assertIn("combined_score", result)


class TestGenerateActionRecommendations(unittest.TestCase):
    """Test suite for generate_action_recommendations() function"""
    
    def test_generate_action_recommendations_aggressive_strategy(self):
        """Test aggressive strategy generation for strong position"""
        # Strong hand with good position should generate aggressive strategy
        combined_analysis = {
            "hand_strength": 0.8,           # Strong hand
            "positional_advantage": 0.75,   # Good position
            "decision_priorities": {
                "safety": 0.3, "efficiency": 0.7,
                "aggression": 0.6, "defense": 0.4
            },
            "combined_score": 0.78          # High combined score
        }
        
        result = generate_action_recommendations(combined_analysis)
        
        # Validate structure
        self.assertIsInstance(result, dict, "Should return recommendations dictionary")
        required_keys = ["primary_strategy", "action_rankings", "risk_tolerance", 
                        "meld_preferences", "discard_guidance"]
        for key in required_keys:
            self.assertIn(key, result, f"Should contain {key}")
        
        # Strong position should yield aggressive strategy
        self.assertIn(result["primary_strategy"], 
                     ["aggressive_push", "balanced_aggressive"],
                     "Strong position should yield aggressive strategy")
        
        # Action rankings should prioritize melds
        self.assertIn("meld", result["action_rankings"][:2], 
                     "Strong hand should prioritize melds early")
        
        # Risk tolerance should be high for strong position
        self.assertGreater(result["risk_tolerance"], 0.6,
                          "Strong position should have high risk tolerance")
        
        # Meld preferences should sum to 1.0
        meld_total = sum(result["meld_preferences"].values())
        self.assertAlmostEqual(meld_total, 1.0, places=5)
        
        # Discard guidance should reflect efficiency priority
        guidance = result["discard_guidance"]
        self.assertGreater(guidance["efficiency_weight"], guidance["safety_weight"],
                          "Aggressive strategy should prioritize efficiency")
    
    def test_generate_action_recommendations_defensive_strategy(self):
        """Test defensive strategy generation for weak position"""
        # Weak hand with poor position should generate defensive strategy
        combined_analysis = {
            "hand_strength": 0.3,           # Weak hand
            "positional_advantage": 0.25,   # Poor position
            "decision_priorities": {
                "safety": 0.7, "efficiency": 0.3,
                "aggression": 0.3, "defense": 0.7
            },
            "combined_score": 0.28          # Low combined score
        }
        
        result = generate_action_recommendations(combined_analysis)
        
        # Weak position should yield defensive strategy
        self.assertIn(result["primary_strategy"], 
                     ["defensive", "balanced_conservative"],
                     "Weak position should yield defensive strategy")
        
        # Action rankings should prioritize safety
        self.assertIn("safe_discard", result["action_rankings"][:2],
                     "Weak hand should prioritize safe discards early")
        
        # Risk tolerance should be low for weak position
        self.assertLess(result["risk_tolerance"], 0.5,
                       "Weak position should have low risk tolerance")
        
        # CHI should be preferred over KAN/PON in defensive strategy
        meld_prefs = result["meld_preferences"]
        self.assertGreaterEqual(meld_prefs["chi"], meld_prefs["kan"],
                               "Defensive strategy should prefer CHI over KAN")
        
        # Discard guidance should reflect safety priority
        guidance = result["discard_guidance"]
        self.assertGreater(guidance["safety_weight"], guidance["efficiency_weight"],
                          "Defensive strategy should prioritize safety")
    
    def test_generate_action_recommendations_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_analysis = {
            "hand_strength": 0.5, "positional_advantage": 0.5,
            "decision_priorities": {"safety": 0.5, "efficiency": 0.5},
            "combined_score": 0.5
        }
        
        # Test invalid input type
        with self.assertRaises(TypeError):
            generate_action_recommendations("not_a_dict")
        
        # Test missing required keys
        incomplete_analysis = {"hand_strength": 0.5}  # Missing other keys
        with self.assertRaises(KeyError):
            generate_action_recommendations(incomplete_analysis)
        
        # Test valid minimal input
        result = generate_action_recommendations(valid_analysis)
        self.assertIsInstance(result, dict)
        
        # Ensure all returned values are in valid ranges
        self.assertTrue(0.0 <= result["risk_tolerance"] <= 1.0)
        self.assertIsInstance(result["action_rankings"], list)
        self.assertTrue(len(result["action_rankings"]) > 0)


class TestCalculateActionUtilities(unittest.TestCase):
    """Test suite for calculate_action_utilities() function"""
    
    def test_calculate_action_utilities_mixed_actions(self):
        """Test utility calculation for mixed action types"""
        # Create mixed actions list
        actions = [
            {"type": "discard", "tile": Tile("Man", 1, 0)},
            {"type": "chi", "tiles": [1, 2, 3], "claimed_tile": 2},
            {"type": "pon", "tiles": [13, 14, 15], "claimed_tile": 15},
            {"type": "pass"}
        ]
        
        # Create hand evaluator metrics
        hand_eval = {
            "triplet_potential": 2,
            "sequence_potential": 3, 
            "pairs_count": 1,
            "complete_melds": 0,
            "isolated_tiles": 3,
            "current_hand": [Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Pin", 5, 13)]
        }
        
        # Create state evaluator metrics
        state_eval = {
            "opponent_patterns": {"recent_focus": "Mixed"},
            "tile_safety": {0: 0.8, 1: 0.6, 13: 0.9},
            "availability_scores": {0: 0.75, 1: 0.5, 13: 0.25},
            "all_discards": {"East": [], "South": [], "West": [], "North": []}
        }
        
        result = calculate_action_utilities(actions, hand_eval, state_eval)
        
        # Validate structure
        self.assertIsInstance(result, list, "Should return list of utility scores")
        self.assertEqual(len(result), len(actions), "Should have one score per action")
        
        # Validate score ranges (CFR scale 0-100)
        for i, score in enumerate(result):
            self.assertTrue(0.0 <= score <= 100.0, 
                           f"Score {i} ({score}) should be in [0.0, 100.0]")
        
        # Basic utility expectations
        discard_utility = result[0]
        chi_utility = result[1]
        pon_utility = result[2]
        pass_utility = result[3]
        
        # Melds should generally have higher utility than PASS (unless very defensive)
        self.assertGreater(max(chi_utility, pon_utility), pass_utility,
                          "Melds should generally have higher utility than PASS")
        
        # All utilities should be reasonable CFR values
        for utility in result:
            self.assertGreater(utility, 10.0, "Utilities should be meaningful for CFR")
    
    def test_calculate_action_utilities_error_handling(self):
        """Test error handling for invalid inputs"""
        valid_actions = [{"type": "discard", "tile": Tile("Man", 1, 0)}]
        valid_hand_eval = {
            "triplet_potential": 1, "sequence_potential": 2, "pairs_count": 0,
            "complete_melds": 0, "isolated_tiles": 4
        }
        valid_state_eval = {"tile_safety": {0: 0.5}}
        
        # Test invalid actions type
        with self.assertRaises(TypeError):
            calculate_action_utilities("not_a_list", valid_hand_eval, valid_state_eval)
        
        # Test invalid hand_eval type
        with self.assertRaises(TypeError):
            calculate_action_utilities(valid_actions, "not_a_dict", valid_state_eval)
        
        # Test invalid state_eval type
        with self.assertRaises(TypeError):
            calculate_action_utilities(valid_actions, valid_hand_eval, "not_a_dict")
        
        # Test empty actions (should return empty list, not error)
        result = calculate_action_utilities([], valid_hand_eval, valid_state_eval)
        self.assertEqual(result, [], "Empty actions should return empty utilities")
        
        # Test with minimal valid data (should work with fallbacks)
        minimal_hand = {"triplet_potential": 0, "sequence_potential": 0, "pairs_count": 0,
                       "complete_melds": 0, "isolated_tiles": 1}
        minimal_state = {"tile_safety": {}}
        result = calculate_action_utilities(valid_actions, minimal_hand, minimal_state)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertTrue(0.0 <= result[0] <= 100.0)


if __name__ == '__main__':
    unittest.main()
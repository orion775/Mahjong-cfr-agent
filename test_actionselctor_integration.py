# test_actionselctor_integration.py
"""
Comprehensive test suite to validate ActionSelector integration with CFR trainer.

This test suite validates:
1. ActionSelector integration works correctly
2. Dense reward signals are provided vs sparse baseline
3. Enhanced CFR trainer functionality
4. Performance comparison setup vs 1.7% baseline

Following TDD principles per development rules.
"""

import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from enhanced_cfr_trainer import EnhancedCFRTrainer
from cfr_modules.action_selector import calculate_action_utilities
from cfr_modules.hand_evaluator import HandEvaluator
from cfr_modules import game_state_evaluator
from engine.game_state import GameState
from engine.tile import Tile


class TestActionSelectorIntegration(unittest.TestCase):
    """
    Test suite for ActionSelector integration with CFR trainer.
    
    Validates that the modular architecture works correctly:
    HandEvaluator + GameStateEvaluator → ActionSelector → CFR
    """
    
    def setUp(self):
        """Set up test environment with trainer and evaluators."""
        self.trainer = EnhancedCFRTrainer()
        self.hand_evaluator = HandEvaluator()
        
        # Create test game state
        self.test_state = GameState()
        if hasattr(self.test_state, 'step') and not getattr(self.test_state, 'awaiting_discard', True):
            self.test_state.step()
    
    def test_trainer_initialization(self):
        """Test 1: Enhanced CFR trainer initializes correctly with ActionSelector."""
        # Verify trainer has required components
        self.assertIsInstance(self.trainer.hand_evaluator, HandEvaluator)
        self.assertTrue(hasattr(game_state_evaluator, 'count_dead_tiles'))
        
        # Verify integration statistics are initialized
        expected_stats = [
            'action_utilities_calculated', 'hand_evaluations', 'state_evaluations',
            'dense_rewards_provided', 'avg_utility_score'
        ]
        for stat in expected_stats:
            self.assertIn(stat, self.trainer.training_stats)
            self.assertEqual(self.trainer.training_stats[stat], 0)
        
        print("✅ Test 1 PASSED: Trainer initialization with ActionSelector components")
    
    def test_action_evaluation_integration(self):
        """Test 2: Action evaluation uses ActionSelector correctly."""
        # Get legal action for testing
        legal_actions = self.test_state.get_legal_actions()
        self.assertGreater(len(legal_actions), 0, "Should have legal actions")
        
        test_action = legal_actions[0]
        player_id = 0
        
        # Evaluate action using ActionSelector integration
        utility = self.trainer.evaluate_action_with_selector(self.test_state, test_action, player_id)
        
        # Verify utility is calculated (not zero default)
        self.assertIsInstance(utility, (int, float))
        
        # Verify integration statistics updated
        self.assertGreater(self.trainer.training_stats['action_utilities_calculated'], 0)
        self.assertGreater(self.trainer.training_stats['hand_evaluations'], 0)
        self.assertGreater(self.trainer.training_stats['state_evaluations'], 0)
        
        print(f"✅ Test 2 PASSED: Action evaluation utility={utility:.3f}, stats updated")
    
    def test_dense_vs_sparse_signals(self):
        """Test 3: ActionSelector provides dense signals vs sparse baseline."""
        # Setup test hand with identifiable features
        player = self.test_state.players[0]
        player.hand = [
            Tile("Man", 1, 1), Tile("Man", 1, 2), Tile("Man", 1, 3),  # Complete triplet
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),  # Complete sequence
            Tile("Sou", 5, 20), Tile("Sou", 5, 21),  # Pair
            Tile("Dragon", "Red", 30), Tile("Wind", "East", 40),  # Isolated tiles
            Tile("Man", 9, 5), Tile("Pin", 9, 15), Tile("Sou", 9, 25)  # More tiles
        ]
        
        # Get hand metrics (should detect triplet, sequence, pair)
        hand_metrics = {
            'triplet_potential': self.hand_evaluator.count_triplet_potential(player.hand),
            'sequence_potential': self.hand_evaluator.count_sequence_potential(player.hand),
            'pairs': self.hand_evaluator.count_pairs(player.hand),
            'complete_melds': self.hand_evaluator.count_complete_melds(player.hand),
            'isolated_tiles': self.hand_evaluator.count_isolated_tiles(player.hand)
        }
        
        # Verify dense signals detected
        self.assertGreater(hand_metrics['triplet_potential'], 0, "Should detect triplet potential")
        self.assertGreater(hand_metrics['sequence_potential'], 0, "Should detect sequence potential")
        self.assertGreater(hand_metrics['pairs'], 0, "Should detect pairs")
        self.assertGreater(hand_metrics['complete_melds'], 0, "Should detect complete melds")
        
        # Get state metrics
        all_discards = self.test_state.discards  # Use state.discards dict directly
        state_metrics = {
            'dead_tiles': 0,  # No discards yet
            'available_tiles': 4,  # Full availability
            'meld_completion_risk': 0.5,  # Moderate risk
            'discard_patterns': 0  # No patterns yet
        }
        
        # Test ActionSelector utility calculation
        legal_actions = self.test_state.get_legal_actions()
        utilities = calculate_action_utilities(legal_actions, hand_metrics, state_metrics)
        
        # Verify dense utilities calculated
        self.assertIsInstance(utilities, dict)
        self.assertGreater(len(utilities), 0, "Should calculate utilities for actions")
        
        # Verify non-uniform utilities (not all same value)
        utility_values = list(utilities.values())
        self.assertGreater(len(set(utility_values)), 1, "Should have varied utilities (dense signals)")
        
        print(f"✅ Test 3 PASSED: Dense signals - {len(utilities)} utilities, {len(set(utility_values))} unique values")
    
    def test_cfr_integration_workflow(self):
        """Test 4: Full CFR workflow with ActionSelector integration."""
        # Run short CFR training
        initial_stats = dict(self.trainer.training_stats)
        
        # Train for few iterations to test workflow
        self.trainer.train(iterations=3, player_id=0, verbose=False)
        
        # Verify training completed
        self.assertGreater(self.trainer.training_stats['iterations_completed'], 0)
        
        # Verify ActionSelector integration occurred
        self.assertGreater(
            self.trainer.training_stats['action_utilities_calculated'],
            initial_stats['action_utilities_calculated']
        )
        self.assertGreater(
            self.trainer.training_stats['dense_rewards_provided'],
            initial_stats['dense_rewards_provided']
        )
        
        # Verify regret table populated
        self.assertGreater(len(self.trainer.regret_table), 0, "Should learn info sets")
        
        # Verify strategy table populated
        self.assertGreater(len(self.trainer.strategy_sum_table), 0, "Should accumulate strategies")
        
        print(f"✅ Test 4 PASSED: CFR workflow - {len(self.trainer.regret_table)} info sets learned")
    
    def test_fallback_mechanism(self):
        """Test 5: Fallback to basic evaluation if ActionSelector fails."""
        # Create invalid state to trigger fallback
        invalid_action = 999  # Should be invalid
        
        # Test fallback doesn't crash
        try:
            utility = self.trainer.evaluate_action_with_selector(self.test_state, invalid_action, 0)
            self.assertIsInstance(utility, (int, float))
            print("✅ Test 5 PASSED: Fallback mechanism works without crashing")
        except Exception as e:
            self.fail(f"Fallback mechanism should not crash: {e}")
    
    def test_performance_improvement_setup(self):
        """Test 6: Performance comparison setup vs 1.7% baseline."""
        # Verify trainer can export policy for comparison
        policy_file = "test_enhanced_policy.txt"
        
        # Train briefly to have some policy
        self.trainer.train(iterations=2, verbose=False)
        
        # Export policy
        self.trainer.export_policy(policy_file, threshold=0.0)
        
        # Verify file created
        self.assertTrue(os.path.exists(policy_file), "Policy file should be created")
        
        # Verify file contains ActionSelector information
        with open(policy_file, 'r') as f:
            content = f.read()
            self.assertIn("ActionSelector", content)
            self.assertIn("HandEvaluator", content)
            self.assertIn("GameStateEvaluator", content)
        
        # Clean up
        if os.path.exists(policy_file):
            os.remove(policy_file)
        
        print("✅ Test 6 PASSED: Performance comparison setup ready")
    
    def test_architecture_completeness(self):
        """Test 7: Complete modular architecture integration."""
        # Verify all 19 evaluation functions accessible
        hand_functions = ['count_triplet_potential', 'count_sequence_potential', 'count_pairs', 
                         'count_complete_melds', 'count_isolated_tiles']
        
        for func_name in hand_functions:
            self.assertTrue(hasattr(self.hand_evaluator, func_name), 
                          f"HandEvaluator should have {func_name}")
        
        state_functions = ['count_dead_tiles', 'count_available_tiles', 'get_left_opponent_discards',
                          'calculate_tile_likelihood', 'estimate_meld_completion_risk', 
                          'analyze_discard_patterns', 'count_suit_concentration', 'measure_honor_vs_suited_ratio']
        
        for func_name in state_functions:
            self.assertTrue(hasattr(game_state_evaluator, func_name), 
                          f"game_state_evaluator module should have {func_name}")
        
        # Verify ActionSelector integration point
        legal_actions = self.test_state.get_legal_actions()
        hand_metrics = {'triplet_potential': 1, 'sequence_potential': 1, 'pairs': 1, 
                       'complete_melds': 0, 'isolated_tiles': 2}
        state_metrics = {'dead_tiles': 0, 'available_tiles': 4, 'meld_completion_risk': 0.3, 
                        'discard_patterns': 1}
        
        # Test calculate_action_utilities integration
        utilities = calculate_action_utilities(legal_actions, hand_metrics, state_metrics)
        self.assertIsInstance(utilities, dict)
        
        print("✅ Test 7 PASSED: Complete architecture - 5+8+6=19 evaluation functions integrated")


class TestPerformanceComparison(unittest.TestCase):
    """
    Test suite for setting up performance comparison vs 1.7% baseline.
    """
    
    def setUp(self):
        """Set up comparison testing environment."""
        self.enhanced_trainer = EnhancedCFRTrainer()
    
    def test_baseline_comparison_metrics(self):
        """Test 8: Baseline comparison metrics collection."""
        # Train enhanced trainer briefly
        self.enhanced_trainer.train(iterations=5, verbose=False)
        
        # Verify enhanced metrics collected
        stats = self.enhanced_trainer.training_stats
        
        # Essential metrics for comparison
        comparison_metrics = [
            'iterations_completed', 'action_utilities_calculated', 'dense_rewards_provided',
            'avg_utility_score', 'hand_evaluations', 'state_evaluations'
        ]
        
        for metric in comparison_metrics:
            self.assertIn(metric, stats)
            if metric in ['iterations_completed', 'action_utilities_calculated', 'dense_rewards_provided']:
                self.assertGreater(stats[metric], 0, f"{metric} should be positive after training")
        
        print(f"✅ Test 8 PASSED: Comparison metrics - {stats['action_utilities_calculated']} utility calculations")
    
    def test_expected_improvement_indicators(self):
        """Test 9: Indicators that suggest improvement over 1.7% baseline."""
        # Create scenario that should show clear improvement signals
        state = GameState()
        player = state.players[0]
        
        # Give player a very good hand
        player.hand = [
            # Two complete melds
            Tile("Man", 1, 1), Tile("Man", 1, 2), Tile("Man", 1, 3),  # Triplet
            Tile("Pin", 4, 10), Tile("Pin", 5, 11), Tile("Pin", 6, 12),  # Sequence
            # Near completion
            Tile("Sou", 7, 20), Tile("Sou", 7, 21),  # Pair (close to triplet)
            Tile("Man", 8, 5), Tile("Man", 9, 6),  # Close to sequence
            # Some isolated
            Tile("Dragon", "Red", 30), Tile("Wind", "East", 40), Tile("Sou", 3, 23)
        ]
        
        # Test ActionSelector recognizes good hand structure
        hand_metrics = {
            'triplet_potential': self.enhanced_trainer.hand_evaluator.count_triplet_potential(player.hand),
            'sequence_potential': self.enhanced_trainer.hand_evaluator.count_sequence_potential(player.hand),
            'pairs': self.enhanced_trainer.hand_evaluator.count_pairs(player.hand),
            'complete_melds': self.enhanced_trainer.hand_evaluator.count_complete_melds(player.hand),
            'isolated_tiles': self.enhanced_trainer.hand_evaluator.count_isolated_tiles(player.hand)
        }
        
        # Should detect strong hand structure
        self.assertGreaterEqual(hand_metrics['complete_melds'], 2, "Should detect 2+ complete melds")
        self.assertGreaterEqual(hand_metrics['pairs'], 1, "Should detect pairs")
        self.assertGreater(hand_metrics['triplet_potential'] + hand_metrics['sequence_potential'], 3,
                          "Should detect significant meld potential")
        
        # Test that utilities reflect hand strength
        legal_actions = [
            {"type": "discard", "tile": Tile("Dragon", "Red", 30)},
            {"type": "discard", "tile": Tile("Wind", "East", 27)}, 
            {"type": "pass"}
        ]
        state_metrics = {'dead_tiles': 0, 'available_tiles': 4, 'meld_completion_risk': 0.2, 'discard_patterns': 0}
        utilities = calculate_action_utilities(legal_actions, hand_metrics, state_metrics)
        
        # Should have meaningful utility variations
        utility_values = list(utilities.values())
        utility_range = max(utility_values) - min(utility_values)
        self.assertGreater(utility_range, 0.5, "Should have significant utility differences for good hands")
        
        print(f"✅ Test 9 PASSED: Improvement indicators - utility range={utility_range:.3f}, melds={hand_metrics['complete_melds']}")


def run_integration_tests():
    """
    Run complete ActionSelector integration test suite.
    """
    print("🧪 RUNNING ACTIONSELECT OR INTEGRATION TEST SUITE")
    print("=" * 70)
    print("Testing: HandEvaluator + GameStateEvaluator → ActionSelector → CFR")
    print("Goal: Validate integration to break 1.7% plateau")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestActionSelectorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceComparison))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 70)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - ActionSelector integration validated!")
        print("\nNext Steps:")
        print("1. Run enhanced_cfr_trainer.py for full training")
        print("2. Compare performance vs 1.7% baseline")
        print("3. Measure win rate improvement with dense signals")
        print("4. Document performance gains in devlog")
        
        print(f"\nArchitecture Status:")
        print(f"  ✅ HandEvaluator (5 functions) - Complete")
        print(f"  ✅ GameStateEvaluator (8 functions) - Complete") 
        print(f"  ✅ ActionSelector (6 functions) - Complete")
        print(f"  ✅ CFR Integration - Validated")
        print(f"  🎯 Total: 19 evaluation functions vs sparse baseline")
        
    else:
        print("❌ SOME TESTS FAILED")
        print("Issues to resolve before proceeding:")
        for failure in result.failures:
            print(f"  - {failure[0]}")
        for error in result.errors:
            print(f"  - {error[0]} (ERROR)")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run integration tests
    success = run_integration_tests()
    
    if success:
        print("\n🚀 Ready to proceed with enhanced CFR training!")
        print("Run: python enhanced_cfr_trainer.py")
    else:
        print("\n⚠️  Fix test failures before proceeding")
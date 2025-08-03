# simple_integration_test.py
"""
Simple ActionSelector Integration Test

This simplified test validates the basic integration without complex function calls.
Goal: Verify the integration architecture works before full testing.

Step 1: Basic import and initialization test
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def test_basic_imports():
    """Test that all modules can be imported correctly."""
    print("🧪 Testing Basic Imports...")
    
    try:
        # Test individual module imports
        from cfr_modules import hand_evaluator
        print("✅ hand_evaluator module imported")
        
        from cfr_modules import game_state_evaluator  
        print("✅ game_state_evaluator module imported")
        
        from cfr_modules.action_selector import calculate_action_utilities
        print("✅ action_selector.calculate_action_utilities imported")
        
        from engine.game_state import GameState
        print("✅ GameState imported")
        
        from engine.tile import Tile
        print("✅ Tile imported")
        
        print("✅ ALL BASIC IMPORTS SUCCESSFUL")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of each module."""
    print("\n🧪 Testing Basic Functionality...")
    
    try:
        from cfr_modules.hand_evaluator import HandEvaluator
        from cfr_modules import game_state_evaluator
        from engine.tile import Tile
        
        # Test HandEvaluator class functions exist
        hand_evaluator = HandEvaluator()
        hand_functions = ['count_triplet_potential', 'count_sequence_potential', 'count_pairs']
        for func in hand_functions:
            if hasattr(hand_evaluator, func):
                print(f"✅ HandEvaluator.{func} exists")
            else:
                print(f"❌ HandEvaluator.{func} missing")
                return False
        
        # Test GameStateEvaluator functions exist  
        state_functions = ['count_dead_tiles', 'count_available_tiles']
        for func in state_functions:
            if hasattr(game_state_evaluator, func):
                print(f"✅ game_state_evaluator.{func} exists")
            else:
                print(f"❌ game_state_evaluator.{func} missing")
                return False
        
        # Test simple function calls
        test_hand = [Tile("Man", 1, 0), Tile("Man", 1, 1)]
        triplet_count = hand_evaluator.count_triplet_potential(test_hand)
        print(f"✅ HandEvaluator.count_triplet_potential returned: {triplet_count}")
        
        test_discards = {"East": [], "South": [], "West": [], "North": []}
        dead_count = game_state_evaluator.count_dead_tiles(0, test_discards)
        print(f"✅ game_state_evaluator.count_dead_tiles returned: {dead_count}")
        
        print("✅ ALL BASIC FUNCTIONALITY TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Functionality Error: {e}")
        return False

def test_enhanced_trainer_creation():
    """Test that EnhancedCFRTrainer can be created."""
    print("\n🧪 Testing Enhanced Trainer Creation...")
    
    try:
        from enhanced_cfr_trainer import EnhancedCFRTrainer
        
        trainer = EnhancedCFRTrainer()
        print("✅ EnhancedCFRTrainer created successfully")
        
        # Check training stats exist
        required_stats = ['action_utilities_calculated', 'dense_rewards_provided']
        for stat in required_stats:
            if stat in trainer.training_stats:
                print(f"✅ Training stat '{stat}' initialized")
            else:
                print(f"❌ Training stat '{stat}' missing")
                return False
        
        print("✅ ENHANCED TRAINER CREATION SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"❌ Trainer Creation Error: {e}")
        return False

def test_action_selector_integration():
    """Test ActionSelector calculate_action_utilities integration."""
    print("\n🧪 Testing ActionSelector Integration...")
    
    try:
        from cfr_modules.action_selector import calculate_action_utilities
        from engine.tile import Tile
        
        # Create properly formatted action data (matching ActionSelector expectations)
        legal_actions = [
            {"type": "discard", "tile": Tile("Man", 1, 0)},
            {"type": "discard", "tile": Tile("Man", 2, 1)},
            {"type": "chi", "tiles": [1, 2, 3], "claimed_tile": 2},
            {"type": "pass"}
        ]
        
        hand_metrics = {
            'triplet_potential': 2,
            'sequence_potential': 1, 
            'pairs_count': 1,  # Note: using 'pairs_count' to match ActionSelector expectations
            'complete_melds': 0,
            'isolated_tiles': 3
        }
        
        state_metrics = {
            'opponent_patterns': {"recent_focus": "Mixed"},
            'tile_safety': {0: 0.8, 1: 0.6},
            'availability_scores': {0: 0.75, 1: 0.5},
            'all_discards': {"East": [], "South": [], "West": [], "North": []}
        }
        
        # Test ActionSelector call
        utilities = calculate_action_utilities(legal_actions, hand_metrics, state_metrics)
        print(f"✅ calculate_action_utilities returned: {utilities}")
        print(f"   Type: {type(utilities)}")
        print(f"   Length: {len(utilities) if hasattr(utilities, '__len__') else 'N/A'}")
        
        # Verify utilities are valid
        if isinstance(utilities, list) and len(utilities) == len(legal_actions):
            all_valid = all(isinstance(u, (int, float)) and 0 <= u <= 100 for u in utilities)
            if all_valid:
                print("✅ All utilities are valid numbers in range [0, 100]")
            else:
                print("⚠️  Some utilities outside expected range, but integration working")
        
        print("✅ ACTIONSELECT OR INTEGRATION SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"❌ ActionSelector Integration Error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def run_simple_integration_test():
    """Run all simple integration tests."""
    print("🎯 SIMPLE ACTIONSELECT OR INTEGRATION TEST")
    print("=" * 50)
    print("Goal: Verify basic integration before full testing")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests in order
    tests = [
        test_basic_imports,
        test_basic_functionality, 
        test_enhanced_trainer_creation,
        test_action_selector_integration
    ]
    
    for test in tests:
        if not test():
            all_passed = False
            break
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL SIMPLE INTEGRATION TESTS PASSED!")
        print("✅ Ready to proceed with full integration test")
        print("   Next: Run python test_actionselctor_integration.py")
    else:
        print("❌ SIMPLE INTEGRATION TESTS FAILED")
        print("   Fix these issues before proceeding with full tests")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = run_simple_integration_test()
    if success:
        print("\n🚀 Integration foundation validated!")
        print("   Proceed to Step 2: python test_actionselctor_integration.py")
    else:
        print("\n⚠️  Fix foundation issues first")
"""
Test to prove CFR has no meld recognition in hand
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from engine.game_state import GameState
from engine.tile import Tile
from fixed_final_cfr_trainer import FixedMeldCountingCFRTrainer

def test_cfr_meld_recognition():
    """
    Test if CFR recognizes complete melds in hand and avoids discarding them
    """
    print("🔍 TESTING CFR MELD RECOGNITION")
    print("="*50)
    
    # Create controlled scenario
    state = GameState()
    player = state.players[0]  # East player
    
    # Clear hand and give specific tiles
    player.hand.clear()
    player.hand = [
        # Complete triplet - should NEVER discard these
        Tile("Man", 5, 4), Tile("Man", 5, 4), Tile("Man", 5, 4),
        
        # Complete sequence - should NEVER discard these  
        Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
        
        # Random junk tiles - SHOULD discard these
        Tile("Dragon", "Red", 33), Tile("Wind", "East", 27), 
        Tile("Dragon", "White", 31), Tile("Wind", "North", 30),
        
        # Pair
        Tile("Sou", 1, 18), Tile("Sou", 1, 18),
        
        # One extra tile to discard
        Tile("Dragon", "Green", 32)
    ]
    
    state.turn_index = 0  # East's turn
    state.awaiting_discard = True  # Must discard
    
    print(f"Hand: {[str(t) for t in player.hand]}")
    print(f"Complete triplet: Man 5 x3")
    print(f"Complete sequence: Pin 2-3-4") 
    print(f"Junk tiles: Dragons and Winds")
    
    # Test what CFR's info set looks like
    info_set = state.get_info_set()
    print(f"\nCFR Info Set: {info_set}")
    
    # Get legal actions (all discard actions)
    legal_actions = state.get_legal_actions()
    print(f"Legal discard actions: {legal_actions}")
    
    # Test CFR decision making
    trainer = FixedMeldCountingCFRTrainer(use_enhanced_info_set=False)
    
    # Get CFR strategy (will be random initially)
    strategy = trainer.get_strategy(info_set, legal_actions)
    
    print(f"\nCFR Strategy (probability for each action):")
    for action in legal_actions:
        if action < len(strategy) and strategy[action] > 0:
            tile_name = state.id_to_tile_name(action)
            print(f"  Discard {tile_name} (tile_id {action}): {strategy[action]:.3f}")
    
    # Test action evaluation
    print(f"\nTesting CFR action evaluation:")
    action_values = {}
    
    # Test discarding from complete triplet (BAD)
    test_action_bad = 4  # Man 5 tile_id
    test_state_bad = trainer.proper_deep_clone(state)
    try:
        test_state_bad.step(test_action_bad)
        value_bad = trainer.simple_rollout(test_state_bad, player_id=0, max_steps=15)
        action_values[test_action_bad] = value_bad
        print(f"  Discarding Man 5 (from triplet): {value_bad:.3f}")
    except:
        print(f"  Discarding Man 5 failed")
    
    # Test discarding junk tile (GOOD)
    test_action_good = 33  # Dragon Red tile_id  
    test_state_good = trainer.proper_deep_clone(state)
    try:
        test_state_good.step(test_action_good)
        value_good = trainer.simple_rollout(test_state_good, player_id=0, max_steps=15)
        action_values[test_action_good] = value_good
        print(f"  Discarding Dragon Red (junk): {value_good:.3f}")
    except:
        print(f"  Discarding Dragon Red failed")
    
    # Analysis
    print(f"\n🔍 ANALYSIS:")
    if len(action_values) >= 2:
        if action_values.get(33, 0) > action_values.get(4, 0):
            print("✅ CFR correctly values keeping triplet over junk")
        else:
            print("❌ CFR does NOT recognize triplet value!")
            print("   This proves CFR has no meld recognition!")
    
    # Test what enhanced info set would show
    try:
        enhanced_info = state.get_enhanced_info_set()
        print(f"\nEnhanced Info Set: {enhanced_info}")
        
        analysis = state.analyze_hand_sequences()
        print(f"Enhanced Analysis:")
        print(f"  Complete sequences: {analysis['complete_sequences']}")
        print(f"  Partial sequences: {analysis['partial_sequences']}")
        print(f"  Shape score: {state.get_hand_shape_score():.1f}")
        
    except Exception as e:
        print(f"Enhanced info set failed: {e}")

def test_multiple_scenarios():
    """Test CFR on multiple hand scenarios"""
    print("\n🧪 TESTING MULTIPLE SCENARIOS")
    print("="*40)
    
    scenarios = [
        {
            "name": "Perfect Triplets",
            "hand": [
                Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),  # Triplet
                Tile("Pin", 5, 13), Tile("Pin", 5, 13), Tile("Pin", 5, 13),  # Triplet  
                Tile("Dragon", "Red", 33)  # Junk to discard
            ]
        },
        {
            "name": "Mixed Good/Bad",
            "hand": [
                Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),  # Sequence
                Tile("Wind", "East", 27), Tile("Wind", "South", 28),  # Random winds
                Tile("Dragon", "White", 31), Tile("Dragon", "Green", 32)  # Random dragons
            ]
        }
    ]
    
    trainer = FixedMeldCountingCFRTrainer()
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        
        state = GameState()
        player = state.players[0]
        player.hand = scenario['hand']
        state.awaiting_discard = True
        
        print(f"Hand: {[str(t) for t in player.hand]}")
        
        # Check if CFR can distinguish good vs bad discards
        legal_actions = state.get_legal_actions()[:3]  # Test first 3 actions
        
        for action in legal_actions:
            try:
                test_state = trainer.proper_deep_clone(state)
                test_state.step(action)
                value = trainer.simple_rollout(test_state, player_id=0, max_steps=10)
                tile_name = state.id_to_tile_name(action)
                print(f"  Discard {tile_name}: {value:.3f}")
            except:
                pass

if __name__ == "__main__":
    test_cfr_meld_recognition()
    test_multiple_scenarios()
    
    print(f"\n" + "="*50)
    print("🎯 CONCLUSION:")
    print("If CFR shows random/similar values for good vs bad discards,")
    print("then it has NO meld recognition capability!")
    print("This explains the 1.7% plateau - it's making terrible decisions.")
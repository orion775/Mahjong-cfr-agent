# scripts/validate_game_engine.py

"""
Comprehensive validation of the game engine to ensure all win detection
and terminal logic is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState, is_winning_hand
from engine.tile import Tile
from engine.player import Player

def create_tile(category, value):
    """Helper to create tiles with proper tile_id."""
    if category == "Man":
        tile_id = value - 1  # 0-8
    elif category == "Pin":
        tile_id = 8 + value  # 9-17
    elif category == "Sou":
        tile_id = 17 + value  # 18-26
    elif category == "Wind":
        wind_map = {"East": 27, "South": 28, "West": 29, "North": 30}
        tile_id = wind_map.get(value, 27)
    elif category == "Dragon":
        dragon_map = {"White": 31, "Green": 32, "Red": 33}
        tile_id = dragon_map.get(value, 31)
    else:
        tile_id = 0
    
    return Tile(category, value, tile_id)

def test_false_winning_hand():
    """Test the exact false winning hand from the log."""
    print("🔍 TESTING FALSE WINNING HAND")
    print("=" * 50)
    
    # Create the exact hand from the log
    hand_tiles = [
        create_tile("Man", 5), create_tile("Man", 9), create_tile("Pin", 5),
        create_tile("Man", 8), create_tile("Pin", 7), create_tile("Pin", 1),
        create_tile("Pin", 6), create_tile("Man", 6), create_tile("Man", 8),
        create_tile("Pin", 3), create_tile("Pin", 1)
    ]
    
    # Add meld tiles
    meld_tiles = [create_tile("Pin", 4), create_tile("Pin", 4), create_tile("Pin", 4)]
    full_hand = hand_tiles + meld_tiles
    
    print(f"Hand: {[str(t) for t in hand_tiles]}")
    print(f"Melds: PON {[str(t) for t in meld_tiles]}")
    print(f"Total tiles: {len(full_hand)}")
    
    # Test is_winning_hand function
    is_win = is_winning_hand(full_hand)
    print(f"is_winning_hand(): {is_win}")
    
    if is_win:
        print("❌ STILL BROKEN: Engine thinks this is a win!")
        return False
    else:
        print("✅ FIXED: Engine correctly identifies this as NOT a win")
        return True

def test_valid_winning_hands():
    """Test some known valid winning hands to ensure we didn't break anything."""
    print("\n🎯 TESTING VALID WINNING HANDS")
    print("=" * 50)
    
    test_cases = [
        {
            "name": "Simple 4 melds + 1 pair",
            "hand": [
                # Triplet 1: Man 1,1,1
                create_tile("Man", 1), create_tile("Man", 1), create_tile("Man", 1),
                # Triplet 2: Pin 2,2,2  
                create_tile("Pin", 2), create_tile("Pin", 2), create_tile("Pin", 2),
                # Triplet 3: Sou 3,3,3
                create_tile("Sou", 3), create_tile("Sou", 3), create_tile("Sou", 3),
                # Triplet 4: East,East,East
                create_tile("Wind", "East"), create_tile("Wind", "East"), create_tile("Wind", "East"),
                # Pair: Red,Red
                create_tile("Dragon", "Red"), create_tile("Dragon", "Red")
            ]
        },
        {
            "name": "Sequence-based hand",
            "hand": [
                # Sequence 1: Man 1,2,3
                create_tile("Man", 1), create_tile("Man", 2), create_tile("Man", 3),
                # Sequence 2: Man 4,5,6
                create_tile("Man", 4), create_tile("Man", 5), create_tile("Man", 6),
                # Sequence 3: Pin 1,2,3
                create_tile("Pin", 1), create_tile("Pin", 2), create_tile("Pin", 3),
                # Triplet: Pin 7,7,7
                create_tile("Pin", 7), create_tile("Pin", 7), create_tile("Pin", 7),
                # Pair: Sou 5,5
                create_tile("Sou", 5), create_tile("Sou", 5)
            ]
        },
        {
            "name": "Seven Pairs",
            "hand": [
                create_tile("Man", 1), create_tile("Man", 1),
                create_tile("Man", 2), create_tile("Man", 2),
                create_tile("Pin", 3), create_tile("Pin", 3),
                create_tile("Pin", 4), create_tile("Pin", 4),
                create_tile("Sou", 5), create_tile("Sou", 5),
                create_tile("Wind", "East"), create_tile("Wind", "East"),
                create_tile("Dragon", "Red"), create_tile("Dragon", "Red")
            ]
        }
    ]
    
    all_passed = True
    for test_case in test_cases:
        name = test_case["name"]
        hand = test_case["hand"]
        
        print(f"\nTesting: {name}")
        print(f"Hand ({len(hand)} tiles): {[str(t) for t in hand]}")
        
        is_win = is_winning_hand(hand)
        print(f"is_winning_hand(): {is_win}")
        
        if is_win:
            print("✅ CORRECT: Valid winning hand detected")
        else:
            print("❌ ERROR: Valid winning hand NOT detected!")
            all_passed = False
    
    return all_passed

def test_game_state_terminal_logic():
    """Test the GameState terminal detection logic."""
    print("\n🎮 TESTING GAME STATE TERMINAL LOGIC")
    print("=" * 50)
    
    # Create a game state
    game = GameState()
    
    # Test initial state
    print(f"Initial terminal state: {game.is_terminal()}")
    
    # Create a player with the false winning hand
    player = game.players[0]  # East player
    
    # Clear the player's hand and set up the false winning hand
    player.hand = [
        create_tile("Man", 5), create_tile("Man", 9), create_tile("Pin", 5),
        create_tile("Man", 8), create_tile("Pin", 7), create_tile("Pin", 1),
        create_tile("Pin", 6), create_tile("Man", 6), create_tile("Man", 8),
        create_tile("Pin", 3), create_tile("Pin", 1)
    ]
    
    # Add the PON meld
    meld_tiles = [create_tile("Pin", 4), create_tile("Pin", 4), create_tile("Pin", 4)]
    player.melds = [("PON", meld_tiles)]
    
    print(f"Player hand: {[str(t) for t in player.hand]}")
    print(f"Player melds: {player.melds}")
    
    # Test check_player_win
    player_wins = game.check_player_win(player)
    print(f"check_player_win(): {player_wins}")
    
    # Test is_terminal
    is_terminal = game.is_terminal()
    print(f"is_terminal(): {is_terminal}")
    
    if player_wins or is_terminal:
        print("❌ ERROR: Game incorrectly detects win/terminal state!")
        return False
    else:
        print("✅ CORRECT: Game correctly does NOT detect win/terminal state")
        return True

def main():
    """Run all validation tests."""
    print("🔧 GAME ENGINE VALIDATION")
    print("=" * 60)
    
    tests = [
        ("False Winning Hand", test_false_winning_hand),
        ("Valid Winning Hands", test_valid_winning_hands),
        ("Game State Terminal Logic", test_game_state_terminal_logic)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🎯 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Game engine is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED! Game engine needs more fixes.")
    
    return all_passed

if __name__ == "__main__":
    main()

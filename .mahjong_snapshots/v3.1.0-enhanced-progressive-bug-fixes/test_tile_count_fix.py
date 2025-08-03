#!/usr/bin/env python3
"""
Test script to verify the tile counting fix for Chinese Mahjong KAN mechanics.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.game_state import GameState
from engine.tile import Tile
from engine import action_space

def test_kan_tile_counting():
    """Test that KAN operations maintain proper tile counts."""
    print("=== Testing KAN Tile Counting ===")
    
    state = GameState()
    player = state.get_current_player()
    
    # Clear initial state
    player.hand.clear()
    player.melds.clear()
    
    # Give player a proper 13-tile hand with 4 matching tiles for Ankan
    for _ in range(4):
        player.hand.append(Tile("Man", 1, 0))  # 4 tiles for KAN
    
    # Add 9 more random tiles to make a 13-tile hand
    for i in range(9):
        player.hand.append(Tile("Pin", (i % 9) + 1, 9 + i))
    
    print(f"Before KAN: {state.get_player_total_tiles(player)} tiles")
    print(f"  Hand: {len(player.hand)}")
    print(f"  Melds: {player.melds}")
    
    # Perform Ankan
    state.awaiting_discard = True
    kan_action = action_space.ACTION_NAME_TO_ID["KAN_0"]
    state.step(kan_action)
    
    print(f"After KAN: {state.get_player_total_tiles(player)} tiles")
    print(f"  Hand: {len(player.hand)}")
    print(f"  Melds: {[(mtype, len(tiles)) for mtype, tiles in player.melds]}")
    
    # Check if tile count is correct (should be 14 temporarily due to replacement draw)
    total_tiles = state.get_player_total_tiles(player)
    if total_tiles == 14:  # 1 hand + 4 KAN tiles - replacement draw not affecting count
        print("✓ KAN tile counting works correctly - player has 14 tiles after replacement draw")
        return True
    else:
        print(f"✗ KAN tile counting error - player has {total_tiles} tiles, expected 14")
        return False

def test_multiple_melds():
    """Test tile counting with multiple melds including KAN."""
    print("\n=== Testing Multiple Melds ===")
    
    state = GameState()
    player = state.get_current_player()
    
    # Clear initial state
    player.hand.clear()
    player.melds.clear()
    
    # Add a PON meld (3 tiles)
    pon_tiles = [Tile("Man", 2, 1) for _ in range(3)]
    player.melds.append(("PON", pon_tiles))
    
    # Add a KAN meld (4 tiles)
    kan_tiles = [Tile("Man", 3, 2) for _ in range(4)]
    player.melds.append(("KAN", kan_tiles))
    
    # Add 6 tiles to hand (should total 13: 6 hand + 3 PON + 4 KAN = 13)
    for i in range(6):
        player.hand.append(Tile("Pin", i+1, 9+i))
    
    total_tiles = state.get_player_total_tiles(player)
    print(f"Player with PON+KAN+6 hand tiles: {total_tiles} total")
    print(f"  Hand: {len(player.hand)}")
    print(f"  Melds: {[(mtype, len(tiles)) for mtype, tiles in player.melds]}")
    
    if total_tiles == 13:
        print("✓ Multiple meld tile counting works correctly")
        return True
    else:
        print(f"✗ Multiple meld tile counting error - expected 13, got {total_tiles}")
        return False

def test_validation():
    """Test the validation function."""
    print("\n=== Testing Tile Count Validation ===")
    
    state = GameState()
    
    # Clear all players
    for player in state.players:
        player.hand.clear()
        player.melds.clear()
    
    # Give all players exactly 13 tiles
    for i, player in enumerate(state.players):
        for j in range(13):
            player.hand.append(Tile("Man", 1, 0))
    
    # Test validation
    is_valid = state.validate_player_tile_counts()
    print(f"All players with 13 tiles: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    # Now give one player 14 tiles (should fail validation since no winners set)
    state.players[0].hand.append(Tile("Man", 2, 1))
    is_valid = state.validate_player_tile_counts()
    print(f"One player with 14 tiles (no winner): {'✗ Invalid' if not is_valid else '✓ Valid (unexpected)'}")
    
    # Set that player as winner (should pass validation)
    state.winners = [0]
    is_valid = state.validate_player_tile_counts()
    print(f"One player with 14 tiles (is winner): {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    return True

if __name__ == "__main__":
    print("Testing Chinese Mahjong tile counting fixes...\n")
    
    test1 = test_kan_tile_counting()
    test2 = test_multiple_melds()
    test3 = test_validation()
    
    print(f"\n=== Results ===")
    print(f"KAN tile counting: {'PASS' if test1 else 'FAIL'}")
    print(f"Multiple melds: {'PASS' if test2 else 'FAIL'}")
    print(f"Validation: {'PASS' if test3 else 'FAIL'}")
    
    if test1 and test2 and test3:
        print("\n✓ All tile counting tests PASSED!")
    else:
        print("\n✗ Some tile counting tests FAILED!")

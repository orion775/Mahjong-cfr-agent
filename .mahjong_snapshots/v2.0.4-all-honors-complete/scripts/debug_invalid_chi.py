# scripts/debug_invalid_chi.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.action_space import decode_chi, encode_chi

print("🔍 DEBUGGING INVALID CHI SEQUENCES")
print("="*50)

# Test what's happening with the invalid CHI
print("Testing CHI decoding:")
try:
    # Try to find what action_id creates ['Man 9', 'Pin 1', 'Pin 2']
    print("Looking for cross-suit CHI sequences...")
    for action_id in range(69, 90):  # CHI action range
        try:
            meld = decode_chi(action_id)
            # Check for cross-suit sequences
            if len(set(tid // 9 for tid in meld)) > 1:  # Different suits
                print(f"❌ INVALID: Action {action_id} decodes to: {meld}")
                print(f"   Tile IDs span multiple suits!")
        except Exception as e:
            print(f"Action {action_id} failed: {e}")
            
    print("\nTesting specific problematic sequences:")
    # Test the sequences we saw in the logs
    test_sequences = [
        [8, 9, 10],   # Man 9, Pin 1, Pin 2
        [17, 0, 1],   # Pin 9, Man 1, Man 2  
        [26, 27, 28]  # Sou 9, Wind East, Wind South
    ]
    
    for seq in test_sequences:
        try:
            action_id = encode_chi(seq)
            print(f"✅ Sequence {seq} encoded as action {action_id}")
        except ValueError as e:
            print(f"❌ Sequence {seq} rejected: {e}")
            
except Exception as e:
    print(f"Error: {e}")


print("\n" + "="*50)
print("TESTING MELD CREATION PROCESS")
print("="*50)

from engine.game_state import GameState
from engine.tile import Tile

# Simulate the problematic scenario
state = GameState()
player = state.players[0]

# Clear hand and set up a scenario
player.hand.clear()
player.hand.extend([
    Tile("Pin", 1, 9),   # Pin 1
    Tile("Pin", 2, 10),  # Pin 2
])

# Set up discard
discard_tile = Tile("Man", 9, 8)  # Man 9
state.last_discard = discard_tile
state.last_discarded_by = 1

print("Testing can_chi with cross-suit scenario:")
print(f"Player hand: {[str(t) for t in player.hand]}")
print(f"Discard tile: {discard_tile}")

can_chi_result = state.can_chi(discard_tile, player)
print(f"can_chi() result: {can_chi_result}")

if can_chi_result:
    print("❌ BUG: can_chi() should return empty list for cross-suit!")
else:
    print("✅ Good: can_chi() correctly rejects cross-suit CHI")


print("\n" + "="*50)
print("TESTING TILE OBJECT CONSISTENCY")
print("="*50)

from engine.tile import Tile

# Create tiles like in the problematic CHI
tile1 = Tile("Man", 9, 8)    # Man 9, tile_id 8
tile2 = Tile("Pin", 1, 9)    # Pin 1, tile_id 9  
tile3 = Tile("Pin", 2, 10)   # Pin 2, tile_id 10

print("Individual tile info:")
print(f"Tile 1: {tile1} (id: {tile1.tile_id})")
print(f"Tile 2: {tile2} (id: {tile2.tile_id})")  
print(f"Tile 3: {tile3} (id: {tile3.tile_id})")

print("\nTesting tile_id sequence:")
tile_ids = [tile1.tile_id, tile2.tile_id, tile3.tile_id]
print(f"Tile IDs: {tile_ids}")

print("This sequence should be rejected by encode_chi:")
try:
    from engine.action_space import encode_chi
    action_id = encode_chi(tile_ids)
    print(f"❌ BUG: encode_chi accepted invalid sequence: {action_id}")
except ValueError as e:
    print(f"✅ Good: encode_chi rejected: {e}")
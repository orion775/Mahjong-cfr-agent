import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.tile import Tile

print("🔍 DEBUGGING MELD DISPLAY")
print("="*40)

# Create the tiles we saw in the summary
sou8 = Tile("Sou", 8, 25)
sou9 = Tile("Sou", 9, 26) 
wind_east = Tile("Wind", "East", 27)

print("Tiles created:")
print(f"  {sou8} (tile_id: {sou8.tile_id})")
print(f"  {sou9} (tile_id: {sou9.tile_id})")  
print(f"  {wind_east} (tile_id: {wind_east.tile_id})")

# Test if this could be a valid CHI sequence
print(f"\nChecking sequence: [{sou8.tile_id}, {sou9.tile_id}, {wind_east.tile_id}]")

# This should not be possible to encode
from engine.action_space import encode_chi
try:
    action_id = encode_chi([25, 26, 27])
    print(f"❌ ERROR: This encoded as {action_id}")
except ValueError as e:
    print(f"✅ Correctly rejected: {e}")

print("\nConclusion: The invalid CHI in the summary might be a display issue,")
print("not a validation issue. The engine correctly prevents invalid CHIs.")
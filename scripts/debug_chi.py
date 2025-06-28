import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.tile import Tile
from engine.action_space import encode_chi

print("🔍 DEBUGGING CHI VALIDATION")
print("="*40)

# Test the invalid CHI we saw
print("Test 1: Invalid CHI (Sou 8, Sou 9, Wind East)")
try:
    invalid_chi = encode_chi([25, 26, 27])  # Sou 8, Sou 9, Wind East
    print(f"❌ BUG: Invalid CHI encoded as: {invalid_chi}")
except ValueError as e:
    print(f"✅ Good! Invalid CHI rejected: {e}")

# Test valid CHI
print("\nTest 2: Valid CHI (Sou 7, Sou 8, Sou 9)")
try:
    valid_chi = encode_chi([24, 25, 26])  # Sou 7, Sou 8, Sou 9
    print(f"✅ Valid CHI encoded as: {valid_chi}")
except ValueError as e:
    print(f"❌ Error with valid CHI: {e}")

# Test tile IDs
print("\nTile ID Reference:")
print("Sou 7 = 24, Sou 8 = 25, Sou 9 = 26")
print("Wind East = 27 (should not be in CHI)")
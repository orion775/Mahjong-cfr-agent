# tests/test_kan_encoding.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.action_space import encode_kan

def test_kan_ids():
    print("🔧 KAN ENCODING TEST")

    tile_ids = [0, 1, 2, 3, 9, 10, 11, 12, 18, 19, 20, 21]  # Some tile_id clusters
    seen_ids = set()

    for tile_id in tile_ids:
        try:
            action_id = encode_kan(tile_id)
            print(f"Tile ID {tile_id} → KAN Action ID {action_id}")
            if action_id in seen_ids:
                print(f"❌ Duplicate action ID: {action_id}")
            seen_ids.add(action_id)
        except Exception as e:
            print(f"❌ Error for tile ID {tile_id}: {e}")

if __name__ == "__main__":
    test_kan_ids()

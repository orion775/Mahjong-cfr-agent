# tests/test_wall.py

import unittest
from engine.wall import generate_wall

class TestWall(unittest.TestCase):
    def test_wall_tile_count(self):
        wall = generate_wall()
        self.assertEqual(len(wall), 136)  # 136 = full set without flowers

    def test_wall_contains_unique_tile_types(self):
        tile_type_counts = {}
        for tile in generate_wall():
            key = (tile.category, tile.value, tile.tile_id)
            tile_type_counts[key] = tile_type_counts.get(key, 0) + 1
        for count in tile_type_counts.values():
            self.assertIn(count, [4])  # Each should appear 4 times

if __name__ == '__main__':
    unittest.main()
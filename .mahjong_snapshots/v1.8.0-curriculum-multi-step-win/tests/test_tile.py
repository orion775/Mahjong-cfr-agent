#tests\test_tile.py

import unittest
from engine.tile import Tile

def main():
    tile1 = Tile("Man", 5, 4)
    tile2 = Tile("Pin", 9, 17)
    tile3 = Tile("Sou", 1, 18)
    tile4 = Tile("Wind", "East", 27)
    tile5 = Tile("Dragon", "Red", 31)

    print("Test Tiles:")
    print(tile1)
    print(tile2)
    print(tile3)
    print(tile4)
    print(tile5)

if __name__ == "__main__":
    main()
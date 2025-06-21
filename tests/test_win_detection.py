#tests\test_win_detection.py

import unittest
from engine.tile import Tile
from engine.game_state import is_winning_hand

class TestWinDetection(unittest.TestCase):
    def test_basic_win(self):
        # Example: Man 1-2-3, Man 1-2-3, Man 4-5-6, Man 7-8-9, Pair of Pin 1
        hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 1, 3), Tile("Man", 2, 4), Tile("Man", 3, 5),
            Tile("Man", 4, 6), Tile("Man", 5, 7), Tile("Man", 6, 8),
            Tile("Man", 7, 9), Tile("Man", 8, 10), Tile("Man", 9, 11),
            Tile("Pin", 1, 12), Tile("Pin", 1, 13),  # Pair
        ]
        print([ (t.category, t.value) for t in hand ])
        print(is_winning_hand(hand))
        self.assertTrue(is_winning_hand(hand))

    def test_not_win(self):
        # Not enough melds
        hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 1, 3), Tile("Man", 2, 4), Tile("Man", 3, 5),
            Tile("Man", 4, 6), Tile("Man", 5, 7), Tile("Man", 6, 8),
            Tile("Man", 7, 9), Tile("Man", 8, 10), Tile("Man", 9, 11),
            Tile("Pin", 1, 12), Tile("Pin", 2, 13),  # Not a pair
        ]
        print([ (t.category, t.value) for t in hand ])
        print(is_winning_hand(hand))
        self.assertFalse(is_winning_hand(hand))

    def test_win_with_pongs(self):
        # 4 pongs and a pair: (3x Man 1, 3x Man 2, 3x Man 3, 3x Pin 4, pair Sou 8)
        hand = (
            [Tile("Man", 1, i) for i in range(3)] +
            [Tile("Man", 2, i+3) for i in range(3)] +
            [Tile("Man", 3, i+6) for i in range(3)] +
            [Tile("Pin", 4, i+9) for i in range(3)] +
            [Tile("Sou", 8, 12), Tile("Sou", 8, 13)]
        )
        print([ (t.category, t.value) for t in hand ])
        print(is_winning_hand(hand))
        self.assertTrue(is_winning_hand(hand))

if __name__ == "__main__":
    unittest.main()
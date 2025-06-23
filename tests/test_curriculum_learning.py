# tests/test_curriculum_learning.py

import unittest
from engine.game_state import GameState
from engine.cfr_trainer import CFRTrainer
from engine.oracle_states import FixedWinGameState_2StepsFromWin
from engine.oracle_states import FixedWinGameState_3StepsFromWin

class FixedWinGameState_2StepsFromWin(GameState):
    """
    Curriculum state: Player 0 must draw twice (no melds) to win. Only discard/draw actions are possible.
    """
    def __init__(self):
        super().__init__()
        from engine.tile import Tile
        # Player 0: 12 tiles, no possible triplets, just two steps from completion
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Man", 9, 8),
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12)
        ]
        self.players[1].hand = []
        self.players[2].hand = []
        self.players[3].hand = []
        # Wall contains the tiles needed to form the last meld and pair
        self.wall = [Tile("Pin", 5, 13), Tile("Pin", 5, 13)]
        self.turn_index = 0
        self.awaiting_discard = False
        self._terminal = False
        self.last_discard = None
        self.discard_pile = [[] for _ in range(4)]
        for p in self.players:
            p.melds = []

class FixedWinGameState_3StepsFromWin(GameState):
    """
    Player 0: 10 tiles, must draw three (from wall) to win. Only discards/draws are possible.
    """
    def __init__(self):
        super().__init__()
        from engine.tile import Tile
        # Hand: 10 different tiles (no possible triplet!)
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Pin", 1, 9), Tile("Pin", 2, 10)
        ]
        self.players[1].hand = []
        self.players[2].hand = []
        self.players[3].hand = []
        # Wall: three unique tiles (to reach win)
        self.wall = [Tile("Pin", 3, 11), Tile("Pin", 4, 12), Tile("Pin", 5, 13)]
        self.turn_index = 0
        self.awaiting_discard = False
        self._terminal = False
        self.last_discard = None
        self.discard_pile = [[] for _ in range(4)]
        for p in self.players:
            p.melds = []
#tests\fixed_meld_state.py

from engine.game_state import GameState
from engine.tile import Tile
from engine.cfr_trainer import CFRTrainer

class FixedMeldGameState(GameState):
    def __init__(self):
        super().__init__()

        self.players[0].hand = [
            Tile("Man", 1, 0),
            Tile("Man", 2, 1),
            Tile("Sou", 9, 26),
            Tile("Pin", 1, 9),
            Tile("Man", 4, 3),
            Tile("Pin", 2, 10),
            Tile("Man", 5, 4),  # enables CHI 3-4-5
        ] + self.players[0].hand[7:]

        self.players[1].hand.clear()
        self.players[2].hand.clear()
        self.players[3].hand.clear()

        self.last_discard = Tile("Man", 3, 2)
        self.last_discarded_by = 3  # North
        self.discards["North"].append(self.last_discard)

        self.turn_index = 0  # South
        self.awaiting_discard = False

class FixedMeldTrainer(CFRTrainer):
    def train(self, iterations=1, player_id=0):
        for _ in range(iterations):
            state = FixedMeldGameState()
            reach_probs = [1.0] * 4
            self.cfr(state, reach_probs, player_id)
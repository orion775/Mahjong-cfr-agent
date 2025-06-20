
from engine.game_state import GameState
from engine.tile import Tile

class FixedWinGameState_SelfDraw(GameState):
    def __init__(self):
        super().__init__()

        # --- Clear out the default dealt hands/wall ---
        for player in self.players:
            player.hand.clear()
            player.melds.clear()

        # --- Player 0's hand: 13 tiles, 1 from win (needs one more Pin 1 for a pair) ---
        # Melds: Man 1-2-3, Pin 2-3-4, Sou 4-5-6, Man 4-5-6, Pair: Pin 1, Pin 1 (after draw)
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
            Tile("Sou", 4, 21), Tile("Sou", 5, 22), Tile("Sou", 6, 23),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9)  # Only one Pin 1 now (will pair after draw)
        ]

        # --- Wall: Only one tile left, and it's Pin 1 (needed for win pair) ---
        self.wall.clear()
        winning_tile = Tile("Pin", 1, 9)
        self.wall.append(winning_tile)

        # --- Other players: empty hands ---
        for i in range(1, 4):
            self.players[i].hand.clear()
            self.players[i].melds.clear()

        # --- No discards, no melds on table ---
        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}

        # --- Set to Player 0's turn, not yet drawn ---
        self.turn_index = 0  # East
        self.awaiting_discard = False  # So next action is a draw

        # Defensive: reset last_discard, last_discarded_by, and terminal flag
        self.last_discard = None
        self.last_discarded_by = None
        if hasattr(self, "_terminal"):
            del self._terminal
# engine/oracle_states.py

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

class FixedWinGameState_Ron(GameState):
    """
    Player 0 (East) is in tenpai (needs 1 tile to win).
    Player 1 (South) has only the winning tile and must discard it.
    After the discard, Player 0 should win by Ron.
    """
    def __init__(self):
        super().__init__()

        # --- Clear out the default dealt hands/wall ---
        for player in self.players:
            player.hand.clear()
            player.melds.clear()

        # Player 0: needs one Pin 1 for a pair after Ron
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
            Tile("Sou", 4, 21), Tile("Sou", 5, 22), Tile("Sou", 6, 23),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9)  # Only one Pin 1 in hand; needs one more from discard
        ]

        # Player 1: Only one tile (Pin 1) to discard
        self.players[1].hand = [Tile("Pin", 1, 9)]
        self.players[1].melds.clear()

        # Other players: empty hands
        for i in [2, 3]:
            self.players[i].hand.clear()
            self.players[i].melds.clear()

        # Wall: empty
        self.wall.clear()

        # No melds/discards yet
        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}

        # Set turn: Player 1 (South) must discard
        self.turn_index = 1  # South
        self.awaiting_discard = True  # So next action is discard

        # Defensive
        self.last_discard = None
        self.last_discarded_by = None
        if hasattr(self, "_terminal"):
            del self._terminal


class FixedWinGameState_CHI(GameState):
    """
    Player 0 (South) is in tenpai and can win by CHI on Player 3's discard.
    """
    def __init__(self):
        super().__init__()

        for player in self.players:
            player.hand.clear()
            player.melds.clear()

        # Player 0: Needs Man 3 for the meld (will win after CHI on Man 3)
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1),  # Can CHI with Man 3
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
            Tile("Sou", 4, 21), Tile("Sou", 5, 22), Tile("Sou", 6, 23),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9), Tile("Pin", 1, 9)   # Pair
        ]

        # Player 3 (East): Has one tile, Man 3, to discard
        self.players[3].hand = [Tile("Man", 3, 2)]
        self.players[3].melds.clear()

        # Other players: empty hands
        self.players[1].hand.clear()
        self.players[2].hand.clear()
        self.players[1].melds.clear()
        self.players[2].melds.clear()

        # Wall: empty
        self.wall.clear()

        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}

        # Set turn: Player 3 (East) must discard Man 3
        self.turn_index = 3  # East
        self.awaiting_discard = True

        self.last_discard = None
        self.last_discarded_by = None
        if hasattr(self, "_terminal"):
            del self._terminal


class FixedWinGameState_PON(GameState):
    """
    Player 0 (South) is in tenpai and can win by calling PON on Player 2's discard.
    """
    def __init__(self):
        super().__init__()

        for player in self.players:
            player.hand.clear()
            player.melds.clear()

        # Player 0 (South): two Man 3s in hand, needs a third for PON to win
        self.players[0].hand = [
            Tile("Man", 3, 2), Tile("Man", 3, 2),  # two Man 3s
            Tile("Man", 1, 0), Tile("Man", 2, 1),  # Man 1, 2
            Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),
            Tile("Sou", 4, 21), Tile("Sou", 5, 22), Tile("Sou", 6, 23),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Pin", 1, 9), Tile("Pin", 1, 9)  # Pair
        ][:13]  # Ensure only 13 tiles

        # Player 2 (West): will discard Man 3
        self.players[2].hand = [Tile("Man", 3, 2)]
        self.players[2].melds.clear()

        # Other players: empty
        self.players[1].hand.clear()
        self.players[3].hand.clear()
        self.players[1].melds.clear()
        self.players[3].melds.clear()

        self.wall.clear()
        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}

        # Turn: Player 2 (West) must discard Man 3
        self.turn_index = 2  # West
        self.awaiting_discard = True

        self.last_discard = None
        self.last_discarded_by = None
        if hasattr(self, "_terminal"):
            del self._terminal

class FixedWinGameState_2StepsFromWin(GameState):
    """
    Player 0 needs two optimal moves to win. All other hands are empty; wall is set for a forced sequence.
    Used for curriculum tests.
    """
    def __init__(self):
        super().__init__()
        from engine.tile import Tile

        # Example: Player 0 has 12 tiles forming three melds and a pair, needs to draw/discard to tenpai, then win.
        # Player 0's hand (example): [1m,2m,3m] [4m,5m,6m] [7m,8m,9m] [1p,1p]
        # Wall: [2p, 3p] (needs to draw 2p, then 3p to win with 1p pair)
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Man", 9, 8),
            Tile("Pin", 1, 9), Tile("Pin", 1, 9),
            Tile("Pin", 2, 10) # Needs to draw Pin 3, will win with [2p,3p,1p,1p] as pair
        ]
        self.players[1].hand = []
        self.players[2].hand = []
        self.players[3].hand = []
        # Only two tiles in wall, must draw both in sequence
        self.wall = [Tile("Pin", 3, 11)]
        self.turn_index = 0
        self.awaiting_discard = False
        self._terminal = False
        self.last_discard = None
        self.discard_pile = [[] for _ in range(4)]
        for p in self.players:
            p.melds = []


class FixedWinGameState_3StepsFromWin(GameState):
    """
    Curriculum state: Player 0 must make three correct moves to win. Only draw/discard actions are possible.
    """
    def __init__(self):
        super().__init__()
        from engine.tile import Tile
        # Player 0: 11 tiles, needs to draw three tiles (from wall) to complete hand and win
        self.players[0].hand = [
            Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
            Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
            Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Man", 9, 8),
            Tile("Pin", 2, 10), Tile("Pin", 3, 11)
        ]
        self.players[1].hand = []
        self.players[2].hand = []
        self.players[3].hand = []
        # Wall contains three required tiles to form melds/pair (the sequence to win)
        self.wall = [
            Tile("Pin", 4, 12),
            Tile("Pin", 5, 13),
            Tile("Pin", 5, 13)
        ]
        self.turn_index = 0
        self.awaiting_discard = False
        self._terminal = False
        self.last_discard = None
        self.discard_pile = [[] for _ in range(4)]
        for p in self.players:
            p.melds = []
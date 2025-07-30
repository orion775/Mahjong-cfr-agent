import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.tile import Tile
from engine.game_state import GameState
def test_chi_trigger():
    print("🔍 CHI TRIGGER TEST")
    state = GameState()
    
    for p in state.players:
        p.hand.clear()
        p.melds.clear()

    discard_tile = Tile("Man", 5, 4)
    state.last_discard = discard_tile
    state.last_discarded_by = 0  # East

    south = state.players[1]
    south.hand = [
        Tile("Man", 4, 3),
        Tile("Man", 6, 5),
        Tile("Pin", 1, 9)
    ]

    state.turn_index = 1
    state.awaiting_discard = False

    melds = state.can_chi(discard_tile, player=south)
    print("CHI Options:", melds)

    actions = state.get_legal_actions()
    chi_actions = [a for a in actions if 85 <= a <= 105]
    print("Legal CHI Actions:", chi_actions)

if __name__ == "__main__":
    test_chi_trigger()

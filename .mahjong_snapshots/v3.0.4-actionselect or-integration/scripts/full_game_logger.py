import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from engine.game_state import GameState
from engine.action_space import PASS

class LoggingAgent:
    def __init__(self, player_id):
        self.player_id = player_id

    def get_action(self, state):
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            return None
        return random.choice(legal_actions)

def describe_action(action, state, player):
    from engine.action_space import decode_chi  # Only decode_chi is available

    if 0 <= action <= 41:
        tile = [t for t in player.hand if t.tile_id == action]
        return f"DISCARD: {tile[0] if tile else action}"
    elif 42 <= action <= 83:
        return f"PON: ActionID {action}"
    elif 85 <= action <= 105:
        try:
            return f"CHI: {decode_chi(action)}"
        except Exception:
            return f"CHI: ActionID {action}"
    elif 106 <= action <= 147:
        return f"KAN: ActionID {action}"
    elif hasattr(state, 'PASS') and action == state.PASS:
        return "PASS"
    elif action == PASS:
        return "PASS"
    else:
        return f"UNKNOWN ACTION {action}"

def run_full_logged_demo(max_turns=300):
    state = GameState()
    agents = [LoggingAgent(i) for i in range(4)]
    transcript = []
    move_number = 0

    # Initial draw
    state.step()
    transcript.append(f"Initial draw. Wall: {len(state.wall)} tiles.")

    while not state.is_terminal() and move_number < max_turns:
        current_player = state.get_current_player()
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            transcript.append(f"Turn {move_number}: No legal actions. Stopping.")
            break

        action = agents[state.turn_index].get_action(state)
        action_desc = describe_action(action, state, current_player)

        # Log before step
        transcript.append(
            f"Turn {move_number}: {current_player.seat} | Action: {action_desc}\n"
            f"    Hand: {[str(t) for t in current_player.hand]}\n"
            f"    Melds: {current_player.melds}"
        )

        try:
            state.step(action)
        except Exception as e:
            transcript.append(f"    ERROR: {e}")
            break

        move_number += 1

    # End-of-game summary
    transcript.append(f"GAME END | Reason: {'Wall exhausted' if len(state.wall)==0 else 'Terminal state'}\n")
    if hasattr(state, 'winners'):
        for winner_id in state.winners:
            winner = state.players[winner_id]
            transcript.append(
                f"WINNER: {winner.seat}\n"
                f"    Hand: {[str(t) for t in winner.hand]}\n"
                f"    Melds: {winner.melds}\n"
            )
    else:
        transcript.append("No winner (draw).\n")

    # Per-player summary
    for i, player in enumerate(state.players):
        transcript.append(
            f"{player.seat}: {len(player.hand)} tiles, Melds: {player.melds}"
        )

    # Write to file
    with open("full_game_transcript.txt", "w", encoding="utf-8") as f:
        for line in transcript:
            f.write(line + "\n")
    print("Full game log written to full_game_transcript.txt.")

if __name__ == "__main__":
    random.seed()
    run_full_logged_demo()
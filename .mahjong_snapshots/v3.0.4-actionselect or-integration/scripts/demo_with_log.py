import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from engine.game_state import GameState
from engine.action_space import PASS
class RandomAgent:
    def __init__(self, player_id):
        self.player_id = player_id

    def get_action(self, state):
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            return None
        return random.choice(legal_actions)
def run_demo(max_turns=200):
    print("🇨🇳 CHINESE MAHJONG 4-PLAYER DEMO")
    print("="*50)
    print("Features: CHI from any player, No KAN bonus draws, Chinese scoring")
    print()

    # Create game and agents
    state = GameState()
    agents = [RandomAgent(i) for i in range(4)]
    state.step()
    turn_count = 0

    with open("turn_by_turn_log.txt", "w", encoding="utf-8") as logfile:
        print("🎲 Game Starting...")
        logfile.write("🎲 Game Starting...\n")
        while not state.is_terminal() and turn_count < max_turns:
            current_player = state.get_current_player()
            legal_actions = state.get_legal_actions()
            if not legal_actions:
                break
            action = agents[state.turn_index].get_action(state)
            if action is None:
                break

            # Print and log state before action
            logline = (
                f"\nTurn {turn_count}: {current_player.seat}'s move\n"
                f"  Hand: {[str(t) for t in current_player.hand]}\n"
                f"  Melds: {current_player.melds}\n"
                f"  Legal actions: {legal_actions}\n"
                f"  Action chosen: {action}\n"
            )
            print(logline)
            logfile.write(logline)

            try:
                state.step(action)
                # Meld indicator
                melds_after = sum(len(p.melds) for p in state.players)
                melds_before = sum(len(p.melds) for p in state.players)
                if melds_after > melds_before:
                    for i, player in enumerate(state.players):
                        if len(player.melds) > melds_before:
                            msg = f" {player.seat} created a meld! (Total: {melds_after})\n"
                            print(msg)
                            logfile.write(msg)
                            break
            except Exception as e:
                err_msg = f"Error: {e}\n"
                print(err_msg)
                logfile.write(err_msg)
                break

            turn_count += 1
            if turn_count % 25 == 0:
                status = f" Turn {turn_count}: Game in progress...\n"
                print(status)
                logfile.write(status)

        # Results
        summary = f"\n🏁 GAME COMPLETE!\nTurns played: {turn_count}\n"
        print(summary)
        logfile.write(summary)

        if state.is_terminal() and hasattr(state, 'winners'):
            for winner_id in state.winners:
                winner = state.players[winner_id]
                chinese_score = state.get_hand_score(winner)
                winner_msg = (f"🏆 WINNER: {winner.seat}\n"
                              f"   Chinese Score: {chinese_score} points\n"
                              f"   Hand: {len(winner.hand)} tiles\n"
                              f"   Melds: {len(winner.melds)}\n")
                print(winner_msg)
                logfile.write(winner_msg)
        else:
            msg = "Game ended without winner (wall exhausted)\n"
            print(msg)
            logfile.write(msg)

        # Final stats
        total_melds = sum(len(p.melds) for p in state.players)
        stats = (f"\n Final Statistics:\n"
                 f"   Total melds created: {total_melds}\n"
                 f"   Average melds per player: {total_melds/4:.1f}\n")
        print(stats)
        logfile.write(stats)
        for i, player in enumerate(state.players):
            score = state.get_hand_score(player)
            pstat = (f"   {player.seat}: {len(player.hand)} tiles, {len(player.melds)} melds, {score} pts\n")
            print(pstat)
            logfile.write(pstat)

        # Generate summary
        state.get_game_summary("demo_summary.txt")
        dsmsg = f"\n📁 Detailed summary saved to: demo_summary.txt\n"
        print(dsmsg)
        logfile.write(dsmsg)

    return state

if __name__ == "__main__":
    import random
    random.seed()
    run_demo()

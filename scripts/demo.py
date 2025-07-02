# scripts/demo.py

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
    
    # Initial draw
    state.step()
    
    turn_count = 0
    
    print("🎲 Game Starting...")
    
    while not state.is_terminal() and turn_count < max_turns:
        current_player = state.get_current_player()
        
        # Get and execute action
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            break
            
        action = agents[state.turn_index].get_action(state)
        if action is None:
            break
        
        # Track melds BEFORE taking action
        melds_before = sum(len(p.melds) for p in state.players)
        player_melds_before = [len(p.melds) for p in state.players]  # Store individual counts
        
        # Execute action
        try:
            state.step(action)
            
            # Show meld creation
            melds_after = sum(len(p.melds) for p in state.players)
            if melds_after > melds_before:
                # Find which player actually got the new meld by comparing before/after
                for i, player in enumerate(state.players):
                    if len(player.melds) > player_melds_before[i]:
                        print(f" {player.seat} created a meld! (Total: {melds_after})")
                        break
                else:
                    print(f" Someone created a meld! (Total: {melds_after})")
                        
        except Exception as e:
            print(f"Error: {e}")
            break
        
        turn_count += 1
        
        # Progress indicator
        if turn_count % 25 == 0:
            print(f" Turn {turn_count}: Game in progress...")
    
    # Results
    print(f"\n🏁 GAME COMPLETE!")
    print(f"Turns played: {turn_count}")
    
    if state.is_terminal() and hasattr(state, 'winners'):
        for winner_id in state.winners:
            winner = state.players[winner_id]
            chinese_score = state.get_hand_score(winner)
            print(f"🏆 WINNER: {winner.seat}")
            print(f"   Chinese Score: {chinese_score} points")
            print(f"   Hand: {len(winner.hand)} tiles")
            print(f"   Melds: {len(winner.melds)}")
    else:
        print("Game ended without winner (wall exhausted)")
    
    # Final stats
    total_melds = sum(len(p.melds) for p in state.players)
    print(f"\n Final Statistics:")
    print(f"   Total melds created: {total_melds}")
    print(f"   Average melds per player: {total_melds/4:.1f}")
    
    for i, player in enumerate(state.players):
        score = state.get_hand_score(player)
        print(f"   {player.seat}: {len(player.hand)} tiles, {len(player.melds)} melds, {score} pts")
    
    # Generate summary
    state.get_game_summary("demo_summary.txt")
    print(f"\n📁 Detailed summary saved to: demo_summary.txt")
    
    return state

if __name__ == "__main__":
    random.seed()  # Random each time
    run_demo()
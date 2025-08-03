"""
Comprehensive Winning Game Logger

This script uses the aggressive model (13%+ win rate) to run games until we get
a WIN (not draw), then logs every single detail to verify the game engine works correctly.

Purpose: Debug the game engine by examining a complete winning game trace.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
from trainers.selfplay_neural_trainer import SelfPlayNeuralTrainer, MahjongDQN
from engine.game_state import GameState
import random
import copy
from datetime import datetime

class WinningGameLogger:
    """Log every detail of a winning game to verify game engine correctness."""
    
    def __init__(self, model_path="checkpoints/selfplay_v4_episode_2000.pth"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Game log storage
        self.game_log = []
        self.move_counter = 0
        
        # Load the model that can actually win
        self.load_model()
    
    def load_model(self):
        """Load the aggressive model that achieved 13%+ wins."""
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
            
            # Initialize network
            self.network = MahjongDQN().to(self.device)
            self.network.load_state_dict(checkpoint['q_network_state_dict'])
            self.network.eval()
            
            print(f"✅ Loaded model: {self.model_path}")
            print(f"   Model win rate: {checkpoint.get('training_stats', {}).get('win_rate', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.network = None
    
    def extract_features(self, game_state, player_id=0):
        """Extract features for the neural network."""
        player = game_state.players[player_id]
        features = []
        
        # Basic hand features
        features.extend([
            len(player.hand) / 15.0,
            len(getattr(player, 'melds', [])) / 5.0,
            len(game_state.wall) / 144.0,
            1.0 if getattr(game_state, 'awaiting_discard', True) else 0.0
        ])
        
        # Tile distribution (simplified)
        tile_counts = [0] * 34
        for tile in player.hand:
            tile_id = getattr(tile, 'tile_id', 0) % 34
            tile_counts[tile_id] += 1
        features.extend([count / 4.0 for count in tile_counts])
        
        # Pad to expected size
        while len(features) < 50:
            features.append(0.0)
        features = features[:50]
        
        return np.array(features, dtype=np.float32)
    
    def select_action(self, game_state, player_id=0):
        """Select action using the trained network."""
        if self.network is None:
            # Fallback to random
            legal_actions = game_state.get_legal_actions()
            return random.choice(legal_actions) if legal_actions else None
        
        legal_actions = game_state.get_legal_actions()
        if not legal_actions:
            return None
        
        # Get Q-values from network
        features = self.extract_features(game_state, player_id)
        state_tensor = torch.FloatTensor(features).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            q_values = self.network(state_tensor)
        
        # Mask illegal actions
        q_values_np = q_values.cpu().numpy()[0]
        masked_q_values = np.full(140, -np.inf)
        for action in legal_actions:
            if action < 140:
                masked_q_values[action] = q_values_np[action]
        
        return np.argmax(masked_q_values)
    
    def log_game_state(self, game_state, action=None, player_id=None, description=""):
        """Log current game state in detail."""
        self.move_counter += 1
        
        log_entry = {
            'move': self.move_counter,
            'timestamp': datetime.now().strftime("%H:%M:%S.%f")[:-3],
            'current_player': getattr(game_state, 'current_player', getattr(game_state, 'turn_index', 0)),
            'awaiting_discard': getattr(game_state, 'awaiting_discard', False),
            'wall_size': len(game_state.wall),
            'action': action,
            'action_player': player_id,
            'description': description,
            'terminal': game_state.is_terminal(),
            'winners': getattr(game_state, 'winners', []),
            'last_discard': str(game_state.last_discard) if game_state.last_discard else None,
            'last_discarded_by': game_state.last_discarded_by,
            'players': []
        }
        
        # Log each player's state
        for i, player in enumerate(game_state.players):
            player_info = {
                'player_id': i,
                'seat': getattr(player, 'seat', f'Player_{i}'),
                'hand_size': len(player.hand),
                'hand_tiles': [str(t) for t in player.hand],
                'melds': [(mtype, [str(t) for t in tiles]) for mtype, tiles in getattr(player, 'melds', [])],
                'meld_count': len(getattr(player, 'melds', [])),
                'bonus_tiles': [str(t) for t in getattr(player, 'bonus_tiles', [])],
                'is_winner': i in getattr(game_state, 'winners', [])
            }
            log_entry['players'].append(player_info)
        
        # Log discards for each seat
        log_entry['discards'] = {}
        for seat in ["East", "South", "West", "North"]:
            discards = game_state.discards.get(seat, [])
            log_entry['discards'][seat] = [str(t) for t in discards]
        
        self.game_log.append(log_entry)
    
    def action_to_description(self, action, game_state):
        """Convert action ID to human-readable description."""
        if action is None:
            return "NO_ACTION"
        elif action < 34:
            return f"DISCARD tile_id_{action}"
        elif action == 84:
            return "PASS"
        elif 34 <= action < 68:
            tile_id = action - 34
            return f"PON tile_id_{tile_id}"
        elif 68 <= action < 84:
            return f"CHI action_{action}"
        elif action >= 106:
            tile_id = action - 106
            return f"KAN tile_id_{tile_id}"
        else:
            return f"UNKNOWN_ACTION_{action}"
    
    def run_until_win(self, max_attempts=100, max_steps_per_game=300):
        """Run games until we get a win, logging the winning game completely."""
        print(f"🎯 SEARCHING FOR WINNING GAME...")
        print(f"   Max attempts: {max_attempts}")
        print(f"   Max steps per game: {max_steps_per_game}")
        print()
        
        for attempt in range(max_attempts):
            print(f"🎮 Attempt {attempt + 1}/{max_attempts}")
            
            # Reset for new game
            self.game_log = []
            self.move_counter = 0
            
            game_state = GameState()
            
            # Log initial state
            self.log_game_state(game_state, description="GAME_START")
            
            # Initial step if needed
            if hasattr(game_state, 'step') and not getattr(game_state, 'awaiting_discard', True):
                game_state.step()
                self.log_game_state(game_state, description="INITIAL_STEP")
            
            step_count = 0
            while not game_state.is_terminal() and step_count < max_steps_per_game:
                # Get current player
                current_player = getattr(game_state, 'current_player', getattr(game_state, 'turn_index', 0))
                
                # Select action
                action = self.select_action(game_state, current_player)
                
                if action is None:
                    self.log_game_state(game_state, action, current_player, "NO_LEGAL_ACTIONS - GAME_END")
                    break
                
                # Log pre-action state
                action_desc = self.action_to_description(action, game_state)
                self.log_game_state(game_state, action, current_player, f"BEFORE: {action_desc}")
                
                # Execute action
                try:
                    game_state.step(action)
                    step_count += 1
                    
                    # Log post-action state
                    self.log_game_state(game_state, action, current_player, f"AFTER: {action_desc}")
                    
                    # Check for win
                    if game_state.is_terminal():
                        if hasattr(game_state, 'winners') and game_state.winners:
                            print(f"🎉 FOUND WINNING GAME! Attempt {attempt + 1}")
                            print(f"   Winner(s): {game_state.winners}")
                            print(f"   Game length: {step_count} moves")
                            self.log_game_state(game_state, None, None, "GAME_WON!")
                            return True  # Success!
                        else:
                            print(f"   Game ended in draw ({step_count} moves)")
                            break  # Try next game
                
                except Exception as e:
                    error_desc = f"ERROR: {str(e)}"
                    self.log_game_state(game_state, action, current_player, error_desc)
                    print(f"   Error at step {step_count}: {e}")
                    break
            
            if step_count >= max_steps_per_game:
                print(f"   Hit step limit ({max_steps_per_game})")
        
        print(f"❌ No winning game found in {max_attempts} attempts")
        return False
    
    def save_log(self, filename=None):
        """Save the detailed game log to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"winning_game_log_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE WINNING GAME LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"Model: {self.model_path}\n")
            f.write(f"Total moves logged: {len(self.game_log)}\n")
            
            # Check if this was actually a winning game
            if self.game_log:
                final_entry = self.game_log[-1]
                winners = final_entry.get('winners', [])
                f.write(f"Game result: {'WIN' if winners else 'DRAW/ERROR'}\n")
                if winners:
                    f.write(f"Winners: {winners}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("MOVE-BY-MOVE DETAILED LOG\n")
            f.write("=" * 80 + "\n\n")
            
            for entry in self.game_log:
                f.write(f"MOVE {entry['move']} [{entry['timestamp']}]\n")
                f.write(f"Description: {entry['description']}\n")
                f.write(f"Current Player: {entry['current_player']}\n")
                f.write(f"Awaiting Discard: {entry['awaiting_discard']}\n")
                f.write(f"Wall Size: {entry['wall_size']}\n")
                f.write(f"Terminal: {entry['terminal']}\n")
                f.write(f"Winners: {entry['winners']}\n")
                f.write(f"Last Discard: {entry['last_discard']} (by Player {entry['last_discarded_by']})\n")
                
                if entry['action'] is not None:
                    f.write(f"Action: {entry['action']} (Player {entry['action_player']})\n")
                
                f.write("\nPLAYER STATES:\n")
                for player in entry['players']:
                    f.write(f"  Player {player['player_id']} ({player['seat']}):\n")
                    f.write(f"    Hand ({player['hand_size']}): {player['hand_tiles']}\n")
                    f.write(f"    Melds ({player['meld_count']}): {player['melds']}\n")
                    if player['bonus_tiles']:
                        f.write(f"    Bonus: {player['bonus_tiles']}\n")
                    if player['is_winner']:
                        f.write(f"    >>> WINNER! <<<\n")
                
                f.write("\nDISCARDS:\n")
                for seat, discards in entry['discards'].items():
                    if discards:
                        f.write(f"  {seat}: {discards}\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
            
            # Final analysis
            f.write("=" * 80 + "\n")
            f.write("FINAL ANALYSIS\n")
            f.write("=" * 80 + "\n")
            
            if self.game_log:
                final = self.game_log[-1]
                f.write(f"Game ended: {final['description']}\n")
                f.write(f"Total moves: {final['move']}\n")
                f.write(f"Final wall size: {final['wall_size']}\n")
                
                if final['winners']:
                    f.write(f"\n🎉 WINNING PLAYERS: {final['winners']}\n")
                    for player in final['players']:
                        if player['is_winner']:
                            f.write(f"\nWinner {player['player_id']} ({player['seat']}) Final State:\n")
                            f.write(f"  Hand: {player['hand_tiles']}\n")
                            f.write(f"  Melds: {player['melds']}\n")
                            f.write(f"  Total tiles: {player['hand_size'] + sum(len(tiles) for _, tiles in player['melds'])}\n")
                else:
                    f.write(f"\n❌ Game ended without winner (draw)\n")
        
        print(f"📄 Detailed log saved: {filename}")
        return filename

def main():
    print("🔍 WINNING GAME LOGGER")
    print("Testing game engine with aggressive model (13%+ wins)")
    print("=" * 60)
    
    logger = WinningGameLogger()
    
    if logger.network is None:
        print("❌ Could not load model - aborting")
        return
    
    # Try to find a winning game
    success = logger.run_until_win(max_attempts=50, max_steps_per_game=300)
    
    if success:
        # Save the winning game log
        log_file = logger.save_log()
        print(f"\n🎉 SUCCESS! Winning game captured and logged.")
        print(f"📄 Check the log file: {log_file}")
        print("\nThe log contains:")
        print("- Every move made by every player")
        print("- Hand states after each action")
        print("- Meld formations and discards")
        print("- Win detection details")
        print("- Complete game trace for analysis")
        
    else:
        print(f"\n❌ Could not find a winning game in 50 attempts")
        print("This suggests potential issues with:")
        print("- Game engine win detection")
        print("- Model strategy (may not pursue wins)")
        print("- Action execution problems")
        
        # Save the last attempted game anyway for analysis
        if logger.game_log:
            log_file = logger.save_log("failed_game_attempt.txt")
            print(f"📄 Last attempt logged: {log_file}")

if __name__ == "__main__":
    main()

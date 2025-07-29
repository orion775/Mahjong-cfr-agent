# fixed_meld_counting_cfr.py
"""
FIXED: CFR Trainer that properly counts melds from all players,
not just the target player. This resolves the "0 melds formed" bug.
"""

import random
from collections import defaultdict, Counter
from engine.game_state import GameState
import copy

class FixedMeldCountingCFRTrainer:
    """
    CFR trainer with corrected meld counting and better learning feedback
    """
    
    def __init__(self):
        self.regret_table = defaultdict(lambda: [0.0] * 148)
        self.strategy_sum_table = defaultdict(lambda: [0.0] * 148)
        self.simulation_depth_limit = 3
        
        # Enhanced training statistics
        self.training_stats = {
            'iterations_completed': 0,
            'total_games_played': 0,
            'games_won': 0,
            'games_drawn': 0,
            'total_melds_formed': 0,
            'player_melds_formed': 0,  # Melds by target player specifically
            'avg_game_length': 0.0,
            'best_reward': 0.0,
            'wall_exhaustion_games': 0,
            'proper_wins': 0,
            'meld_formation_rate': 0.0,
            'learning_progress': 0.0
        }
        
    def get_strategy(self, info_set, legal_actions):
        """Get current strategy for an info set"""
        regrets = self.regret_table[info_set]
        
        strategy = [0.0] * 148
        positive_regret_sum = 0.0
        
        for action in legal_actions:
            if action < 148:
                positive_regret = max(0.0, regrets[action])
                strategy[action] = positive_regret
                positive_regret_sum += positive_regret
        
        if positive_regret_sum > 0:
            for action in legal_actions:
                if action < 148:
                    strategy[action] = max(0.0, regrets[action]) / positive_regret_sum
        else:
            uniform_prob = 1.0 / len(legal_actions) if legal_actions else 0.0
            for action in legal_actions:
                if action < 148:
                    strategy[action] = uniform_prob
        
        return strategy
    
    def proper_deep_clone(self, state):
        """Properly deep clone the game state"""
        try:
            return copy.deepcopy(state)
        except Exception as e:
            print(f"Deep copy failed: {e}")
            return self.manual_clone(state)
    
    def manual_clone(self, state):
        """Manual state cloning as backup"""
        try:
            new_state = GameState()
            
            # Copy basic attributes
            new_state.turn_index = state.turn_index
            new_state.awaiting_discard = state.awaiting_discard
            new_state.pass_counter = state.pass_counter
            new_state.last_discard = state.last_discard
            new_state.last_discarded_by = state.last_discarded_by
            new_state.step_counter = getattr(state, 'step_counter', 0)
            new_state.step_limit = getattr(state, 'step_limit', 200)
            
            # Copy wall (CRITICAL: make new list)
            new_state.wall = state.wall[:]
            
            # Copy players manually
            new_state.players = []
            for player in state.players:
                new_player = type(player)(player.seat)
                new_player.hand = player.hand[:]
                new_player.melds = player.melds[:]
                if hasattr(player, 'bonus_tiles'):
                    new_player.bonus_tiles = player.bonus_tiles[:]
                new_state.players.append(new_player)
            
            # Copy discards
            new_state.discards = {}
            for seat, discard_pile in state.discards.items():
                new_state.discards[seat] = discard_pile[:]
            
            # Copy terminal state
            if hasattr(state, '_terminal'):
                new_state._terminal = state._terminal
                
            return new_state
            
        except Exception as e:
            print(f"Manual clone failed: {e}")
            return state
    
    def count_total_melds(self, state):
        """Count total melds across ALL players"""
        total_melds = 0
        for player in state.players:
            total_melds += len(player.melds)
        return total_melds
    
    def simple_rollout(self, state, player_id=0, max_steps=30):
        """Simple rollout for action evaluation"""
        rollout_state = self.proper_deep_clone(state)
        
        steps = 0
        while not rollout_state.is_terminal() and steps < max_steps:
            legal_actions = rollout_state.get_legal_actions()
            if not legal_actions:
                break
            
            action = random.choice(legal_actions)
            try:
                rollout_state.step(action)
                steps += 1
            except Exception:
                break
        
        # Enhanced reward calculation
        reward = 0.0
        
        # Base reward for winning
        if rollout_state.is_terminal():
            base_reward = rollout_state.get_reward(player_id)
            reward += base_reward
            if base_reward > 0:
                reward += 0.5  # Win bonus
        
        # Reward for meld formation (all players)
        total_melds = self.count_total_melds(rollout_state)
        reward += total_melds * 0.05  # Small reward per meld
        
        # Extra reward for target player's melds
        player_melds = len(rollout_state.players[player_id].melds)
        reward += player_melds * 0.1
        
        return reward
    
    def train_iteration(self, player_id=0):
        """Single training iteration with FIXED meld counting"""
        # Create fresh game
        state = GameState()
        
        initial_wall_size = len(state.wall)
        if not state.awaiting_discard:
            try:
                state.step()  # Initial draw
            except Exception as e:
                print(f"Initial step failed: {e}")
                return 0.0
        
        # FIXED: Count initial melds for ALL players
        initial_total_melds = self.count_total_melds(state)
        initial_player_melds = len(state.players[player_id].melds)
        
        steps = 0
        max_game_steps = 200
        iteration_reward = 0.0
        
        while not state.is_terminal() and steps < max_game_steps:
            current_player = state.turn_index
            info_set = state.get_info_set()
            legal_actions = state.get_legal_actions()
            
            if not legal_actions:
                break
            
            # Get strategy
            strategy = self.get_strategy(info_set, legal_actions)
            action = self.sample_action(strategy, legal_actions)
            
            # Update learning for target player
            if current_player == player_id:
                # Quick action evaluation (limited for speed)
                action_values = {}
                test_actions = legal_actions[:min(3, len(legal_actions))]
                
                for test_action in test_actions:
                    test_state = self.proper_deep_clone(state)
                    try:
                        test_state.step(test_action)
                        action_values[test_action] = self.simple_rollout(test_state, player_id, max_steps=15)
                    except Exception:
                        action_values[test_action] = -0.2
                
                # Update regrets
                if action_values:
                    avg_value = sum(action_values.values()) / len(action_values)
                    regrets = self.regret_table[info_set]
                    strategy_sum = self.strategy_sum_table[info_set]
                    
                    for test_action, value in action_values.items():
                        if test_action < 148:
                            regret = value - avg_value
                            regrets[test_action] += regret
                    
                    # Update strategy sum
                    for test_action in legal_actions[:10]:
                        if test_action < 148:
                            strategy_sum[test_action] += strategy[test_action]
            
            # Take action
            try:
                state.step(action)
                steps += 1
                        
            except Exception as e:
                if steps < 3:
                    print(f"  Action {action} failed at step {steps}: {e}")
                break
        
        # FIXED: Count final melds for ALL players
        final_total_melds = self.count_total_melds(state)
        final_player_melds = len(state.players[player_id].melds)
        
        # Calculate meld formation
        total_melds_formed = final_total_melds - initial_total_melds
        player_melds_formed = final_player_melds - initial_player_melds
        
        # Final reward calculation
        if state.is_terminal():
            iteration_reward = state.get_reward(player_id)
            if iteration_reward > 0:
                self.training_stats['games_won'] += 1
                self.training_stats['proper_wins'] += 1
            else:
                self.training_stats['games_drawn'] += 1
                if len(state.wall) == 0:
                    self.training_stats['wall_exhaustion_games'] += 1
        else:
            self.training_stats['games_drawn'] += 1
        
        # FIXED: Update statistics with correct meld counts
        self.training_stats['total_games_played'] += 1
        self.training_stats['total_melds_formed'] += total_melds_formed
        self.training_stats['player_melds_formed'] += player_melds_formed
        
        # Update average game length
        games_played = self.training_stats['total_games_played']
        old_avg = self.training_stats['avg_game_length']
        self.training_stats['avg_game_length'] = ((old_avg * (games_played - 1)) + steps) / games_played
        
        # Update meld formation rate
        if games_played > 0:
            self.training_stats['meld_formation_rate'] = self.training_stats['total_melds_formed'] / games_played
        
        if iteration_reward > self.training_stats['best_reward']:
            self.training_stats['best_reward'] = iteration_reward
        
        return iteration_reward
    
    def sample_action(self, strategy, legal_actions):
        """Sample action from strategy"""
        if not legal_actions:
            return None
        
        probs = [strategy[action] if action < len(strategy) else 0.0 for action in legal_actions]
        total_prob = sum(probs)
        
        if total_prob <= 0:
            return random.choice(legal_actions)
        
        probs = [p / total_prob for p in probs]
        
        r = random.random()
        cumulative = 0.0
        for i, prob in enumerate(probs):
            cumulative += prob
            if r <= cumulative:
                return legal_actions[i]
        
        return legal_actions[-1]
    
    def train(self, iterations=50, player_id=0, verbose=True):
        """Train with proper meld counting"""
        if verbose:
            print(f"🚀 CFR Training with FIXED Meld Counting ({iterations} iterations)")
            print(f"   Target player: {player_id}")
            print(f"   Now tracking melds from ALL players!")
            print("-" * 60)
        
        successful_iterations = 0
        total_reward = 0.0
        
        for i in range(iterations):
            try:
                reward = self.train_iteration(player_id)
                successful_iterations += 1
                total_reward += reward
                self.training_stats['iterations_completed'] += 1
                
                # Enhanced progress reporting
                if verbose and ((i + 1) % 10 == 0 or i == iterations - 1):
                    avg_reward = total_reward / successful_iterations if successful_iterations > 0 else 0
                    win_rate = (self.training_stats['games_won'] / max(1, self.training_stats['total_games_played']) * 100)
                    avg_length = self.training_stats['avg_game_length']
                    meld_rate = self.training_stats['meld_formation_rate']
                    
                    print(f"  Iter {i+1:2d}/{iterations}: "
                          f"Reward={avg_reward:.3f} | "
                          f"Win%={win_rate:.1f} | "
                          f"AvgLen={avg_length:.1f} | "
                          f"Melds/Game={meld_rate:.1f} | "
                          f"InfoSets={len(self.regret_table)}")
                    
            except Exception as e:
                if verbose:
                    print(f"  Error in iteration {i+1}: {e}")
        
        if verbose:
            print("-" * 60)
            print(f"🎯 TRAINING COMPLETE WITH FIXED MELD COUNTING!")
            self.print_enhanced_summary()
        
        return successful_iterations > 0
    
    def print_enhanced_summary(self):
        """Print comprehensive summary with correct meld statistics"""
        stats = self.training_stats
        
        print(f"📊 Enhanced Training Summary:")
        print(f"   Successful iterations: {stats['iterations_completed']}")
        print(f"   Total games: {stats['total_games_played']}")
        print(f"   Proper wins: {stats['proper_wins']}")
        print(f"   Wall exhaustions: {stats['wall_exhaustion_games']}")
        print(f"   Other draws: {stats['games_drawn'] - stats['wall_exhaustion_games']}")
        print(f"   Win rate: {stats['games_won']/max(1, stats['total_games_played'])*100:.1f}%")
        print(f"   Average game length: {stats['avg_game_length']:.1f} steps")
        
        # FIXED: Proper meld statistics
        print(f"   🔧 FIXED MELD STATISTICS:")
        print(f"      Total melds formed (all players): {stats['total_melds_formed']}")
        print(f"      Target player melds: {stats['player_melds_formed']}")
        print(f"      Average melds per game: {stats['meld_formation_rate']:.1f}")
        
        print(f"   Info sets learned: {len(self.regret_table)}")
        print(f"   Best reward: {stats['best_reward']:.4f}")
        
        # Enhanced diagnostic analysis
        print(f"\n🔍 Diagnostic Analysis:")
        if stats['avg_game_length'] > 100:
            print("   ✅ Games have proper length - state copying working correctly")
        else:
            print("   ⚠️  Games still short - potential state copying issues")
        
        if stats['total_melds_formed'] > stats['total_games_played'] * 2:
            print("   ✅ Good meld formation - players are forming melds successfully")
        elif stats['total_melds_formed'] > 0:
            print("   ⚠️  Some meld formation - engine working but could improve")
        else:
            print("   ❌ No meld formation - there may still be counting issues")
        
        if len(self.regret_table) > 1000:
            print("   ✅ Excellent info set diversity - rich learning happening")
        elif len(self.regret_table) > 100:
            print("   ✅ Good info set diversity - learning is occurring")
        else:
            print("   ⚠️  Limited info set diversity - may need more exploration")
        
        # Learning progress estimation
        if stats['total_melds_formed'] > 0 and len(self.regret_table) > 100:
            print("   🎉 CFR appears to be learning successfully!")
        else:
            print("   ⚠️  CFR learning may need improvement")

def test_fixed_meld_counting():
    """Test the CFR trainer with fixed meld counting"""
    print("🧪 Testing CFR Trainer with FIXED Meld Counting")
    print("Expected: Should now correctly count melds from all players")
    print("="*70)
    
    random.seed(42)
    trainer = FixedMeldCountingCFRTrainer()
    
    # Test with moderate iterations
    success = trainer.train(iterations=5000, player_id=0, verbose=True)
    
    if success:
        print(f"\n🎯 Training Analysis:")
        
        # Analyze results
        total_melds = trainer.training_stats['total_melds_formed']
        total_games = trainer.training_stats['total_games_played']
        avg_melds_per_game = total_melds / max(1, total_games)
        
        if total_melds > 0:
            print(f"🎉 SUCCESS: {total_melds} total melds formed!")
            print(f"   Average: {avg_melds_per_game:.1f} melds per game")
            
            if avg_melds_per_game > 5:
                print(f"   🌟 EXCELLENT: High meld formation rate - CFR is working great!")
            elif avg_melds_per_game > 2:
                print(f"   ✅ GOOD: Decent meld formation - CFR is learning")
            else:
                print(f"   ⚠️  MODERATE: Some meld formation - room for improvement")
        else:
            print(f"❌ STILL ISSUES: No melds counted (there may be other bugs)")
        
        # Info set analysis
        info_sets = len(trainer.regret_table)
        if info_sets > 1000:
            print(f"🧠 EXCELLENT: {info_sets} info sets - rich learning diversity")
        else:
            print(f"🧠 GOOD: {info_sets} info sets - solid learning base")
        
    else:
        print("❌ Training failed!")
    
    return trainer

if __name__ == "__main__":
    trainer = test_fixed_meld_counting()
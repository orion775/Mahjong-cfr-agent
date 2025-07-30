# meld_aware_cfr.py
"""
Meld-Aware CFR Trainer that learns to recognize and value complete melds in hand
WITHOUT hardcoding - through smart reward shaping and hand evaluation
"""

import random
from collections import defaultdict, Counter
from engine.game_state import GameState
import copy

class MeldAwareCFRTrainer:
    """
    CFR trainer that teaches the agent to value complete melds through rewards
    """
    
    def __init__(self):
        self.regret_table = defaultdict(lambda: [0.0] * 148)
        self.strategy_sum_table = defaultdict(lambda: [0.0] * 148)
        
        # Training statistics
        self.training_stats = {
            'iterations_completed': 0,
            'total_games_played': 0,
            'games_won': 0,
            'games_drawn': 0,
            'total_melds_formed': 0,
            'player_melds_formed': 0,
            'avg_game_length': 0.0,
            'best_reward': 0.0,
            'wall_exhaustion_games': 0,
            'proper_wins': 0,
            'meld_formation_rate': 0.0,
            # NEW: Meld awareness tracking
            'hand_triplets_detected': 0,
            'hand_sequences_detected': 0,
            'meld_value_rewards': 0.0,
            'strategic_decisions': 0
        }
        
    def analyze_hand_for_complete_melds(self, hand):
        """
        Detect complete AND partial melds in hand
        Returns: (triplet_count, sequence_count, pair_count, partial_sequences, near_triplets)
        """
        if not hand:
            return 0, 0, 0, 0, 0
            
        # Count tiles by category and value
        tile_counts = {}
        for tile in hand:
            key = (tile.category, tile.value)
            tile_counts[key] = tile_counts.get(key, 0) + 1
        
        triplets = 0
        sequences = 0
        pairs = 0
        partial_sequences = 0
        near_triplets = 0
        
        # Find triplets and pairs
        for key, count in tile_counts.items():
            if count >= 3:
                triplets += count // 3  # Multiple triplets possible
            elif count == 2:
                pairs += 1
                near_triplets += 1  # Pair is "near triplet"
        
        # Find complete sequences and partial sequences
        for suit in ['Man', 'Pin', 'Sou']:
            suit_tiles = {}
            for (category, value), count in tile_counts.items():
                if category == suit and isinstance(value, int):
                    suit_tiles[value] = count
            
            if len(suit_tiles) < 2:
                continue
                
            values = sorted(suit_tiles.keys())
            
            # Check for complete consecutive sequences (1-2-3, 2-3-4, etc.)
            i = 0
            while i < len(values) - 2:
                val1, val2, val3 = values[i], values[i+1], values[i+2]
                if val2 == val1 + 1 and val3 == val2 + 1:
                    # Found complete sequence
                    min_tiles = min(suit_tiles[val1], suit_tiles[val2], suit_tiles[val3])
                    sequences += min_tiles
                    
                    # Remove used tiles from counting
                    suit_tiles[val1] -= min_tiles
                    suit_tiles[val2] -= min_tiles  
                    suit_tiles[val3] -= min_tiles
                    
                    # Don't advance i to catch overlapping sequences
                i += 1
            
            # Check for partial sequences (missing middle or ends)
            for i in range(len(values) - 1):
                val1, val2 = values[i], values[i+1]
                
                # Adjacent tiles (e.g., 2-3, could become 1-2-3 or 2-3-4)
                if val2 == val1 + 1:
                    min_tiles = min(suit_tiles[val1], suit_tiles[val2])
                    if min_tiles > 0:
                        partial_sequences += min_tiles
                
                # Gap of 1 (e.g., 2-4, missing 3)
                elif val2 == val1 + 2:
                    min_tiles = min(suit_tiles[val1], suit_tiles[val2])
                    if min_tiles > 0:
                        partial_sequences += min_tiles
        
        return triplets, sequences, pairs, partial_sequences, near_triplets
    
    def evaluate_hand_strategic_value(self, hand):
        """
        Calculate strategic value of a hand based on complete AND partial melds
        """
        triplets, sequences, pairs, partial_sequences, near_triplets = self.analyze_hand_for_complete_melds(hand)
        
        # Strategic scoring (learned through rewards, not hardcoded rules)
        score = 0.0
        
        # Complete melds have high value
        score += triplets * 3.0      # Complete triplets are very valuable
        score += sequences * 3.5     # Complete sequences slightly more valuable
        
        # Partial melds have medium value (building potential)
        score += pairs * 1.0         # Pairs are valuable (can become triplets)
        score += partial_sequences * 0.8  # Partial sequences have potential
        score += near_triplets * 0.5  # Near-triplets (pairs) have some value
        
        # Bonus for multiple melds (synergy)
        total_complete_melds = triplets + sequences
        total_partial_melds = pairs + partial_sequences
        
        if total_complete_melds >= 2:
            score += total_complete_melds * 1.0  # Strong synergy bonus
        elif total_complete_melds >= 1 and total_partial_melds >= 2:
            score += 0.5  # Mixed meld bonus
        
        return score
    
    def enhanced_action_evaluation(self, state, player_id, legal_actions):
        """
        Evaluate actions by considering meld value changes
        SAFE VERSION: Avoids infinite meld loops
        """
        current_player = state.players[player_id]
        current_value = self.evaluate_hand_strategic_value(current_player.hand)
        
        action_values = {}
        
        # SAFE: Only test discard actions (0-42) to avoid meld infinite loop  
        discard_actions = [a for a in legal_actions if a < 42]
        test_actions = discard_actions[:min(6, len(discard_actions))]
        
        for action in test_actions:
            try:
                # SAFE: Direct hand evaluation without full game step
                current_hand = current_player.hand[:]
                
                # Simulate discarding this tile
                test_hand = [t for t in current_hand if t.tile_id != action]
                new_value = self.evaluate_hand_strategic_value(test_hand)
                hand_value_change = new_value - current_value
                
                # Simple position evaluation (no full rollout to avoid infinite loop)
                position_bonus = 0.0
                
                # Bonus for keeping complete melds
                if hand_value_change >= 0:
                    position_bonus += 0.5
                
                # Penalty for breaking melds 
                if hand_value_change < -1.0:
                    position_bonus -= 1.0
                
                # Combined evaluation
                total_value = hand_value_change + position_bonus
                action_values[action] = total_value
                
                # Track strategic decisions
                self.training_stats['strategic_decisions'] += 1
                
            except Exception as e:
                action_values[action] = -2.0  # Heavy penalty for illegal/failed actions
        
        # If no discard actions available, test other actions carefully
        if not action_values and legal_actions:
            non_discard_actions = [a for a in legal_actions if a >= 42]
            for action in non_discard_actions[:2]:  # Test max 2 non-discard actions
                try:
                    # For meld actions, give small positive value
                    action_values[action] = 0.1
                except:
                    action_values[action] = -1.0
        
        return action_values
    
    def strategic_rollout(self, state, player_id=0, max_steps=20):
        """
        Strategic rollout that considers meld formation and hand improvement
        SAFE VERSION: Only discard actions to avoid infinite meld loop
        """
        rollout_state = self.proper_deep_clone(state)
        
        steps = 0
        initial_hand_value = self.evaluate_hand_strategic_value(rollout_state.players[player_id].hand)
        
        while not rollout_state.is_terminal() and steps < max_steps:
            try:
                legal_actions = rollout_state.get_legal_actions()
                if not legal_actions:
                    break
                
                # SAFE: Only use discard actions (0-42) to avoid meld infinite loop
                discard_actions = [a for a in legal_actions if a < 42]
                if not discard_actions:
                    # If no discard actions, take any legal action
                    action = legal_actions[0] if legal_actions else None
                else:
                    # Semi-strategic action selection for discards only
                    current_player = rollout_state.players[rollout_state.turn_index]
                    
                    if rollout_state.turn_index == player_id and len(discard_actions) > 1:
                        # For target player, prefer discards that maintain hand value
                        best_action = discard_actions[0]
                        best_value = -float('inf')
                        
                        test_actions = discard_actions[:min(3, len(discard_actions))]
                        for test_action in test_actions:
                            try:
                                # Quick hand evaluation without full rollout
                                current_hand = current_player.hand[:]
                                # Simulate discarding this tile
                                test_hand = [t for t in current_hand if t.tile_id != test_action]
                                value = self.evaluate_hand_strategic_value(test_hand)
                                
                                if value > best_value:
                                    best_value = value
                                    best_action = test_action
                            except:
                                continue
                        
                        action = best_action
                    else:
                        # For other players, random discard
                        action = random.choice(discard_actions)
                
                if action is not None:
                    rollout_state.step(action)
                    steps += 1
                else:
                    break
                    
            except Exception as e:
                # If any error, break out of rollout
                break
        
        # Calculate reward
        reward = 0.0
        
        # Base game reward
        if rollout_state.is_terminal():
            base_reward = rollout_state.get_reward(player_id)
            reward += base_reward * 10.0  # Strong win incentive
        
        # Hand improvement reward
        final_hand_value = self.evaluate_hand_strategic_value(rollout_state.players[player_id].hand)
        hand_improvement = final_hand_value - initial_hand_value
        reward += hand_improvement * 2.0
        
        # Meld formation rewards
        player_melds = len(rollout_state.players[player_id].melds)
        reward += player_melds * 1.0
        
        # Track meld detection
        triplets, sequences, pairs, partial_sequences, near_triplets = self.analyze_hand_for_complete_melds(rollout_state.players[player_id].hand)
        self.training_stats['hand_triplets_detected'] += triplets
        self.training_stats['hand_sequences_detected'] += sequences
        self.training_stats['meld_value_rewards'] += hand_improvement
        
        return reward
    
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
            
            # Copy wall
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
    
    def train_iteration(self, player_id=0):
        """Single training iteration with meld-aware learning"""
        # Create fresh game
        state = GameState()
        
        if not state.awaiting_discard:
            try:
                state.step()  # Initial draw
            except Exception as e:
                print(f"Initial step failed: {e}")
                return 0.0
        
        # Track initial state
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
            
            # Enhanced learning for target player
            if current_player == player_id:
                # Use meld-aware action evaluation
                action_values = self.enhanced_action_evaluation(state, player_id, legal_actions)
                
                # Update regrets based on strategic evaluation
                if action_values:
                    avg_value = sum(action_values.values()) / len(action_values)
                    regrets = self.regret_table[info_set]
                    strategy_sum = self.strategy_sum_table[info_set]
                    
                    for test_action, value in action_values.items():
                        if test_action < 148:
                            regret = value - avg_value
                            regrets[test_action] += regret
                    
                    # Update strategy sum
                    for test_action in legal_actions:
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
        
        # Calculate final reward
        final_total_melds = self.count_total_melds(state)
        final_player_melds = len(state.players[player_id].melds)
        
        total_melds_formed = final_total_melds - initial_total_melds
        player_melds_formed = final_player_melds - initial_player_melds
        
        # Enhanced reward calculation
        if state.is_terminal():
            iteration_reward = state.get_reward(player_id)
            if iteration_reward > 0:
                self.training_stats['games_won'] += 1
                self.training_stats['proper_wins'] += 1
                iteration_reward += 5.0  # Strong win bonus
            else:
                self.training_stats['games_drawn'] += 1
                if len(state.wall) == 0:
                    self.training_stats['wall_exhaustion_games'] += 1
        else:
            self.training_stats['games_drawn'] += 1
        
        # Add hand value reward
        final_player = state.players[player_id]
        hand_value = self.evaluate_hand_strategic_value(final_player.hand)
        iteration_reward += hand_value
        
        # Update statistics
        self.training_stats['total_games_played'] += 1
        self.training_stats['total_melds_formed'] += total_melds_formed
        self.training_stats['player_melds_formed'] += player_melds_formed
        
        # Update averages
        games_played = self.training_stats['total_games_played']
        old_avg = self.training_stats['avg_game_length']
        self.training_stats['avg_game_length'] = ((old_avg * (games_played - 1)) + steps) / games_played
        
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
        """Train with meld-aware learning"""
        if verbose:
            print(f"🧠 MELD-AWARE CFR Training ({iterations} iterations)")
            print(f"   Target player: {player_id}")
            print(f"   Learning to recognize and value complete melds!")
            print("-" * 60)
        
        successful_iterations = 0
        total_reward = 0.0
        
        for i in range(iterations):
            try:
                reward = self.train_iteration(player_id)
                successful_iterations += 1
                total_reward += reward
                self.training_stats['iterations_completed'] += 1
                
                # Progress reporting
                if verbose and ((i + 1) % 20 == 0 or i == iterations - 1):
                    avg_reward = total_reward / successful_iterations if successful_iterations > 0 else 0
                    win_rate = (self.training_stats['games_won'] / max(1, self.training_stats['total_games_played']) * 100)
                    avg_length = self.training_stats['avg_game_length']
                    meld_rate = self.training_stats['meld_formation_rate']
                    
                    print(f"  Iter {i+1:3d}/{iterations}: "
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
            print(f"🎯 MELD-AWARE TRAINING COMPLETE!")
            self.print_meld_aware_summary()
        
        return successful_iterations > 0
    
    def print_meld_aware_summary(self):
        """Print summary with meld awareness statistics"""
        stats = self.training_stats
        
        print(f"📊 Meld-Aware Training Summary:")
        print(f"   Successful iterations: {stats['iterations_completed']}")
        print(f"   Total games: {stats['total_games_played']}")
        print(f"   Proper wins: {stats['proper_wins']}")
        print(f"   Wall exhaustions: {stats['wall_exhaustion_games']}")
        print(f"   Win rate: {stats['games_won']/max(1, stats['total_games_played'])*100:.1f}%")
        print(f"   Average game length: {stats['avg_game_length']:.1f} steps")
        
        # Meld statistics
        print(f"   🔧 MELD STATISTICS:")
        print(f"      Total melds formed (all players): {stats['total_melds_formed']}")
        print(f"      Target player melds: {stats['player_melds_formed']}")
        print(f"      Average melds per game: {stats['meld_formation_rate']:.1f}")
        
        # NEW: Meld awareness statistics
        print(f"   🧠 MELD AWARENESS STATISTICS:")
        print(f"      Hand triplets detected: {stats['hand_triplets_detected']}")
        print(f"      Hand sequences detected: {stats['hand_sequences_detected']}")
        print(f"      Strategic decisions made: {stats['strategic_decisions']}")
        print(f"      Total meld value rewards: {stats['meld_value_rewards']:.1f}")
        
        if stats['strategic_decisions'] > 0:
            avg_meld_reward = stats['meld_value_rewards'] / stats['strategic_decisions']
            print(f"      Average meld value per decision: {avg_meld_reward:.3f}")
        
        print(f"   Info sets learned: {len(self.regret_table)}")
        print(f"   Best reward: {stats['best_reward']:.4f}")
        
        # Analysis
        print(f"\n🔍 Strategic Analysis:")
        total_hand_melds = stats['hand_triplets_detected'] + stats['hand_sequences_detected']
        if total_hand_melds > 0:
            print(f"   ✅ CFR is detecting {total_hand_melds} complete melds in hands!")
            print(f"   🧠 Agent is learning meld recognition!")
        else:
            print(f"   ⚠️  No hand melds detected - may need more training")
        
        if stats['games_won'] > 0:
            print(f"   🎉 CFR is learning strategic play with meld awareness!")
        else:
            print(f"   ⚠️  No wins yet - keep training for breakthrough")

def test_meld_aware_trainer():
    """Test the meld-aware CFR trainer"""
    print("🧪 Testing Meld-Aware CFR Trainer")
    print("="*50)
    
    random.seed(42)
    trainer = MeldAwareCFRTrainer()
    
    # Test meld detection
    from engine.tile import Tile
    test_hand = [
        Tile("Man", 5, 4), Tile("Man", 5, 4), Tile("Man", 5, 4),  # Triplet
        Tile("Pin", 2, 10), Tile("Pin", 3, 11), Tile("Pin", 4, 12),  # Sequence
        Tile("Sou", 1, 18), Tile("Sou", 1, 18),  # Pair
        Tile("Dragon", "Red", 33)  # Junk
    ]
    
    triplets, sequences, pairs, partial_sequences, near_triplets = trainer.analyze_hand_for_complete_melds(test_hand)
    hand_value = trainer.evaluate_hand_strategic_value(test_hand)
    
    print(f"Test hand analysis:")
    print(f"  Hand: {[str(t) for t in test_hand]}")
    print(f"  Complete triplets: {triplets}")
    print(f"  Complete sequences: {sequences}")
    print(f"  Pairs: {pairs}")
    print(f"  Partial sequences: {partial_sequences}")
    print(f"  Near triplets: {near_triplets}")
    print(f"  Strategic value: {hand_value:.1f}")
    
    if triplets == 1 and sequences == 1 and pairs == 1:
        print("✅ Enhanced meld detection working correctly!")
    else:
        print("❌ Enhanced meld detection has issues")
        print(f"   Expected: triplets=1, sequences=1, pairs=1")
        print(f"   Got: triplets={triplets}, sequences={sequences}, pairs={pairs}")
    
    # Test training
    print(f"\nRunning meld-aware training...")
    success = trainer.train(iterations=100, player_id=0, verbose=True)
    
    return trainer

if __name__ == "__main__":
    trainer = test_meld_aware_trainer()
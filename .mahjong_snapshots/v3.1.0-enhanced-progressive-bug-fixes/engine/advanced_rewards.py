"""
Advanced Reward System for Mahjong AI Learning

This module provides sophisticated reward calculation that gives the AI
rich learning signals throughout the game, not just binary win/loss.

Key principles:
1. Continuous feedback - rewards for good moves, not just final outcomes
2. Strategic depth - rewards for building melds, improving hand shape, efficiency
3. Adaptive scaling - early game vs late game different reward magnitudes
4. Risk/reward balance - calculated risks should be rewarded appropriately
"""

import math
from collections import Counter

class AdvancedRewardCalculator:
    """
    Calculates sophisticated rewards for Mahjong AI training.
    Provides much richer learning signals than binary win/loss.
    """
    
    def __init__(self):
        # Reward scaling factors
        self.WIN_REWARD = 100.0          # Base win reward
        self.MELD_FORMATION = 15.0       # Reward for completing melds
        self.HAND_IMPROVEMENT = 5.0      # Reward for improving hand potential
        self.EFFICIENCY_BONUS = 3.0      # Reward for efficient play
        self.STRATEGIC_ACTION = 2.0      # Reward for strategic meld claims
        self.DISCARD_SAFETY = 1.0        # Reward for safe discards
        
        # Penalty factors
        self.DANGEROUS_DISCARD = -8.0    # Penalty for feeding opponents
        self.INEFFICIENT_PLAY = -2.0     # Penalty for wasteful moves
        self.MISSED_OPPORTUNITY = -5.0   # Penalty for missing good melds
        
        # Game phase multipliers
        self.EARLY_GAME_MULTIPLIER = 0.5   # Turns 1-50
        self.MID_GAME_MULTIPLIER = 1.0     # Turns 51-120
        self.LATE_GAME_MULTIPLIER = 1.5    # Turns 121+
    
    def calculate_comprehensive_reward(self, game_state, player_id, action, prev_game_state=None):
        """
        Calculate comprehensive reward for a player's action.
        This is the main reward function that should replace the broken binary system.
        """
        total_reward = 0.0
        player = game_state.players[player_id]
        
        # 1. Terminal rewards (winning/losing)
        if game_state.is_terminal():
            total_reward += self._calculate_terminal_reward(game_state, player_id)
        
        # 2. Hand improvement rewards
        if prev_game_state is not None:
            total_reward += self._calculate_hand_improvement_reward(
                prev_game_state.players[player_id], player
            )
        
        # 3. Meld formation rewards
        total_reward += self._calculate_meld_reward(game_state, player_id, action)
        
        # 4. Strategic action rewards
        total_reward += self._calculate_strategic_reward(game_state, player_id, action)
        
        # 5. Efficiency and safety rewards
        total_reward += self._calculate_efficiency_reward(game_state, player_id, action)
        
        # 6. Apply game phase multiplier
        game_phase_multiplier = self._get_game_phase_multiplier(game_state)
        total_reward *= game_phase_multiplier
        
        # 7. Add exploration bonus for diverse actions
        total_reward += self._calculate_exploration_bonus(action)
        
        return total_reward
    
    def _calculate_terminal_reward(self, game_state, player_id):
        """Calculate rewards for game completion."""
        reward = 0.0
        
        if hasattr(game_state, 'winners') and game_state.winners:
            if player_id in game_state.winners:
                # Winning bonus scaled by hand value
                hand_score = game_state.get_hand_score(game_state.players[player_id])
                reward += self.WIN_REWARD + (hand_score * 5.0)
            else:
                # Small consolation for completing the game without winning
                reward += -5.0
        else:
            # Draw game - reward based on final hand quality
            hand_quality = self._evaluate_hand_quality(game_state.players[player_id])
            reward += hand_quality * 2.0  # Scaled reward for good hands even in draws
        
        return reward
    
    def _calculate_hand_improvement_reward(self, prev_player, current_player):
        """Reward improvements in hand potential and efficiency."""
        reward = 0.0
        
        # Compare hand metrics before and after
        prev_metrics = self._get_hand_metrics(prev_player.hand)
        current_metrics = self._get_hand_metrics(current_player.hand)
        
        # Reward improvements in key metrics
        improvements = {
            'sequences': current_metrics['sequence_potential'] - prev_metrics['sequence_potential'],
            'triplets': current_metrics['triplet_potential'] - prev_metrics['triplet_potential'],
            'pairs': current_metrics['pairs'] - prev_metrics['pairs'],
            'efficiency': current_metrics['efficiency'] - prev_metrics['efficiency']
        }
        
        for metric, improvement in improvements.items():
            if improvement > 0:
                reward += improvement * self.HAND_IMPROVEMENT
            elif improvement < 0:
                reward += improvement * self.INEFFICIENT_PLAY * 0.5  # Smaller penalty
        
        return reward
    
    def _calculate_meld_reward(self, game_state, player_id, action):
        """Reward meld formation and strategic meld decisions."""
        reward = 0.0
        player = game_state.players[player_id]
        
        # Check if action resulted in new meld formation
        if hasattr(player, 'melds'):
            num_melds = len(player.melds)
            
            # Reward for each meld type
            for meld_type, meld_tiles in player.melds:
                if meld_type == "PON":
                    reward += self.MELD_FORMATION * 0.8  # PON slightly less valuable
                elif meld_type == "CHI":
                    reward += self.MELD_FORMATION * 1.0  # CHI good for sequences
                elif meld_type == "KAN":
                    reward += self.MELD_FORMATION * 1.2  # KAN most valuable
            
            # Bonus for having multiple melds (getting closer to win)
            if num_melds >= 2:
                reward += num_melds * 3.0
            if num_melds >= 3:
                reward += 10.0  # Strong bonus for 3+ melds
        
        return reward
    
    def _calculate_strategic_reward(self, game_state, player_id, action):
        """Reward strategic decisions beyond basic meld formation."""
        reward = 0.0
        
        # Reward strategic action types
        if action == 84:  # PASS action
            # Passing can be strategic - don't always penalize
            if self._is_strategic_pass(game_state, player_id):
                reward += self.STRATEGIC_ACTION * 0.5
            else:
                reward += self.INEFFICIENT_PLAY
                
        elif action >= 68 and action < 84:  # CHI actions
            reward += self.STRATEGIC_ACTION * 1.2  # CHI is strategic
            
        elif action >= 34 and action < 68:  # PON actions
            reward += self.STRATEGIC_ACTION * 1.0
            
        elif action >= 106:  # KAN actions
            reward += self.STRATEGIC_ACTION * 1.5  # KAN very strategic
        
        # Reward based on timing of strategic actions
        if game_state.step_counter > 100:  # Late game strategic actions more valuable
            reward *= 1.3
        
        return reward
    
    def _calculate_efficiency_reward(self, game_state, player_id, action):
        """Reward efficient and safe play."""
        reward = 0.0
        player = game_state.players[player_id]
        
        # Reward discard safety (not feeding opponents dangerous tiles)
        if action < 34:  # Discard action
            safety_score = self._evaluate_discard_safety(game_state, player_id, action)
            reward += safety_score * self.DISCARD_SAFETY
        
        # Reward hand efficiency improvements
        hand_efficiency = self._evaluate_hand_efficiency(player.hand)
        reward += hand_efficiency * self.EFFICIENCY_BONUS
        
        # Penalize holding too many isolated tiles late in game
        if game_state.step_counter > 80:
            isolated_tiles = self._count_isolated_tiles(player.hand)
            if isolated_tiles > 5:
                reward += self.INEFFICIENT_PLAY * (isolated_tiles - 5)
        
        return reward
    
    def _get_game_phase_multiplier(self, game_state):
        """Get multiplier based on game phase."""
        step_count = getattr(game_state, 'step_counter', 0)
        
        if step_count <= 50:
            return self.EARLY_GAME_MULTIPLIER
        elif step_count <= 120:
            return self.MID_GAME_MULTIPLIER
        else:
            return self.LATE_GAME_MULTIPLIER
    
    def _calculate_exploration_bonus(self, action):
        """Small bonus for action diversity to encourage exploration."""
        # Give small bonuses for different action types
        if action >= 106:  # KAN actions
            return 0.5
        elif action >= 68:  # CHI actions
            return 0.3
        elif action >= 34:  # PON actions
            return 0.2
        else:  # Discard actions
            return 0.1
    
    def _get_hand_metrics(self, hand_tiles):
        """Extract detailed hand metrics for comparison."""
        metrics = {
            'sequence_potential': 0,
            'triplet_potential': 0,
            'pairs': 0,
            'efficiency': 0
        }
        
        if not hand_tiles:
            return metrics
        
        # Count tile frequencies
        tile_counts = Counter(t.tile_id for t in hand_tiles)
        
        # Count pairs and triplets
        for tile_id, count in tile_counts.items():
            if count >= 2:
                metrics['pairs'] += 1
            if count >= 3:
                metrics['triplet_potential'] += 1
        
        # Count sequence potential (simplified)
        for tile in hand_tiles:
            if tile.category in ["Man", "Pin", "Sou"]:
                # Check for adjacent tiles in hand
                adjacent_count = 0
                for other_tile in hand_tiles:
                    if (other_tile.category == tile.category and 
                        abs(other_tile.value - tile.value) == 1):
                        adjacent_count += 1
                
                if adjacent_count >= 1:
                    metrics['sequence_potential'] += 0.5
        
        # Calculate overall efficiency (fewer isolated tiles = higher efficiency)
        total_tiles = len(hand_tiles)
        connected_tiles = metrics['pairs'] * 2 + metrics['sequence_potential']
        metrics['efficiency'] = connected_tiles / max(total_tiles, 1)
        
        return metrics
    
    def _evaluate_hand_quality(self, player):
        """Evaluate overall hand quality for draw scenarios."""
        if not hasattr(player, 'hand') or not player.hand:
            return 0.0
        
        metrics = self._get_hand_metrics(player.hand)
        melds_count = len(getattr(player, 'melds', []))
        
        # Quality score based on multiple factors
        quality = (
            metrics['sequence_potential'] * 2.0 +
            metrics['triplet_potential'] * 2.5 +
            metrics['pairs'] * 1.5 +
            metrics['efficiency'] * 3.0 +
            melds_count * 4.0
        )
        
        return min(quality, 20.0)  # Cap at reasonable value
    
    def _is_strategic_pass(self, game_state, player_id):
        """Determine if a PASS action was strategic."""
        # Pass is strategic if:
        # 1. Last discard would complete opponent's likely winning hand
        # 2. Player is close to winning and wants to avoid risky claims
        # 3. Player is waiting for specific tiles
        
        player = game_state.players[player_id]
        
        # Simple heuristic: pass is strategic if player has 2+ melds
        if hasattr(player, 'melds') and len(player.melds) >= 2:
            return True
        
        # Pass is strategic if player has many pairs (close to win)
        metrics = self._get_hand_metrics(player.hand)
        if metrics['pairs'] >= 3:
            return True
        
        return False
    
    def _evaluate_discard_safety(self, game_state, player_id, tile_id):
        """Evaluate how safe a discard is (doesn't feed opponents)."""
        # Simplified safety evaluation
        # In a full implementation, this would analyze:
        # - What tiles opponents have discarded
        # - What tiles opponents might be waiting for
        # - Whether this tile completes common hand patterns
        
        # For now, simple heuristic based on tile type
        if tile_id in range(27, 34):  # Honor tiles
            return 0.5  # Generally safer
        elif tile_id in [0, 8, 9, 17, 18, 26]:  # Terminal tiles
            return 0.3  # Moderately safe
        else:  # Middle tiles
            return 0.1  # Less safe
    
    def _evaluate_hand_efficiency(self, hand_tiles):
        """Evaluate how efficiently the hand is structured."""
        if not hand_tiles:
            return 0.0
        
        metrics = self._get_hand_metrics(hand_tiles)
        
        # Efficiency based on connected tiles vs isolated tiles
        efficiency = metrics['efficiency'] * 2.0
        
        # Bonus for suit concentration
        suit_counts = Counter(t.category for t in hand_tiles 
                            if t.category in ["Man", "Pin", "Sou"])
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit_count >= 7:  # Concentrated in one suit
            efficiency += 1.0
        
        return efficiency
    
    def _count_isolated_tiles(self, hand_tiles):
        """Count tiles that don't contribute to melds or sequences."""
        if not hand_tiles:
            return 0
        
        tile_counts = Counter(t.tile_id for t in hand_tiles)
        isolated = 0
        
        for tile_id, count in tile_counts.items():
            if count == 1:  # Single tiles are potentially isolated
                # Check if it's part of a potential sequence
                # Simplified check for now
                isolated += 1
        
        return isolated

# Global instance for easy access
reward_calculator = AdvancedRewardCalculator()

def get_advanced_reward(game_state, player_id, action, prev_game_state=None):
    """
    Main function to get advanced rewards for any game situation.
    This should replace the broken binary get_reward() function.
    """
    return reward_calculator.calculate_comprehensive_reward(
        game_state, player_id, action, prev_game_state
    )

def get_terminal_reward(game_state, player_id):
    """
    Get terminal reward that provides value even for draws.
    Much better than binary win/loss.
    """
    if game_state.is_terminal():
        return reward_calculator._calculate_terminal_reward(game_state, player_id)
    return 0.0

def get_hand_quality_score(player):
    """Get hand quality score for any player state."""
    return reward_calculator._evaluate_hand_quality(player)

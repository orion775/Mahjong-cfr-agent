"""
Balanced Reward System for Mahjong AI Learning

The advanced reward system caused unintended behavior - the AI learned to 
prolong games indefinitely rather than pursue wins. This balanced version
addresses the reward hacking by strongly incentivizing actual wins while
still providing learning signals during play.

Key fixes:
1. Massive win bonuses that dwarf prolonging strategies
2. Penalties for excessively long games
3. Risk-taking rewards for pursuing tenpai (ready hands)
4. Progressive urgency bonuses as wall depletes
"""

import math
from collections import Counter

class BalancedRewardCalculator:
    """
    Balanced reward system that prevents defensive reward hacking
    while still providing rich learning signals.
    """
    
    def __init__(self):
        # WINNING IS EVERYTHING - massive rewards
        self.WIN_REWARD_BASE = 1000.0        # Huge win bonus
        self.WIN_SCALING = 500.0             # Additional per special hand
        
        # Learning signals (much smaller than win rewards)
        self.MELD_FORMATION = 10.0           # Reward for melds
        self.HAND_IMPROVEMENT = 3.0          # Small improvement bonus
        self.TENPAI_BONUS = 50.0             # Bonus for ready hands
        self.EFFICIENCY_BONUS = 2.0          # Efficiency rewards
        
        # ANTI-DEFENSIVE penalties
        self.LONG_GAME_PENALTY = -5.0        # Penalty for dragging games
        self.PASS_PENALTY = -8.0             # Strong penalty for excessive passing  
        self.RISK_AVOIDANCE_PENALTY = -15.0  # Penalty for avoiding good opportunities
        
        # Game urgency (as wall depletes)
        self.URGENCY_MULTIPLIER = 2.0        # Multiply rewards as wall gets low
        self.WALL_DEPLETION_THRESHOLD = 30   # When urgency kicks in
    
    def calculate_balanced_reward(self, game_state, player_id, action, prev_game_state=None):
        """
        Calculate balanced reward that strongly favors winning while providing
        learning signals and preventing defensive reward hacking.
        """
        total_reward = 0.0
        player = game_state.players[player_id]
        
        # 1. TERMINAL REWARDS - Winning is everything!
        if game_state.is_terminal():
            total_reward += self._calculate_win_focused_terminal_reward(game_state, player_id)
        
        # 2. Tenpai (ready hand) detection and rewards
        total_reward += self._calculate_tenpai_rewards(game_state, player_id)
        
        # 3. Meld formation (moderate rewards)
        total_reward += self._calculate_strategic_meld_reward(game_state, player_id, action)
        
        # 4. Anti-defensive penalties
        total_reward += self._calculate_anti_defensive_penalties(game_state, player_id, action)
        
        # 5. Game urgency scaling
        urgency_multiplier = self._get_urgency_multiplier(game_state)
        if urgency_multiplier > 1.0:
            total_reward *= urgency_multiplier
        
        # 6. Long game penalties
        total_reward += self._calculate_long_game_penalties(game_state)
        
        return total_reward
    
    def _calculate_win_focused_terminal_reward(self, game_state, player_id):
        """Calculate terminal rewards heavily focused on actual wins."""
        reward = 0.0
        
        if hasattr(game_state, 'winners') and game_state.winners:
            if player_id in game_state.winners:
                # MASSIVE win reward that dwarfs all other strategies
                base_win = self.WIN_REWARD_BASE
                
                # Scale by hand value
                hand_score = game_state.get_hand_score(game_state.players[player_id])
                scaled_reward = base_win + (hand_score * self.WIN_SCALING)
                
                reward += scaled_reward
                print(f"[REWARD] Player {player_id} WINS! Reward: {scaled_reward}")
            else:
                # Small loss penalty
                reward += -50.0
        else:
            # Draw penalty - discourage prolonging games to draws
            hand_quality = self._evaluate_hand_quality(game_state.players[player_id])
            
            # Wall exhaustion is penalized more than step limit
            if not game_state.wall:
                reward += -100.0 + (hand_quality * 2.0)  # Wall exhaustion penalty
            else:
                reward += -20.0 + (hand_quality * 1.0)   # Step limit penalty
            
            print(f"[REWARD] Player {player_id} draws. Penalty applied.")
        
        return reward
    
    def _calculate_tenpai_rewards(self, game_state, player_id):
        """Reward for being in tenpai (ready to win)."""
        player = game_state.players[player_id]
        reward = 0.0
        
        # Check if player is in tenpai (one tile away from winning)
        if self._is_tenpai(player):
            # Strong bonus for being ready to win
            reward += self.TENPAI_BONUS
            
            # Additional bonus if wall is getting low (urgency)
            if len(game_state.wall) < self.WALL_DEPLETION_THRESHOLD:
                reward += self.TENPAI_BONUS * 2.0
            
            print(f"[REWARD] Player {player_id} in TENPAI! Bonus: {reward}")
        
        return reward
    
    def _calculate_strategic_meld_reward(self, game_state, player_id, action):
        """Moderate rewards for meld formation - much less than wins."""
        reward = 0.0
        player = game_state.players[player_id]
        
        # Reward meld actions
        if action >= 34 and action < 84:  # PON actions
            reward += self.MELD_FORMATION * 0.8
        elif action >= 68 and action < 84:  # CHI actions  
            reward += self.MELD_FORMATION * 1.0
        elif action >= 106:  # KAN actions
            reward += self.MELD_FORMATION * 1.5
        
        # Small bonus for having melds (building toward win)
        num_melds = len(getattr(player, 'melds', []))
        if num_melds >= 3:
            reward += 20.0  # Getting close to 4 melds
        elif num_melds >= 2:
            reward += 10.0
        
        return reward
    
    def _calculate_anti_defensive_penalties(self, game_state, player_id, action):
        """Penalties designed to prevent defensive reward hacking."""
        penalty = 0.0
        
        # Heavy penalty for excessive passing
        if action == 84:  # PASS action
            penalty += self.PASS_PENALTY
            
            # Escalating penalty if wall is getting low
            if len(game_state.wall) < 50:
                penalty += self.PASS_PENALTY  # Double penalty when urgent
        
        # Penalty for avoiding good meld opportunities
        legal_actions = game_state.get_legal_actions()
        meld_actions = [a for a in legal_actions if a >= 34]  # All non-discard actions
        
        if len(meld_actions) > 1 and action < 34:  # Had meld options but discarded
            # Small penalty for missing opportunities
            penalty += self.RISK_AVOIDANCE_PENALTY * 0.2
        
        return penalty
    
    def _get_urgency_multiplier(self, game_state):
        """Get urgency multiplier based on remaining wall tiles."""
        remaining_tiles = len(game_state.wall)
        
        if remaining_tiles <= 20:
            return 3.0  # High urgency
        elif remaining_tiles <= 40:
            return 2.0  # Medium urgency
        elif remaining_tiles <= 60:
            return 1.5  # Low urgency
        else:
            return 1.0  # No urgency
    
    def _calculate_long_game_penalties(self, game_state):
        """Penalty for excessively long games."""
        step_count = getattr(game_state, 'step_counter', 0)
        
        if step_count > 150:
            return self.LONG_GAME_PENALTY * (step_count - 150) * 0.1
        
        return 0.0
    
    def _is_tenpai(self, player):
        """Check if player is in tenpai (one tile away from winning)."""
        # Simplified tenpai detection
        hand = player.hand
        melds = getattr(player, 'melds', [])
        
        # Need 4 melds + pair, or special hands
        num_melds = len(melds)
        
        if num_melds == 4:
            # Just need a pair
            return len(hand) == 2 and hand[0].tile_id == hand[1].tile_id
        elif num_melds == 3:
            # Need one more meld + pair (5 tiles)
            if len(hand) == 5:
                return self._can_form_final_meld_and_pair(hand)
        
        # TODO: Add more sophisticated tenpai detection for special hands
        return False
    
    def _can_form_final_meld_and_pair(self, tiles):
        """Check if tiles can form exactly one meld and one pair."""
        if len(tiles) != 5:
            return False
        
        from collections import Counter
        counts = Counter(t.tile_id for t in tiles)
        
        # Try each possible pair
        for tile_id, count in counts.items():
            if count >= 2:
                # Remove pair, check if remaining 3 tiles form meld
                remaining_tiles = []
                pair_removed = 0
                for t in tiles:
                    if t.tile_id == tile_id and pair_removed < 2:
                        pair_removed += 1
                        continue
                    remaining_tiles.append(t)
                
                if len(remaining_tiles) == 3:
                    if self._is_valid_meld(remaining_tiles):
                        return True
        
        return False
    
    def _is_valid_meld(self, tiles):
        """Check if 3 tiles form a valid meld."""
        if len(tiles) != 3:
            return False
        
        # Check triplet
        if all(t.tile_id == tiles[0].tile_id for t in tiles):
            return True
        
        # Check sequence (must be same suit and consecutive)
        if all(t.category in ["Man", "Pin", "Sou"] for t in tiles):
            if all(t.category == tiles[0].category for t in tiles):
                values = sorted([t.value for t in tiles])
                return values == [values[0], values[0] + 1, values[0] + 2]
        
        return False
    
    def _evaluate_hand_quality(self, player):
        """Evaluate hand quality for draw scenarios."""
        if not hasattr(player, 'hand') or not player.hand:
            return 0.0
        
        hand = player.hand
        melds = getattr(player, 'melds', [])
        
        # Quality based on melds and potential
        quality = len(melds) * 3.0
        
        # Add potential for remaining tiles
        if hand:
            tile_counts = Counter(t.tile_id for t in hand)
            pairs = sum(1 for count in tile_counts.values() if count >= 2)
            quality += pairs * 1.5
        
        return min(quality, 15.0)

# Global instance
balanced_calculator = BalancedRewardCalculator()

def get_balanced_reward(game_state, player_id, action, prev_game_state=None):
    """
    Main function to get balanced rewards that prevent reward hacking.
    This should replace the advanced reward system that caused defensive play.
    """
    return balanced_calculator.calculate_balanced_reward(
        game_state, player_id, action, prev_game_state
    )

def get_balanced_terminal_reward(game_state, player_id):
    """Get terminal reward focused on actual wins."""
    if game_state.is_terminal():
        return balanced_calculator._calculate_win_focused_terminal_reward(game_state, player_id)
    return 0.0

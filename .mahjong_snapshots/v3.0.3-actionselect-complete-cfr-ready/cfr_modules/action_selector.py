# cfr_modules/action_selector.py

"""
ActionSelector Module for Mahjong CFR Agent

This module combines HandEvaluator and GameStateEvaluator outputs to make informed
decisions about actions (discards, claims, melds). Provides utility scores for CFR
learning without hardcoding strategies.

Design Principles:
- Combine HandEvaluator + GameStateEvaluator outputs intelligently
- Translate analysis into actionable recommendations with utility scores
- Use only observable information, let CFR learn strategic meaning
- Support modular CFR architecture: HandEvaluator + GameStateEvaluator → ActionSelector → CFR

Architecture Integration:
HandEvaluator (hand metrics) + GameStateEvaluator (state metrics) → ActionSelector (decisions) → CFR Trainer

Current Implementation Status:
- evaluate_discard_options(): ✅ Implemented (first function)
- Additional functions: Planned for incremental development

Version: v3.0.3+ ActionSelector Foundation
"""

from cfr_modules.hand_evaluator import HandEvaluator
from cfr_modules.game_state_evaluator import (
    count_dead_tiles, count_available_tiles, estimate_meld_completion_risk,
    analyze_discard_patterns
)


def evaluate_discard_options(hand, available_actions, game_state):
    """
    Evaluate all possible discard options using combined hand and game state analysis.
    
    This function integrates HandEvaluator metrics with GameStateEvaluator metrics
    to score each possible discard. Returns utility scores for CFR learning without
    hardcoding which discards are "good" - the agent learns through experience.
    
    Args:
        hand (list): List of Tile objects in player's hand
        available_actions (list): List of action dictionaries with "type": "discard" 
                                and "tile": Tile object
        game_state (dict): Dictionary containing:
            - "discards": dict with seat -> list of discarded Tiles
            - "visible_melds": dict with seat -> list of meld dictionaries
            - "current_seat": string indicating current player seat
            
    Returns:
        dict: Dictionary mapping action_index -> utility_score
              Higher scores indicate potentially better discards for CFR learning
              
    Example:
        hand = [Tile("Man", 1, 0), Tile("Man", 2, 1), ...]
        actions = [{"type": "discard", "tile": Tile("Man", 1, 0)}, ...]
        game_state = {"discards": {...}, "visible_melds": {...}, "current_seat": "East"}
        
        Returns: {0: 0.75, 1: 0.82, 2: 0.45, ...}  # Utility scores for each action
    """
    # Input validation
    if not isinstance(hand, list):
        raise TypeError("hand must be a list of Tile objects")
    if not isinstance(available_actions, list):
        raise TypeError("available_actions must be a list of action dictionaries")
    if not isinstance(game_state, dict):
        raise TypeError("game_state must be a dictionary")
    
    # Validate required game_state keys
    required_keys = ["discards", "visible_melds", "current_seat"]
    for key in required_keys:
        if key not in game_state:
            raise KeyError(f"game_state missing required key: {key}")
    
    # Filter to only discard actions
    discard_actions = [
        (i, action) for i, action in enumerate(available_actions)
        if action.get("type") == "discard" and "tile" in action
    ]
    
    if not discard_actions:
        return {}
    
    # Initialize HandEvaluator for hand analysis
    hand_evaluator = HandEvaluator()
    
    # Get baseline hand metrics
    baseline_triplet_potential = hand_evaluator.count_triplet_potential(hand)
    baseline_sequence_potential = hand_evaluator.count_sequence_potential(hand)
    baseline_isolated_tiles = hand_evaluator.count_isolated_tiles(hand)
    
    utility_scores = {}
    
    for action_index, action in discard_actions:
        discard_tile = action["tile"]
        
        # Create hypothetical hand after discard
        remaining_hand = [tile for tile in hand if tile != discard_tile]
        
        # Calculate hand metrics after discard
        new_triplet_potential = hand_evaluator.count_triplet_potential(remaining_hand)
        new_sequence_potential = hand_evaluator.count_sequence_potential(remaining_hand)
        new_isolated_tiles = hand_evaluator.count_isolated_tiles(remaining_hand)
        
        # Calculate hand improvement metrics (change from baseline)
        triplet_change = new_triplet_potential - baseline_triplet_potential
        sequence_change = new_sequence_potential - baseline_sequence_potential
        isolation_change = new_isolated_tiles - baseline_isolated_tiles
        
        # Game state analysis for the discard tile
        tile_id = getattr(discard_tile, 'tile_id', 0)
        dead_count = count_dead_tiles(tile_id, game_state["discards"])
        
        # Convert visible_melds from dict format to list format expected by count_available_tiles
        all_visible_melds = []
        for seat_melds in game_state["visible_melds"].values():
            all_visible_melds.extend(seat_melds)
        
        available_count = count_available_tiles(
            tile_id, game_state["discards"], all_visible_melds
        )
        
        # Calculate normalized safety score (more dead tiles = safer to discard)
        max_copies = 4  # Standard Mahjong has 4 copies of each tile
        safety_score = dead_count / max_copies if max_copies > 0 else 0.0
        
        # Calculate availability score (fewer available = safer to discard)
        availability_score = 1.0 - (available_count / max_copies) if max_copies > 0 else 0.0
        
        # Combine metrics into utility score
        # Positive factors: safety, availability, reducing isolation
        # Negative factors: losing potential (sequences/triplets)
        utility_score = (
            0.3 * safety_score +           # 30% weight on safety
            0.2 * availability_score +     # 20% weight on availability  
            0.2 * (-isolation_change) +    # 20% weight on reducing isolation
            0.15 * triplet_change +        # 15% weight on triplet potential change
            0.15 * sequence_change         # 15% weight on sequence potential change
        )
        
        # Ensure score is in reasonable range [0.0, 1.0]
        utility_score = max(0.0, min(1.0, utility_score + 0.5))  # Shift to positive range
        
        utility_scores[action_index] = utility_score
    
    return utility_scores


def select_optimal_discard(hand, game_state_metrics):
    """
    Select the single best discard option from available actions using combined analysis.
    
    This function takes the utility scores from evaluate_discard_options and selects
    the optimal action for CFR learning. Handles tie-breaking and provides the
    final decision recommendation.
    
    Args:
        hand (list): List of Tile objects in player's hand
        game_state_metrics (dict): Game state containing:
            - "discards": dict with seat -> list of discarded Tiles
            - "visible_melds": dict with seat -> list of meld dictionaries  
            - "current_seat": string indicating current player seat
            - "available_actions": list of action dictionaries
            
    Returns:
        dict: Single optimal action dictionary or None if no valid discards
              Format: {"type": "discard", "tile": Tile object, "utility_score": float}
              
    Example:
        hand = [Tile("Man", 1, 0), Tile("Man", 2, 1), ...]
        game_state_metrics = {
            "discards": {...}, 
            "visible_melds": {...}, 
            "current_seat": "East",
            "available_actions": [{"type": "discard", "tile": Tile("Man", 1, 0)}, ...]
        }
        
        Returns: {"type": "discard", "tile": Tile("Man", 1, 0), "utility_score": 0.85}
    """
    # Input validation
    if not isinstance(hand, list):
        raise TypeError("hand must be a list of Tile objects")
    if not isinstance(game_state_metrics, dict):
        raise TypeError("game_state_metrics must be a dictionary")
    
    # Validate required keys
    required_keys = ["discards", "visible_melds", "current_seat", "available_actions"]
    for key in required_keys:
        if key not in game_state_metrics:
            raise KeyError(f"game_state_metrics missing required key: {key}")
    
    # Get utility scores for all discard options
    available_actions = game_state_metrics["available_actions"]
    utility_scores = evaluate_discard_options(hand, available_actions, game_state_metrics)
    
    if not utility_scores:
        return None  # No valid discard actions available
    
    # Find action with highest utility score
    best_action_index = max(utility_scores.keys(), key=lambda k: utility_scores[k])
    best_utility = utility_scores[best_action_index]
    best_action = available_actions[best_action_index].copy()
    
    # Add utility score to the action for CFR learning
    best_action["utility_score"] = best_utility
    
    return best_action


def assess_meld_opportunity(meld_action, game_state):
    """
    Assess the value of a meld opportunity (CHI/PON/KAN) using combined analysis.
    
    This function evaluates whether claiming a meld is beneficial by analyzing
    hand improvement, game state factors, and strategic considerations for
    Chinese Mahjong rules (CHI from any player, KAN replacement draws).
    
    Args:
        meld_action (dict): Meld action dictionary containing:
            - "type": "chi", "pon", or "kan"
            - "tiles": list of tile IDs involved in the meld
            - "claimed_tile": tile being claimed from discard (if applicable)
        game_state (dict): Game state containing:
            - "current_hand": list of current player's Tile objects
            - "discards": dict with seat -> list of discarded Tiles
            - "visible_melds": dict with seat -> list of meld dictionaries
            - "current_seat": string indicating current player seat
            - "last_discard": Tile object that was just discarded (or None)
            
    Returns:
        dict: Assessment dictionary containing:
            - "utility_score": float 0.0-1.0 indicating meld value
            - "hand_improvement": float change in hand evaluation metrics
            - "strategic_value": float based on game state considerations
            - "risk_factors": dict with various risk assessments
            
    Example:
        meld_action = {"type": "chi", "tiles": [10, 11, 12], "claimed_tile": 11}
        game_state = {"current_hand": [...], "discards": {...}, ...}
        
        Returns: {
            "utility_score": 0.72,
            "hand_improvement": 0.15,
            "strategic_value": 0.8,
            "risk_factors": {"exposure": 0.3, "efficiency": 0.9}
        }
    """
    # Input validation
    if not isinstance(meld_action, dict):
        raise TypeError("meld_action must be a dictionary")
    if not isinstance(game_state, dict):
        raise TypeError("game_state must be a dictionary")
    
    # Validate meld_action structure
    required_meld_keys = ["type", "tiles"]
    for key in required_meld_keys:
        if key not in meld_action:
            raise KeyError(f"meld_action missing required key: {key}")
    
    # Validate game_state structure  
    required_state_keys = ["current_hand", "discards", "visible_melds", "current_seat"]
    for key in required_state_keys:
        if key not in game_state:
            raise KeyError(f"game_state missing required key: {key}")
    
    meld_type = meld_action["type"].lower()
    if meld_type not in ["chi", "pon", "kan"]:
        raise ValueError("meld_action type must be 'chi', 'pon', or 'kan'")
    
    current_hand = game_state["current_hand"]
    hand_evaluator = HandEvaluator()
    
    # Calculate baseline hand metrics
    baseline_triplets = hand_evaluator.count_triplet_potential(current_hand)
    baseline_sequences = hand_evaluator.count_sequence_potential(current_hand)
    baseline_pairs = hand_evaluator.count_pairs(current_hand)
    baseline_isolated = hand_evaluator.count_isolated_tiles(current_hand)
    
    # Simulate hand after meld
    # Remove tiles used in meld from hand simulation
    meld_tile_ids = set(meld_action["tiles"])
    claimed_tile = meld_action.get("claimed_tile")
    
    simulated_hand = []
    tiles_to_remove = meld_tile_ids.copy()
    
    # Remove meld tiles from hand (except claimed tile from discard)
    for tile in current_hand:
        tile_id = getattr(tile, 'tile_id', 0)
        if tile_id in tiles_to_remove and tile_id != claimed_tile:
            tiles_to_remove.remove(tile_id)
        else:
            simulated_hand.append(tile)
    
    # Calculate post-meld hand metrics
    new_triplets = hand_evaluator.count_triplet_potential(simulated_hand)
    new_sequences = hand_evaluator.count_sequence_potential(simulated_hand)
    new_pairs = hand_evaluator.count_pairs(simulated_hand)
    new_isolated = hand_evaluator.count_isolated_tiles(simulated_hand)
    
    # Calculate improvements
    triplet_improvement = new_triplets - baseline_triplets
    sequence_improvement = new_sequences - baseline_sequences  
    pair_improvement = new_pairs - baseline_pairs
    isolation_improvement = baseline_isolated - new_isolated  # Positive = better
    
    # Hand improvement score (0.0 to 1.0)
    hand_improvement = (
        0.3 * max(0, triplet_improvement) +
        0.3 * max(0, sequence_improvement) + 
        0.2 * max(0, pair_improvement) +
        0.2 * max(0, isolation_improvement)
    ) / 2.0  # Normalize to reasonable range
    
    # Strategic value based on meld type and game state
    strategic_value = 0.5  # Base value
    
    # CHI strategic considerations
    if meld_type == "chi":
        # CHI improves hand structure but exposes information
        strategic_value += 0.2  # Sequence formation bonus
        if len(simulated_hand) <= 7:  # Getting close to winning
            strategic_value += 0.1
    
    # PON strategic considerations  
    elif meld_type == "pon":
        # PON is generally stronger than CHI
        strategic_value += 0.3  # Triplet bonus
        if claimed_tile and hasattr(game_state.get("last_discard"), 'category'):
            last_discard = game_state["last_discard"]
            if last_discard.category in ["Wind", "Dragon"]:  # Honor PON
                strategic_value += 0.1  # Honor tiles more valuable
    
    # KAN strategic considerations
    elif meld_type == "kan":
        # KAN provides replacement tile draw (Chinese rules)
        strategic_value += 0.4  # Strong bonus for replacement draw
        strategic_value += 0.1  # Additional tile access
    
    # Risk factors assessment
    risk_factors = {
        "exposure": 0.3,  # Base exposure risk from revealing meld
        "efficiency": min(1.0, max(0.0, 0.5 + hand_improvement))  # Hand efficiency
    }
    
    # Adjust for hand size - more risk if hand is large
    hand_size = len(current_hand)
    if hand_size > 10:
        risk_factors["exposure"] += 0.2
    elif hand_size < 8:
        risk_factors["exposure"] -= 0.1
    
    # Calculate final utility score
    utility_score = (
        0.4 * hand_improvement +
        0.4 * strategic_value +
        0.2 * (1.0 - risk_factors["exposure"])  # Lower exposure = higher utility
    )
    
    # Ensure score is in valid range
    utility_score = max(0.0, min(1.0, utility_score))
    
    return {
        "utility_score": utility_score,
        "hand_improvement": hand_improvement,
        "strategic_value": strategic_value,
        "risk_factors": risk_factors
    }


def combine_hand_and_state_analysis(hand_metrics, state_metrics):
    """
    Combine HandEvaluator and GameStateEvaluator outputs into unified analysis.
    
    This function merges hand analysis (triplet potential, sequences, etc.) with
    game state analysis (dead tiles, opponent patterns, etc.) to create comprehensive
    decision support data for CFR learning.
    
    Args:
        hand_metrics (dict): HandEvaluator output containing:
            - "triplet_potential": int count of near-triplets
            - "sequence_potential": int count of near-sequences  
            - "pairs_count": int count of pairs
            - "complete_melds": int count of formed melds
            - "isolated_tiles": int count of disconnected tiles
        state_metrics (dict): GameStateEvaluator output containing:
            - "opponent_patterns": dict with pattern analysis
            - "tile_safety": dict with safety scores by tile_id
            - "availability_scores": dict with availability by tile_id
            - "risk_assessments": dict with meld completion risks
            
    Returns:
        dict: Combined analysis containing:
            - "hand_strength": float 0.0-1.0 overall hand evaluation
            - "positional_advantage": float 0.0-1.0 based on game state
            - "decision_priorities": dict with weighted decision factors
            - "combined_score": float 0.0-1.0 unified evaluation
            
    Example:
        hand_metrics = {
            "triplet_potential": 2, "sequence_potential": 3, 
            "pairs_count": 1, "complete_melds": 1, "isolated_tiles": 2
        }
        state_metrics = {
            "opponent_patterns": {"recent_focus": "Man"}, 
            "tile_safety": {0: 0.8, 1: 0.6}, ...
        }
        
        Returns: {
            "hand_strength": 0.65,
            "positional_advantage": 0.72, 
            "decision_priorities": {"safety": 0.4, "efficiency": 0.6},
            "combined_score": 0.68
        }
    """
    # Input validation
    if not isinstance(hand_metrics, dict):
        raise TypeError("hand_metrics must be a dictionary")
    if not isinstance(state_metrics, dict):
        raise TypeError("state_metrics must be a dictionary")
    
    # Validate hand_metrics structure
    required_hand_keys = ["triplet_potential", "sequence_potential", "pairs_count", 
                          "complete_melds", "isolated_tiles"]
    for key in required_hand_keys:
        if key not in hand_metrics:
            raise KeyError(f"hand_metrics missing required key: {key}")
    
    # Validate state_metrics structure (flexible - use what's available)
    if not any(key in state_metrics for key in ["opponent_patterns", "tile_safety", 
                                               "availability_scores", "risk_assessments"]):
        raise KeyError("state_metrics must contain at least one analysis component")
    
    # Calculate hand strength (0.0 to 1.0)
    # Weight different hand components based on their strategic value
    triplet_score = min(1.0, hand_metrics["triplet_potential"] / 4.0)  # Up to 4 triplets
    sequence_score = min(1.0, hand_metrics["sequence_potential"] / 4.0)  # Up to 4 sequences
    pairs_score = min(1.0, hand_metrics["pairs_count"] / 7.0)  # Seven pairs maximum
    meld_score = min(1.0, hand_metrics["complete_melds"] / 4.0)  # Up to 4 melds
    isolation_penalty = min(1.0, hand_metrics["isolated_tiles"] / 13.0)  # Penalty for isolation
    
    hand_strength = (
        0.25 * meld_score +        # 25% - completed melds most important
        0.20 * triplet_score +     # 20% - triplet potential 
        0.20 * sequence_score +    # 20% - sequence potential
        0.15 * pairs_score +       # 15% - pair formation
        0.20 * (1.0 - isolation_penalty)  # 20% - penalty for isolated tiles
    )
    
    # Calculate positional advantage based on game state
    positional_advantage = 0.5  # Base neutral position
    
    # Opponent pattern advantages
    if "opponent_patterns" in state_metrics:
        patterns = state_metrics["opponent_patterns"]
        if isinstance(patterns, dict):
            # Advantage if opponents are focused on different suits
            focus_diversity = patterns.get("recent_focus", "None")
            if focus_diversity in ["Mixed", "None"]:
                positional_advantage += 0.1
            elif focus_diversity in ["Man", "Pin", "Sou"]:
                positional_advantage += 0.05  # Some predictability advantage
    
    # Tile safety advantages
    if "tile_safety" in state_metrics:
        safety_scores = state_metrics["tile_safety"]
        if isinstance(safety_scores, dict) and safety_scores:
            avg_safety = sum(safety_scores.values()) / len(safety_scores)
            positional_advantage += 0.2 * (avg_safety - 0.5)  # +/- based on avg safety
    
    # Availability advantages
    if "availability_scores" in state_metrics:
        availability = state_metrics["availability_scores"] 
        if isinstance(availability, dict) and availability:
            avg_availability = sum(availability.values()) / len(availability)
            positional_advantage += 0.2 * avg_availability  # More available = better
    
    # Ensure positional advantage stays in valid range
    positional_advantage = max(0.0, min(1.0, positional_advantage))
    
    # Determine decision priorities based on hand and state
    decision_priorities = {}
    
    # Safety vs Efficiency trade-off
    if hand_strength < 0.4:  # Weak hand - prioritize safety
        decision_priorities["safety"] = 0.7
        decision_priorities["efficiency"] = 0.3
    elif hand_strength > 0.7:  # Strong hand - prioritize efficiency  
        decision_priorities["safety"] = 0.3
        decision_priorities["efficiency"] = 0.7
    else:  # Balanced hand - balanced priorities
        decision_priorities["safety"] = 0.5
        decision_priorities["efficiency"] = 0.5
    
    # Aggression vs Defense based on position
    if positional_advantage > 0.6:  # Good position - more aggressive
        decision_priorities["aggression"] = 0.6
        decision_priorities["defense"] = 0.4
    else:  # Poor position - more defensive
        decision_priorities["aggression"] = 0.4
        decision_priorities["defense"] = 0.6
    
    # Calculate combined score
    combined_score = (
        0.6 * hand_strength +          # 60% weight on hand quality
        0.4 * positional_advantage     # 40% weight on positional factors
    )
    
    return {
        "hand_strength": hand_strength,
        "positional_advantage": positional_advantage,
        "decision_priorities": decision_priorities,
        "combined_score": combined_score
    }


def generate_action_recommendations(combined_analysis):
    """
    Generate ranked action recommendations based on combined hand and state analysis.
    
    This function takes unified analysis data and produces a prioritized list of
    action types and strategic recommendations for CFR decision making. Provides
    high-level guidance without hardcoding specific actions.
    
    Args:
        combined_analysis (dict): Output from combine_hand_and_state_analysis containing:
            - "hand_strength": float 0.0-1.0 overall hand evaluation
            - "positional_advantage": float 0.0-1.0 based on game state
            - "decision_priorities": dict with weighted decision factors
            - "combined_score": float 0.0-1.0 unified evaluation
            
    Returns:
        dict: Action recommendations containing:
            - "primary_strategy": string indicating main strategic approach
            - "action_rankings": list of action types ordered by priority
            - "risk_tolerance": float 0.0-1.0 indicating acceptable risk level
            - "meld_preferences": dict with CHI/PON/KAN preference weights
            - "discard_guidance": dict with safety vs efficiency preferences
            
    Example:
        combined_analysis = {
            "hand_strength": 0.65, "positional_advantage": 0.72,
            "decision_priorities": {"safety": 0.4, "efficiency": 0.6, ...},
            "combined_score": 0.68
        }
        
        Returns: {
            "primary_strategy": "balanced_aggressive",
            "action_rankings": ["meld", "efficient_discard", "safe_discard"],
            "risk_tolerance": 0.7,
            "meld_preferences": {"chi": 0.3, "pon": 0.4, "kan": 0.3},
            "discard_guidance": {"safety_weight": 0.4, "efficiency_weight": 0.6}
        }
    """
    # Input validation
    if not isinstance(combined_analysis, dict):
        raise TypeError("combined_analysis must be a dictionary")
    
    # Validate required keys
    required_keys = ["hand_strength", "positional_advantage", "decision_priorities", "combined_score"]
    for key in required_keys:
        if key not in combined_analysis:
            raise KeyError(f"combined_analysis missing required key: {key}")
    
    hand_strength = combined_analysis["hand_strength"]
    positional_advantage = combined_analysis["positional_advantage"]
    priorities = combined_analysis["decision_priorities"]
    combined_score = combined_analysis["combined_score"]
    
    # Determine primary strategy based on combined metrics
    if combined_score >= 0.75:
        primary_strategy = "aggressive_push"
    elif combined_score >= 0.6 and positional_advantage >= 0.6:
        primary_strategy = "balanced_aggressive"
    elif combined_score >= 0.4:
        primary_strategy = "balanced_conservative"
    elif positional_advantage >= 0.6:
        primary_strategy = "opportunistic"
    else:
        primary_strategy = "defensive"
    
    # Generate action rankings based on strategy and priorities
    action_rankings = []
    
    # Strong hands prioritize meld completion
    if hand_strength >= 0.6:
        action_rankings.extend(["meld", "efficient_discard", "safe_discard"])
    # Weak hands prioritize safety
    elif hand_strength <= 0.4:
        action_rankings.extend(["safe_discard", "defensive_meld", "pass"])
    # Balanced hands use priorities
    else:
        if priorities.get("efficiency", 0.5) > priorities.get("safety", 0.5):
            action_rankings.extend(["efficient_discard", "meld", "safe_discard"])
        else:
            action_rankings.extend(["safe_discard", "meld", "efficient_discard"])
    
    # Add aggressive actions for good position
    if positional_advantage >= 0.7:
        action_rankings.insert(0, "aggressive_meld")
    
    # Add defensive actions for poor position  
    if positional_advantage <= 0.3:
        action_rankings.append("pass")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_rankings = []
    for action in action_rankings:
        if action not in seen:
            unique_rankings.append(action)
            seen.add(action)
    action_rankings = unique_rankings
    
    # Calculate risk tolerance
    base_risk = combined_score * 0.5  # Base on overall performance
    position_risk = positional_advantage * 0.3  # Position adjustment
    aggression_risk = priorities.get("aggression", 0.5) * 0.2  # Aggression bonus
    risk_tolerance = base_risk + position_risk + aggression_risk
    risk_tolerance = max(0.0, min(1.0, risk_tolerance))  # Clamp to valid range
    
    # Determine meld preferences based on hand and position
    meld_preferences = {"chi": 0.33, "pon": 0.34, "kan": 0.33}  # Base equal
    
    # Adjust based on hand strength and strategy
    if primary_strategy in ["aggressive_push", "balanced_aggressive"]:
        meld_preferences["kan"] += 0.1  # KAN gives replacement tile
        meld_preferences["pon"] += 0.05  # PON more powerful
        meld_preferences["chi"] -= 0.15
    elif primary_strategy == "defensive":
        meld_preferences["chi"] += 0.1  # CHI less exposing
        meld_preferences["pon"] -= 0.05
        meld_preferences["kan"] -= 0.05
    
    # Normalize meld preferences
    total_meld = sum(meld_preferences.values())
    if total_meld > 0:
        meld_preferences = {k: v/total_meld for k, v in meld_preferences.items()}
    
    # Generate discard guidance
    safety_weight = priorities.get("safety", 0.5)
    efficiency_weight = priorities.get("efficiency", 0.5)
    
    discard_guidance = {
        "safety_weight": safety_weight,
        "efficiency_weight": efficiency_weight,
        "prefer_honors": primary_strategy == "defensive",
        "prefer_terminals": hand_strength < 0.4,  # Weak hands avoid middle tiles
        "prefer_isolated": True  # Generally good to discard isolated tiles
    }
    
    return {
        "primary_strategy": primary_strategy,
        "action_rankings": action_rankings,
        "risk_tolerance": risk_tolerance,
        "meld_preferences": meld_preferences,
        "discard_guidance": discard_guidance
    }


def calculate_action_utilities(actions, hand_eval, state_eval):
    """
    Calculate utility scores for all available actions using combined evaluator outputs.
    
    This function serves as the main CFR integration point, taking raw evaluator outputs
    and converting them into utility scores that CFR can use for regret minimization
    learning. Handles all action types: discards, CHI, PON, KAN.
    
    Args:
        actions (list): List of action dictionaries, each containing:
            - "type": "discard", "chi", "pon", "kan", or "pass"
            - "tile": Tile object (for discards) or "tiles": list (for melds)
            - Additional action-specific data
        hand_eval (dict): HandEvaluator metrics containing:
            - "triplet_potential", "sequence_potential", "pairs_count", etc.
        state_eval (dict): GameStateEvaluator metrics containing:
            - "opponent_patterns", "tile_safety", "availability_scores", etc.
            
    Returns:
        list: Utility scores corresponding to each action (same order as input)
              Scores are floats scaled for CFR learning (typically 0.0-100.0)
              
    Example:
        actions = [
            {"type": "discard", "tile": Tile("Man", 1, 0)},
            {"type": "chi", "tiles": [1, 2, 3]},
            {"type": "pass"}
        ]
        hand_eval = {"triplet_potential": 2, "sequence_potential": 3, ...}
        state_eval = {"tile_safety": {0: 0.8, 1: 0.6}, ...}
        
        Returns: [45.2, 67.8, 30.0]  # Utility scores for CFR
    """
    # Input validation
    if not isinstance(actions, list):
        raise TypeError("actions must be a list of action dictionaries")
    if not isinstance(hand_eval, dict):
        raise TypeError("hand_eval must be a dictionary")
    if not isinstance(state_eval, dict):
        raise TypeError("state_eval must be a dictionary")
    
    if not actions:
        return []  # Empty actions list returns empty utilities
    
    # Combine hand and state analysis
    try:
        combined_analysis = combine_hand_and_state_analysis(hand_eval, state_eval)
        recommendations = generate_action_recommendations(combined_analysis)
    except (KeyError, ValueError) as e:
        # If analysis fails, use conservative fallback
        combined_analysis = {
            "hand_strength": 0.5, "positional_advantage": 0.5,
            "decision_priorities": {"safety": 0.6, "efficiency": 0.4},
            "combined_score": 0.5
        }
        recommendations = {
            "primary_strategy": "balanced_conservative",
            "risk_tolerance": 0.4,
            "meld_preferences": {"chi": 0.4, "pon": 0.3, "kan": 0.3},
            "discard_guidance": {"safety_weight": 0.6, "efficiency_weight": 0.4}
        }
    
    utility_scores = []
    base_utility = 50.0  # CFR base score (0-100 scale)
    
    for action in actions:
        action_type = action.get("type", "unknown").lower()
        utility = base_utility  # Start with base
        
        # Handle different action types
        if action_type == "discard":
            # Use existing discard evaluation logic
            if "tile" in action:
                # Create simplified game state for discard evaluation
                simplified_state = {
                    "discards": state_eval.get("all_discards", {"East": [], "South": [], "West": [], "North": []}),
                    "visible_melds": {"East": [], "South": [], "West": [], "North": []},
                    "current_seat": "East"
                }
                
                # Get current hand from hand_eval context (fallback if not available)
                current_hand = hand_eval.get("current_hand", [action["tile"]])
                
                try:
                    discard_scores = evaluate_discard_options(current_hand, [action], simplified_state)
                    if 0 in discard_scores:
                        utility = discard_scores[0] * 100.0  # Scale 0.0-1.0 to 0.0-100.0
                        # Ensure minimum utility for CFR learning
                        utility = max(20.0, utility)
                except Exception:
                    # Fallback: use safety preference
                    safety_weight = recommendations["discard_guidance"]["safety_weight"]
                    utility = base_utility + (safety_weight - 0.5) * 20.0
        
        elif action_type in ["chi", "pon", "kan"]:
            # Use meld assessment logic
            try:
                # Create simplified game state for meld assessment
                simplified_state = {
                    "current_hand": hand_eval.get("current_hand", []),
                    "discards": state_eval.get("all_discards", {"East": [], "South": [], "West": [], "North": []}),
                    "visible_melds": {"East": [], "South": [], "West": [], "North": []},
                    "current_seat": "East"
                }
                
                meld_assessment = assess_meld_opportunity(action, simplified_state)
                utility = meld_assessment["utility_score"] * 100.0
                
                # Apply meld preferences from recommendations
                meld_bonus = recommendations["meld_preferences"].get(action_type, 0.33) * 10.0
                utility += meld_bonus
                
                # Ensure minimum utility for melds
                utility = max(30.0, utility)
                
            except Exception:
                # Fallback: use meld preferences and risk tolerance
                meld_preference = recommendations["meld_preferences"].get(action_type, 0.33)
                risk_tolerance = recommendations["risk_tolerance"]
                utility = base_utility + (meld_preference * 30.0) + (risk_tolerance * 20.0)
        
        elif action_type == "pass":
            # PASS utility based on strategy and risk tolerance
            if recommendations["primary_strategy"] == "defensive":
                utility = base_utility + 10.0  # Defensive strategy values PASS
            elif recommendations["risk_tolerance"] < 0.4:
                utility = base_utility + 5.0   # Low risk tolerance slightly favors PASS
            else:
                utility = base_utility - 10.0  # Aggressive strategies penalize PASS
            
            # Ensure PASS has minimum utility
            utility = max(15.0, utility)
        
        else:
            # Unknown action type - use neutral utility with minimum
            utility = max(25.0, base_utility)
        
        # Apply strategic modifiers based on recommendations
        strategy = recommendations["primary_strategy"]
        
        # Strategy-based adjustments
        if strategy == "aggressive_push" and action_type in ["chi", "pon", "kan"]:
            utility += 15.0  # Aggressive strategy bonus for melds
        elif strategy == "defensive" and action_type == "discard":
            utility += 10.0  # Defensive strategy bonus for safe discards
        elif strategy == "balanced_aggressive" and action_type != "pass":
            utility += 5.0   # Small bonus for active actions
        
        # Risk tolerance adjustments
        risk_tolerance = recommendations["risk_tolerance"]
        if action_type in ["chi", "pon", "kan"]:
            utility += (risk_tolerance - 0.5) * 20.0  # Higher risk tolerance = higher meld utility
        
        # Ensure utility is in reasonable range for CFR with meaningful minimum
        utility = max(15.0, min(100.0, utility))  # Changed minimum from 0.0 to 15.0
        utility_scores.append(utility)
    
    return utility_scores
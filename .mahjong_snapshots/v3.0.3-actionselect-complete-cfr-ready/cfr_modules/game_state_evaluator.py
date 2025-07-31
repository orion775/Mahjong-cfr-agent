# cfr_modules/game_state_evaluator.py

"""
GameStateEvaluator Module for Mahjong CFR Agent

This module analyzes visible game state information to provide probabilistic 
intelligence for CFR decision making. Functions calculate metrics from observable 
data (discards, visible melds, seat positions) without making assumptions about 
hidden information.

Design Principles:
- Only use visible information (no hidden state guessing)
- Return numerical metrics, let CFR learn strategic meaning
- Calculate probabilities from observable data
- Support modular CFR architecture development

Architecture: GameStateEvaluator (visible analysis) + HandEvaluator (hand analysis) 
             → ActionSelector (decisions) → CFR Trainer

Current Implementation Status:
- count_dead_tiles(): ✅ Implemented
- Additional functions: Planned for incremental development

Version: v3.0.1+ GameStateEvaluator Foundation
"""

def count_dead_tiles(tile_type, discards):
    """
    Count how many copies of a specific tile type have been discarded.
    
    This function analyzes all visible discards to determine how many copies
    of a tile type are no longer available for claiming or forming melds.
    
    Args:
        tile_type (int): Tile ID (0-41 for standard + bonus tiles)
        discards (dict): Dictionary mapping seat names to lists of discarded tiles
                        Format: {"East": [tile_obj1, tile_obj2], "South": [...], ...}
    
    Returns:
        int: Number of copies of tile_type that have been discarded (0-4)
             Maximum is 4 since each tile type has exactly 4 copies in the wall
    
    Example:
        >>> discards = {
        ...     "East": [Tile("Man", 1, 0), Tile("Pin", 5, 13)],
        ...     "South": [Tile("Man", 1, 0), Tile("Dragon", "Red", 31)],
        ...     "West": [Tile("Man", 1, 0)],
        ...     "North": []
        ... }
        >>> count_dead_tiles(0, discards)  # Man 1 has tile_id=0
        3
    
    Design Notes:
        - Only counts visible discards, not tiles in hands or concealed melds
        - Provides foundation for probability calculations in other functions
        - Used by action selector to assess tile availability for meld formation
        - Critical for opponent modeling and risk assessment
    """
    if not isinstance(discards, dict):
        raise TypeError("discards must be a dictionary mapping seats to tile lists")
    
    if not isinstance(tile_type, int) or tile_type < 0 or tile_type > 41:
        raise ValueError("tile_type must be an integer between 0-41 (inclusive)")
    
    dead_count = 0
    
    # Iterate through all seats' discard piles
    for seat, discard_pile in discards.items():
        if not isinstance(discard_pile, list):
            raise TypeError(f"Discard pile for seat {seat} must be a list")
        
        # Count tiles in this seat's discards
        for tile in discard_pile:
            if hasattr(tile, 'tile_id') and tile.tile_id == tile_type:
                dead_count += 1
    
    # Sanity check: each tile type has exactly 4 copies maximum
    if dead_count > 4:
        # This shouldn't happen in a valid game, but return 4 as maximum
        return 4
    
    return dead_count

def count_available_tiles(tile_type, discards, visible_melds):
    """
    Count how many copies of a specific tile type are still available in play.
    
    This function calculates remaining tile availability by subtracting discarded
    and visible meld tiles from the total supply of 4 copies per tile type.
    
    Args:
        tile_type (int): Tile ID (0-41 for standard + bonus tiles)
        discards (dict): Dictionary mapping seat names to lists of discarded tiles
                        Format: {"East": [tile_obj1, tile_obj2], "South": [...], ...}
        visible_melds (list): List of all visible melds across all players
                             Each meld contains tiles that are no longer available
    
    Returns:
        int: Number of copies of tile_type still available (0-4)
             Calculated as: 4 - (discarded_count + visible_meld_count)
    
    Example:
        >>> discards = {"East": [Tile("Man", 1, 0)], "South": [], "West": [], "North": []}
        >>> visible_melds = [[Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0)]]
        >>> count_available_tiles(0, discards, visible_melds)  # Man 1
        0  # 4 total - 1 discarded - 3 in visible meld = 0 available
    
    Design Notes:
        - Accounts for both discarded tiles and tiles locked in visible melds
        - Provides foundation for meld formation probability calculations
        - Used by opponent modeling to assess tile scarcity
        - Critical for risk assessment when deciding which tiles to discard
    """
    if not isinstance(discards, dict):
        raise TypeError("discards must be a dictionary mapping seats to tile lists")
    
    if not isinstance(tile_type, int) or tile_type < 0 or tile_type > 41:
        raise ValueError("tile_type must be an integer between 0-41 (inclusive)")
    
    if not isinstance(visible_melds, list):
        raise TypeError("visible_melds must be a list of meld objects")
    
    # Count dead tiles in discards (reuse existing function)
    dead_count = count_dead_tiles(tile_type, discards)
    
    # Count tiles in visible melds
    meld_count = 0
    for meld in visible_melds:
        if not isinstance(meld, list):
            raise TypeError("Each meld in visible_melds must be a list of tiles")
        
        for tile in meld:
            if hasattr(tile, 'tile_id') and tile.tile_id == tile_type:
                meld_count += 1
    
    # Calculate available tiles: 4 total - used tiles
    used_total = dead_count + meld_count
    available = 4 - used_total
    
    # Defensive: ensure non-negative result
    return max(0, available)

def get_left_opponent_discards(current_seat, all_discards):
    """
    Get the discard pile of the player to the current player's left.
    
    In Mahjong, only the player to your left can be interrupted for CHI claims,
    making their discards strategically important for meld formation opportunities.
    
    Args:
        current_seat (str): Current player's seat ("East", "South", "West", "North")
        all_discards (dict): Dictionary mapping all seats to their discard piles
                           Format: {"East": [tiles], "South": [tiles], ...}
    
    Returns:
        list: List of tiles discarded by the left opponent
              Empty list if no discards or invalid seat
    
    Example:
        >>> all_discards = {
        ...     "East": [tile1, tile2],
        ...     "South": [tile3],
        ...     "West": [tile4, tile5, tile6],
        ...     "North": [tile7]
        ... }
        >>> get_left_opponent_discards("South", all_discards)  # South's left is East
        [tile1, tile2]
    
    Design Notes:
        - Seat order: East → South → West → North → East (clockwise)
        - Left opponent is the previous seat in clockwise order
        - Used for CHI opportunity analysis and meld timing decisions
        - Critical for understanding which tiles are immediately claimable
    """
    if not isinstance(current_seat, str):
        raise TypeError("current_seat must be a string")
    
    if not isinstance(all_discards, dict):
        raise TypeError("all_discards must be a dictionary")
    
    # Define seat order (clockwise: East → South → West → North → East)
    seat_order = ["East", "South", "West", "North"]
    
    if current_seat not in seat_order:
        raise ValueError(f"current_seat must be one of {seat_order}")
    
    # Find current seat index
    current_index = seat_order.index(current_seat)
    
    # Left opponent is previous seat in clockwise order (wrap around)
    left_index = (current_index - 1) % 4
    left_seat = seat_order[left_index]
    
    # Return left opponent's discards (empty list if not found)
    return all_discards.get(left_seat, [])

def calculate_tile_likelihood(tile_type, opponent_discards):
    """
    Calculate probability that an opponent still has a specific tile type.
    
    Uses opponent's discard pattern to estimate likelihood they still possess
    copies of the target tile type. Based on principle that discarded tiles
    indicate reduced probability of holding remaining copies.
    
    Args:
        tile_type (int): Tile ID (0-41 for standard + bonus tiles)
        opponent_discards (list): List of tiles discarded by specific opponent
    
    Returns:
        float: Probability between 0.0-1.0 that opponent holds tile_type
               1.0 = high likelihood (no discards of this type)
               0.0 = no likelihood (all copies discarded or max discarded)
    
    Example:
        >>> opponent_discards = [
        ...     Tile("Man", 1, 0),      # Discarded 1 copy of Man 1
        ...     Tile("Pin", 5, 13),
        ...     Tile("Dragon", "Red", 31)
        ... ]
        >>> calculate_tile_likelihood(0, opponent_discards)  # Man 1
        0.75  # 3 remaining out of 4 total = 75% chance they hold one
    
    Design Notes:
        - Simple probability model: (4 - discarded_count) / 4
        - Assumes uniform distribution of remaining tiles
        - Provides foundation for opponent modeling without strategy assumptions
        - Used by risk assessment and meld formation decisions
    """
    if not isinstance(tile_type, int) or tile_type < 0 or tile_type > 41:
        raise ValueError("tile_type must be an integer between 0-41 (inclusive)")
    
    if not isinstance(opponent_discards, list):
        raise TypeError("opponent_discards must be a list of tile objects")
    
    # Count how many of target tile type opponent has discarded
    discarded_count = 0
    for tile in opponent_discards:
        if hasattr(tile, 'tile_id') and tile.tile_id == tile_type:
            discarded_count += 1
    
    # Calculate probability: remaining tiles / total tiles
    # If opponent discarded N copies, they have (4-N) potential remaining
    remaining_possible = max(0, 4 - discarded_count)
    likelihood = remaining_possible / 4.0
    
    return likelihood

def estimate_meld_completion_risk(tile_candidates, opponent_patterns):
    """
    Estimate risk of helping opponents complete melds by discarding tile candidates.
    
    Analyzes opponent discard patterns to assess likelihood that discarding
    each candidate tile would enable opponent meld formation (CHI/PON/KAN).
    
    Args:
        tile_candidates (list): List of tile_ids being considered for discard
        opponent_patterns (dict): Dict mapping opponents to their discard analysis
                                 Format: {"East": {"recent_discards": [tiles], 
                                                  "suit_focus": "Man"}, ...}
    
    Returns:
        dict: Risk scores for each candidate tile_id
              Format: {tile_id: risk_score} where risk_score is 0.0-1.0
              Higher scores indicate greater risk of helping opponents
    
    Design Notes:
        - Analyzes sequential patterns (potential CHI setups)  
        - Considers triplet formation opportunities (PON potential)
        - Weights by opponent position and recent discard behavior
        - Returns numerical risk without strategic interpretation
    """
    if not isinstance(tile_candidates, list):
        raise TypeError("tile_candidates must be a list of tile IDs")
    
    if not isinstance(opponent_patterns, dict):
        raise TypeError("opponent_patterns must be a dictionary")
    
    risk_scores = {}
    
    for tile_id in tile_candidates:
        if not isinstance(tile_id, int) or tile_id < 0 or tile_id > 41:
            raise ValueError(f"Invalid tile_id {tile_id}: must be 0-41")
        
        total_risk = 0.0
        
        # Analyze risk from each opponent
        for opponent, patterns in opponent_patterns.items():
            if not isinstance(patterns, dict):
                continue
                
            recent_discards = patterns.get("recent_discards", [])
            
            # Calculate sequential risk (CHI potential)
            sequential_risk = 0.0
            for tile in recent_discards:
                if hasattr(tile, 'tile_id'):
                    # Check if tile_id forms sequence potential
                    if abs(tile.tile_id - tile_id) <= 2:  # Within CHI range
                        sequential_risk += 0.2
            
            # Calculate triplet risk (PON potential)  
            triplet_risk = 0.0
            matching_discards = sum(1 for tile in recent_discards 
                                  if hasattr(tile, 'tile_id') and tile.tile_id == tile_id)
            triplet_risk = matching_discards * 0.3  # Higher risk for matching tiles
            
            opponent_risk = min(1.0, sequential_risk + triplet_risk)
            total_risk += opponent_risk
        
        # Normalize by number of opponents and cap at 1.0
        risk_scores[tile_id] = min(1.0, total_risk / max(1, len(opponent_patterns)))
    
    return risk_scores

def analyze_discard_patterns(opponent_discards):
    """
    Analyze numerical patterns in opponent's discards without strategic interpretation.
    
    Extracts statistical patterns from discard sequence to support opponent modeling.
    Returns raw numerical data for CFR to learn strategic meaning.
    
    Args:
        opponent_discards (list): List of tiles discarded by specific opponent
    
    Returns:
        dict: Pattern analysis with numerical metrics
              Format: {
                  "total_discards": int,
                  "suit_distribution": {"Man": count, "Pin": count, "Sou": count},
                  "honor_count": int,
                  "terminal_count": int,
                  "recent_focus": str,  # Most common suit in last 3 discards
                  "discard_diversity": float  # 0.0-1.0, higher = more varied
              }
    
    Design Notes:
        - Provides factual analysis without assuming strategy
        - Focuses on observable patterns and distributions
        - Supports probabilistic opponent modeling
        - Raw data for CFR learning without hardcoded interpretations
    """
    if not isinstance(opponent_discards, list):
        raise TypeError("opponent_discards must be a list of tile objects")
    
    if not opponent_discards:
        return {
            "total_discards": 0,
            "suit_distribution": {"Man": 0, "Pin": 0, "Sou": 0},
            "honor_count": 0,
            "terminal_count": 0,
            "recent_focus": "None",
            "discard_diversity": 0.0
        }
    
    # Count suit distributions
    suit_counts = {"Man": 0, "Pin": 0, "Sou": 0}
    honor_count = 0
    terminal_count = 0
    
    for tile in opponent_discards:
        if hasattr(tile, 'category'):
            if tile.category in suit_counts:
                suit_counts[tile.category] += 1
                # Check for terminals (1s and 9s)
                if hasattr(tile, 'value') and tile.value in [1, 9]:
                    terminal_count += 1
            elif tile.category in ["Wind", "Dragon"]:
                honor_count += 1
    
    # Analyze recent focus (last 3 discards)
    recent_suits = []
    for tile in opponent_discards[-3:]:
        if hasattr(tile, 'category') and tile.category in suit_counts:
            recent_suits.append(tile.category)
    
    if recent_suits:
        from collections import Counter
        recent_focus = Counter(recent_suits).most_common(1)[0][0]
    else:
        recent_focus = "None"
    
    # Calculate diversity (Shannon entropy approximation)
    total_suits = sum(suit_counts.values())
    if total_suits > 0:
        diversity = 0.0
        for count in suit_counts.values():
            if count > 0:
                p = count / total_suits
                diversity -= p * (p ** 0.5)  # Simplified diversity measure
        discard_diversity = min(1.0, diversity)
    else:
        discard_diversity = 0.0
    
    return {
        "total_discards": len(opponent_discards),
        "suit_distribution": suit_counts,
        "honor_count": honor_count,
        "terminal_count": terminal_count,
        "recent_focus": recent_focus,
        "discard_diversity": discard_diversity
    }

def count_suit_concentration(opponent_discards):
    """
    Measure opponent's focus on specific suits through discard analysis.
    
    Calculates concentration metrics to identify if opponent is focusing
    on particular suits or playing broadly across all suits.
    
    Args:
        opponent_discards (list): List of tiles discarded by specific opponent
    
    Returns:
        dict: Concentration metrics for each suit
              Format: {
                  "Man": float,     # 0.0-1.0 concentration score
                  "Pin": float,     # Higher = more focused on this suit
                  "Sou": float,
                  "max_concentration": float,  # Highest individual suit score
                  "concentration_suit": str    # Suit with highest concentration
              }
    
    Design Notes:
        - Higher scores indicate opponent keeping/collecting that suit
        - Lower scores suggest opponent discarding that suit freely
        - Provides foundation for suit-based opponent modeling
        - Numerical metrics without strategic assumptions
    """
    if not isinstance(opponent_discards, list):
        raise TypeError("opponent_discards must be a list of tile objects")
    
    # Count discards by suit
    suit_discards = {"Man": 0, "Pin": 0, "Sou": 0}
    total_suit_discards = 0
    
    for tile in opponent_discards:
        if hasattr(tile, 'category') and tile.category in suit_discards:
            suit_discards[tile.category] += 1
            total_suit_discards += 1
    
    if total_suit_discards == 0:
        return {
            "Man": 0.0,
            "Pin": 0.0,
            "Sou": 0.0,
            "max_concentration": 0.0,
            "concentration_suit": "None"
        }
    
    # Calculate concentration scores (inverse of discard rate)
    # More discards = lower concentration (opponent not keeping this suit)
    concentration_scores = {}
    for suit, discard_count in suit_discards.items():
        # Inverse relationship: fewer discards = higher concentration
        if total_suit_discards > 0:
            discard_rate = discard_count / total_suit_discards
            concentration_scores[suit] = max(0.0, 1.0 - discard_rate)
        else:
            concentration_scores[suit] = 0.0
    
    # Find maximum concentration
    max_concentration = max(concentration_scores.values())
    concentration_suit = max(concentration_scores, key=concentration_scores.get) if max_concentration > 0 else "None"
    
    return {
        "Man": concentration_scores["Man"],
        "Pin": concentration_scores["Pin"], 
        "Sou": concentration_scores["Sou"],
        "max_concentration": max_concentration,
        "concentration_suit": concentration_suit
    }
def measure_honor_vs_suited_ratio(opponent_discards):
    """
    Measure the ratio of honor tiles vs suited tiles in opponent's discards.
    
    Analyzes discard composition to understand opponent's tile type preferences.
    Higher honor ratios may indicate focus on suited tile collection.
    
    Args:
        opponent_discards (list): List of tiles discarded by specific opponent
    
    Returns:
        dict: Ratio analysis of discard composition
              Format: {
                  "honor_discards": int,      # Count of Wind/Dragon discards
                  "suited_discards": int,     # Count of Man/Pin/Sou discards  
                  "total_analyzed": int,      # Total tiles analyzed
                  "honor_ratio": float,       # 0.0-1.0, honor/(honor+suited)
                  "suited_ratio": float,      # 0.0-1.0, suited/(honor+suited)
                  "composition": str          # "Honor_Heavy", "Suited_Heavy", "Balanced"
              }
    
    Design Notes:
        - Only analyzes regular tiles (ignores bonus tiles)
        - Provides composition metrics for opponent modeling
        - Numerical ratios without strategic interpretation
        - Foundation for understanding opponent hand development patterns
    """
    if not isinstance(opponent_discards, list):
        raise TypeError("opponent_discards must be a list of tile objects")
    
    honor_count = 0
    suited_count = 0
    
    # Count tiles by category
    for tile in opponent_discards:
        if hasattr(tile, 'category'):
            if tile.category in ["Wind", "Dragon"]:
                honor_count += 1
            elif tile.category in ["Man", "Pin", "Sou"]:
                suited_count += 1
            # Ignore bonus tiles and invalid categories
    
    total_analyzed = honor_count + suited_count
    
    if total_analyzed == 0:
        return {
            "honor_discards": 0,
            "suited_discards": 0,
            "total_analyzed": 0,
            "honor_ratio": 0.0,
            "suited_ratio": 0.0,
            "composition": "No_Data"
        }
    
    # Calculate ratios
    honor_ratio = honor_count / total_analyzed
    suited_ratio = suited_count / total_analyzed
    
    # Determine composition category
    if honor_ratio > 0.6:
        composition = "Honor_Heavy"
    elif suited_ratio > 0.6:
        composition = "Suited_Heavy"
    else:
        composition = "Balanced"
    
    return {
        "honor_discards": honor_count,
        "suited_discards": suited_count,
        "total_analyzed": total_analyzed,
        "honor_ratio": honor_ratio,
        "suited_ratio": suited_ratio,
        "composition": composition
    }
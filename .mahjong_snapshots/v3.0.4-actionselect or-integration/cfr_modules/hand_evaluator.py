# cfr_modules/hand_evaluator.py

"""
HandEvaluator Module for Mahjong CFR Agent

Analyzes hand composition for strategic value without hardcoding specific strategies.
Agent learns through experience which patterns lead to wins.

Design Principles:
- No hardcoded tile values or "good/bad" classifications
- Returns numerical metrics that CFR can learn from
- Focuses on structural patterns (pairs, triplets, sequences)
- All functions are pure (no side effects)
"""

from collections import Counter
from engine.tile import Tile

class HandEvaluator:
    """Evaluates hand composition for strategic decision making."""
    
    def __init__(self):
        pass
    
    def count_triplet_potential(self, hand_tiles):
        """
        Count how many tiles are 2-of-a-kind (close to forming triplets).
        
        This gives CFR a signal about meld-building potential without
        hardcoding which tiles are "good" - the agent learns through experience.
        
        Args:
            hand_tiles (list): List of Tile objects in player's hand
            
        Returns:
            int: Number of different tile types that appear exactly 2 times
            
        Example:
            Hand: [1m, 1m, 2m, 3m, 3m, 4m, 5m, 6m, 7m, 8m, 9m, East, East]
            Returns: 3 (pairs of 1m, 3m, East are close to triplets)
        """
        if not hand_tiles:
            return 0
            
        # Count occurrences of each tile type
        tile_counts = Counter()
        for tile in hand_tiles:
            # Use tile's string representation as key for counting
            tile_key = str(tile)
            tile_counts[tile_key] += 1
        
        # Count how many tile types appear exactly 2 times
        pairs_count = sum(1 for count in tile_counts.values() if count == 2)
        
        return pairs_count
    
    def count_sequence_potential(self, hand_tiles):
        """
        Count how many tiles could potentially form sequences (CHI melds).
        
        Looks for consecutive tiles in the same suit that are close to forming
        sequences. This gives CFR a signal about CHI potential without hardcoding
        which sequences are "good" - the agent learns through experience.
        
        Args:
            hand_tiles (list): List of Tile objects in player's hand
            
        Returns:
            int: Number of tiles that are part of potential sequences
            
        Example:
            Hand: [1m, 2m, 4m, 5m, 7m, 8m, East, Red]
            Potential sequences: (1m,2m need 3m), (4m,5m need 3m or 6m), (7m,8m need 6m or 9m)
            Returns: 6 (all the suited tiles that are in potential sequences)
        """
        if not hand_tiles:
            return 0
        
        # Separate suited tiles by suit
        suited_tiles = {}
        for tile in hand_tiles:
            if tile.category in ["Man", "Pin", "Sou"]:
                suit = tile.category
                if suit not in suited_tiles:
                    suited_tiles[suit] = []
                suited_tiles[suit].append(tile.value)
        
        sequence_potential_count = 0
        
        # For each suit, find tiles that could form sequences
        for suit, values in suited_tiles.items():
            # Sort values and get unique ones with their counts
            value_counts = Counter(values)
            unique_values = sorted(value_counts.keys())
            
            # Check each value to see if it's part of a potential sequence
            for value in unique_values:
                is_part_of_sequence = False
                
                # Check if this value can form a sequence with adjacent values
                # Look for patterns like: (n, n+1), (n-1, n), (n, n+1, n+2), etc.
                for other_value in unique_values:
                    if other_value != value:
                        # Check if they're consecutive (difference of 1 or 2)
                        diff = abs(value - other_value)
                        if diff == 1 or diff == 2:
                            is_part_of_sequence = True
                            break
                
                # If this value is part of potential sequence, count all copies
                if is_part_of_sequence:
                    sequence_potential_count += value_counts[value]
        
        return sequence_potential_count
    
    def count_pairs(self, hand_tiles):
        """
        Count how many different pairs (exactly 2 of same tile) exist in hand.
        
        This is useful for detecting pair-based winning hands like Seven Pairs
        or identifying the pair needed for a standard winning hand. Different
        from triplet_potential as this counts actual pairs, not potential triplets.
        
        Args:
            hand_tiles (list): List of Tile objects in player's hand
            
        Returns:
            int: Number of different tile types that appear exactly 2 times
            
        Example:
            Hand: [1m, 1m, 2m, 3m, 3m, 3m, 4m, 4m, East]
            Pairs: 1m(2), 4m(2) = 2 pairs
            Note: 3m appears 3 times so it's a triplet, not a pair
        """
        if not hand_tiles:
            return 0
            
        # Count occurrences of each tile type
        tile_counts = Counter()
        for tile in hand_tiles:
            tile_key = str(tile)
            tile_counts[tile_key] += 1
        
        # Count tile types that appear exactly 2 times
        pairs_count = sum(1 for count in tile_counts.values() if count == 2)
        
        return pairs_count
    def count_complete_melds(self, hand_tiles):
        """
        Count how many complete melds (triplets and sequences) exist in current hand.
        
        This counts melds that are already formed but not yet called/claimed.
        Helps CFR understand when a hand has strong meld foundation vs scattered tiles.
        
        Args:
            hand_tiles (list): List of Tile objects in player's hand
            
        Returns:
            int: Number of complete melds found in hand
            
        Example:
            Hand: [1m, 1m, 1m, 2p, 3p, 4p, 5s, 6s, East, East, Red]
            Complete melds: 1m triplet + 2p-3p-4p sequence = 2 melds
        """
        if not hand_tiles or len(hand_tiles) < 3:
            return 0
        
        # Count tile occurrences
        tile_counts = Counter()
        for tile in hand_tiles:
            tile_key = str(tile)
            tile_counts[tile_key] += 1
        
        complete_melds = 0
        
        # Count triplets (3 or 4 of same tile)
        for tile_str, count in tile_counts.items():
            if count >= 3:
                complete_melds += count // 3  # Count how many triplets possible
        
        # Count sequences for suited tiles
        suited_tiles = {}
        for tile in hand_tiles:
            if tile.category in ["Man", "Pin", "Sou"]:
                suit = tile.category
                if suit not in suited_tiles:
                    suited_tiles[suit] = []
                suited_tiles[suit].append(tile.value)
        
        # Find sequences in each suit
        for suit, values in suited_tiles.items():
            value_counts = Counter(values)
            unique_values = sorted(value_counts.keys())
            
            # Simple sequence detection: look for consecutive triplets
            i = 0
            while i < len(unique_values) - 2:
                val1, val2, val3 = unique_values[i], unique_values[i+1], unique_values[i+2]
                
                # Check if consecutive (like 1,2,3 or 5,6,7)
                if val2 == val1 + 1 and val3 == val2 + 1:
                    # Check if we have at least one of each value
                    min_count = min(value_counts[val1], value_counts[val2], value_counts[val3])
                    if min_count > 0:
                        complete_melds += min_count
                        # Remove used tiles from counting
                        value_counts[val1] -= min_count
                        value_counts[val2] -= min_count
                        value_counts[val3] -= min_count
                
                i += 1
        
        return complete_melds
    
    def count_isolated_tiles(self, hand_tiles):
        """
        Count how many tiles are isolated (no meld potential with other hand tiles).
        
        An isolated tile has no pairs, triplets, or sequence connections with other
        tiles in the hand. These are often good candidates for discarding.
        
        Args:
            hand_tiles (list): List of Tile objects in player's hand
            
        Returns:
            int: Number of tiles that are completely isolated
            
        Example:
            Hand: [1m, 3m, 5m, 7m, 9m, East, Red]
            All tiles are isolated (no pairs, no consecutive sequences)
            Returns: 7
            
            Hand: [1m, 1m, 2m, 5p, East, Red]  
            1m-1m are paired, 1m-2m have sequence potential
            Only 5p, East, Red are isolated
            Returns: 3
        """
        if not hand_tiles:
            return 0
        
        # Count tile occurrences
        tile_counts = Counter()
        tile_objects = {}  # Store actual tile objects for suit checking
        
        for tile in hand_tiles:
            tile_key = str(tile)
            tile_counts[tile_key] += 1
            tile_objects[tile_key] = tile
        
        isolated_count = 0
        
        for tile_str, count in tile_counts.items():
            tile = tile_objects[tile_str]
            is_isolated = True
            
            # Not isolated if it's a pair or more
            if count >= 2:
                is_isolated = False
            else:
                # Check for sequence potential with other tiles (suited tiles only)
                if tile.category in ["Man", "Pin", "Sou"]:
                    for other_tile_str, other_tile in tile_objects.items():
                        if (other_tile_str != tile_str and 
                            other_tile.category == tile.category):
                            # Check if values are within sequence range (diff of 1 or 2)
                            value_diff = abs(tile.value - other_tile.value)
                            if value_diff <= 2:
                                is_isolated = False
                                break
            
            # If still isolated, count all copies of this tile
            if is_isolated:
                isolated_count += count
        
        return isolated_count
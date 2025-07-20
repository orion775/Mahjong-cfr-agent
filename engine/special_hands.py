# engine/special_hands.py



def _can_form_melds(tiles):
    """Helper function to check if remaining tiles can form valid melds."""
    from collections import Counter
    if not tiles:
        return True
    
    tiles = sorted(tiles, key=lambda t: (t.category, t.value))
    first = tiles[0]
    
    # Try Pong (triplet)
    if sum(1 for t in tiles if t.category == first.category and t.value == first.value) >= 3:
        remaining = []
        removed = 0
        for t in tiles:
            if t.category == first.category and t.value == first.value and removed < 3:
                removed += 1
            else:
                remaining.append(t)
        if _can_form_melds(remaining):
            return True
    
    # Try Chi (sequence, only for suits)
    if first.category in ["Man", "Pin", "Sou"]:
        val2 = first.value + 1
        val3 = first.value + 2
        i2 = i3 = -1
        for i, t in enumerate(tiles[1:], 1):
            if i2 == -1 and t.category == first.category and t.value == val2:
                i2 = i
            elif i3 == -1 and t.category == first.category and t.value == val3:
                i3 = i
        if i2 != -1 and i3 != -1:
            remaining = [t for i, t in enumerate(tiles) if i not in [0, i2, i3]]
            if _can_form_melds(remaining):
                return True
                
    return False
def check_seven_pairs(hand_tiles):
    """
    Check if a 14-tile hand forms Seven Pairs (Qi Dui Zi).
    
    Seven Pairs rules:
    - Exactly 14 tiles
    - Exactly 7 distinct pairs (no triplets or quads allowed)
    - All tiles must be different types (no identical pairs)
    
    Args:
        hand_tiles: List of 14 Tile objects
        
    Returns:
        bool: True if hand is Seven Pairs, False otherwise
    """
    from collections import Counter
    
    if len(hand_tiles) != 14:
        return False
    
    # Count tiles by (category, value)
    counts = Counter((t.category, t.value) for t in hand_tiles)
    
    # Must have exactly 7 pairs (no singles, triplets, or quads)
    if len(counts) != 7:
        return False
    
    # Every tile type must appear exactly twice
    for count in counts.values():
        if count != 2:
            return False
    
    return True

def check_thirteen_orphans(hand_tiles):
    """Check if hand is Thirteen Orphans (Shi San Yao)"""
    from collections import Counter
    
    if len(hand_tiles) != 14:
        return False
    
    # Required 13 terminal/honor types
    required_types = {
        ("Man", 1), ("Man", 9),
        ("Pin", 1), ("Pin", 9), 
        ("Sou", 1), ("Sou", 9),
        ("Wind", "East"), ("Wind", "South"), ("Wind", "West"), ("Wind", "North"),
        ("Dragon", "Red"), ("Dragon", "Green"), ("Dragon", "White")
    }
    
    counts = Counter((t.category, t.value) for t in hand_tiles)
    
    # Must have exactly the 13 required types
    if set(counts.keys()) != required_types:
        return False
    
    # Must have 12 singles and 1 pair
    count_values = list(counts.values())
    if count_values.count(1) != 12 or count_values.count(2) != 1:
        return False
    
    return True

def check_all_honors(hand_tiles):
    """
    Check if hand is All Honors (Zi Yi Se) - only honor tiles (winds + dragons).
    Must follow standard 4 melds + 1 pair structure.
    """
    if len(hand_tiles) != 14:
        return False
    
    # Check that ALL tiles are honor tiles (winds or dragons)
    for tile in hand_tiles:
        if tile.category not in ["Wind", "Dragon"]:
            return False
    
    # Since all tiles are honors, check if they form standard structure (4 melds + 1 pair)
    from collections import Counter
    
    counts = Counter((t.category, t.value) for t in hand_tiles)
    
    # Try every possible pair
    for pair, n in counts.items():
        if n >= 2:
            # Create remaining tiles after removing the pair
            remaining = list(hand_tiles)
            # Remove pair
            removed = 0
            for i in range(len(remaining)-1, -1, -1):
                if (remaining[i].category, remaining[i].value) == pair:
                    del remaining[i]
                    removed += 1
                    if removed == 2:
                        break
            
            # Check if remaining 12 tiles can form 4 triplets
            if _can_form_honor_melds(remaining):
                return True
    
    return False

def _can_form_honor_melds(tiles):
    """
    Helper function to check if honor tiles can form valid melds (only triplets/quads).
    Honor tiles cannot form sequences, only triplets or quads.
    """
    if not tiles:
        return True
    
    if len(tiles) % 3 != 0:
        return False
    
    tiles = sorted(tiles, key=lambda t: (t.category, t.value))
    first = tiles[0]
    
    # Try to form a triplet with the first tile
    matching_count = sum(1 for t in tiles if t.category == first.category and t.value == first.value)
    
    if matching_count >= 3:
        # Remove triplet and check remaining
        remaining = []
        removed = 0
        for t in tiles:
            if t.category == first.category and t.value == first.value and removed < 3:
                removed += 1
            else:
                remaining.append(t)
        
        return _can_form_honor_melds(remaining)
    
    # If we can't form a triplet with the first tile, this configuration is invalid
    return False

def check_all_terminals(hand_tiles):
    """
    Check if hand is All Terminals (Yao Jiu) - only terminal tiles (1s and 9s).
    Must follow standard 4 melds + 1 pair structure.
    """
    if len(hand_tiles) != 14:
        return False
    
    # Check that ALL tiles are terminal tiles (1s or 9s from suits only)
    for tile in hand_tiles:
        if tile.category not in ["Man", "Pin", "Sou"]:
            return False
        if tile.value not in [1, 9]:
            return False
    
    # Since all tiles are terminals, check if they form standard structure (4 melds + 1 pair)
    from collections import Counter
    
    counts = Counter((t.category, t.value) for t in hand_tiles)
    
    # Try every possible pair
    for pair, n in counts.items():
        if n >= 2:
            # Create remaining tiles after removing the pair
            remaining = list(hand_tiles)
            # Remove pair
            removed = 0
            for i in range(len(remaining)-1, -1, -1):
                if (remaining[i].category, remaining[i].value) == pair:
                    del remaining[i]
                    removed += 1
                    if removed == 2:
                        break
            
            # Check if remaining 12 tiles can form 4 melds
            if _can_form_melds(remaining):
                return True
    
    return False
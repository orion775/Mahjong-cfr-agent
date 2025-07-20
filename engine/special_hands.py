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

def check_all_one_suit(hand_tiles):
    """
    Check if hand is All One Suit (Qing Yi Se) - only tiles from one suit.
    
    Args:
        hand_tiles: List of Tile objects (should be 14 tiles)
        
    Returns:
        bool: True if all tiles are from exactly one suit (Man, Pin, or Sou)
        
    Rules:
        - All tiles must be from the same suit (Man, Pin, or Sou only)
        - No honor tiles (Winds, Dragons) allowed
        - Can be any combination of sequences and triplets
        - Must still form valid 4 melds + 1 pair structure
    """
    if len(hand_tiles) != 14:
        return False
    
    # Get all suit categories in the hand
    suits = set(tile.category for tile in hand_tiles)
    
    # Must have exactly one suit, and it must be a numbered suit
    if len(suits) != 1:
        return False
    
    suit = suits.pop()
    if suit not in ["Man", "Pin", "Sou"]:
        return False
    
    # All tiles are from one valid suit
    return True

def check_little_four_winds(hand_tiles):
    """
    Check if hand is Little Four Winds (Xiao Si Xi) - 3 wind triplets + 1 wind pair.
    """
    if len(hand_tiles) != 14:
        return False
    
    from collections import Counter
    
    # Count each wind type
    wind_counts = Counter()
    for tile in hand_tiles:
        if tile.category == "Wind":
            wind_counts[tile.value] += 1
    
    # Must have all 4 wind types
    all_winds = {"East", "South", "West", "North"}
    if set(wind_counts.keys()) != all_winds:
        return False
    
    # Count how many winds have 3+ tiles (triplets) vs 2 tiles (pairs)
    triplet_winds = 0
    pair_winds = 0
    
    for wind, count in wind_counts.items():
        if count >= 3:
            triplet_winds += 1
        elif count == 2:
            pair_winds += 1
        else:
            return False  # Must have at least 2 of each wind
    
    # Little Four Winds: exactly 3 triplets and 1 pair
    return triplet_winds == 3 and pair_winds == 1

def check_big_three_dragons(hand_tiles):
    """
    Check if hand is Big Three Dragons (Da San Yuan) - PON/KAN of all three dragons.
    
    Args:
        hand_tiles: List of Tile objects (should be 14 tiles)
        
    Returns:
        bool: True if hand contains triplets/quads of all three dragon types
        
    Rules:
        - Must have PON (3) or KAN (4) of Red Dragon
        - Must have PON (3) or KAN (4) of Green Dragon  
        - Must have PON (3) or KAN (4) of White Dragon
        - Remaining tiles form one more meld + pair
    """
    if len(hand_tiles) != 14:
        return False
    
    from collections import Counter
    
    # Count each dragon type
    dragon_counts = Counter()
    for tile in hand_tiles:
        if tile.category == "Dragon":
            dragon_counts[tile.value] += 1
    
    # Must have at least 3 of each dragon type
    required_dragons = {"Red", "Green", "White"}
    for dragon in required_dragons:
        if dragon_counts[dragon] < 3:
            return False
    
    # All three dragons have at least 3 tiles each
    return True

def is_big_four_winds(hand):
    """
    Check if hand is Big Four Winds (大四喜):
    Four PON/KAN sets, one for each wind tile (East, South, West, North).
   
    Args:
        hand: List of 14-15 Tile objects (15 for KAN wins)
       
    Returns:
        bool: True if hand is Big Four Winds
    """
    from collections import Counter
   
    # Allow 14 or 15 tiles (15 for wins after KAN replacement)
    if len(hand) not in [14, 15]:
        return False
   
    # Count all tiles
    counts = Counter((t.category, t.value) for t in hand)
   
    # Must have exactly 4 wind triplets/quads
    wind_sets = 0
    winds_found = set()
   
    for (category, value), count in counts.items():
        if category == "Wind":
            if count >= 3:  # Triplet or quad
                wind_sets += 1
                winds_found.add(value)
            elif count == 2:
                # A wind pair - not allowed in Big Four Winds
                return False
            elif count == 1:
                # Single wind tile - not allowed
                return False
   
    # Must have all 4 winds as sets
    required_winds = {"East", "South", "West", "North"}
    if wind_sets != 4 or winds_found != required_winds:
        return False
   
    # Check that remaining tiles form a valid pair
    remaining_tiles = []
    for (category, value), count in counts.items():
        if category == "Wind":
            continue
        else:
            remaining_tiles.extend([(category, value)] * count)
   
    # For both 14-tile and 15-tile hands, remaining tiles should form a valid pair
    if len(remaining_tiles) == 2:
        # Standard pair
        if remaining_tiles[0] != remaining_tiles[1]:
            return False
    elif len(remaining_tiles) == 1:
        # Single tile remaining (valid for some 15-tile KAN scenarios)
        pass
    elif len(remaining_tiles) == 3:
        # Check if 3 tiles form a triplet (15-tile KAN scenario)
        if len(set(remaining_tiles)) != 1:
            return False
    else:
        return False
   
    return True

def check_all_green(hand):
    """
    Check if hand is All Green (绿一色):
    Hand contains only green tiles (2,3,4,6,8 Bamboo and Green Dragon).
    
    Args:
        hand: List of 14-15 Tile objects
        
    Returns:
        bool: True if hand is All Green
    """
    # Allow 14 or 15 tiles (15 for wins after KAN replacement)
    if len(hand) not in [14, 15]:
        return False
    
    # Define green tiles: 2,3,4,6,8 of Bamboo (Sou) + Green Dragon
    green_tiles = {
        ("Sou", 2), ("Sou", 3), ("Sou", 4), ("Sou", 6), ("Sou", 8),
        ("Dragon", "Green")
    }
    
    # Check that ALL tiles in hand are green
    for tile in hand:
        tile_type = (tile.category, tile.value)
        if tile_type not in green_tiles:
            return False
    
    # If we get here, all tiles are green
    return True

def check_nine_gates(hand):
    """
    Check if hand is Nine Gates (九莲宝灯):
    Pure suit hand with pattern 1112345678999 + any tile from same suit.
    
    Args:
        hand: List of 14-15 Tile objects
        
    Returns:
        bool: True if hand is Nine Gates
    """
    from collections import Counter
    
    # Allow 14 or 15 tiles (15 for wins after KAN replacement)
    if len(hand) not in [14, 15]:
        return False
    
    # Check that all tiles are from the same suit (Man, Pin, or Sou only)
    suits = set()
    for tile in hand:
        if tile.category in ["Man", "Pin", "Sou"]:
            suits.add(tile.category)
        else:
            # Honor tiles not allowed in Nine Gates
            return False
    
    # Must be exactly one suit
    if len(suits) != 1:
        return False
    
    suit = suits.pop()
    
    # Count tiles by value within the suit
    value_counts = Counter()
    for tile in hand:
        if tile.category == suit:
            value_counts[tile.value] += 1
    
    # Nine Gates pattern: 1112345678999 + one extra tile
    # This means: 1(3), 2(1), 3(1), 4(1), 5(1), 6(1), 7(1), 8(1), 9(3) + one more
    
    # Check if we have the base pattern (without the extra tile)
    base_pattern = {1: 3, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 3}
    
    # Make a copy to check against
    remaining_counts = dict(value_counts)
    
    # Remove the base pattern
    for value, required_count in base_pattern.items():
        if remaining_counts.get(value, 0) < required_count:
            return False
        remaining_counts[value] -= required_count
    
    # After removing base pattern, should have exactly 1 tile left (the 14th tile)
    total_remaining = sum(remaining_counts.values())
    if total_remaining != 1:
        return False
    
    # The remaining tile must be from values 1-9 in the same suit
    for value, count in remaining_counts.items():
        if count > 0:
            if not (1 <= value <= 9):
                return False
    
    return True
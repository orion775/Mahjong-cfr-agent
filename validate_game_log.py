#!/usr/bin/env python3
"""
Validate the tile counts in the winning game log against proper Chinese Mahjong rules.
"""

import re

def parse_player_state(player_text):
    """Parse a player state from the game log."""
    lines = player_text.strip().split('\n')
    
    # Find hand line
    hand_match = re.search(r'Hand \((\d+)\): \[(.*?)\]', player_text)
    hand_count = int(hand_match.group(1)) if hand_match else 0
    
    # Find melds
    meld_matches = re.findall(r"\('(\w+)', \[(.*?)\]\)", player_text)
    melds = []
    total_meld_tiles = 0
    
    for meld_type, meld_tiles_str in meld_matches:
        # Count tiles in this meld
        tile_count = len([t for t in meld_tiles_str.split("', '") if t.strip("'")])
        if meld_type == "KAN":
            total_meld_tiles += 4
        else:  # PON or CHI
            total_meld_tiles += 3
        melds.append((meld_type, tile_count))
    
    return {
        'hand_count': hand_count,
        'melds': melds,
        'total_meld_tiles': total_meld_tiles,
        'total_tiles': hand_count + total_meld_tiles
    }

def validate_game_log():
    """Validate the winning game log."""
    print("=== Validating Winning Game Log ===\n")
    
    # Read the game log with proper encoding
    with open('winning_game_log_20250803_202327.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the final game state (MOVE 295)
    final_move_match = re.search(r'MOVE 295.*?PLAYER STATES:(.*?)DISCARDS:', content, re.DOTALL)
    if not final_move_match:
        print("Could not find final game state in log")
        return
    
    player_states_text = final_move_match.group(1)
    
    # Find winners
    winners_match = re.search(r'Winners: \[(\d+)\]', content)
    winners = [int(winners_match.group(1))] if winners_match else []
    
    print(f"Winners: {winners}")
    print()
    
    # Parse each player state
    player_patterns = [
        r'Player 0 \(East\):(.*?)Player 1',
        r'Player 1 \(South\):(.*?)Player 2', 
        r'Player 2 \(West\):(.*?)Player 3',
        r'Player 3 \(North\):(.*?)(?=\n\n|\Z)'
    ]
    
    validation_errors = []
    
    for i, pattern in enumerate(player_patterns):
        match = re.search(pattern, player_states_text, re.DOTALL)
        if match:
            player_data = parse_player_state(match.group(1))
            is_winner = i in winners
            
            print(f"Player {i} ({'Winner' if is_winner else 'Non-winner'}):")
            print(f"  Hand: {player_data['hand_count']} tiles")
            print(f"  Melds: {player_data['melds']}")
            print(f"  Total meld tiles: {player_data['total_meld_tiles']}")
            print(f"  Total tiles: {player_data['total_tiles']}")
            
            # Validate according to Chinese Mahjong rules
            expected_tiles = 14 if is_winner else 13
            if is_winner and player_data['total_tiles'] not in [14, 15]:
                validation_errors.append(f"Player {i} (winner) has {player_data['total_tiles']} tiles, should be 14-15")
                print(f"  ❌ ERROR: Winner should have 14-15 tiles")
            elif not is_winner and player_data['total_tiles'] != 13:
                validation_errors.append(f"Player {i} (non-winner) has {player_data['total_tiles']} tiles, should be 13")
                print(f"  ❌ ERROR: Non-winner should have exactly 13 tiles")
            else:
                print(f"  ✅ Tile count correct ({player_data['total_tiles']} tiles)")
            
            # Validate KAN meld tile counts
            for meld_type, actual_count in player_data['melds']:
                expected_count = 4 if meld_type == "KAN" else 3
                if meld_type == "KAN" and actual_count != 4:
                    validation_errors.append(f"Player {i} KAN meld has {actual_count} tiles, should be 4")
                    print(f"  ❌ ERROR: KAN meld should have 4 tiles, not {actual_count}")
            
            print()
    
    # Summary
    print("=== Validation Summary ===")
    if validation_errors:
        print("❌ VALIDATION FAILED!")
        for error in validation_errors:
            print(f"  - {error}")
        print(f"\nTotal errors: {len(validation_errors)}")
    else:
        print("✅ All tile counts are valid according to Chinese Mahjong rules!")
    
    return len(validation_errors) == 0

if __name__ == "__main__":
    validate_game_log()

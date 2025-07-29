import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.tile import Tile
from engine.game_state import GameState
from engine.action_space import encode_chi, decode_chi

def test_chi_detection():
    """Test if CHI detection is working"""
    print("🔍 TESTING CHI DETECTION")
    print("="*30)
    
    state = GameState()
    
    # Clear all hands for controlled test
    for p in state.players:
        p.hand.clear()
        p.melds.clear()
    
    # Set up CHI scenario: East discards Man 5, South can CHI
    discard_tile = Tile("Man", 5, 4)  # Man 5, tile_id=4
    state.last_discard = discard_tile
    state.last_discarded_by = 0  # East discards
    
    # South has Man 4 and Man 6 for CHI (4-5-6 sequence)
    south = state.players[1]
    south.hand = [
        Tile("Man", 4, 3),  # Man 4, tile_id=3
        Tile("Man", 6, 5),  # Man 6, tile_id=5
        Tile("Pin", 1, 9)   # Extra tile
    ]
    
    state.turn_index = 1  # South's turn
    state.awaiting_discard = False  # Reaction phase
    
    print(f"Setup:")
    print(f"  {state.players[0].seat} discards: {discard_tile}")
    print(f"  {south.seat} hand: {[str(t) for t in south.hand]}")
    print(f"  Expected CHI: [Man 4, Man 5, Man 6]")
    
    # Test can_chi function
    chi_melds = state.can_chi(discard_tile, player=south)
    print(f"\ncan_chi() result: {chi_melds}")
    
    if chi_melds:
        print("✅ CHI detection working")
        
        # Test if CHI actions are in legal actions
        legal_actions = state.get_legal_actions()
        chi_actions = [a for a in legal_actions if 85 <= a <= 105]
        print(f"Legal CHI actions: {chi_actions}")
        
        if chi_actions:
            print("✅ CHI actions available in legal actions")
            
            # Test encoding/decoding
            expected_sequence = [3, 4, 5]  # tile_ids for Man 4, 5, 6
            try:
                action_id = encode_chi(expected_sequence)
                decoded = decode_chi(action_id)
                print(f"CHI encoding: {expected_sequence} -> {action_id} -> {decoded}")
                
                if decoded == expected_sequence:
                    print("✅ CHI encoding/decoding working")
                else:
                    print("❌ CHI encoding/decoding broken")
            except Exception as e:
                print(f"❌ CHI encoding failed: {e}")
        else:
            print("❌ No CHI actions in legal actions")
    else:
        print("❌ CHI detection not working")
        
        # Debug why CHI detection failed
        print("\nDebugging CHI failure:")
        print(f"  Discard category: {discard_tile.category}")
        print(f"  Discard tile_id: {discard_tile.tile_id}")
        print(f"  Hand tile_ids: {[t.tile_id for t in south.hand]}")
        print(f"  Player == discarder: {south == state.players[state.last_discarded_by]}")

def test_chi_in_random_game():
    """Test CHI in a more realistic random game scenario"""
    print("\n🎲 TESTING CHI IN RANDOM GAME")
    print("="*35)
    
    # Run a short game and look for CHI opportunities
    state = GameState()
    state.step()  # Initial draw
    
    turns = 0
    chi_opportunities = 0
    
    while not state.is_terminal() and turns < 50:
        current_player = state.get_current_player()
        legal_actions = state.get_legal_actions()
        
        # Check for CHI opportunities
        chi_actions = [a for a in legal_actions if 85 <= a <= 105]
        if chi_actions:
            chi_opportunities += 1
            print(f"Turn {turns}: {current_player.seat} has CHI opportunity!")
            print(f"  CHI actions: {chi_actions}")
            print(f"  Last discard: {state.last_discard}")
            print(f"  Hand: {[str(t) for t in current_player.hand]}")
            
            # Take the first CHI action
            action = chi_actions[0]
            try:
                state.step(action)
                print(f"  ✅ CHI executed successfully!")
                print(f"  New melds: {current_player.melds}")
            except Exception as e:
                print(f"  ❌ CHI failed: {e}")
        else:
            # Take a random legal action
            if legal_actions:
                import random
                action = random.choice(legal_actions)
                try:
                    state.step(action)
                except:
                    pass  # Ignore errors in this test
        
        turns += 1
    
    print(f"\nGame summary:")
    print(f"  Turns played: {turns}")
    print(f"  CHI opportunities found: {chi_opportunities}")
    
    if chi_opportunities == 0:
        print("❌ No CHI opportunities found in random game")
        print("   This suggests CHI detection or legal action generation is broken")
    else:
        print("✅ CHI opportunities found and working")

def test_chi_action_space():
    """Test CHI action space encoding/decoding"""
    print("\n🔧 TESTING CHI ACTION SPACE")
    print("="*32)
    
    # Test valid CHI sequences
    valid_sequences = [
        [0, 1, 2],    # Man 1-2-3
        [3, 4, 5],    # Man 4-5-6  
        [6, 7, 8],    # Man 7-8-9
        [9, 10, 11],  # Pin 1-2-3
        [18, 19, 20], # Sou 1-2-3
        [24, 25, 26]  # Sou 7-8-9
    ]
    
    print("Testing valid CHI sequences:")
    for seq in valid_sequences:
        try:
            action_id = encode_chi(seq)
            decoded = decode_chi(action_id)
            success = decoded == seq
            print(f"  {seq} -> {action_id} -> {decoded} {'✅' if success else '❌'}")
        except Exception as e:
            print(f"  {seq} -> ERROR: {e}")
    
    # Test invalid CHI sequences  
    invalid_sequences = [
        [8, 9, 10],   # Cross-suit (Man 9, Pin 1, Pin 2)
        [26, 27, 28], # Cross-suit (Sou 9, Wind East, Wind South)
        [7, 8, 9],    # Would be Man 8-9-10 (10 doesn't exist)
    ]
    
    print("\nTesting invalid CHI sequences (should fail):")
    for seq in invalid_sequences:
        try:
            action_id = encode_chi(seq)
            print(f"  {seq} -> {action_id} ❌ (should have failed)")
        except Exception as e:
            print(f"  {seq} -> ERROR: {e} ✅ (correctly rejected)")

if __name__ == "__main__":
    test_chi_detection()
    test_chi_in_random_game() 
    test_chi_action_space()
    
    print("\n" + "="*50)
    print("🇨🇳 CHI DEBUGGING COMPLETE")
    print("="*50)
    print("If CHI detection/legal actions are broken, we found the issue.")
    print("If no CHI opportunities appear in random games, that's the problem.")
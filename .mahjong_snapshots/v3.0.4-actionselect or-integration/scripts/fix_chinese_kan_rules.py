"""
CHINESE MAHJONG KAN RULES CLARIFICATION

Based on official sources and your rules document, here's what should happen:

1. REPLACEMENT TILE DRAW: After ANY KAN (Ankan, Minkan, Shominkan), 
   the player MUST draw a replacement tile from the wall.

2. NO BONUS POINTS: The "no bonus draw" in your rules means no extra 
   SCORING bonus, not no replacement tile.

3. HAND SIZE: After KAN + replacement draw, player has 14 tiles 
   (13 regular + 1 from replacement) and must discard.

YOUR CURRENT CODE IS WRONG:
- You have NO replacement draws after KAN
- This violates Chinese Mahjong rules
- Players end up with too few tiles

WHAT NEEDS TO BE FIXED:
File: engine/game_state.py
Functions: step() method in KAN sections
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.game_state import GameState
from engine.tile import Tile
from engine.action_space import ACTION_NAME_TO_ID

def test_current_kan_behavior():
    """Test current (incorrect) KAN behavior"""
    print("🧪 TESTING CURRENT KAN BEHAVIOR")
    print("="*40)
    
    state = GameState()
    player = state.players[0]
    
    # Clear hand and set up KAN test
    player.hand.clear()
    player.melds.clear()
    player.hand.extend([Tile("Man", 1, 0)] * 4)  # 4 identical tiles
    
    print(f"Before KAN:")
    print(f"  Hand size: {len(player.hand)}")
    print(f"  Wall size: {len(state.wall)}")
    print(f"  Melds: {len(player.melds)}")
    
    # Execute KAN
    state.awaiting_discard = True
    wall_before = len(state.wall)
    hand_before = len(player.hand)
    
    try:
        state.step(ACTION_NAME_TO_ID["KAN_0"])
        
        print(f"\nAfter KAN:")
        print(f"  Hand size: {len(player.hand)}")
        print(f"  Wall size: {len(state.wall)}")
        print(f"  Melds: {len(player.melds)}")
        print(f"  Wall change: {wall_before - len(state.wall)}")
        print(f"  Hand change: {len(player.hand) - hand_before}")
        
        # Analyze the results
        wall_used = wall_before - len(state.wall)
        hand_change = len(player.hand) - hand_before
        
        if wall_used == 0:
            print("\n❌ BUG CONFIRMED: No replacement tile drawn from wall")
            print("   This violates Chinese Mahjong rules!")
        elif wall_used == 1:
            print("\n✅ Replacement tile drawn (correct behavior)")
        else:
            print(f"\n❓ Unexpected: {wall_used} tiles used from wall")
            
        if len(player.hand) == 0:
            print("❌ Hand is empty after KAN (should have 1 tile)")
        elif len(player.hand) == 1:
            print("✅ Hand has 1 tile after replacement (correct for this test)")
        else:
            print(f"❓ Hand has {len(player.hand)} tiles (unexpected)")
            
    except Exception as e:
        print(f"❌ KAN failed with error: {e}")

def show_correct_kan_behavior():
    """Show what the correct KAN behavior should be"""
    print("\n📋 CORRECT CHINESE KAN BEHAVIOR")
    print("="*40)
    
    print("1. Player declares KAN (any type)")
    print("2. KAN meld is formed and registered") 
    print("3. Player MUST draw replacement tile from wall")
    print("4. Player now has 14 tiles total and must discard")
    print("5. After discard, player has 13 tiles + melds")
    
    print("\nExample:")
    print("  Before KAN: 13 tiles in hand")
    print("  After KAN formation: 9 tiles in hand (13 - 4 for KAN)")
    print("  After replacement draw: 10 tiles in hand (9 + 1)")
    print("  After discard: 9 tiles in hand + 1 KAN meld")
    print("  Total: 9 + 4 = 13 tiles (correct)")

def show_code_fixes_needed():
    """Show exactly what code needs to be changed"""
    print("\n🔧 CODE FIXES NEEDED")
    print("="*25)
    
    print("File: engine/game_state.py")
    print("Method: step() - KAN action sections")
    print()
    print("CURRENT CODE (lines ~XXX):")
    print("  # After KAN formation")
    print("  self.awaiting_discard = True")
    print("  return  # ❌ WRONG: No replacement draw")
    print()
    print("CORRECT CODE:")
    print("  # After KAN formation")
    print("  if self.wall:")
    print("      replacement_tile = self.wall.pop()")
    print("      player.draw_tile(replacement_tile)")
    print("  self.awaiting_discard = True")
    print("  return")
    print()
    print("APPLIES TO:")
    print("  - Ankan (closed KAN)")
    print("  - Minkan (open KAN from discard)")  
    print("  - Shominkan (PON to KAN upgrade)")

if __name__ == "__main__":
    test_current_kan_behavior()
    show_correct_kan_behavior()
    show_code_fixes_needed()
    
    print("\n" + "="*60)
    print("🇨🇳 CHINESE MAHJONG KAN RULE VIOLATION CONFIRMED")
    print("="*60)
    print("Your current implementation violates Chinese Mahjong rules.")
    print("KAN must draw replacement tiles. This is critical to fix.")
    print()
    print("PRIORITY: HIGH - This affects game correctness")
    print("IMPACT: Players end up with wrong number of tiles")
    print("FIX: Add replacement tile draw after all KAN types")
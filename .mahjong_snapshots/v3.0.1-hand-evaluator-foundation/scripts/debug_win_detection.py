import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.tile import Tile
from engine.game_state import is_winning_hand
from engine.special_hands import _can_form_melds
from collections import Counter

def test_demo_winning_hand():
    """Test the exact winning hand from demo_summary.txt"""
    print("🏆 TESTING DEMO WINNING HAND")
    print("="*35)
    
    # Player 3's exact winning hand from demo_summary.txt
    print("From demo_summary.txt - Player 3 (North):")
    print("Hand (2 tiles): ['Sou 9', 'Sou 9']")
    print("Melds (4): [('PON', ['Dragon Green'x3]), ('PON', ['Wind East'x3]), ('PON', ['Pin 1'x3]), ('PON', ['Wind West'x3])]")
    
    # Recreate the exact hand
    hand_tiles = [Tile("Sou", 9, 26), Tile("Sou", 9, 26)]  # Pair
    
    # Meld tiles (4 PONs)
    meld_tiles = [
        # PON 1: Dragon Green x3
        Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32),
        # PON 2: Wind East x3
        Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
        # PON 3: Pin 1 x3
        Tile("Pin", 1, 9), Tile("Pin", 1, 9), Tile("Pin", 1, 9),
        # PON 4: Wind West x3
        Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29)
    ]
    
    full_hand = hand_tiles + meld_tiles
    
    print(f"\nRecreated hand:")
    print(f"  Hand tiles: {[str(t) for t in hand_tiles]} ({len(hand_tiles)} tiles)")
    print(f"  Meld tiles: {len(meld_tiles)} tiles from 4 PONs")
    print(f"  Total: {len(full_hand)} tiles")
    
    # This should be a perfect winning hand: 4 PONs + 1 pair
    print(f"\nStructure analysis:")
    counts = Counter((t.category, t.value) for t in full_hand)
    melds = pairs = invalid = 0
    
    for (cat, val), count in counts.items():
        if count == 3:
            melds += 1
            print(f"  ✅ MELD: {cat} {val} x{count}")
        elif count == 2:
            pairs += 1
            print(f"  ✅ PAIR: {cat} {val} x{count}")
        else:
            invalid += 1
            print(f"  ❌ INVALID: {cat} {val} x{count}")
    
    print(f"\nExpected: 4 melds + 1 pair")
    print(f"Found: {melds} melds + {pairs} pairs + {invalid} invalid")
    
    if melds == 4 and pairs == 1 and invalid == 0:
        print("✅ Perfect winning hand structure")
    else:
        print("❌ Invalid hand structure")
        return False
    
    # Test win detection
    print(f"\nTesting is_winning_hand():")
    result = is_winning_hand(full_hand)
    print(f"  Result: {result}")
    
    if result:
        print("✅ Win detection working correctly")
        return True
    else:
        print("❌ CRITICAL BUG: Win detection failed on valid hand")
        return False

def test_can_form_melds_directly():
    """Test the _can_form_melds function directly"""
    print("\n🔧 TESTING _can_form_melds FUNCTION")
    print("="*40)
    
    # Test with 12 tiles that should form 4 perfect triplets
    test_tiles = [
        # Triplet 1: Dragon Green x3
        Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32), Tile("Dragon", "Green", 32),
        # Triplet 2: Wind East x3
        Tile("Wind", "East", 27), Tile("Wind", "East", 27), Tile("Wind", "East", 27),
        # Triplet 3: Pin 1 x3
        Tile("Pin", 1, 9), Tile("Pin", 1, 9), Tile("Pin", 1, 9),
        # Triplet 4: Wind West x3
        Tile("Wind", "West", 29), Tile("Wind", "West", 29), Tile("Wind", "West", 29)
    ]
    
    print(f"Testing _can_form_melds with 12 tiles (4 perfect triplets):")
    print(f"  Input: {[str(t) for t in test_tiles]}")
    
    result = _can_form_melds(test_tiles)
    print(f"  _can_form_melds() result: {result}")
    
    if result:
        print("✅ _can_form_melds working correctly")
    else:
        print("❌ CRITICAL BUG: _can_form_melds failed on perfect triplets")
        
        # Debug why it failed
        print("\n🔍 Debugging _can_form_melds failure:")
        counts = Counter((t.category, t.value) for t in test_tiles)
        print("  Tile counts:")
        for (cat, val), count in counts.items():
            print(f"    {cat} {val}: {count} tiles")
        
        # Check if all are triplets
        all_triplets = all(count == 3 for count in counts.values())
        print(f"  All tiles form triplets: {all_triplets}")
        
        if all_triplets:
            print("  ✅ Input is mathematically perfect")
            print("  ❌ Bug is definitely in _can_form_melds logic")
    
    return result

def test_simple_winning_hands():
    """Test other simple winning hand patterns"""
    print("\n🧪 TESTING SIMPLE WINNING HANDS")
    print("="*35)
    
    # Test 1: All sequences + pair
    print("Test 1: All sequences + pair")
    hand1 = [
        # 4 sequences  
        Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
        Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
        Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
        Tile("Pin", 4, 12), Tile("Pin", 5, 13), Tile("Pin", 6, 14),
        # 1 pair
        Tile("Sou", 1, 18), Tile("Sou", 1, 18)
    ]
    
    result1 = is_winning_hand(hand1)
    print(f"  Result: {result1} {'✅' if result1 else '❌'}")
    
    # Test 2: Mixed melds + pair
    print("\nTest 2: Mixed triplets and sequences + pair")
    hand2 = [
        # 2 triplets
        Tile("Man", 1, 0), Tile("Man", 1, 0), Tile("Man", 1, 0),
        Tile("Pin", 9, 17), Tile("Pin", 9, 17), Tile("Pin", 9, 17),
        # 2 sequences
        Tile("Sou", 2, 19), Tile("Sou", 3, 20), Tile("Sou", 4, 21),
        Tile("Sou", 5, 22), Tile("Sou", 6, 23), Tile("Sou", 7, 24),
        # 1 pair
        Tile("Wind", "East", 27), Tile("Wind", "East", 27)
    ]
    
    result2 = is_winning_hand(hand2)
    print(f"  Result: {result2} {'✅' if result2 else '❌'}")

if __name__ == "__main__":
    demo_ok = test_demo_winning_hand()
    melds_ok = test_can_form_melds_directly()
    test_simple_winning_hands()
    
    print("\n" + "="*60)
    print("🏆 WIN DETECTION DIAGNOSIS")
    print("="*60)
    
    if demo_ok and melds_ok:
        print("✅ Win detection appears to be working correctly")
        print("   The issue might be elsewhere (game state, terminal detection, etc.)")
    elif not melds_ok:
        print("❌ CRITICAL BUG CONFIRMED: _can_form_melds() is broken")
        print("   This function needs to be fixed immediately")
        print("   Location: engine/game_state.py - _can_form_melds() function")
    elif not demo_ok:
        print("❌ Win detection failed on demo hand")
        print("   Need to investigate is_winning_hand() logic")
    
    print("\nNext step: Fix the broken function identified above")
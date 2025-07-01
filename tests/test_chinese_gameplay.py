import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import random
from engine.game_state import GameState
from engine.action_space import PASS

class TestRandomAgent:
    """Random agent for testing Chinese Mahjong gameplay"""
    def __init__(self, player_id):
        self.player_id = player_id
        self.name = f"TestAgent_{player_id}"
    
    def get_action(self, state):
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            return None
        return random.choice(legal_actions)
    

def test_single_game(game_num=1, max_turns=150, verbose=True):
    """Test a single game with Chinese rules"""
    if verbose:
        print(f"\n{'='*50}")
        print(f"TESTING CHINESE MAHJONG GAME #{game_num}")
        print(f"{'='*50}")
    
    # Create game and agents
    state = GameState()
    agents = [TestRandomAgent(i) for i in range(4)]
    
    # Initial draw for East player
    state.step()
    
    turn_count = 0
    meld_count = 0
    total_actions = 0
    
    while not state.is_terminal() and turn_count < max_turns:
        current_player = state.get_current_player()
        agent = agents[state.turn_index]
        
        # Get legal actions
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            if verbose:
                print(f"Turn {turn_count}: No legal actions for {current_player.seat}")
            break
        
        # Agent chooses action
        action = agent.get_action(state)
        if action is None:
            if verbose:
                print(f"Turn {turn_count}: Agent returned None for {current_player.seat}")
            break
        
        # Track statistics before action
        melds_before = sum(len(p.melds) for p in state.players)
        
        if verbose and turn_count % 20 == 0:  # Print every 20 turns
            print(f"Turn {turn_count}: {current_player.seat} (Hand: {len(current_player.hand)}, Melds: {len(current_player.melds)})")
        
        # Take action
        try:
            state.step(action)
            total_actions += 1
            
            # Track meld creation
            melds_after = sum(len(p.melds) for p in state.players)
            if melds_after > melds_before:
                meld_count += 1
                if verbose:
                    print(f"  -> MELD CREATED! Total melds in game: {melds_after}")
            
        except Exception as e:
            if verbose:
                print(f"ERROR on turn {turn_count}: {e}")
            break
        
        turn_count += 1
        
        # Check for win
        if state.is_terminal():
            break
    
    # Game summary
    if verbose:
        print(f"\n{'='*30}")
        print(f"GAME #{game_num} COMPLETE")
        print(f"{'='*30}")
        print(f"Turns: {turn_count}")
        print(f"Total actions: {total_actions}")
        print(f"Melds created: {meld_count}")
        print(f"Terminal: {state.is_terminal()}")
        
        if state.is_terminal():
            if hasattr(state, 'winners'):
                for winner_id in state.winners:
                    winner = state.players[winner_id]
                    chinese_score = state.get_hand_score(winner)
                    cfr_reward = state.get_reward(winner_id)
                    print(f"WINNER: {winner.seat} (Player {winner_id})")
                    print(f"  Chinese Score: {chinese_score} points")
                    print(f"  CFR Reward: {cfr_reward}")
                    print(f"  Hand: {len(winner.hand)} tiles")
                    print(f"  Melds: {len(winner.melds)}")
        
        # Final player states
        print(f"\nFinal Player States:")
        for i, player in enumerate(state.players):
            chinese_score = state.get_hand_score(player)
            print(f"  {player.seat}: {len(player.hand)} tiles, {len(player.melds)} melds, {chinese_score} points")
    
    # Generate detailed summary file
    summary_filename = f"test_game_{game_num}_summary.txt"
    state.get_game_summary(summary_filename)
    
    return {
        'game_num': game_num,
        'turns': turn_count,
        'actions': total_actions,
        'melds': meld_count,
        'terminal': state.is_terminal(),
        'winners': getattr(state, 'winners', []),
        'summary_file': summary_filename
    }

def test_multiple_games(num_games=3, max_turns=150):
    """Test multiple games and collect statistics"""
    print("🎮 TESTING CHINESE MAHJONG ENGINE")
    print("="*60)
    
    results = []
    total_turns = 0
    total_melds = 0
    terminal_games = 0
    
    for i in range(num_games):
        result = test_single_game(i+1, max_turns, verbose=(i == 0))  # Only verbose for first game
        results.append(result)
        
        total_turns += result['turns']
        total_melds += result['melds']
        if result['terminal']:
            terminal_games += 1
    
    # Overall statistics
    print(f"\n🏆 OVERALL TEST RESULTS")
    print("="*40)
    print(f"Games tested: {num_games}")
    print(f"Games completed: {terminal_games}/{num_games} ({terminal_games/num_games*100:.1f}%)")
    print(f"Average turns per game: {total_turns/num_games:.1f}")
    print(f"Average melds per game: {total_melds/num_games:.1f}")
    print(f"Total actions executed: {sum(r['actions'] for r in results)}")
    
    # Check for any issues
    issues = []
    for r in results:
        if not r['terminal']:
            issues.append(f"Game {r['game_num']}: Did not reach terminal state")
        if r['turns'] >= max_turns:
            issues.append(f"Game {r['game_num']}: Hit turn limit ({max_turns})")
        if r['melds'] == 0:
            issues.append(f"Game {r['game_num']}: No melds created")
    
    if issues:
        print(f"\n⚠️  POTENTIAL ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ NO ISSUES DETECTED!")
    
    print(f"\n📁 Summary files generated:")
    for r in results:
        print(f"  - {r['summary_file']}")
    
    return results

def test_chinese_rules_specifically():
    """Test specific Chinese rule implementations"""
    print(f"\n🇨🇳 TESTING CHINESE RULE IMPLEMENTATIONS")
    print("="*50)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: CHI from any player
    print("Test 1: CHI from any player...")
    state = GameState()
    player = state.players[2]  # West player
    from engine.tile import Tile
    test_tile = Tile("Man", 3, 2)
    
    # Set up CHI scenario
    player.hand = [Tile("Man", 2, 1), Tile("Man", 4, 3)]
    state.last_discard = test_tile
    state.last_discarded_by = 0  # East discarded
    
    can_chi = state.can_chi(test_tile, player)
    tests_total += 1
    if len(can_chi) > 0:
        print("  ✅ CHI from any player works")
        tests_passed += 1
    else:
        print("  ❌ CHI from any player failed")
    
    # Test 2: No KAN bonus draws
    print("Test 2: No KAN bonus draws...")
    state = GameState()
    player = state.players[0]
    player.hand = [Tile("Man", 1, 0)] * 4
    wall_before = len(state.wall)
    
    state.awaiting_discard = True
    from engine.action_space import ACTION_NAME_TO_ID
    try:
        state.step(ACTION_NAME_TO_ID["KAN_0"])
        wall_after = len(state.wall)
        tests_total += 1
        if wall_after == wall_before:
            print("  ✅ No bonus draw after KAN")
            tests_passed += 1
        else:
            print("  ❌ Bonus draw still happening after KAN")
    except Exception as e:
        print(f"  ❌ KAN test failed with error: {e}")
        tests_total += 1
    
    # Test 3: Chinese scoring
    print("Test 3: Chinese scoring system...")
    state = GameState()
    player = state.players[0]
    
    # Create winning hand
    player.hand = [
        Tile("Man", 1, 0), Tile("Man", 2, 1), Tile("Man", 3, 2),
        Tile("Man", 4, 3), Tile("Man", 5, 4), Tile("Man", 6, 5),
        Tile("Man", 7, 6), Tile("Man", 8, 7), Tile("Man", 9, 8),
        Tile("Pin", 1, 9), Tile("Pin", 2, 10), Tile("Pin", 3, 11),
        Tile("Sou", 1, 18), Tile("Sou", 1, 19)
    ]
    
    chinese_score = state.get_hand_score(player)
    cfr_reward = state.get_reward(0)
    
    tests_total += 1
    if chinese_score >= 2:  # Should get points for winning
        print(f"  ✅ Chinese scoring works (got {chinese_score} points)")
        tests_passed += 1
    else:
        print(f"  ❌ Chinese scoring failed (got {chinese_score} points)")
    
    print(f"\n🎯 CHINESE RULES TEST SUMMARY:")
    print(f"  Tests passed: {tests_passed}/{tests_total}")
    print(f"  Success rate: {tests_passed/tests_total*100:.1f}%")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    # Set random seed for reproducible testing
    random.seed(42)
    
    print("🚀 STARTING CHINESE MAHJONG ENGINE TESTS")
    print("="*60)
    
    # Phase 1: Test Chinese rule implementations
    chinese_rules_ok = test_chinese_rules_specifically()
    
    if chinese_rules_ok:
        print("\n✅ Chinese rules validation passed!")
        
        # Phase 2: Test multiple games
        results = test_multiple_games(num_games=3, max_turns=150)
        
        print(f"\n🎉 TESTING COMPLETE!")
        print("Your Chinese Mahjong engine is ready for demo!")
        
    else:
        print("\n❌ Chinese rules validation failed!")
        print("Fix the issues above before proceeding.")
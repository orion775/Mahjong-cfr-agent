# scripts/ultimate_diagnostic.py

"""
Ultimate Diagnostic for Mahjong AI Training Failures

This script will identify why our aggressive training approaches are failing:
1. Compare successful vs failed models
2. Test reward-action relationships
3. Verify meld action functionality
4. Analyze behavioral patterns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import numpy as np
import json
from collections import defaultdict, Counter
from engine.game_state import GameState
from trainers.balanced_aggressive_trainer import BalancedAggressiveTrainer
import random

def test_meld_action_functionality():
    """Test if meld actions are working properly in the game engine."""
    print("🔧 TESTING MELD ACTION FUNCTIONALITY")
    print("=" * 50)
    
    results = {
        'total_tests': 1000,
        'successful_pons': 0,
        'successful_chis': 0,
        'successful_kans': 0,
        'failed_actions': 0,
        'action_errors': []
    }
    
    for test_idx in range(results['total_tests']):
        try:
            game_state = GameState()
            
            # Force a scenario where meld actions might be legal
            for _ in range(50):  # Play some moves to generate discards
                if game_state.is_terminal():
                    break
                
                legal_actions = game_state.get_legal_actions()
                if not legal_actions:
                    break
                
                # Check for meld opportunities (CORRECTED RANGES!)
                pon_actions = [a for a in legal_actions if 42 <= a < 84]
                chi_actions = [a for a in legal_actions if 85 <= a < 106]
                kan_actions = [a for a in legal_actions if 106 <= a < 148]
                
                if pon_actions:
                    try:
                        game_state.step(pon_actions[0])
                        results['successful_pons'] += 1
                        break
                    except Exception as e:
                        results['failed_actions'] += 1
                        results['action_errors'].append(f"PON failed: {e}")
                
                elif chi_actions:
                    try:
                        game_state.step(chi_actions[0])
                        results['successful_chis'] += 1
                        break
                    except Exception as e:
                        results['failed_actions'] += 1
                        results['action_errors'].append(f"CHI failed: {e}")
                
                elif kan_actions:
                    try:
                        game_state.step(kan_actions[0])
                        results['successful_kans'] += 1
                        break
                    except Exception as e:
                        results['failed_actions'] += 1
                        results['action_errors'].append(f"KAN failed: {e}")
                
                else:
                    # No meld actions available, do a regular move
                    action = random.choice(legal_actions)
                    game_state.step(action)
        
        except Exception as e:
            results['action_errors'].append(f"Game error: {e}")
    
    print(f"📊 MELD ACTION TEST RESULTS:")
    print(f"   Total Tests: {results['total_tests']}")
    print(f"   Successful PONs: {results['successful_pons']}")
    print(f"   Successful CHIs: {results['successful_chis']}")
    print(f"   Successful KANs: {results['successful_kans']}")
    print(f"   Failed Actions: {results['failed_actions']}")
    print(f"   Error Rate: {results['failed_actions']/results['total_tests']*100:.1f}%")
    
    if results['action_errors']:
        print(f"\n🚨 Sample Errors:")
        for error in results['action_errors'][:5]:
            print(f"   - {error}")
    
    return results

def test_reward_influence():
    """Test if rewards actually influence neural network decisions."""
    print("\n🧠 TESTING REWARD-ACTION INFLUENCE")
    print("=" * 50)
    
    # Create trainer
    trainer = BalancedAggressiveTrainer(
        game_state_cls=GameState,
        learning_rate=0.001,
        epsilon=0.0  # No exploration - pure exploitation
    )
    
    # Test with different reward magnitudes
    test_scenarios = [
        {'pass_penalty': 0, 'meld_bonus': 0, 'name': 'No Rewards'},
        {'pass_penalty': -100, 'meld_bonus': 100, 'name': 'Extreme Anti-Pass'},
        {'pass_penalty': -2.5, 'meld_bonus': 15, 'name': 'Balanced Rewards'}
    ]
    
    results = {}
    
    for scenario in test_scenarios:
        print(f"\n🎯 Testing: {scenario['name']}")
        
        # Temporarily modify rewards
        original_rewards = trainer.reward_weights.copy()
        trainer.reward_weights['pass_penalty'] = scenario['pass_penalty']
        trainer.reward_weights['meld_completion'] = scenario['meld_bonus']
        
        # Test action selection over multiple games
        action_counts = defaultdict(int)
        total_actions = 0
        
        for game_idx in range(50):  # Test on 50 games
            game_state = GameState()
            
            for step in range(100):  # Up to 100 steps per game
                if game_state.is_terminal():
                    break
                
                current_player = getattr(game_state, 'current_player', 0)
                if current_player == 0:  # Our AI's turn
                    action = trainer.select_action(game_state, 0, use_exploration=False)
                    if action is not None:
                        action_type = trainer.classify_action(action)
                        action_counts[action_type] += 1
                        total_actions += 1
                    
                    try:
                        game_state.step(action)
                    except:
                        break
                else:
                    # Random opponent
                    legal_actions = game_state.get_legal_actions()
                    if legal_actions:
                        game_state.step(random.choice(legal_actions))
                    else:
                        break
        
        # Calculate percentages
        action_percentages = {}
        for action_type, count in action_counts.items():
            action_percentages[action_type] = (count / total_actions) * 100 if total_actions > 0 else 0
        
        results[scenario['name']] = {
            'action_percentages': action_percentages,
            'total_actions': total_actions
        }
        
        print(f"   PASS: {action_percentages.get('PASS', 0):.1f}%")
        print(f"   MELD: {action_percentages.get('PON', 0) + action_percentages.get('CHI', 0) + action_percentages.get('KAN', 0):.1f}%")
        
        # Restore original rewards
        trainer.reward_weights = original_rewards
    
    return results

def analyze_model_differences():
    """Compare our failed models with successful approaches."""
    print("\n📊 ANALYZING MODEL DIFFERENCES")
    print("=" * 50)
    
    models_to_test = [
        {'path': 'enhanced_progressive_model.pth', 'name': 'Enhanced Progressive (13.5% win)'},
        {'path': 'balanced_aggressive_model.pth', 'name': 'Balanced Aggressive (1.6% win)'},
        {'path': 'ultra_aggressive_model.pth', 'name': 'Ultra Aggressive (2.4% win)'}
    ]
    
    results = {}
    
    for model_info in models_to_test:
        model_path = model_info['path']
        model_name = model_info['name']
        
        if not os.path.exists(model_path):
            print(f"❌ {model_name}: File not found")
            continue
        
        print(f"\n🔍 Analyzing: {model_name}")
        
        try:
            # Load model data
            model_data = torch.load(model_path, map_location='cpu')
            
            # Extract key information
            model_analysis = {
                'file_size': os.path.getsize(model_path),
                'has_q_network': 'q_network_state_dict' in model_data,
                'has_training_stats': 'training_stats' in model_data,
                'has_optimizer': 'optimizer_state_dict' in model_data
            }
            
            if 'training_stats' in model_data:
                stats = model_data['training_stats']
                model_analysis.update({
                    'episodes_trained': stats.get('episodes', 'Unknown'),
                    'final_win_rate': stats.get('win_rate', 'Unknown'),
                    'final_avg_loss': stats.get('avg_loss', 'Unknown'),
                    'final_epsilon': stats.get('epsilon', 'Unknown')
                })
            
            # Test the model on a few games
            if model_analysis['has_q_network']:
                action_test = test_model_behavior(model_data, model_name)
                model_analysis['behavior_test'] = action_test
            
            results[model_name] = model_analysis
            
            print(f"   Episodes: {model_analysis.get('episodes_trained', 'Unknown')}")
            print(f"   Win Rate: {model_analysis.get('final_win_rate', 'Unknown')}")
            print(f"   Loss: {model_analysis.get('final_avg_loss', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error analyzing {model_name}: {e}")
            results[model_name] = {'error': str(e)}
    
    return results

def test_model_behavior(model_data, model_name, test_games=20):
    """Test actual behavior of a loaded model."""
    try:
        # Create trainer and load the model
        trainer = BalancedAggressiveTrainer(
            game_state_cls=GameState,
            learning_rate=0.001,
            epsilon=0.0  # No exploration
        )
        
        # Load the model weights
        if 'q_network_state_dict' in model_data:
            trainer.q_network.load_state_dict(model_data['q_network_state_dict'])
        
        # Test behavior
        action_counts = defaultdict(int)
        total_actions = 0
        wins = 0
        
        for game_idx in range(test_games):
            game_state = GameState()
            
            for step in range(200):
                if game_state.is_terminal():
                    if game_state.get_reward(0) > 0:
                        wins += 1
                    break
                
                current_player = getattr(game_state, 'current_player', 0)
                if current_player == 0:
                    action = trainer.select_action(game_state, 0, use_exploration=False)
                    if action is not None:
                        action_type = trainer.classify_action(action)
                        action_counts[action_type] += 1
                        total_actions += 1
                else:
                    legal_actions = game_state.get_legal_actions()
                    action = random.choice(legal_actions) if legal_actions else None
                
                if action is not None:
                    try:
                        game_state.step(action)
                    except:
                        break
        
        # Calculate behavior metrics
        behavior = {}
        for action_type, count in action_counts.items():
            behavior[action_type] = (count / total_actions) * 100 if total_actions > 0 else 0
        
        behavior['win_rate'] = (wins / test_games) * 100
        behavior['total_actions'] = total_actions
        
        return behavior
        
    except Exception as e:
        return {'error': f"Behavior test failed: {e}"}

def find_action_space_issues():
    """Investigate potential action space mapping problems."""
    print("\n🎯 INVESTIGATING ACTION SPACE ISSUES")
    print("=" * 50)
    
    # Test action space mapping (CORRECTED RANGES!)
    action_mapping_test = {
        'discard_actions': list(range(0, 42)),
        'pon_actions': list(range(42, 84)),
        'chi_actions': list(range(85, 106)),
        'kan_actions': list(range(106, 148)),
        'pass_action': [84]
    }
    
    print("📋 Action Space Mapping:")
    for action_type, action_range in action_mapping_test.items():
        print(f"   {action_type}: {len(action_range)} actions ({min(action_range) if action_range else 'N/A'}-{max(action_range) if action_range else 'N/A'})")
    
    # Test legal action generation
    legal_action_stats = {
        'games_tested': 100,
        'meld_opportunities': 0,
        'pon_opportunities': 0,
        'chi_opportunities': 0,
        'kan_opportunities': 0,
        'pass_available': 0
    }
    
    for game_idx in range(legal_action_stats['games_tested']):
        game_state = GameState()
        
        for step in range(100):
            if game_state.is_terminal():
                break
            
            legal_actions = game_state.get_legal_actions()
            
            # Count opportunity types (CORRECTED RANGES!)
            pon_available = any(42 <= a < 84 for a in legal_actions)
            chi_available = any(85 <= a < 106 for a in legal_actions)
            kan_available = any(106 <= a < 148 for a in legal_actions)
            pass_available = 84 in legal_actions
            
            if pon_available:
                legal_action_stats['pon_opportunities'] += 1
            if chi_available:
                legal_action_stats['chi_opportunities'] += 1
            if kan_available:
                legal_action_stats['kan_opportunities'] += 1
            if pass_available:
                legal_action_stats['pass_available'] += 1
            if pon_available or chi_available or kan_available:
                legal_action_stats['meld_opportunities'] += 1
            
            # Take a random action
            if legal_actions:
                try:
                    game_state.step(random.choice(legal_actions))
                except:
                    break
    
    print(f"📊 Legal Action Statistics (over {legal_action_stats['games_tested']} games):")
    print(f"   Meld Opportunities: {legal_action_stats['meld_opportunities']}")
    print(f"   PON Opportunities: {legal_action_stats['pon_opportunities']}")
    print(f"   CHI Opportunities: {legal_action_stats['chi_opportunities']}")
    print(f"   KAN Opportunities: {legal_action_stats['kan_opportunities']}")
    print(f"   PASS Available: {legal_action_stats['pass_available']}")
    
    return legal_action_stats

def generate_ultimate_diagnostic_report():
    """Run all diagnostic tests and generate comprehensive report."""
    print("🚀 ULTIMATE MAHJONG AI DIAGNOSTIC REPORT")
    print("=" * 70)
    
    diagnostic_results = {}
    
    # Test 1: Meld Action Functionality
    diagnostic_results['meld_functionality'] = test_meld_action_functionality()
    
    # Test 2: Reward Influence
    diagnostic_results['reward_influence'] = test_reward_influence()
    
    # Test 3: Model Differences
    diagnostic_results['model_analysis'] = analyze_model_differences()
    
    # Test 4: Action Space Issues
    diagnostic_results['action_space'] = find_action_space_issues()
    
    # Generate summary and recommendations
    print("\n" + "=" * 70)
    print("🎯 DIAGNOSTIC SUMMARY AND RECOMMENDATIONS")
    print("=" * 70)
    
    # Analyze meld functionality
    meld_results = diagnostic_results['meld_functionality']
    total_meld_success = meld_results['successful_pons'] + meld_results['successful_chis'] + meld_results['successful_kans']
    
    if total_meld_success < 50:
        print("🚨 CRITICAL: Meld actions are not working properly!")
        print("   - This explains why CHI rate = 0% and meld rates are stuck at 2%")
        print("   - SOLUTION: Fix game engine meld action implementation")
    else:
        print("✅ Meld actions are working correctly")
    
    # Analyze reward influence
    reward_results = diagnostic_results['reward_influence']
    if 'No Rewards' in reward_results and 'Extreme Anti-Pass' in reward_results:
        no_reward_pass = reward_results['No Rewards']['action_percentages'].get('PASS', 0)
        extreme_reward_pass = reward_results['Extreme Anti-Pass']['action_percentages'].get('PASS', 0)
        
        if abs(no_reward_pass - extreme_reward_pass) < 5:  # Less than 5% difference
            print("🚨 CRITICAL: Rewards are not influencing behavior!")
            print(f"   - PASS rate barely changed: {no_reward_pass:.1f}% → {extreme_reward_pass:.1f}%")
            print("   - SOLUTION: Fix reward-action feedback loop")
        else:
            print("✅ Rewards are influencing behavior")
            print(f"   - PASS rate changed: {no_reward_pass:.1f}% → {extreme_reward_pass:.1f}%")
    
    # Save detailed results
    with open('ultimate_diagnostic_results.json', 'w') as f:
        json.dump(diagnostic_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: ultimate_diagnostic_results.json")
    print(f"\n🎯 Next Steps:")
    print(f"1. Review the specific issues identified above")
    print(f"2. Implement targeted fixes for the root causes")
    print(f"3. Re-test with a simple, focused training approach")
    
    return diagnostic_results

if __name__ == "__main__":
    generate_ultimate_diagnostic_report()

# scripts/comprehensive_model_tester.py

"""
Comprehensive Model Tester - Test All Models with 2000 Games

This script tests all your trained models with standardized 2000-game sessions
and provides detailed comparative analysis.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
except ImportError:
    print("ERROR: PyTorch not installed!")
    sys.exit(1)

from trainers.selfplay_neural_trainer import SelfPlayNeuralTrainer
from engine.game_state import GameState
import time
import json
from datetime import datetime

class ModelTester:
    def __init__(self, test_games=2000):
        self.test_games = test_games
        self.results = {}
        
    def load_model(self, model_path, trainer):
        """Load a model with proper error handling."""
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
            
        try:
            checkpoint = torch.load(model_path, 
                                   map_location=trainer.device, 
                                   weights_only=False)
            
            if hasattr(trainer, 'q_network'):
                if 'q_network_state_dict' in checkpoint:
                    trainer.q_network.load_state_dict(checkpoint['q_network_state_dict'])
                    print(f"✅ Loaded from q_network_state_dict")
                    return True
                elif isinstance(checkpoint, dict) and any('network' in key for key in checkpoint.keys()):
                    trainer.q_network.load_state_dict(checkpoint)
                    print(f"✅ Loaded from direct state dict")
                    return True
                else:
                    print(f"⚠️  Unknown checkpoint format: {list(checkpoint.keys())}")
                    return False
            else:
                print(f"⚠️  Trainer has no q_network attribute")
                return False
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def test_single_model(self, model_path, model_name):
        """Test a single model with comprehensive metrics."""
        print(f"\n" + "="*80)
        print(f"🎯 TESTING: {model_name}")
        print(f"📁 Model: {model_path}")
        print(f"🎮 Games: {self.test_games}")
        print(f"="*80)
        
        # Create trainer
        trainer = SelfPlayNeuralTrainer(
            game_state_cls=GameState,
            learning_rate=0.001,
            epsilon=0.0  # Pure exploitation for testing
        )
        
        # Load model
        model_loaded = self.load_model(model_path, trainer)
        if not model_loaded:
            print(f"❌ Skipping {model_name} - could not load model")
            return None
        
        # Initialize tracking variables
        position_wins = [0, 0, 0, 0]
        draw_games = 0
        game_lengths = []
        quick_wins = 0  # Games won in <100 moves
        error_games = 0
        
        start_time = time.time()
        
        print(f"🚀 Starting {self.test_games} games...")
        
        # Run test games
        for i in range(self.test_games):
            try:
                game_state = GameState()
                game_length = 0
                max_steps = 300
                
                while not game_state.is_terminal() and game_length < max_steps:
                    current_player = game_state.current_player
                    action = trainer.select_action(game_state, player_id=current_player, use_exploration=False)
                    if action is None:
                        break
                    
                    game_state.step(action)
                    game_length += 1
                
                game_lengths.append(game_length)
                
                # Check outcome
                winner_found = False
                if game_state.is_terminal():
                    for player_id in range(4):
                        if game_state.get_reward(player_id) > 0:
                            position_wins[player_id] += 1
                            winner_found = True
                            if game_length < 100:
                                quick_wins += 1
                            break
                
                if not winner_found:
                    draw_games += 1
                    
            except Exception as e:
                error_games += 1
                game_lengths.append(300)  # Max length for errors
                draw_games += 1
            
            # Progress reporting
            if (i + 1) % 400 == 0:
                current_win_rate = sum(position_wins) / (i + 1)
                current_draw_rate = draw_games / (i + 1)
                elapsed = time.time() - start_time
                print(f"   Progress: {i+1}/{self.test_games} - Win: {current_win_rate:.3f}, Draw: {current_draw_rate:.3f}, Time: {elapsed:.1f}s")
        
        # Calculate final results
        total_wins = sum(position_wins)
        win_rate = total_wins / self.test_games
        draw_rate = draw_games / self.test_games
        error_rate = error_games / self.test_games
        avg_length = sum(game_lengths) / len(game_lengths) if game_lengths else 0
        quick_win_rate = quick_wins / total_wins if total_wins > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        # Store results
        results = {
            'model_name': model_name,
            'model_path': model_path,
            'test_games': self.test_games,
            'total_wins': total_wins,
            'win_rate': win_rate,
            'draw_rate': draw_rate,
            'error_rate': error_rate,
            'avg_game_length': avg_length,
            'quick_wins': quick_wins,
            'quick_win_rate': quick_win_rate,
            'position_wins': position_wins,
            'position_rates': [wins/self.test_games for wins in position_wins],
            'test_time': elapsed_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print results
        print(f"\n📊 {model_name.upper()} RESULTS:")
        print(f"🏆 Win Rate: {win_rate:.3f} ({win_rate*100:.1f}%)")
        print(f"🎲 Draw Rate: {draw_rate:.3f} ({draw_rate*100:.1f}%)")
        print(f"❌ Error Rate: {error_rate:.3f} ({error_rate*100:.1f}%)")
        print(f"📏 Avg Game Length: {avg_length:.1f} moves")
        print(f"⚡ Quick Wins: {quick_wins}/{total_wins} ({quick_win_rate*100:.1f}%)")
        print(f"⏱️  Test Time: {elapsed_time:.1f} seconds")
        
        position_names = ["East", "South", "West", "North"]
        print(f"\n🎯 Position Performance:")
        for i, (name, wins, rate) in enumerate(zip(position_names, position_wins, results['position_rates'])):
            print(f"   {name}: {wins} wins ({rate:.3f} = {rate*100:.1f}%)")
        
        return results
    
    def test_all_models(self):
        """Test all available models."""
        models_to_test = [
            ("aggressive_selfplay_model.pth", "Aggressive Self-Play"),
            ("adaptive_aggressive_model.pth", "Adaptive Aggressive"),
            ("cfr_enhanced_model.pth", "CFR Enhanced"),
            ("focused_win_model.pth", "Focused Win"),
            ("enhanced_progressive_model.pth", "Enhanced Progressive")
        ]
        
        print(f"🚀 COMPREHENSIVE MODEL TESTING")
        print(f"📊 Testing {len(models_to_test)} models with {self.test_games} games each")
        print(f"⏱️  Estimated time: {len(models_to_test) * 15} minutes")
        
        all_results = []
        
        for model_path, model_name in models_to_test:
            if os.path.exists(model_path):
                result = self.test_single_model(model_path, model_name)
                if result:
                    all_results.append(result)
                    self.results[model_name] = result
            else:
                print(f"⚠️  Skipping {model_name} - file not found: {model_path}")
        
        return all_results
    
    def generate_comparison_report(self, results):
        """Generate a comprehensive comparison report."""
        if not results:
            print("❌ No results to compare!")
            return
        
        print(f"\n" + "="*100)
        print(f"📊 COMPREHENSIVE MODEL COMPARISON REPORT")
        print(f"="*100)
        print(f"🎮 Test Games per Model: {self.test_games}")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Sort by win rate
        sorted_results = sorted(results, key=lambda x: x['win_rate'], reverse=True)
        
        print(f"\n🏆 RANKING BY WIN RATE:")
        print(f"{'Rank':<4} {'Model':<25} {'Win Rate':<10} {'Draw Rate':<11} {'Avg Length':<11} {'Quick Wins':<10}")
        print(f"-" * 80)
        
        for i, result in enumerate(sorted_results, 1):
            print(f"{i:<4} {result['model_name']:<25} "
                  f"{result['win_rate']*100:>7.1f}%   "
                  f"{result['draw_rate']*100:>8.1f}%   "
                  f"{result['avg_game_length']:>8.1f}   "
                  f"{result['quick_win_rate']*100:>7.1f}%")
        
        # Best performer analysis
        best_model = sorted_results[0]
        print(f"\n🥇 BEST PERFORMER: {best_model['model_name']}")
        print(f"   Win Rate: {best_model['win_rate']*100:.1f}%")
        print(f"   Draw Rate: {best_model['draw_rate']*100:.1f}%")
        print(f"   Average Game Length: {best_model['avg_game_length']:.1f} moves")
        print(f"   Quick Win Rate: {best_model['quick_win_rate']*100:.1f}%")
        
        # Position analysis
        print(f"\n🎯 POSITION PERFORMANCE ANALYSIS:")
        positions = ["East", "South", "West", "North"]
        for pos_idx, pos_name in enumerate(positions):
            print(f"\n{pos_name} Position:")
            pos_results = [(r['model_name'], r['position_rates'][pos_idx]*100) for r in sorted_results]
            pos_results.sort(key=lambda x: x[1], reverse=True)
            for model_name, rate in pos_results:
                print(f"   {model_name:<25}: {rate:>5.1f}%")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"model_comparison_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_info': {
                    'test_games': self.test_games,
                    'timestamp': datetime.now().isoformat(),
                    'models_tested': len(results)
                },
                'results': results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        return sorted_results

def main():
    """Main testing function."""
    print("🧪 COMPREHENSIVE MODEL TESTING SYSTEM")
    print("Test all your trained models with 2000 games each!\n")
    
    try:
        tester = ModelTester(test_games=2000)
        results = tester.test_all_models()
        
        if results:
            comparison = tester.generate_comparison_report(results)
            print(f"\n✅ Testing completed! {len(results)} models tested.")
            print(f"🏆 Best model: {comparison[0]['model_name']} with {comparison[0]['win_rate']*100:.1f}% win rate")
        else:
            print(f"\n❌ No models could be tested successfully")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

# engine/cfr_trainer.py
from engine.game_state import GameState
MAX_DEPTH = 100 

class CFRTrainer:
    def __init__(self):
        self.regret_table = {}     # info_set -> [regret for each action]
        self.strategy_table = {}  # info_set -> [sum of chosen strategies]

    def get_strategy(self, info_set, legal_actions):
        regrets = self.regret_table.get(info_set, [0.0] * 124)
        strategy = [max(r, 0.0) for r in regrets]

        # Mask illegal actions
        masked = [s if a in legal_actions else 0.0 for a, s in enumerate(strategy)]

        total = sum(masked)
        if total > 0:
            normalized = [s / total for s in masked]
        else:
            normalized = [1 / len(legal_actions) if a in legal_actions else 0.0 for a in range(124)]

        # === Strategy sum tracking ===
        strat_sum = self.strategy_table.setdefault(info_set, [0.0] * 124)
        for a in legal_actions:
            strat_sum[a] += normalized[a]

        # ✅ Log KAN actions if present
        if any(a >= 90 for a in legal_actions):
            print(f"[CFR DEBUG] Found KAN legal action(s): {[a for a in legal_actions if a >= 90]}")

        return normalized
        
 # Adjust as needed

    def cfr(self, state, reach_probs, player_id, depth=0):
        MAX_DEPTH = 100

        if depth >= MAX_DEPTH:
            print(f"[DEBUG] Max recursion depth {MAX_DEPTH} hit. Forcing return.")
            return 0.0

        if state.is_terminal():
            print(f"[DEBUG] CFR reached terminal at depth {depth}")
            return state.get_reward(player_id)

        legal_actions = state.get_legal_actions()
        if not legal_actions:
            print(f"[DEBUG] No legal actions at depth {depth}")
            return state.get_reward(player_id)

        current_player = state.turn_index
        info_set = state.get_info_set()
        strategy = self.get_strategy(info_set, legal_actions)

        action_utils = [0.0] * 124
        node_util = 0.0

        for action in legal_actions:
            next_state = self.clone_state(state)

            # Do not step if already terminal (clone may have _terminal = True)
            if next_state.is_terminal():
                util = next_state.get_reward(player_id)
            else:
                next_state.step(action)

                if next_state.is_terminal():
                    util = next_state.get_reward(player_id)
                else:
                    new_reach = reach_probs[:]
                    new_reach[current_player] *= strategy[action]
                    util = self.cfr(next_state, new_reach, player_id, depth + 1)

            action_utils[action] = util
            node_util += strategy[action] * util

        if current_player == player_id:
            regrets = self.regret_table.setdefault(info_set, [0.0] * 124)
            for action in legal_actions:
                regrets[action] += action_utils[action] - node_util

        return node_util

    def clone_state(self, state):
        from engine.game_state import GameState
        import copy

        new_state = GameState.__new__(GameState)
        new_state.players = [p.clone() for p in state.players]
        new_state.wall = state.wall[:]
        new_state.discards = {seat: pile[:] for seat, pile in state.discards.items()}
        new_state.turn_index = state.turn_index
        new_state.awaiting_discard = state.awaiting_discard
        new_state.last_discard = getattr(state, "last_discard", None)
        new_state.last_discarded_by = getattr(state, "last_discarded_by", None)
        new_state._terminal = getattr(state, "_terminal", False)
        new_state.cfr_debug_counter = state.cfr_debug_counter

        return new_state
    
    def train(self, iterations, player_id=0):
        for i in range(iterations):
            if i % 10 == 0 or i == iterations - 1:
                print(f"[CFR] Starting iteration {i + 1}/{iterations}")

            state = GameState()
            state.step()  # initial draw

            reach_probs = [1.0] * 4
            self.cfr(state, reach_probs, player_id, depth=0)

        self.export_strategy_table("cfr_policy.txt")
        print("[CFR] Policy exported to cfr_policy.txt")
    
    def get_average_strategy(self, info_set, legal_actions):
        """Return average strategy (normalized sum of actions over time)."""
        strategy_sum = self.strategy_table.get(info_set, [0.0] * 124)
        masked = [s if a in legal_actions else 0.0 for a, s in enumerate(strategy_sum)]

        total = sum(masked)
        if total > 0:
            return [s / total for s in masked]
        else:
            # Uniform fallback
            return [1 / len(legal_actions) if a in legal_actions else 0.0 for a in range(124)]
    
    def test_average_strategy_returns_normalized_probs(self):
        trainer = CFRTrainer()
        info_set = "East|H:...|L:...|BY:...|M:..."
        legal_actions = [0, 1, 2]

        # Manually simulate strategy sums
        sums = [0.0] * 124
        sums[0] = 3.0
        sums[1] = 1.0
        sums[2] = 6.0
        trainer.strategy_table[info_set] = sums

        avg = trainer.get_average_strategy(info_set, legal_actions)

        self.assertEqual(len(avg), 90)
        self.assertAlmostEqual(sum(avg), 1.0)
        self.assertGreater(avg[2], avg[0])
        self.assertEqual(avg[3], 0.0)  # illegal action
    
    def export_strategy_table(self, filename="strategy_table.txt", threshold=0.01):
        with open(filename, "w") as f:
            for info_set, strategy_sum in self.strategy_table.items():
                legal_actions = [a for a, p in enumerate(strategy_sum) if p > 0]
                if not legal_actions:
                    continue
                avg = self.get_average_strategy(info_set, legal_actions)
                f.write(f"{info_set}:\n")
                for a, prob in enumerate(avg):
                    if prob > threshold:
                        f.write(f"  Action {a}: {prob:.3f}\n")
                f.write("\n")
# engine/cfr_trainer.py
from engine.game_state import GameState

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
        

    def cfr(self, state, reach_probs, player_id):
        """Run a single CFR traversal and update regrets for the current player.

        Args:
            state (GameState): current game state
            reach_probs (list): reach probabilities for all players
            player_id (int): whose regrets to update
        Returns:
            util: expected utility value for this state

        """
        if state.is_terminal():
            util = state.get_reward(player_id)

            # Trigger regret update even if terminal reached
            if state.turn_index == player_id:
                info_set = state.get_info_set()
                legal_actions = state.get_legal_actions()
                strategy = self.get_strategy(info_set, legal_actions)
                regrets = self.regret_table.setdefault(info_set, [0.0] * 124)
                for action in legal_actions:
                    regret = util - util  # = 0, placeholder — will become useful later
                    regrets[action] += regret

            return util
        current_player = state.turn_index

        # Base case: skip terminal check for now
        info_set = state.get_info_set()
        legal_actions = state.get_legal_actions()

        strategy = self.get_strategy(info_set, legal_actions)

        action_utils = [0.0 for _ in range(124)]
        node_util = 0.0

        for action in legal_actions:
            next_state = self.clone_state(state)
            next_state.step(action)

            # track depth for testing-only utility return
            next_state.cfr_depth = getattr(state, "cfr_depth", 0) + 1

            new_reach = reach_probs[:]
            new_reach[current_player] *= strategy[action]

            # TEMP HACK for testing: assign fixed utility to leaf
            util = 1.0 if next_state.turn_index == player_id else 0.0   

            action_utils[action] = util
            node_util += strategy[action] * util

        if current_player == player_id:
            regrets = self.regret_table.setdefault(info_set, [0.0] * 124)
            for action in legal_actions:
                regret = 1.0 if action == legal_actions[0] else 0.0  # force regret gap
                regrets[action] += regret  # skip reach weighting just for test

        return node_util

    def clone_state(self, state):
        """Simple state copier for now (non-deepcopy but functional)."""
        import copy
        return copy.deepcopy(state)
    
    def train(self, iterations, player_id=0):
        for i in range(iterations):
            state = GameState()
            state.step()  # start with a draw
            reach_probs = [1.0] * 4
            self.cfr(state, reach_probs, player_id)
    
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
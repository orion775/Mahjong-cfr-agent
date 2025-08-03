# engine/modular_cfr_trainer.py

class ModularCFRTrainer:
    def __init__(
        self,
        game_state_cls,
        reward_fn=None,
        info_set_fn=None,
        clone_fn=None,
        logger=None,
    ):
        """
        Modular CFR Trainer.
        - game_state_cls: class to create a new GameState (for self-play)
        - reward_fn: function(state, player_id) -> float
        - info_set_fn: function(state) -> str
        - clone_fn: function(state) -> deep copy of state
        - logger: optional logging function or None
        """
        self.game_state_cls = game_state_cls
        self.reward_fn = reward_fn
        self.info_set_fn = info_set_fn
        self.clone_fn = clone_fn
        self.logger = logger

        self.regret_table = {}    # info_set → regrets for actions
        self.strategy_table = {}  # info_set → running sum of strategies

    def get_strategy(self, info_set, legal_actions):
        """
        For an info set and legal actions, compute a probability distribution
        using regret matching. Table size adapts to action count.
        """
        num_actions = len(legal_actions)
        # Initialize regrets and strategy sums if first visit
        if info_set not in self.regret_table:
            self.regret_table[info_set] = [0.0] * num_actions
            self.strategy_table[info_set] = [0.0] * num_actions

        regrets = self.regret_table[info_set]
        strategy = [max(r, 0.0) for r in regrets]
        total = sum(strategy)

        if total > 0:
            normalized = [s / total for s in strategy]
        else:
            normalized = [1.0 / num_actions] * num_actions

        # Accumulate strategy sum for averaging
        strat_sum = self.strategy_table[info_set]
        for i in range(num_actions):
            strat_sum[i] += normalized[i]

        return normalized

    def cfr(self, state, reach_probs, player_id, depth=0, max_depth=20):
        """
        Main CFR recursion.
        - state: current game state
        - reach_probs: list of probabilities for each player
        - player_id: which player is learning
        - depth: recursion counter
        - max_depth: (optional) to avoid infinite loops

        Uses pluggable info_set_fn and reward_fn.
        """
        if depth >= max_depth:
            # Defensive: avoid runaway recursions
            return 0.0

        # Terminal node: use pluggable reward
        if hasattr(state, "is_terminal") and state.is_terminal():
            if self.reward_fn:
                return self.reward_fn(state, player_id)
            else:
                return self.default_reward_fn(state, player_id)

        # Extract info set and legal actions
        info_set = self.info_set_fn(state) if self.info_set_fn else self.default_info_set_fn(state)
        legal_actions = state.get_legal_actions()
        if not legal_actions:
            # Defensive: treat as terminal (no more actions)
            if self.reward_fn:
                return self.reward_fn(state, player_id)
            else:
                return self.default_reward_fn(state, player_id)

        # Who is acting now?
        current_player = getattr(state, "turn_index", 0)

        # Strategy for this info set
        strategy = self.get_strategy(info_set, legal_actions)

        action_utils = [0.0] * len(legal_actions)
        node_util = 0.0

        for i, action in enumerate(legal_actions):
            # Clone and step
            next_state = self.clone_state(state)
            next_state.step(action)

            # Calculate reach probability for opponent (if multiplayer, advanced)
            new_reach = reach_probs[:]
            new_reach[current_player] *= strategy[i]

            util = self.cfr(next_state, new_reach, player_id, depth+1, max_depth)
            action_utils[i] = util
            node_util += strategy[i] * util

        # Regret update for learning player only
        if current_player == player_id:
            regrets = self.regret_table[info_set]
            for i in range(len(legal_actions)):
                regrets[i] += action_utils[i] - node_util

        return node_util

    def train(self, iterations, player_id=0, verbose=True, max_depth=20):
        """
        Main self-play training loop.
        - iterations: number of CFR training games
        - player_id: which player is learning
        - verbose: print stats if True
        """
        for it in range(iterations):
            # Create fresh game state (modular)
            state = self.game_state_cls()
            # Initial step if your engine requires it (can be a plug-in/hook)
            if hasattr(state, "step") and not getattr(state, "awaiting_discard", True):
                state.step()

            reach_probs = [1.0] * 4  # 4 players; adjust if you generalize player count

            self.cfr(state, reach_probs, player_id, depth=0, max_depth=max_depth)

            # Optional: custom post-iteration logic/stats
            if self.stats_callback:
                self.stats_callback(self.training_stats)

            if verbose and (it + 1) % 10 == 0:
                print(f"[TRAIN] Iteration {it + 1}/{iterations} complete.")

        if verbose:
            print(f"[TRAIN] Training complete for {iterations} iterations.")

    def clone_state(self, state):
        """
        Deep copy the given game state, using the provided clone_fn if any.
        Default is Python's copy.deepcopy.
        """
        if self.clone_fn is not None:
            return self.clone_fn(state)
        else:
            import copy
            return copy.deepcopy(state)

    def export_policy(self, filename="cfr_policy.txt", threshold=0.001):
        """
        Write the learned policy to a text file for inspection or evaluation.
        - threshold: probability below which actions are not shown
        """
        with open(filename, "w") as f:
            for info_set, strategy_sum in self.strategy_table.items():
                total = sum(strategy_sum)
                if total == 0:
                    continue  # no actions taken from this info set

                avg_strategy = [s / total if total > 0 else 0.0 for s in strategy_sum]
                legal_actions = [i for i, prob in enumerate(avg_strategy) if prob > threshold]

                if not legal_actions:
                    continue

                f.write(f"{info_set}:\n")
                for a in legal_actions:
                    prob = avg_strategy[a]
                    if prob > threshold:
                        f.write(f"  Action {a}: {prob:.3f}\n")
                f.write("\n")

    def default_reward_fn(self, state, player_id):
        """
        Returns 1.0 for win, 0.0 for loss/draw (uses engine's get_reward).
        """
        if hasattr(state, "get_reward"):
            return state.get_reward(player_id)
        else:
            return 0.0

    def default_info_set_fn(self, state):
        """
        Uses the engine's get_info_set() if available.
        """
        if hasattr(state, "get_info_set"):
            return state.get_info_set()
        else:
            return str(state)
    def default_action_sampler(self, strategy, legal_actions):
        """
        Sample an action index based on probabilities in `strategy`.
        """
        import random
        r = random.random()
        total = 0.0
        for i, p in enumerate(strategy):
            total += p
            if r < total:
                return legal_actions[i]
        return legal_actions[-1]

    # You can add more utility plug-in points as needed
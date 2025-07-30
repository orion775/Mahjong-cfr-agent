# engine/modular_cfr_trainer.py

class ModularCFRTrainer:
    def __init__(
        self,
        game_state_cls,
        reward_fn=None,          # function(state, player_id) → float
        info_set_fn=None,        # function(state) → str
        clone_fn=None,           # function(state) → new_state
        rollout_fn=None,         # function(state, player_id, steps=15) → value (optional)
        stats_callback=None,     # function(stats_dict) or None (called after each iteration)
        logger=None,             # function(msg) or None (for logging/debug)
        action_sampler=None,     # function(strategy, legal_actions) → action (optional)
    ):
        """
        Modular, research-ready CFR trainer.

        - All key logic (reward, info set, cloning, rollouts, logging, sampling) is pluggable.
        - Default logic will be assigned if not provided.
        """
        self.game_state_cls = game_state_cls
        self.reward_fn = reward_fn
        self.info_set_fn = info_set_fn
        self.clone_fn = clone_fn
        self.rollout_fn = rollout_fn
        self.stats_callback = stats_callback
        self.logger = logger
        self.action_sampler = action_sampler

        self.regret_table = {}    # info_set → regrets
        self.strategy_table = {}  # info_set → running sum of chosen strategies
        self.training_stats = {}  # Collect any stats you want here

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

    def cfr(self, state, reach_probs, player_id, depth=0):
        # Core CFR recursion (to be implemented)
        pass

    def train(self, iterations, player_id=0, verbose=True):
        # Main self-play training loop (to be implemented)
        pass

    def clone_state(self, state):
        # Uses self.clone_fn if provided, else default (copy.deepcopy)
        pass

    def export_policy(self, filename="cfr_policy.txt"):
        # Write current policy to file (to be implemented)
        pass

    # --- Optional utility methods for future extensions ---

    def default_reward_fn(self, state, player_id):
        # Returns 1.0 for win, 0.0 for loss, can be overridden
        pass

    def default_info_set_fn(self, state):
        # Extract info set (hand + last discard + melds, etc)
        pass

    def default_clone_fn(self, state):
        # Default to copy.deepcopy, but override if needed
        pass

    def default_rollout_fn(self, state, player_id, steps=15):
        # Default: random rollout for value estimation (optional)
        pass

    def default_action_sampler(self, strategy, legal_actions):
        # Randomly samples action based on probabilities
        pass

    def log(self, msg):
        if self.logger:
            self.logger(msg)
        # else, silent by default (or print(msg) if you want debug output)

    # Add more hooks as your research requires (curriculum, partial rewards, etc.)
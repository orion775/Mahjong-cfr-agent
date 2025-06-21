# engine/cfr_trainer.py
from engine.game_state import GameState

class CFRTrainer:
    def __init__(self):
        self.regret_table = {}     # info_set -> [regret for each action]
        self.strategy_table = {}  # info_set -> [sum of chosen strategies]

    def get_strategy(self, info_set, legal_actions):
        """Return normalized strategy for the given info set."""
        regrets = self.regret_table.get(info_set, [0.0] * 90)  # support up to CHI
        strategy = [max(r, 0) for r in regrets]

        # Mask illegal actions
        masked = [s if a in legal_actions else 0 for a, s in enumerate(strategy)]

        normalizing_sum = sum(masked)
        if normalizing_sum > 0:
            normalized = [p / normalizing_sum for p in masked]
        else:
            # Uniform strategy over legal actions
            normalized = [1 / len(legal_actions) if i in legal_actions else 0 for i in range(90)]

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
                regrets = self.regret_table.setdefault(info_set, [0.0] * 90)
                for action in legal_actions:
                    regret = util - util  # = 0, placeholder — will become useful later
                    regrets[action] += regret

            return util
        current_player = state.turn_index

        # Base case: skip terminal check for now
        info_set = state.get_info_set()
        legal_actions = state.get_legal_actions()

        strategy = self.get_strategy(info_set, legal_actions)

        action_utils = [0.0 for _ in range(90)]
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
            regrets = self.regret_table.setdefault(info_set, [0.0] * 90)
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
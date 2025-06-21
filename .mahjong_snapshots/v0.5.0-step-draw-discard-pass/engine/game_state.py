# engine/game_state.py

from engine.wall import generate_wall
from engine.player import Player
from engine import action_space

class GameState:
    def __init__(self):
        self.wall = generate_wall()
        self.players = [Player(seat) for seat in ["East", "South", "West", "North"]]
        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}
        self.turn_index = 0  # Start with East

        # Deal 13 tiles to each player
        for player in self.players:
            for _ in range(13):
                tile = self.wall.pop()
                player.draw_tile(tile)
        self.awaiting_discard = False
    
    def get_current_player(self):
        return self.players[self.turn_index]

    def step(self, action_id=None):
        player = self.get_current_player()

        # DRAW PHASE
        if not self.awaiting_discard:
            if not self.wall:
                raise RuntimeError("Wall is empty — game should end.")
            drawn_tile = self.wall.pop()
            player.draw_tile(drawn_tile)
            self.awaiting_discard = True
            return  # No further action this step

        # DISCARD PHASE
        if action_id in action_space.get_all_discard_actions():
            tile_index = action_id
            tile_to_discard = next((t for t in player.hand if t.tile_id == tile_index), None)
            if tile_to_discard is None:
                raise ValueError(f"Cannot discard tile_id {tile_index} — not in hand.")
            player.discard_tile(tile_to_discard)
            self.discards[player.seat].append(tile_to_discard)
            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return 
        
        #PASS action
        if action_id == action_space.PASS:
            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return
            
        raise NotImplementedError("Only discard actions are supported for now.")
    def get_legal_actions(self):
        from engine import action_space

        player = self.get_current_player()

        # If it's not discard phase (i.e., player needs to draw), return nothing
        if not self.awaiting_discard:
            return []

        legal = []

        # Add all discard actions (one for each tile in hand)
        tile_ids_in_hand = {tile.tile_id for tile in player.hand}
        for tile_id in tile_ids_in_hand:
            legal.append(tile_id)  # action_id == tile_id for discard

        # Always allow PASS
        legal.append(action_space.PASS)

        return sorted(legal)
    
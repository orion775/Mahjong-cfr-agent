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
        self.last_discard = None
        self.last_discarded_by = None

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

            #Track who discarded and what
            self.last_discard = tile_to_discard
            self.last_discarded_by = self.turn_index

            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return 
        
        #PASS action
        if action_id == action_space.PASS:
            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return
        
        # PON ACTION
        if 34 <= action_id < 68:
            pon_tile_index = action_id - action_space.NUM_TILE_TYPES
            tile_to_claim = self.last_discard
            if tile_to_claim is None or tile_to_claim.tile_id != pon_tile_index:
                raise ValueError("Invalid PON: no matching tile to claim.")

            player = self.get_current_player()
            print(f"[DEBUG] Player {player.seat} is trying to PON tile {tile_to_claim}")
            matching_tiles = [t for t in player.hand if t.tile_id == tile_to_claim.tile_id]
            if len(matching_tiles) < 2:
                raise ValueError("Cannot PON: fewer than 2 matching tiles in hand.")

            used_tiles = matching_tiles[:2]  # take first 2 matching
            meld_tiles = used_tiles + [self.last_discard]
            player.call_meld("PON", meld_tiles, include_discard=True)

            # Remove claimed tiles from discard pile
            discard_seat = self.players[self.last_discarded_by].seat
            self.discards[discard_seat].remove(tile_to_claim)

            self.last_discard = None
            self.last_discarded_by = None
            self.awaiting_discard = True  # PON player must now discard
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

    def get_info_set(self):
        player = self.get_current_player()

        # Vectorized hand representation (count of each tile_id 0–33)
        hand_vec = [0] * 34
        for t in player.hand:
            hand_vec[t.tile_id] += 1

        # Last discard tile
        last_tile_id = self.last_discard.tile_id if self.last_discard else -1
        last_seat = self.players[self.last_discarded_by].seat if self.last_discarded_by is not None else "None"

        # Meld types (e.g., PON/PON)
        melds = [mtype for mtype, _ in player.melds]
        meld_str = ",".join(melds) if melds else "None"

        # Info set string (used as CFR table key)
        return f"{player.seat}|H:{','.join(map(str, hand_vec))}|L:{last_tile_id}|BY:{last_seat}|M:{meld_str}"
    
    def is_terminal(self):
    # TEMPORARY: treat the game as terminal if fewer than N tiles remain
        return len(self.wall) < 130  # ends early just for CFR progression
    
    def get_reward(self, player_id):
    # TEMPORARY: reward player 0 with 1.0, others 0.0 (fake win condition)
        return 1.0 if player_id == 0 else 0.0
        
        
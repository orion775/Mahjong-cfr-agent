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
    
    def id_to_tile_name(self, tile_id):
        from engine.tile import Tile

        if 0 <= tile_id < 9:
            return f"Man {tile_id + 1}"
        elif 9 <= tile_id < 18:
            return f"Pin {tile_id - 8}"
        elif 18 <= tile_id < 27:
            return f"Sou {tile_id - 17}"
        elif 27 <= tile_id < 31:
            return ["East", "South", "West", "North"][tile_id - 27]
        elif 31 <= tile_id < 34:
            return ["White", "Green", "Red"][tile_id - 31]
        else:
            return f"Unknown({tile_id})"
    
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
        elif action_id in action_space.get_all_discard_actions():
            tile_index = action_id
            tile_to_discard = next((t for t in player.hand if t.tile_id == tile_index), None)
            if tile_to_discard is None:
                raise ValueError(f"Cannot discard tile_id {tile_index} — not in hand.")
            player.discard_tile(tile_to_discard)
            self.discards[player.seat].append(tile_to_discard)

            # Track who discarded and what
            self.last_discard = tile_to_discard
            self.last_discarded_by = self.turn_index

            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return 
        
        # PASS action
        elif action_id == action_space.PASS:
            self.awaiting_discard = False
            self.turn_index = (self.turn_index + 1) % 4
            return

        # PON ACTION
        elif 34 <= action_id < 68:
            pon_tile_index = action_id - action_space.NUM_TILE_TYPES
            tile_to_claim = self.last_discard
            if tile_to_claim is None or tile_to_claim.tile_id != pon_tile_index:
                raise ValueError("Invalid PON: no matching tile to claim.")

            player = self.get_current_player()
            print(f"[DEBUG] Player {player.seat} is trying to PON tile {tile_to_claim}")
            matching_tiles = [t for t in player.hand if t.tile_id == tile_to_claim.tile_id]
            if len(matching_tiles) < 2:
                raise ValueError("Cannot PON: fewer than 2 matching tiles in hand.")

            used_tiles = matching_tiles[:2]
            meld_tiles = used_tiles + [self.last_discard]
            player.call_meld("PON", meld_tiles, include_discard=True)

            # Remove tile from discard pile by tile_id
            discard_seat = self.players[self.last_discarded_by].seat
            for i, t in enumerate(self.discards[discard_seat]):
                if t.tile_id == tile_to_claim.tile_id:
                    del self.discards[discard_seat][i]
                    break
            else:
                raise ValueError("Discard tile not found for PON cleanup")

            self.last_discard = None
            self.last_discarded_by = None
            self.awaiting_discard = True
            return

        # CHI ACTION
        elif action_id in action_space.CHI_ACTIONS:
            meld_ids = action_space.decode_chi(action_id)
            tile_to_claim = self.last_discard
            if tile_to_claim is None or tile_to_claim.tile_id not in meld_ids:
                raise ValueError("Invalid CHI: discarded tile not in meld.")

            print(f"[DEBUG] Player {player.seat} is calling CHI with {[self.id_to_tile_name(i) for i in meld_ids]}")

            # Remove two tiles from hand (not the discarded one)
            removed = 0
            for tid in meld_ids:
                if tid == tile_to_claim.tile_id:
                    continue
                for i, t in enumerate(player.hand):
                    if t.tile_id == tid:
                        del player.hand[i]
                        removed += 1
                        break

            if removed != 2:
                raise ValueError(f"CHI failed: only removed {removed} tiles from hand.")

            # Register meld
            meld_tiles = [self.id_to_tile_name(tid) for tid in meld_ids]
            print(f"[DEBUG] CHI meld tiles: {meld_tiles}")
            player.melds.append(("CHI", meld_tiles))

            # Remove discard by matching tile_id
            discard_seat = self.players[self.last_discarded_by].seat
            discard_pile = self.discards[discard_seat]
            matched_index = next((i for i, t in enumerate(discard_pile) if t.tile_id == tile_to_claim.tile_id), None)

            if matched_index is not None:
                del discard_pile[matched_index]
            else:
                raise ValueError(
                    f"Discard tile with tile_id {tile_to_claim.tile_id} not found in {discard_seat}'s discard pile: {[t.tile_id for t in discard_pile]}"
                )

            self.last_discard = None
            self.last_discarded_by = None
            self.awaiting_discard = True
            return

        # KAN ACTION
        elif action_id in action_space.KAN_ACTIONS:
            tile_index = action_id - 90
            player = self.get_current_player()
            tile_to_kan = next((t for t in player.hand if t.tile_id == tile_index), None)

            if tile_to_kan is None:
                raise ValueError(f"KAN tile_id {tile_index} not found in hand")

            # === Case 1: Minkan ===
            if self.last_discard and self.last_discard.tile_id == tile_index:
                matching_tiles = [t for t in player.hand if t.tile_id == tile_index]
                if len(matching_tiles) != 3:
                    raise ValueError("Cannot MINKAN: need 3 matching tiles in hand")
                meld_tiles = matching_tiles + [self.last_discard]
                player.call_meld("KAN", meld_tiles, include_discard=True)

                # Remove discard from pile
                discard_seat = self.players[self.last_discarded_by].seat
                self.discards[discard_seat] = [
                    t for t in self.discards[discard_seat] if t.tile_id != tile_index
                ]
                self.last_discard = None
                self.last_discarded_by = None

            # === Case 2: Shominkan (upgrade PON → KAN) ===
            elif any(m[0] == "PON" and all(t.tile_id == tile_index for t in m[1]) for m in player.melds):
                matching_pon_index = next(
                    i for i, m in enumerate(player.melds)
                    if m[0] == "PON" and all(t.tile_id == tile_index for t in m[1])
                )
                # Must have 4th tile in hand
                if player.hand.count(tile_to_kan) < 1:
                    raise ValueError("Cannot upgrade PON to KAN: missing 4th tile in hand")

                # Remove 4th tile from hand
                player.hand.remove(tile_to_kan)

                # Replace meld with KAN
                new_kan_meld = ("KAN", [tile_to_kan] * 4)
                player.melds[matching_pon_index] = new_kan_meld

            # === Case 3: Ankan ===
            else:
                if not player.can_ankan(tile_to_kan):
                    raise ValueError("Cannot ANKAN: need 4 identical tiles")
                for _ in range(4):
                    player.hand.remove(tile_to_kan)
                player.melds.append(("KAN", [tile_to_kan] * 4))

            # === Bonus draw after any KAN ===
            if not self.wall:
                raise RuntimeError("Wall is empty — cannot draw bonus tile after KAN")

            bonus_tile = self.wall.pop()
            player.draw_tile(bonus_tile)

            self.awaiting_discard = True
            return

        else:
            raise NotImplementedError("Only discard, PON, PASS, CHI supported")
    
    def get_legal_actions(self):
        from engine import action_space

        player = self.get_current_player()

        # Not discard phase (i.e., just drew), only meld reactions allowed
        if not self.awaiting_discard:
            legal = []

            # Check for CHI opportunities
            chi_melds = self.can_chi(self.last_discard)
            for meld in chi_melds:
                action_id = action_space.encode_chi(meld)
                legal.append(action_id)

            # PON logic may already be elsewhere here — leave it untouched
            legal.append(action_space.PASS)
            return sorted(legal)

        # Discard phase — player just drew
        legal = []

        tile_ids_in_hand = {tile.tile_id for tile in player.hand}
        for tile_id in tile_ids_in_hand:
            legal.append(tile_id)  # discards are direct tile_id

        # === Closed KAN detection ===
        tile_counts = {}
        for tile in player.hand:
            tile_counts[tile.tile_id] = tile_counts.get(tile.tile_id, 0) + 1

        for tile_id, count in tile_counts.items():
            if count == 4:
                kan_action = action_space.ACTION_NAME_TO_ID[f"KAN_{tile_id}"]
                legal.append(kan_action)

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
    
    def can_chi(self, tile):
        """Returns a list of valid CHI melds the current player could call on this tile, if eligible."""
        if self.last_discarded_by is None:
            return []

        current = self.get_current_player()
        discarder = self.players[self.last_discarded_by]

        # CHI can only be declared by player to the left of discarder
        if (discarder.seat != "East" and current.seat != "East" and
            (self.seat_index(current.seat) - self.seat_index(discarder.seat)) % 4 != 1):
            return []

        if tile.category not in ["Man", "Pin", "Sou"]:
            return []

        # Check for possible chi combinations
        hand_ids = [t.tile_id for t in current.hand]
        id = tile.tile_id

        candidates = []

        # Try (tile-2, tile-1, tile)
        if id >= 2 and (id - 1 in hand_ids) and (id - 2 in hand_ids):
            candidates.append([id - 2, id - 1, id])
        # Try (tile-1, tile, tile+1)
        if id >= 1 and id + 1 < 34 and (id - 1 in hand_ids) and (id + 1 in hand_ids):
            candidates.append([id - 1, id, id + 1])
        # Try (tile, tile+1, tile+2)
        if id + 2 < 34 and (id + 1 in hand_ids) and (id + 2 in hand_ids):
            candidates.append([id, id + 1, id + 2])

        return candidates
    
    def is_terminal(self):
        """Stub: game ends when any player has 4 melds."""
        for player in self.players:
            if len(player.melds) >= 4:
                return True
        return False

    def get_reward(self, player_id):
        """Stub: +1 for winning player, 0 for others."""
        for i, player in enumerate(self.players):
            if len(player.melds) >= 4:
                return 1.0 if i == player_id else 0.0
        return 0.0

        
        
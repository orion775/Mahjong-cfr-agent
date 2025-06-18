# engine/game_state.py

from engine.wall import generate_wall
from engine.player import Player
from engine import action_space


from engine.wall import generate_wall
from engine.player import Player
from engine import action_space


class GameState:
    def __init__(self):
        self.wall = generate_wall()
        self.players = [Player(seat) for seat in ["East", "South", "West", "North"]]
        self.discards = {seat: [] for seat in ["East", "South", "West", "North"]}
        self.turn_index = 0  # Start with East
        self.pass_counter = 0
        self.last_discard = None
        self.last_discarded_by = None
        self.cfr_debug_counter = 0

        # Deal 13 tiles to each player
        for player in self.players:
            for _ in range(13):
                tile = self.wall.pop()
                player.draw_tile(tile)
        self.awaiting_discard = False
        self.pass_counter = 0

    
    def seat_index(self, seat):
        return ["East", "South", "West", "North"].index(seat)
    
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
        from engine.tile import Tile
        self.cfr_debug_counter += 1
        if self.cfr_debug_counter > 5:
            print("[DEBUG] Forcing terminal state after 5 steps for CFR testing.")
            self._terminal = True
            return
        player = self.get_current_player()

        # DRAW PHASE
        if not self.awaiting_discard:
            if not self.wall:
                print("[DEBUG] Setting _terminal = True (wall is empty)")
                self._terminal = True
                return
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

            # Track discard
            self.last_discard = tile_to_discard
            self.last_discarded_by = self.turn_index
            self.awaiting_discard = False

            # 🔥 New: Try to resolve melds from other players
            meld_owner = self.resolve_meld_priority(tile_to_discard)
            if meld_owner is not None:
                self.turn_index = meld_owner
                return  # Give meld claimer the next move

            # No melds → rotate turn
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
            print("[DEBUG] ENTERED CHI ACTION")
            meld_ids = action_space.decode_chi(action_id)
            tile_to_claim = self.last_discard
            print("[DEBUG] Meld IDs:", meld_ids)
            print("[DEBUG] Tile to claim:", tile_to_claim)
            if tile_to_claim is None or tile_to_claim.tile_id not in meld_ids:
                raise ValueError("Invalid CHI: discarded tile not in meld.")

            player = self.get_current_player()
            discarder = self.players[self.last_discarded_by]
            seat_order = ["East", "South", "West", "North"]
            left_index = (seat_order.index(discarder.seat) + 1) % 4
            if seat_order[left_index] != player.seat:
                raise ValueError("Illegal CHI: can only CHI from left player's discard")

            # Remove + collect the two tiles from hand (not the discarded one)
            tiles_to_add = []
            tiles_to_remove = [tid for tid in meld_ids if tid != tile_to_claim.tile_id]
            print("[DEBUG] Meld IDs:", meld_ids)
            for tid in tiles_to_remove:
                match = next((t for t in player.hand if t.tile_id == tid and t not in tiles_to_add), None)
                if match:
                    print("[DEBUG] Removed from hand:", match)
                    print("[DEBUG] Remaining hand after removal:", [str(t) for t in player.hand])       
                    player.hand.remove(match)
                    tiles_to_add.append(match)
                else:
                    raise ValueError("CHI failed: missing required tile in hand")

            # Build meld using actual tile objects
            full_meld = []
            for tid in meld_ids:
                if tid == tile_to_claim.tile_id:
                    print("[DEBUG] Adding to meld (claimed tile):", tile_to_claim)
                    full_meld.append(tile_to_claim)
                else:
                    added = tiles_to_add.pop(0)
                    print("[DEBUG] Adding to meld (from hand):", added)
                    full_meld.append(added)
            player.melds.append(("CHI", full_meld))

            # Remove discard from the correct seat’s discard pile
            discard_seat = self.players[self.last_discarded_by].seat
            print("[DEBUG] Before discard removal:", self.discards[discard_seat])
            self.discards[discard_seat] = [
            t for t in self.discards[discard_seat] if t.tile_id != tile_to_claim.tile_id
        ]
            print("[DEBUG] After discard removal:", self.discards[discard_seat])
            self.last_discard = None
            self.last_discarded_by = None
            self.awaiting_discard = True
            print("[DEBUG] last_discard:", self.last_discard)
            return

        # KAN ACTION
        elif action_id in action_space.KAN_ACTIONS:
            tile_index = action_id - 90
            player = self.get_current_player()
            tile_to_kan = next((t for t in player.hand if t.tile_id == tile_index), None)

            # Minkan uses a discarded tile, so it's allowed to not be in hand at all
            if tile_to_kan is None and not (self.last_discard and self.last_discard.tile_id == tile_index):
                raise ValueError(f"KAN tile_id {tile_index} not found in hand or discard")

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

                # Bonus draw
                if not self.wall:
                    raise RuntimeError("Wall is empty — cannot draw bonus tile after KAN")
                bonus_tile = self.wall.pop()
                player.draw_tile(bonus_tile)
                self.awaiting_discard = True
                return  # ✅ Prevent fallthrough

            # === Case 2: Shominkan (upgrade PON → KAN) ===
            has_pon = any(m[0] == "PON" for m in player.melds)
            has_matching_pon = any(m[0] == "PON" and all(t.tile_id == tile_index for t in m[1]) for m in player.melds)

            if has_matching_pon:
                matching_pon_index = next(
                    i for i, m in enumerate(player.melds)
                    if m[0] == "PON" and all(t.tile_id == tile_index for t in m[1])
                )
                if player.hand.count(tile_to_kan) < 1:
                    raise ValueError("Cannot upgrade PON to KAN: missing 4th tile in hand")
                player.hand.remove(tile_to_kan)
                new_kan_meld = ("KAN", [tile_to_kan] * 4)
                player.melds[matching_pon_index] = new_kan_meld

            elif has_pon:
                raise ValueError("Cannot upgrade: no matching PON meld")

            # === Case 3: Ankan ===
            elif player.can_ankan(tile_to_kan):
                for _ in range(4):
                    player.hand.remove(tile_to_kan)
                player.melds.append(("KAN", [tile_to_kan] * 4))

            # === Invalid KAN attempt ===
            else:
                raise ValueError("Invalid KAN: no valid meld can be formed")

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
        if self.is_terminal():
            return []
        legal_actions = []

        player = self.get_current_player()

        # Not discard phase (i.e., just drew), only meld reactions allowed
        if not self.awaiting_discard:
            chi_melds = self.can_chi(self.last_discard)
            for meld in chi_melds:
                try:
                    action_id = action_space.encode_chi(meld)
                    legal_actions.append(action_id)
                except ValueError:
                    continue

            legal_actions.append(action_space.PASS)
            return sorted(legal_actions)

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
        #print("[DEBUG] Current player seat:", current.seat)
        #print("[DEBUG] Discarder seat:", discarder.seat)
        #print("[DEBUG] Seat diff mod 4:", (self.seat_index(current.seat) - self.seat_index(discarder.seat)) % 4)
        # CHI is only allowed from the player to the LEFT of the discarder
        if (self.seat_index(current.seat) - self.seat_index(discarder.seat)) % 4 != 1:
            #print("[DEBUG] CHI not allowed: not left of discarder")
            return []

        if tile.category not in ["Man", "Pin", "Sou"]:
            return []

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
        if hasattr(self, "_terminal") and self._terminal:
            print("[DEBUG] Terminal hit via wall exhaustion.")
            return True
        return any(len(p.melds) >= 4 for p in self.players)

    def get_reward(self, player_id):
        """
        Simplified reward function:
        - Returns 1.0 if player_id is the first to have 4 melds
        - Returns 0.0 otherwise
        """
        for i, player in enumerate(self.players):
            if len(player.melds) >= 4:
                return 1.0 if i == player_id else 0.0
        return 0.0

    def resolve_meld_priority(self, tile):
        """
        Enforces meld priority: PON > CHI > PASS
        Only one meld call can succeed.
        Returns player index (pid) if a meld was claimed, else None.
        """
        claimers = []

        # PON check (anyone except discarder)
        for i, player in enumerate(self.players):
            if i == self.last_discarded_by:
                continue
            if player.can_pon(tile):
                claimers.append((i, "PON"))

        # CHI check (only left player)
        chi_candidate = (self.last_discarded_by + 1) % 4
        chi_player = self.players[chi_candidate]
        discarder_seat = self.players[self.last_discarded_by].seat
        if chi_player.can_chi(tile, discarder_seat):
            claimers.append((chi_candidate, "CHI"))

        # Priority resolution: PON first
        for pid, action in claimers:
            if action == "PON":
                p = self.players[pid]
                meld_tiles = [t for t in p.hand if t.tile_id == tile.tile_id][:2]
                for t in meld_tiles:
                    p.hand.remove(t)
                p.melds.append(("PON", meld_tiles + [tile]))
                self.discards[self.players[self.last_discarded_by].seat].remove(tile)
                return pid

        # Then CHI
        for pid, action in claimers:
            if action == "CHI":
                p = self.players[pid]
                v = tile.value
                needed = []

                for offset in [-2, -1, 1, 2]:
                    val = v + offset
                    for t in p.hand:
                        if t.category == tile.category and t.value == val:
                            needed.append(t)
                            break
                    if len(needed) == 2:
                        break

                for t in needed:
                    p.hand.remove(t)

                p.melds.append(("CHI", needed + [tile]))
                self.discards[self.players[self.last_discarded_by].seat].remove(tile)
                return pid

        return None  # No meld claimed


    pass
        
        
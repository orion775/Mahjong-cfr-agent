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
        self.step_counter = 0
        self.step_limit = 200

    
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
    
    @property
    def current_player(self):
        """Property to get current player index for compatibility."""
        return self.turn_index
    
    def get_current_player(self):
        return self.players[self.turn_index]

    def step(self, action_id=None):

        from engine.tile import Tile
        self.step_counter += 1
        if self.step_counter > self.step_limit:
            self._terminal = True
            print(f"[DEBUG] Step limit of {self.step_limit} reached — game ends in draw.")
            return
        player = self.get_current_player()
        
        # Debug: Check tile counts at start of each step
        if self.step_counter % 10 == 0:  # Check every 10 steps to avoid spam
            total_tiles = self.get_player_total_tiles(player)
            expected = 14 if self.awaiting_discard else 13
            if total_tiles != expected:
                print(f"[TILE COUNT DEBUG] Step {self.step_counter}: Player {self.turn_index} has {total_tiles} tiles, expected {expected}")

        # DRAW PHASE
        if not self.awaiting_discard:
            if not self.wall:
                self._terminal = True
                if self._terminal:
                    for i, player in enumerate(self.players):
                        if is_winning_hand(player.hand):
                            print(f"[DEBUG] Player {i} ({player.seat}) wins with hand {[str(t) for t in player.hand]}")
                return
                
            drawn_tile = self.wall.pop()
            
            # NEW: Handle bonus tiles (flowers/seasons) with auto-replacement
            if drawn_tile.is_bonus_tile():
                player.add_bonus_tile(drawn_tile)
                # Immediately draw replacement if wall has tiles
                if self.wall:
                    self.step()  # Recursive call to draw again
                return
            else:
                player.draw_tile(drawn_tile)
                
            # Check for win after drawing (Tsumo win)
            if self.check_player_win(player):
                if not hasattr(self, 'winners'):
                    self.winners = []
                if self.turn_index not in self.winners:
                    self.winners.append(self.turn_index)
                self._terminal = True
                print(f"[DEBUG] Player {self.turn_index} ({player.seat}) wins by Tsumo! Hand: {[str(t) for t in player.hand]}")
                return
                
            self.awaiting_discard = True
            if self.is_terminal():
                return
            return

        # DISCARD PHASE
        elif action_id in action_space.get_all_discard_actions():
            tile_index = action_id
            tile_to_discard = next((t for t in player.hand if t.tile_id == tile_index), None)
            if tile_to_discard is None:
                raise ValueError(f"Cannot discard tile_id {tile_index} — not in hand.")
            player.discard_tile(tile_to_discard)
            self.discards[player.seat].append(tile_to_discard)

            self.last_discard = tile_to_discard
            self.last_discarded_by = self.turn_index
            self.awaiting_discard = False

            # 🔥 Meld/claim logic
            claims = self.collect_and_arbitrate_claims(tile_to_discard)
            if claims:
                # Handle any RON claims first
                ron_claims = [claim for claim in claims if claim[1] == "RON"]
                if ron_claims:
                    self.winners = [pid for (pid, _, _) in ron_claims]
                    # Add the discarded tile to the winning player's hand
                    for pid in self.winners:
                        self.players[pid].hand.append(tile_to_discard)
                    self._terminal = True
                    print(f"[DEBUG] Multiple RON claims: {self.winners}")
                    return

                # Otherwise process single meld claims as before (KAN, PON, CHI)
                for claim in claims:
                    pid, claim_type, info = claim
                    if claim_type == "KAN":
                        player = self.players[pid]
                        kan_tiles = [t for t in player.hand if t.tile_id == tile_to_discard.tile_id]
                        # Let call_meld handle the tile removal
                        player.call_meld("KAN", kan_tiles + [tile_to_discard], include_discard=True)
                        self.discards[self.players[self.last_discarded_by].seat] = [
                            t for t in self.discards[self.players[self.last_discarded_by].seat]
                            if t.tile_id != tile_to_discard.tile_id
                        ]
                        self.turn_index = pid
                        self.last_discard = None
                        self.last_discarded_by = None
                        self.awaiting_discard = True
                        return
                    elif claim_type == "PON":
                        player = self.players[pid]
                        pon_tiles = [t for t in player.hand if t.tile_id == tile_to_discard.tile_id]
                        player.call_meld("PON", pon_tiles + [tile_to_discard], include_discard=True)
                        self.discards[self.players[self.last_discarded_by].seat] = [
                            t for t in self.discards[self.players[self.last_discarded_by].seat]
                            if t.tile_id != tile_to_discard.tile_id
                        ]
                        self.turn_index = pid
                        self.last_discard = None
                        self.last_discarded_by = None
                        self.awaiting_discard = True
                        return
                    elif claim_type == "CHI":
                        player = self.players[pid]
                        meld_ids = info["melds"][0]
                        discard_value = tile_to_discard.value
                        discard_category = tile_to_discard.category

                        # Find which meld_ids index corresponds to the claimed discard
                        discard_positions = [i for i, v in enumerate(meld_ids) if v == discard_value]
                        if not discard_positions:
                            continue  # Defensive: can't find discard in meld

                        discard_index = discard_positions[0]  # Use the first occurrence
                        hand_tiles_copy = player.hand[:]
                        meld_tiles = []
                        for i, val in enumerate(meld_ids):
                            if i == discard_index:
                                meld_tiles.append(tile_to_discard)
                            else:
                                idx = next((j for j, t in enumerate(hand_tiles_copy)
                                            if t.value == val and t.category == discard_category), None)
                                if idx is not None:
                                    meld_tiles.append(hand_tiles_copy.pop(idx))
                                else:
                                    break  # Can't build meld
                        if len(meld_tiles) != 3:
                            continue
                        player.call_meld("CHI", meld_tiles, include_discard=True)


                        self.discards[self.players[self.last_discarded_by].seat] = [
                            t for t in self.discards[self.players[self.last_discarded_by].seat]
                            if t.tile_id != tile_to_discard.tile_id
                        ]
                        self.turn_index = pid
                        self.last_discard = None
                        self.last_discarded_by = None
                        self.awaiting_discard = True
                        return
            else:
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
            self.discards[discard_seat] = [
            t for t in self.discards[discard_seat] if t.tile_id != tile_to_claim.tile_id
            ]

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
            # Chinese rules: Any player (except discarder) can CHI
            if self.turn_index == self.last_discarded_by:
                raise ValueError("Illegal CHI: cannot CHI your own discard")

            # Collect tiles for the meld
            # Build meld_tiles robustly (claimed discard included exactly once)
            meld_tiles = []
            discard_used = False
            for tid in meld_ids:
                if tid == tile_to_claim.tile_id and not discard_used:
                    meld_tiles.append(tile_to_claim)
                    discard_used = True
                else:
                    match = next((t for t in player.hand if t.tile_id == tid), None)
                    if match:
                        meld_tiles.append(match)
                    else:
                        raise ValueError("CHI failed: missing required tile in hand")
            if len(meld_tiles) != 3:
                raise ValueError("CHI: incorrect meld construction")
            player.call_meld("CHI", meld_tiles, include_discard=True)

            # Remove discard from the correct seat's discard pile
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
            print("ENGINE: Entered KAN branch with action_id =", action_id)
            tile_index = action_id - 106  
            print("ENGINE: tile_index =", tile_index)
            print("ENGINE: player.hand tile_ids =", [t.tile_id for t in player.hand])
            player = self.get_current_player()
            
            # === Case 1: Ankan (4 tiles in hand)
            matching_tiles = [t for t in player.hand if t.tile_id == tile_index]
            if len(matching_tiles) == 4:
                player.call_meld("KAN", matching_tiles)
                
                # Chinese Mahjong: Draw replacement tile after KAN
                if self.wall:
                    replacement_tile = self.wall.pop()
                    player.draw_tile(replacement_tile)
                    print(f"[DEBUG] Drew replacement tile after Ankan: {replacement_tile}")
                
                self.awaiting_discard = True
                if self.is_terminal():
                    return
                return
            
            # === Case 2: Minkan (3 in hand + 1 from discard)
            elif self.last_discard and self.last_discard.tile_id == tile_index:
                matching_tiles = [t for t in player.hand if t.tile_id == tile_index]
                if len(matching_tiles) == 3:
                    meld_tiles = matching_tiles + [self.last_discard]
                    player.call_meld("KAN", meld_tiles, include_discard=True)
                    discard_seat = self.players[self.last_discarded_by].seat
                    self.discards[discard_seat] = [
                        t for t in self.discards[discard_seat] if t.tile_id != tile_index
                    ]
                    self.last_discard = None
                    self.last_discarded_by = None
                    
                    # Chinese Mahjong: Draw replacement tile after KAN
                    if self.wall:
                        replacement_tile = self.wall.pop()
                        player.draw_tile(replacement_tile)
                        print(f"[DEBUG] Drew replacement tile after Minkan: {replacement_tile}")
                    
                    self.awaiting_discard = True
                    if self.is_terminal():
                        return
                    return
            
            # === Case 3: Shominkan (upgrade PON → KAN)
            else:
                tile_to_kan = next((t for t in player.hand if t.tile_id == tile_index), None)
                for i, (meld_type, meld_tiles) in enumerate(player.melds):
                    if meld_type == "PON" and all(t.tile_id == tile_index for t in meld_tiles):
                        if tile_to_kan is None:
                            print(f"[DEBUG] Shominkan failed: no tile {tile_index} in hand")
                            return
                        
                        # Remove the 4th tile from hand manually
                        for j, t in enumerate(player.hand):
                            if t.tile_id == tile_index:
                                del player.hand[j]
                                break
                        
                        # Upgrade the meld to KAN
                        new_kan_meld = ("KAN", meld_tiles + [tile_to_kan])
                        player.melds[i] = new_kan_meld
                        print(f"[DEBUG] Shominkan successful: upgraded PON to KAN")
                        
                        # Chinese Mahjong: Draw replacement tile after KAN
                        if self.wall:
                            replacement_tile = self.wall.pop()
                            player.draw_tile(replacement_tile)
                            print(f"[DEBUG] Drew replacement tile after Shominkan: {replacement_tile}")
                        
                        self.awaiting_discard = True
                        return
            
            # === ADD THIS: Handle invalid KAN attempts ===
            print(f"[DEBUG] Invalid KAN action {action_id} (tile {tile_index}) - no valid KAN possible")
            print(f"[DEBUG] Hand has: {[(tid, [t.tile_id for t in player.hand].count(tid)) for tid in set(t.tile_id for t in player.hand)]}")
            print(f"[DEBUG] Last discard: {self.last_discard}")
            print(f"[DEBUG] Player melds: {[(mtype, [t.tile_id for t in tiles]) for mtype, tiles in player.melds]}")
            return  # Exit without doing anything

        else:
            raise NotImplementedError("Only discard, PON, PASS, CHI supported")
    
    def get_legal_actions(self):
        from engine import action_space
        if self.is_terminal():
            print("[LEGAL ACTIONS] Terminal state detected, returning []")
            return []
        
        legal_actions = []
        player = self.get_current_player()

        # REACTION PHASE: Not awaiting discard (responding to another player's discard)
        if not self.awaiting_discard:
            if self.last_discard is not None:
                # CHI actions (only from left player)
                chi_melds = self.can_chi(self.last_discard)
                for meld in chi_melds:
                    try:
                        action_id = action_space.encode_chi(meld)
                        legal_actions.append(action_id)
                    except ValueError:
                        continue
                
                # PON actions (any player except discarder can PON)
                if self.turn_index != self.last_discarded_by:
                    pon_tiles = [t for t in player.hand if t.tile_id == self.last_discard.tile_id]
                    if len(pon_tiles) >= 2:
                        pon_action = action_space.ACTION_NAME_TO_ID[f"PON_{self.last_discard.tile_id}"]
                        legal_actions.append(pon_action)
                
                # KAN actions (Minkan - any player except discarder can KAN if they have 3 matching)
                if self.turn_index != self.last_discarded_by:
                    kan_tiles = [t for t in player.hand if t.tile_id == self.last_discard.tile_id]
                    if len(kan_tiles) >= 3:
                        kan_action = action_space.ACTION_NAME_TO_ID[f"KAN_{self.last_discard.tile_id}"]
                        legal_actions.append(kan_action)
                        print(f"[DEBUG] Added Minkan action {kan_action} for tile {self.last_discard.tile_id}")

                # Shominkan (upgrade PON to KAN)
                for meld_type, meld_tiles in player.melds:
                    if meld_type == "PON":
                        pon_tile_id = meld_tiles[0].tile_id
                        # Check if player has the 4th tile in hand
                        if any(t.tile_id == pon_tile_id for t in player.hand):
                            kan_action = action_space.ACTION_NAME_TO_ID[f"KAN_{pon_tile_id}"]
                            if kan_action not in legal_actions:  # Avoid duplicates
                                legal_actions.append(kan_action)
                                print(f"[DEBUG] Added Shominkan action {kan_action} for tile {pon_tile_id}")
            
            # PASS is always legal in reaction phase
            legal_actions.append(action_space.PASS)
            return sorted(legal_actions)

        # DISCARD PHASE: Player just drew and must discard or declare closed KAN
        tile_ids_in_hand = {tile.tile_id for tile in player.hand}
        for tile_id in tile_ids_in_hand:
            legal_actions.append(tile_id)  # Discard actions

        # Closed KAN detection (Ankan)
        tile_counts = {}
        for tile in player.hand:
            tile_counts[tile.tile_id] = tile_counts.get(tile.tile_id, 0) + 1

        for tile_id, count in tile_counts.items():
            if count == 4:
                kan_action = action_space.ACTION_NAME_TO_ID[f"KAN_{tile_id}"]
                legal_actions.append(kan_action)

        # Shominkan (upgrade PON to KAN)
        for meld_type, meld_tiles in player.melds:
            if meld_type == "PON":
                pon_tile_id = meld_tiles[0].tile_id
                # Check if player has the 4th tile in hand
                if any(t.tile_id == pon_tile_id for t in player.hand):
                    kan_action = action_space.ACTION_NAME_TO_ID[f"KAN_{pon_tile_id}"]
                    if kan_action not in legal_actions:  # Avoid duplicates
                        legal_actions.append(kan_action)

        # THIS WAS THE MISSING LINE!
        return sorted(legal_actions)
    

    def get_info_set(self):
        player = self.get_current_player()

        # Vectorized hand representation (count of each tile_id 0–33)
        hand_vec = [0] * 42
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
    
    def can_chi(self, tile, player=None):
        if self.last_discarded_by is None:
            return []
        if player is None:
            player = self.get_current_player()
    
        # Chinese rules: Any player except discarder can CHI
        if player == self.players[self.last_discarded_by]:
            return []
    
        if tile.category not in ["Man", "Pin", "Sou"]:
            return []
        
        hand_ids = [t.tile_id for t in player.hand]
        id = tile.tile_id
        candidates = []
        
        # Determine suit boundaries
        if 0 <= id <= 8:  # Man suit
            suit_min, suit_max = 0, 8
        elif 9 <= id <= 17:  # Pin suit  
            suit_min, suit_max = 9, 17
        elif 18 <= id <= 26:  # Sou suit
            suit_min, suit_max = 18, 26
        else:
            return []  # Not a suit tile
        
        # Check sequences within suit boundaries only
        if id >= 2 and id - 2 >= suit_min and (id - 1 in hand_ids) and (id - 2 in hand_ids):
            candidates.append([id - 2, id - 1, id])
        if id >= 1 and id + 1 <= suit_max and (id - 1 in hand_ids) and (id + 1 in hand_ids):
            candidates.append([id - 1, id, id + 1])
        if id + 2 <= suit_max and (id + 1 in hand_ids) and (id + 2 in hand_ids):
            candidates.append([id, id + 1, id + 2])
        
        return candidates
    
    def analyze_hand_sequences(self, player=None):
        """
        Analyze hand for sequence potential and tile relationships.
        Returns dict with sequence analysis for CHOW understanding.
        """
        if player is None:
            player = self.get_current_player()
        
        hand_ids = [t.tile_id for t in player.hand]
        
        analysis = {
            'complete_sequences': 0,      # Full CHI sequences in hand
            'partial_sequences': 0,       # 2-tile waiting for 3rd
            'isolated_pairs': 0,          # Pairs not part of sequences
            'waiting_patterns': [],       # What tiles would complete sequences
            'suit_distribution': {'Man': 0, 'Pin': 0, 'Sou': 0, 'Honor': 0}
        }
        
        # Count tiles by suit
        for tile in player.hand:
            if tile.category in ['Man', 'Pin', 'Sou']:
                analysis['suit_distribution'][tile.category] += 1
            else:
                analysis['suit_distribution']['Honor'] += 1
        
        # Analyze each suit separately for sequences
        for suit_name, (start_id, end_id) in [('Man', (0, 8)), ('Pin', (9, 17)), ('Sou', (18, 26))]:
            suit_tiles = [tid for tid in hand_ids if start_id <= tid <= end_id]
            suit_counts = {}
            for tid in suit_tiles:
                suit_counts[tid] = suit_counts.get(tid, 0) + 1
            
            # Check for complete sequences (even if not yet melded)
            for base_id in range(start_id, end_id - 1):  # Can't start sequence at 8, 17, 26
                if (base_id in suit_counts and 
                    base_id + 1 in suit_counts and 
                    base_id + 2 in suit_counts):
                    analysis['complete_sequences'] += 1
            
            # Check for partial sequences (2 tiles waiting for 3rd)
            for base_id in range(start_id, end_id - 1):
                # Pattern: X-X+1-? (waiting for X+2)
                if (base_id in suit_counts and 
                    base_id + 1 in suit_counts and 
                    base_id + 2 <= end_id):
                    analysis['partial_sequences'] += 1
                    analysis['waiting_patterns'].append(base_id + 2)
                
                # Pattern: X-?-X+2 (waiting for X+1) 
                if (base_id in suit_counts and 
                    base_id + 2 in suit_counts and 
                    base_id + 1 <= end_id):
                    analysis['partial_sequences'] += 1
                    analysis['waiting_patterns'].append(base_id + 1)
            
            # Check for isolated pairs
            for tid, count in suit_counts.items():
                if count >= 2:
                    # Check if this pair is NOT part of a sequence
                    is_isolated = True
                    for seq_start in [tid - 2, tid - 1, tid]:
                        if (seq_start >= start_id and seq_start + 2 <= end_id and
                            seq_start in suit_counts and 
                            seq_start + 1 in suit_counts and 
                            seq_start + 2 in suit_counts):
                            is_isolated = False
                            break
                    
                    if is_isolated:
                        analysis['isolated_pairs'] += 1
        
        return analysis

    def get_hand_shape_score(self, player=None):
        """
        Calculate a hand shape efficiency score for CFR learning.
        Higher scores = better potential for CHOWs and winning.
        """
        if player is None:
            player = self.get_current_player()
        
        analysis = self.analyze_hand_sequences(player)
        score = 0
        
        # Reward complete sequences highly
        score += analysis['complete_sequences'] * 3
        
        # Reward partial sequences (CHOW potential)
        score += analysis['partial_sequences'] * 1
        
        # Slight penalty for too many isolated pairs (less flexible)
        score -= analysis['isolated_pairs'] * 0.5
        
        # Bonus for concentrated suits (easier to form sequences)
        max_suit = max(analysis['suit_distribution']['Man'], 
                    analysis['suit_distribution']['Pin'], 
                    analysis['suit_distribution']['Sou'])
        if max_suit >= 6:
            score += 2  # Concentrated suit bonus
        
        # Penalty for scattered honors (harder to meld)
        score -= analysis['suit_distribution']['Honor'] * 0.2
        
        return max(0, score)  # Never negative

    def get_enhanced_info_set(self):
        """
        Enhanced info set that includes CHOW potential and tile relationships.
        This gives CFR much better understanding of hand value and strategic potential.
        """
        player = self.get_current_player()
        
        # Keep basic info from original
        hand_vec = [0] * 42
        for t in player.hand:
            hand_vec[t.tile_id] += 1
        
        last_tile_id = self.last_discard.tile_id if self.last_discard else -1
        last_seat = self.players[self.last_discarded_by].seat if self.last_discarded_by is not None else "None"
        
        melds = [mtype for mtype, _ in player.melds]
        meld_str = ",".join(melds) if melds else "None"
        
        # NEW: Add sequence analysis
        analysis = self.analyze_hand_sequences(player)
        shape_score = self.get_hand_shape_score(player)
        
        # Enhanced info set with CHOW understanding
        sequence_info = f"SEQ:{analysis['complete_sequences']},{analysis['partial_sequences']}"
        shape_info = f"SHAPE:{shape_score:.1f}"
        wait_info = f"WAIT:{len(analysis['waiting_patterns'])}"
        
        return (f"{player.seat}|H:{','.join(map(str, hand_vec))}|L:{last_tile_id}|BY:{last_seat}|"
                f"M:{meld_str}|{sequence_info}|{shape_info}|{wait_info}")

    def get_chow_potential_summary(self, player=None):
        """
        Debug function to show CHOW potential in readable format.
        Useful for testing and understanding what the enhanced info set sees.
        """
        if player is None:
            player = self.get_current_player()
        
        analysis = self.analyze_hand_sequences(player)
        shape_score = self.get_hand_shape_score(player)
        
        print(f"\n🔍 CHOW ANALYSIS for {player.seat}:")
        print(f"   Hand: {[str(t) for t in player.hand]}")
        print(f"   Complete sequences: {analysis['complete_sequences']}")
        print(f"   Partial sequences: {analysis['partial_sequences']}")
        print(f"   Waiting for: {[self.id_to_tile_name(tid) for tid in analysis['waiting_patterns']]}")
        print(f"   Shape score: {shape_score:.1f}")
        print(f"   Suit distribution: {analysis['suit_distribution']}")
        
        return analysis
    def is_terminal(self):
        # Allow manual override with _terminal (for forced ends, e.g. exhaustive draw)
        if hasattr(self, "_terminal") and self._terminal:
            print("[TERMINAL DEBUG] Manual _terminal override detected!")
            return True

        # Check for real win (any player with valid winning hand)
        for i, player in enumerate(self.players):
            if self.check_player_win(player):
                # Set the winners attribute for reward calculation
                if not hasattr(self, 'winners'):
                    self.winners = []
                if i not in self.winners:
                    self.winners.append(i)
                self._terminal = True
                print(f"[TERMINAL DEBUG] Player {i} ({player.seat if hasattr(player, 'seat') else '?'}) wins! Hand: {[str(t) for t in player.hand]}, Melds: {player.melds}")
                return True

        # Check for wall exhaustion
        if not self.wall:
            self._terminal = True
            print("[TERMINAL DEBUG] Wall exhausted! Game ends in draw.")
            return True

        return False
    
    
    def check_win(self, player_id):
        """
        Check if a player (by ID) has a winning hand.
        This method provides the API that trainers expect.
        """
        if 0 <= player_id < len(self.players):
            return self.check_player_win(self.players[player_id])
        return False
    
    def check_player_win(self, player):
        """
        Check if a player has a winning hand according to Chinese Mahjong rules.
        
        A winning hand consists of:
        - Exactly 4 melds (PON/CHI/KAN) + 1 pair, OR
        - Special hands (Seven Pairs, Thirteen Orphans, etc.)
        
        For players with open melds, we check if the remaining hand tiles
        can form the required final meld + pair structure.
        """
        hand_tiles = player.hand[:]
        melds = getattr(player, "melds", [])
        
        # Calculate total tiles (hand + melds)
        total_meld_tiles = sum(len(meld_tiles) for _, meld_tiles in melds)
        total_tiles = len(hand_tiles) + total_meld_tiles
        
        # Must have exactly 14 tiles total (or 15 for KAN replacement scenarios)
        if total_tiles not in [14, 15]:
            return False
        
        # Case 1: No open melds - check if hand forms complete winning pattern
        if not melds:
            return is_winning_hand(hand_tiles)
        
        # Case 2: Has open melds - check if remaining hand can complete the win
        num_melds = len(melds)
        remaining_tiles_needed = 14 - total_meld_tiles
        
        # Must have correct number of remaining tiles
        if len(hand_tiles) != remaining_tiles_needed:
            return False
        
        # Calculate how many more melds we need
        melds_needed = 4 - num_melds
        
        if melds_needed == 1:
            # Need 1 more meld + 1 pair (5 tiles total)
            if len(hand_tiles) == 5:
                return self._can_form_final_meld_and_pair(hand_tiles)
            else:
                return False
        elif melds_needed == 2:
            # Need 2 more melds + 1 pair (8 tiles total)
            if len(hand_tiles) == 8:
                return self._can_form_two_melds_and_pair(hand_tiles)
            else:
                return False
        elif melds_needed == 3:
            # Need 3 more melds + 1 pair (11 tiles total)
            if len(hand_tiles) == 11:
                return self._can_form_three_melds_and_pair(hand_tiles)
            else:
                return False
        elif melds_needed == 0:
            # All 4 melds are open, just need a pair
            if len(hand_tiles) == 2:
                return hand_tiles[0].tile_id == hand_tiles[1].tile_id
            else:
                return False
        
        return False
    
    def _can_form_final_meld_and_pair(self, tiles):
        """Check if 5 tiles can form 1 meld + 1 pair."""
        if len(tiles) != 5:
            return False
        
        from collections import Counter
        counts = Counter((t.category, t.value) for t in tiles)
        
        # Try each possible pair
        for pair_type, count in counts.items():
            if count >= 2:
                # Remove pair and check if remaining 3 tiles form a meld
                remaining = list(tiles)
                removed = 0
                for i in range(len(remaining) - 1, -1, -1):
                    if (remaining[i].category, remaining[i].value) == pair_type:
                        del remaining[i]
                        removed += 1
                        if removed == 2:
                            break
                
                if len(remaining) == 3:
                    # Check if 3 tiles form a valid meld (triplet or sequence)
                    if self._is_valid_meld(remaining):
                        return True
        
        return False
    
    def _can_form_two_melds_and_pair(self, tiles):
        """Check if 8 tiles can form 2 melds + 1 pair."""
        if len(tiles) != 8:
            return False
        
        from collections import Counter
        counts = Counter((t.category, t.value) for t in tiles)
        
        # Try each possible pair
        for pair_type, count in counts.items():
            if count >= 2:
                # Remove pair and check if remaining 6 tiles form 2 melds
                remaining = list(tiles)
                removed = 0
                for i in range(len(remaining) - 1, -1, -1):
                    if (remaining[i].category, remaining[i].value) == pair_type:
                        del remaining[i]
                        removed += 1
                        if removed == 2:
                            break
                
                if len(remaining) == 6:
                    # Check if 6 tiles can form exactly 2 melds
                    if self._can_form_n_melds(remaining, 2):
                        return True
        
        return False
    
    def _can_form_three_melds_and_pair(self, tiles):
        """Check if 11 tiles can form 3 melds + 1 pair."""
        if len(tiles) != 11:
            return False
        
        from collections import Counter
        counts = Counter((t.category, t.value) for t in tiles)
        
        # Try each possible pair
        for pair_type, count in counts.items():
            if count >= 2:
                # Remove pair and check if remaining 9 tiles form 3 melds
                remaining = list(tiles)
                removed = 0
                for i in range(len(remaining) - 1, -1, -1):
                    if (remaining[i].category, remaining[i].value) == pair_type:
                        del remaining[i]
                        removed += 1
                        if removed == 2:
                            break
                
                if len(remaining) == 9:
                    # Check if 9 tiles can form exactly 3 melds
                    if self._can_form_n_melds(remaining, 3):
                        return True
        
        return False
    
    def _is_valid_meld(self, tiles):
        """Check if 3 tiles form a valid meld (triplet or sequence)."""
        if len(tiles) != 3:
            return False
        
        # Check for triplet
        if all(t.tile_id == tiles[0].tile_id for t in tiles):
            return True
        
        # Check for sequence (only for suit tiles)
        if all(t.category in ["Man", "Pin", "Sou"] for t in tiles):
            if all(t.category == tiles[0].category for t in tiles):
                values = sorted([t.value for t in tiles])
                if values == [values[0], values[0] + 1, values[0] + 2]:
                    return True
        
        return False
    
    def _can_form_n_melds(self, tiles, n):
        """Check if tiles can form exactly n melds."""
        if len(tiles) != n * 3:
            return False
        
        if n == 0:
            return len(tiles) == 0
        
        if not tiles:
            return n == 0
        
        # Try to form a meld with the first tile
        first_tile = tiles[0]
        
        # Try triplet
        matching_tiles = [t for t in tiles if t.tile_id == first_tile.tile_id]
        if len(matching_tiles) >= 3:
            # Form triplet and check remaining
            remaining = list(tiles)
            removed = 0
            for i in range(len(remaining) - 1, -1, -1):
                if remaining[i].tile_id == first_tile.tile_id and removed < 3:
                    del remaining[i]
                    removed += 1
            
            if self._can_form_n_melds(remaining, n - 1):
                return True
        
        # Try sequence (only for suit tiles)
        if first_tile.category in ["Man", "Pin", "Sou"]:
            val2 = first_tile.value + 1
            val3 = first_tile.value + 2
            
            tile2 = next((t for t in tiles[1:] if t.category == first_tile.category and t.value == val2), None)
            tile3 = next((t for t in tiles[1:] if t.category == first_tile.category and t.value == val3), None)
            
            if tile2 and tile3:
                # Form sequence and check remaining
                remaining = [t for t in tiles if t not in [first_tile, tile2, tile3]]
                if self._can_form_n_melds(remaining, n - 1):
                    return True
        
        return False
    
    def get_player_total_tiles(self, player):
        """
        Calculate the total number of tiles a player has (hand + melds).
        Accounts for KAN having 4 tiles vs PON/CHI having 3 tiles.
        """
        hand_size = len(player.hand)
        meld_tiles = 0
        
        for meld_type, meld_tiles_list in player.melds:
            if meld_type == "KAN":
                meld_tiles += 4
            else:  # PON or CHI
                meld_tiles += 3
        
        return hand_size + meld_tiles
    
    def validate_player_tile_counts(self):
        """
        Validate that all players have proper tile counts according to Chinese Mahjong rules.
        - Non-winning players: exactly 13 tiles
        - Winning players: 14 or 15 tiles (15 only if winning after KAN replacement)
        """
        for i, player in enumerate(self.players):
            total_tiles = self.get_player_total_tiles(player)
            is_winner = i in getattr(self, 'winners', [])
            
            if is_winner:
                if total_tiles not in [14, 15]:
                    print(f"[TILE COUNT ERROR] Winner Player {i} has {total_tiles} tiles, should be 14-15")
                    return False
            else:
                if total_tiles != 13:
                    print(f"[TILE COUNT ERROR] Non-winner Player {i} has {total_tiles} tiles, should be 13")
                    print(f"  Hand: {len(player.hand)} tiles")
                    print(f"  Melds: {[(mtype, len(tiles)) for mtype, tiles in player.melds]}")
                    return False
        
        return True
    
    def get_reward(self, player_id):
        """
        Get reward using the balanced reward system that prevents reward hacking.
        This provides massive win bonuses while preventing defensive play.
        """
        from engine.balanced_rewards import get_balanced_terminal_reward
        
        if self.is_terminal():
            # Use balanced terminal rewards that heavily favor wins
            return get_balanced_terminal_reward(self, player_id)
        else:
            # Very small ongoing reward to avoid encouraging prolonged games
            return 0.1
    
    def get_action_reward(self, player_id, action, prev_game_state=None):
        """
        Get balanced reward for a specific action.
        This prevents reward hacking while encouraging wins.
        """
        from engine.balanced_rewards import get_balanced_reward
        
        return get_balanced_reward(self, player_id, action, prev_game_state)
    
    def get_hand_score(self, player):
        """
        Calculate Chinese Mahjong hand score (points).
        Returns integer score based on hand composition and win type.
        """
        if not self.check_player_win(player):
            return 0
        
        score = 2  # Base score for any win
        hand = player.hand[:]
        
        # Add meld tiles to full hand for analysis
        for meld_type, meld_tiles in player.melds:
            hand.extend(meld_tiles)
        
        # Basic scoring rules (simplified Chinese system)
        
        # 1. All one suit (清一色) - high value
        suits = set(t.category for t in hand if t.category in ["Man", "Pin", "Sou"])
        if len(suits) == 1:
            score += 6  # All one suit bonus
        
        # 2. All terminals and honors (老头) 
        terminals_honors = all(
            (t.category in ["Wind", "Dragon"]) or 
            (t.category in ["Man", "Pin", "Sou"] and t.value in [1, 9])
            for t in hand
        )
        if terminals_honors:
            score += 4
        
        # 3. No terminals or honors (断幺九)
        no_terminals = all(
            t.category in ["Man", "Pin", "Sou"] and t.value not in [1, 9]
            for t in hand
        )
        if no_terminals:
            score += 1
        
        # 4. Bonus for each KAN
        kan_count = sum(1 for meld_type, _ in player.melds if meld_type == "KAN")
        score += kan_count * 2
        
        # 5. All CHI (no PON/KAN) - sequence hand
        has_only_chi = all(meld_type == "CHI" for meld_type, _ in player.melds)
        if has_only_chi and len(player.melds) > 0:
            score += 1

        # 6. Bonus tile scoring (flowers and seasons)
        flower_count = sum(1 for t in player.bonus_tiles if t.category == "Flower")
        season_count = sum(1 for t in player.bonus_tiles if t.category == "Season")

        # 1 point per flower/season
        score += flower_count + season_count

        # Special bonuses
        if flower_count == 4:
            score += 3  # "Four Flowers" bonus
        if season_count == 4:
            score += 3  # "Four Seasons" bonus

        
        return max(score, 2)  # Minimum 2 points for any win
    
    
    def get_game_summary(self, filename="game_summary.txt"):
        """
        Write a detailed game summary to a text file including:
        - Final player states (hands, melds, scores)
        - CFR rewards vs Chinese scores
        - Game statistics
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== MAHJONG GAME SUMMARY ===\n")
            f.write(f"Game Terminal: {self.is_terminal()}\n")
            f.write(f"Wall Remaining: {len(self.wall)} tiles\n\n")
            
            # Player summaries
            for i, player in enumerate(self.players):
                f.write(f"=== PLAYER {i}: {player.seat} ===\n")
                f.write(f"Hand ({len(player.hand)} tiles): {[str(t) for t in player.hand]}\n")
                f.write(f"Melds ({len(player.melds)}): {[(mtype, [str(t) for t in tiles]) for mtype, tiles in player.melds]}\n")
                
                # Scoring
                chinese_score = self.get_hand_score(player)
                cfr_reward = self.get_reward(i)
                is_winner = i in getattr(self, 'winners', [])
                
                f.write(f"Chinese Score: {chinese_score} points\n")
                f.write(f"CFR Reward: {cfr_reward}\n")
                f.write(f"Winner: {is_winner}\n")
                
                if is_winner:
                    f.write(">>> WIN ANALYSIS <<<\n")
                    if chinese_score >= 8:
                        f.write("HIGH VALUE HAND!\n")
                    elif chinese_score >= 4:
                        f.write("Good scoring hand\n")
                    else:
                        f.write("Basic win\n")
                
                f.write(f"Discards: {[str(t) for t in self.discards.get(player.seat, [])]}\n")
                f.write("\n")
            
            # Game statistics
            f.write("=== GAME STATISTICS ===\n")
            total_chinese_score = sum(self.get_hand_score(p) for p in self.players)
            total_cfr_reward = sum(self.get_reward(i) for i in range(4))
            
            f.write(f"Total Chinese Points: {total_chinese_score}\n")
            f.write(f"Total CFR Rewards: {total_cfr_reward}\n")
            f.write(f"Highest Scoring Player: Player {max(range(4), key=lambda i: self.get_hand_score(self.players[i]))}\n")
            
            if hasattr(self, 'winners'):
                f.write(f"Winners: {[self.players[i].seat for i in self.winners]}\n")
            
            f.write("\n=== END SUMMARY ===\n")
        
        print(f"Game summary written to {filename}")

    def collect_and_arbitrate_claims(self, tile):
        """
        Checks all possible claims (Ron, KAN, PON, CHI) from players other than the discarder,
        applies priority, and returns the (player_index, claim_type, extra_data).
        If no claim, returns None.
        """
        claims = []

        # Loop through all players except the discarder
        for i, player in enumerate(self.players):
            if i == self.last_discarded_by:
                continue

            # RON (win on discard): must come first
            full_hand = player.hand[:] + [tile]
            if len(full_hand) in [14, 15] and is_winning_hand(full_hand):
                claims.append((i, "RON", {}))
                continue  # Ron always highest priority; but multiple Ron is possible

            # KAN (Minkan only): must have 3 in hand
            kan_tiles = [t for t in player.hand if t.tile_id == tile.tile_id]
            if len(kan_tiles) == 3:
                claims.append((i, "KAN", {"tile": tile}))

            # PON: must have 2 in hand
            pon_tiles = [t for t in player.hand if t.tile_id == tile.tile_id]
            if len(pon_tiles) == 2:
                claims.append((i, "PON", {"tile": tile}))

        # CHI: any player except discarder (Chinese rules)
        for i, player in enumerate(self.players):
            if i == self.last_discarded_by:
                continue  # Skip discarder
            melds = self.can_chi(tile, player=player)
            if melds:
                claims.append((i, "CHI", {"melds": melds, "tile": tile}))

        # Now resolve claims by Mahjong priority
        # If multiple Ron, all win (for now, Japanese rules: all can win on Ron)
        ron_claims = [c for c in claims if c[1] == "RON"]
        if ron_claims:
            # For now, return all RON claimers (you may want to support multiple Ron wins)
            return ron_claims

        # Otherwise, find highest priority single claim
        for kind in ("KAN", "PON", "CHI"):
            for c in claims:
                if c[1] == kind:
                    return [c]

        # No claim
        return None

def is_winning_hand(hand_tiles):
    from .special_hands import (
        check_seven_pairs, check_thirteen_orphans, check_all_honors,
        check_all_terminals, _can_form_melds, check_all_one_suit,
        check_big_three_dragons, check_little_four_winds, is_big_four_winds,
        check_all_green, check_nine_gates, check_four_concealed_triplets,
        check_all_red
    )
    from collections import Counter


    if len(hand_tiles) not in [14, 15]:
        return False

    # Check special hands first
    if check_seven_pairs(hand_tiles):
        return True
    if check_thirteen_orphans(hand_tiles):
        return True
    if check_all_honors(hand_tiles):
        return True
    if check_all_terminals(hand_tiles):
        return True
    if check_all_one_suit(hand_tiles):
        return True
    if check_big_three_dragons(hand_tiles):
        return True
    if check_little_four_winds(hand_tiles):
        return True
    if is_big_four_winds(hand_tiles):
        return True
    if check_all_green(hand_tiles):
        return True
    if check_nine_gates(hand_tiles):
        return True
    if check_four_concealed_triplets(hand_tiles):
        return True
    if check_all_red(hand_tiles):
        return True

    # Standard win: 4 melds + 1 pair
    counts = Counter((t.category, t.value) for t in hand_tiles)
    for pair, count in counts.items():
        if count >= 2:
            remaining = list(hand_tiles)
            removed = 0
            for i in range(len(remaining) - 1, -1, -1):
                if (remaining[i].category, remaining[i].value) == pair:
                    del remaining[i]
                    removed += 1
                    if removed == 2:
                        break
            if _can_form_melds(remaining):
                return True

    return False

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
        player = self.get_current_player()

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
    def is_terminal(self):
        # Allow manual override with _terminal (for forced ends, e.g. exhaustive draw)
        if hasattr(self, "_terminal") and self._terminal:
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
                return True
        
        # Check for wall exhaustion
        if not self.wall:
            self._terminal = True
            return True
            
        return False
    
    
    def check_player_win(self, player):
        """
        Check if a player has a winning hand by combining hand tiles with meld tiles.
        Returns True if the player has a valid Mahjong win.
        """
        # Combine hand + all tiles from open melds (flattened)
        full_hand = player.hand[:]
        for meld_type, meld_tiles in getattr(player, "melds", []):
            full_hand.extend(meld_tiles)
        
        return is_winning_hand(full_hand)

    def get_reward(self, player_id):
        if hasattr(self, 'winners'):
            return 1.0 if player_id in self.winners else 0.0
        return 0.0
    
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
            if is_winning_hand(full_hand):
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
    
    from collections import Counter
    if len(hand_tiles) != 14:
        return False
        
    counts = Counter((t.category, t.value) for t in hand_tiles)
    
    # Try every possible pair
    for pair, n in counts.items():
        if n >= 2:
            remaining = list(hand_tiles)
            # Remove pair
            removed = 0
            for i in range(len(remaining)-1, -1, -1):
                if (remaining[i].category, remaining[i].value) == pair:
                    del remaining[i]
                    removed += 1
                    if removed == 2:
                        break
            
            if _can_form_melds(remaining):  # ← CORRECT
                return True
    return False

def _can_form_melds(tiles):
    """Helper function to check if remaining tiles can form valid melds."""
    from collections import Counter
    if not tiles:
        return True
    
    tiles = sorted(tiles, key=lambda t: (t.category, t.value))
    first = tiles[0]
    
    # Try Pong (triplet)
    if sum(1 for t in tiles if t.category == first.category and t.value == first.value) >= 3:
        remaining = []
        removed = 0
        for t in tiles:
            if t.category == first.category and t.value == first.value and removed < 3:
                removed += 1
            else:
                remaining.append(t)
        if _can_form_melds(remaining):
            return True
    
    # Try Chi (sequence, only for suits)
    if first.category in ["Man", "Pin", "Sou"]:
        val2 = first.value + 1
        val3 = first.value + 2
        i2 = i3 = -1
        for i, t in enumerate(tiles[1:], 1):
            if i2 == -1 and t.category == first.category and t.value == val2:
                i2 = i
            elif i3 == -1 and t.category == first.category and t.value == val3:
                i3 = i
        if i2 != -1 and i3 != -1:
            remaining = [t for i, t in enumerate(tiles) if i not in [0, i2, i3]]
            if _can_form_melds(remaining):
                return True
                
    
    return False


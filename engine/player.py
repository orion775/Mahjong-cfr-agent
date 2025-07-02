# engine/player.py

class Player:
    def __init__(self, seat):
        self.seat = seat            # "East", "South", "West", "North"
        self.hand = []              # List of Tile objects
        self.melds = []             # List of tuples like ("PON", tile list)
        self.bonus_tiles = []       # NEW: Store flowers and seasons separately

    def draw_tile(self, tile):
        self.hand.append(tile)

    def discard_tile(self, tile):
        if tile in self.hand:
            self.hand.remove(tile)
            return tile
        else:
            raise ValueError("Tile not in hand")
        
    def can_pon(self, tile):
        return self.hand.count(tile) >= 2
    
    def can_chi(self, tile, source_seat=None):
        """
        Returns a list of value-sequences that would complete a CHI with the given tile,
        enforcing strict suit boundaries (no wraparound like 9-1-2).
        """
        if tile.category not in ["Man", "Pin", "Sou"]:
            return []

        hand_values = sorted([t.value for t in self.hand if t.category == tile.category])
        candidates = []
        val = tile.value
        # [val-2, val-1, val]
        if (val-2 in hand_values and val-1 in hand_values and 1 <= val-2 <= 9):
            candidates.append([val-2, val-1, val])
        # [val-1, val, val+1]
        if (val-1 in hand_values and val+1 in hand_values and 1 <= val-1 <= 9 and 1 <= val+1 <= 9):
            candidates.append([val-1, val, val+1])
        # [val, val+1, val+2]
        if (val+1 in hand_values and val+2 in hand_values and 1 <= val+1 <= 9 and 1 <= val+2 <= 9):
            candidates.append([val, val+1, val+2])
        return candidates
    
    def call_meld(self, meld_type, tiles, include_discard=False):
        print(f"[DEBUG] Calling meld: {meld_type} with {[str(t) for t in tiles]}")
        print(f"[DEBUG] Hand before: {[str(t) for t in self.hand]}")
        
        hand_tiles_to_remove = []
        discard_skipped = False

        for t in tiles:
            matching_tile = next((hand_tile for hand_tile in self.hand if hand_tile.tile_id == t.tile_id), None)
            if matching_tile:
                self.hand.remove(matching_tile)
                hand_tiles_to_remove.append(matching_tile)
                print(f"[DEBUG] Removed {matching_tile} from hand")
            elif include_discard and not discard_skipped:
                discard_skipped = True
                print(f"[DEBUG] Skipped removal for {t} (discarded tile)")
            else:
                raise ValueError(f"Cannot declare {meld_type}, missing tile: {t}")

        # Safety check: For melds using a discard, only one skipped removal allowed
        expected_removed = len(tiles) - 1 if include_discard else len(tiles)
        if len(hand_tiles_to_remove) != expected_removed:
            raise RuntimeError(f"{meld_type}: expected to remove {expected_removed} from hand, but removed {len(hand_tiles_to_remove)}.")

        # Create new tile objects for the meld to avoid sharing references
        from engine.tile import Tile
        meld_tiles_copy = [Tile(t.category, t.value, t.tile_id) for t in tiles]
        self.melds.append((meld_type, meld_tiles_copy))
        
        print(f"[DEBUG] Meld appended: {meld_type}")
        print(f"[DEBUG] Melds now: {[(m[0], [str(t) for t in m[1]]) for m in self.melds]}")

    def can_ankan(self, tile):
        return self.hand.count(tile) == 4
    
    def clone(self):
        new_player = Player(self.seat)
        new_player.hand = self.hand[:]
        new_player.melds = [tuple(m) for m in self.melds]
        return new_player
    
    def add_bonus_tile(self, tile):
        """Add a flower/season tile to bonus collection. Returns True if successful."""
        if tile.is_bonus_tile():
            self.bonus_tiles.append(tile)
            return True
        return False
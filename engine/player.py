# engine/player.py

class Player:
    def __init__(self, seat):
        self.seat = seat            # "East", "South", "West", "North"
        self.hand = []              # List of Tile objects
        self.melds = []             # List of tuples like ("PON", tile list)

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
    
    def can_chi(self, tile, source_seat):
        # Chinese rules: Any player can CHI (remove seat restriction)
        
        if tile.category not in ["Man", "Pin", "Sou"]:
            return False

        values = [t.value for t in self.hand if t.category == tile.category]
        val = tile.value
        # Check for 3-tile sequences: [val-2, val-1], [val-1, val+1], [val+1, val+2]
        return (
            (val - 2 in values and val - 1 in values) or
            (val - 1 in values and val + 1 in values) or
            (val + 1 in values and val + 2 in values)
        )
    
    def call_meld(self, meld_type, tiles, include_discard=False):
        print(f"[DEBUG] Calling meld: {meld_type} with {[str(t) for t in tiles]}")
        print(f"[DEBUG] Hand before: {[str(t) for t in self.hand]}")
    
        removed = 0
        for t in tiles:
            # Find tile by tile_id instead of object equality
            matching_tile = next((hand_tile for hand_tile in self.hand if hand_tile.tile_id == t.tile_id), None)
            if matching_tile:
                self.hand.remove(matching_tile)
                removed += 1
                print(f"[DEBUG] Removed {matching_tile} from hand")
            elif not include_discard:
                raise ValueError(f"Cannot declare {meld_type}, missing tile: {t}")
            else:
                print(f"[DEBUG] Skipped removal for {t} (discarded tile)")
    
        print(f"[DEBUG] Total removed: {removed}, required: {len(tiles) - 1}")
        if include_discard and removed < len(tiles) - 1:
            raise ValueError("Not enough tiles in hand for meld")
    
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
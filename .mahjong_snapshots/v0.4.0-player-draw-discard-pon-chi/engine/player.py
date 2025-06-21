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
        # Player can only Chi from the left (East→South→West→North→East)
        seat_order = ["East", "South", "West", "North"]
        my_index = seat_order.index(self.seat)
        left_index = (my_index + 1) % 4
        if seat_order[left_index] != source_seat:
            return False

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
    
    def call_meld(self, meld_type, tiles):
        """
        Register a meld (e.g., PON, CHI).
        - meld_type: "PON", "CHI", etc.
        - tiles: List[Tile] used for the meld (2 tiles from hand)
        """
        for t in tiles:
            if t in self.hand:
                self.hand.remove(t)
            else:
                raise ValueError(f"Cannot declare {meld_type}, missing tile: {t}")
        self.melds.append((meld_type, tiles))
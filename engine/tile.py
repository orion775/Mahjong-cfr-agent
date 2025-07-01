# engine/tile.py

class Tile:
    def __init__(self, category, value, tile_id):
        self.category = category  # e.g., "Man", "Pin", "Sou", "Wind", "Dragon"
        self.value = value        # e.g., 1–9 or "East", "Red"
        self.tile_id = tile_id    # Unique integer ID (0–41)

    def __str__(self):
        return f"{self.category} {self.value}"

    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return self.tile_id == other.tile_id
    
    def __hash__(self):
        return hash(self.tile_id)
        
    def is_bonus_tile(self):

        #"""Returns True if this is a Flower or Season tile (bonus tiles)"""
        return self.category in ["Flower", "Season"]


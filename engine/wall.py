# engine/wall.py

from engine.tile import Tile
import random

def generate_wall():
    wall = []

    # Suits: Man, Pin, Sou (1–9)
    for suit_index, suit_name in enumerate(["Man", "Pin", "Sou"]):
        for value in range(1, 10):
            tile_id = suit_index * 9 + (value - 1)
            for _ in range(4):  # 4 copies of each
                wall.append(Tile(suit_name, value, tile_id))

    # Winds: East, South, West, North
    winds = ["East", "South", "West", "North"]
    for i, wind in enumerate(winds):
        tile_id = 27 + i
        for _ in range(4):
            wall.append(Tile("Wind", wind, tile_id))

    # Dragons: Red, Green, White
    dragons = ["Red", "Green", "White"]
    for i, dragon in enumerate(dragons):
        tile_id = 31 + i
        for _ in range(4):
            wall.append(Tile("Dragon", dragon, tile_id))

    # Flowers and Seasons (optional for now)
    # Skipping for now — you can add them later
    # Flowers: Plum, Orchid, Chrysanthemum, Bamboo
    flowers = ["Plum", "Orchid", "Chrysanthemum", "Bamboo"]
    for i, flower in enumerate(flowers):
        tile_id = 34 + i
        wall.append(Tile("Flower", flower, tile_id))

    # Seasons: Spring, Summer, Autumn, Winter
    seasons = ["Spring", "Summer", "Autumn", "Winter"]
    for i, season in enumerate(seasons):
        tile_id = 38 + i
        wall.append(Tile("Season", season, tile_id))

    random.shuffle(wall)
    return wall
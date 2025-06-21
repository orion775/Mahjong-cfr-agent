# engine/action_space.py

# -----------------------------
# Tile constants
# -----------------------------

NUM_TILE_TYPES = 34  # Man (0–8), Pin (9–17), Sou (18–26), Winds (27–30), Dragons (31–33)

# -----------------------------
# Action ID Ranges
# -----------------------------

DISCARD_ACTIONS = list(range(NUM_TILE_TYPES))                        # 0–33
PON_ACTIONS = list(range(NUM_TILE_TYPES, NUM_TILE_TYPES * 2))        # 34–67
PASS = NUM_TILE_TYPES * 2                                            # 68

ALL_ACTIONS = DISCARD_ACTIONS + PON_ACTIONS + [PASS]

# -----------------------------
# ID ↔ Name Mappings
# -----------------------------

ACTION_ID_TO_NAME = {}

# Add discards
for i in DISCARD_ACTIONS:
    ACTION_ID_TO_NAME[i] = f"DISCARD_{i}"

# Add pon actions
for i, action_id in enumerate(PON_ACTIONS):
    ACTION_ID_TO_NAME[action_id] = f"PON_{i}"

# Add PASS
ACTION_ID_TO_NAME[PASS] = "PASS"

# Reverse map
ACTION_NAME_TO_ID = {v: k for k, v in ACTION_ID_TO_NAME.items()}

# -----------------------------
# Helper functions
# -----------------------------

def get_all_discard_actions():
    return DISCARD_ACTIONS

def get_all_pon_actions():
    return PON_ACTIONS

def get_all_actions():
    return ALL_ACTIONS

# -----------------------------
# Chi Actions (Sequences)
# -----------------------------

CHI_BASE_ID = PASS + 1  # = 69
CHI_ACTIONS = []

# Mapping suit → starting tile_id
suit_offsets = {
    "MAN": 0,     # Man 1 starts at tile_id 0
    "PIN": 9,     # Pin 1 starts at tile_id 9
    "SOU": 18     # Sou 1 starts at tile_id 18
}

chi_action_id = CHI_BASE_ID

for suit in ["MAN", "PIN", "SOU"]:
    offset = suit_offsets[suit]
    for start in range(1, 8):  # Start values 1 to 7
        tile_id = offset + (start - 1)
        action_name = f"CHI_{suit}_{start}"  # e.g., CHI_MAN_3
        ACTION_ID_TO_NAME[chi_action_id] = action_name
        ACTION_NAME_TO_ID[action_name] = chi_action_id
        CHI_ACTIONS.append(chi_action_id)
        chi_action_id += 1

ALL_ACTIONS += CHI_ACTIONS

def get_all_chi_actions():
    return CHI_ACTIONS
# engine/action_space.py

# -----------------------------
# Tile constants
# -----------------------------

NUM_TILE_TYPES = 42  # Man (0–8), Pin (9–17), Sou (18–26), Winds (27–30), Dragons (31–33), Flowers (34–37), Seasons (38–41)
# -----------------------------
# Action ID Ranges
# -----------------------------

DISCARD_ACTIONS = list(range(NUM_TILE_TYPES))                        # 0–41
PON_ACTIONS = list(range(NUM_TILE_TYPES, NUM_TILE_TYPES * 2)) 
PASS = NUM_TILE_TYPES * 2      # 84 (42 * 2 = 84)
# -----------------------------
# Chi Actions (Sequences)
# -----------------------------
CHI_BASE_ID = PASS + 1  # = 85 (84 + 1)
CHI_ACTIONS = []
KAN_BASE = CHI_BASE_ID + 21  # 85 + 21 = 106
KAN_ACTIONS = list(range(KAN_BASE, KAN_BASE + NUM_TILE_TYPES))  # 106–147

ALL_ACTIONS = DISCARD_ACTIONS + PON_ACTIONS + KAN_ACTIONS + [PASS]

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

# Add kan actions
for i, action_id in enumerate(KAN_ACTIONS):
    ACTION_ID_TO_NAME[action_id] = f"KAN_{i}"

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

def get_all_kan_actions():
    return KAN_ACTIONS

# -----------------------------
# Chi Actions (Sequences)
# -----------------------------



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

def encode_chi(meld):
    """Given a sorted meld like [3,4,5], return its CHI action ID."""
    if len(meld) != 3:
        raise ValueError("CHI meld must have 3 tiles")

    base = meld[0]

    # ❗ Prevent CHI that would run past tile 9 in any suit
    if base in [7, 8, 16, 17, 25, 26]:
        raise ValueError(f"Invalid CHI start tile_id: {base} — sequence runs off end of suit")

    if not (0 <= base <= 24):  # Ensure it's within Man/Pin/Sou 1–7
        raise ValueError(f"Base tile_id {base} out of range for CHI")

    if meld != [base, base + 1, base + 2]:
        raise ValueError("Invalid CHI sequence")

    if base < 9:
        suit = "MAN"
        start = base - 0 + 1
    elif base < 18:
        suit = "PIN"
        start = base - 9 + 1
    elif base < 27:
        suit = "SOU"
        start = base - 18 + 1
    else:
        raise ValueError("Invalid CHI suit")

    action_name = f"CHI_{suit}_{start}"
    return ACTION_NAME_TO_ID[action_name]

def decode_chi(action_id):
    """Given a CHI action ID, return the meld as [tile_id1, tile_id2, tile_id3]."""
    name = ACTION_ID_TO_NAME.get(action_id, "")
    if not name.startswith("CHI_"):
        raise ValueError("Not a CHI action")

    _, suit, start = name.split("_")
    start = int(start)

    if suit == "MAN":
        base = 0 + (start - 1)
    elif suit == "PIN":
        base = 9 + (start - 1)
    elif suit == "SOU":
        base = 18 + (start - 1)
    else:
        raise ValueError("Unknown CHI suit")

    return [base, base + 1, base + 2]

def tile_id_from_action(action_id: int) -> int:
    """Extract tile_id from an action_id if it's a tile-based action (e.g., discard, meld)."""
    if 0 <= action_id < 42:        # Discard (was 34, now 42)
        return action_id
    elif 42 <= action_id < 84:     # PON (was 34-68, now 42-84)
        return action_id - 42
    elif 106 <= action_id < 148:   # KAN (was 90-124, now 106-148)
        return action_id - 106
    raise ValueError(f"Cannot extract tile_id from action_id: {action_id}")
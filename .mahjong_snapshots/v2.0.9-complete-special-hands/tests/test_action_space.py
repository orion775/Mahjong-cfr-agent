import unittest
from engine import action_space
from engine.action_space import tile_id_from_action

class TestActionSpace(unittest.TestCase):
    def test_discard_action_ids(self):
        actions = action_space.get_all_discard_actions()
        self.assertEqual(len(actions), 42)
        self.assertEqual(actions[0], 0)
        self.assertEqual(actions[-1], 41)

    def test_pass_action_exists(self):
        self.assertIn(action_space.PASS, action_space.get_all_actions())
        self.assertEqual(action_space.ACTION_ID_TO_NAME[action_space.PASS], "PASS")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["PASS"], action_space.PASS)

    def test_pon_action_ids(self):
        pon_actions = action_space.get_all_pon_actions()
        self.assertEqual(len(pon_actions), 42)
        self.assertEqual(pon_actions[0], 42)
        self.assertEqual(pon_actions[-1], 83)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[43], "PON_1")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["PON_1"], 43)
        
    def test_chi_action_ids(self):
        chi = action_space.get_all_chi_actions()
        self.assertEqual(len(chi), 21)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[85], "CHI_MAN_1")
        self.assertEqual(action_space.ACTION_ID_TO_NAME[105], "CHI_SOU_7")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["CHI_PIN_5"], 96)

    def test_encode_decode_chi(self):
        from engine import action_space

        melds = [
            [0, 1, 2],
            [10, 11, 12],
            [24, 25, 26]
        ]

        for meld in melds:
            action_id = action_space.encode_chi(meld)
            decoded = action_space.decode_chi(action_id)
            self.assertEqual(decoded, meld)

        with self.assertRaises(ValueError):
            action_space.encode_chi([1, 2, 4])

        with self.assertRaises(ValueError):
            action_space.encode_chi([27, 28, 29])
    
    def test_kan_action_ids(self):
        kan = action_space.get_all_kan_actions()
        self.assertEqual(len(kan), 42)
        self.assertEqual(kan[0], 106)
        self.assertEqual(kan[-1], 147)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[106], "KAN_0")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["KAN_0"], 106)
    
    def test_tile_id_from_action(self):
        # Discards (0-41)
        self.assertEqual(tile_id_from_action(0), 0)
        self.assertEqual(tile_id_from_action(41), 41)

        # PON (42-83)
        self.assertEqual(tile_id_from_action(42), 0)
        self.assertEqual(tile_id_from_action(83), 41)

        # KAN (106-147)
        self.assertEqual(tile_id_from_action(106), 0)
        self.assertEqual(tile_id_from_action(147), 41)

        # Out of range
        with self.assertRaises(ValueError):
            tile_id_from_action(148)

if __name__ == '__main__':
    unittest.main()
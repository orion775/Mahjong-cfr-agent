#tests\test_action_space.py

import unittest
from engine import action_space
from engine.action_space import tile_id_from_action

class TestActionSpace(unittest.TestCase):
    def test_discard_action_ids(self):
        actions = action_space.get_all_discard_actions()
        self.assertEqual(len(actions), 34)
        self.assertEqual(actions[0], 0)
        self.assertEqual(actions[-1], 33)

    def test_pass_action_exists(self):
        self.assertIn(action_space.PASS, action_space.get_all_actions())
        self.assertEqual(action_space.ACTION_ID_TO_NAME[action_space.PASS], "PASS")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["PASS"], action_space.PASS)

    def test_pon_action_ids(self):
        pon_actions = action_space.get_all_pon_actions()
        self.assertEqual(len(pon_actions), 34)
        self.assertEqual(pon_actions[0], 34)
        self.assertEqual(pon_actions[-1], 67)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[35], "PON_1")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["PON_1"], 35)
        
    def test_chi_action_ids(self):
        chi = action_space.get_all_chi_actions()
        self.assertEqual(len(chi), 21)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[69], "CHI_MAN_1")
        self.assertEqual(action_space.ACTION_ID_TO_NAME[89], "CHI_SOU_7")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["CHI_PIN_5"], 80)

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
        self.assertEqual(len(kan), 34)
        self.assertEqual(kan[0], 90)
        self.assertEqual(kan[-1], 123)
        self.assertEqual(action_space.ACTION_ID_TO_NAME[90], "KAN_0")
        self.assertEqual(action_space.ACTION_NAME_TO_ID["KAN_0"], 90)
    
    def test_tile_id_from_action(self):
        # Discards
        self.assertEqual(tile_id_from_action(0), 0)
        self.assertEqual(tile_id_from_action(33), 33)

        # PON
        self.assertEqual(tile_id_from_action(34), 0)
        self.assertEqual(tile_id_from_action(67), 33)

        # KAN
        self.assertEqual(tile_id_from_action(90), 0)
        self.assertEqual(tile_id_from_action(123), 33)

        # Out of range
        with self.assertRaises(ValueError):
            tile_id_from_action(124)

if __name__ == '__main__':
    unittest.main()
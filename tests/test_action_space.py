
import unittest
from engine import action_space

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

if __name__ == '__main__':
    unittest.main()
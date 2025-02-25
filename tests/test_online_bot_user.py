"""Tests for online_bot_user.py."""

import unittest

from src.generate.online_bot_user import OnlineBotUser, Perf, PerfType


TEST_ONLINE_BOT_USER_JSON = """
{
  "id": "test_username",
  "username": "Test_Username",
  "perfs": {
    "bullet": {
        "games": 123,
        "rating": 1450
    },
    "blitz": {
        "games": 456,
        "rating": 1500
    },
    "rapid": {
        "games": 789,
        "rating": 1550,
        "prov": true
    }
  }
}
"""


class TestLichessClient(unittest.TestCase):
  def test_perf_type_from_json_parses_all_perf_types(self) -> None:
    self.assertEqual(PerfType.from_json("bullet"), PerfType.BULLET)
    self.assertEqual(PerfType.from_json("blitz"), PerfType.BLITZ)
    self.assertEqual(PerfType.from_json("rapid"), PerfType.RAPID)
    self.assertEqual(PerfType.from_json("classical"), PerfType.CLASSICAL)
    self.assertEqual(PerfType.from_json("correspondence"), PerfType.CORRESPONDENCE)
    self.assertEqual(PerfType.from_json("crazyhouse"), PerfType.CRAZYHOUSE)
    self.assertEqual(PerfType.from_json("chess960"), PerfType.CHESS960)
    self.assertEqual(PerfType.from_json("kingOfTheHill"), PerfType.KING_OF_THE_HILL)
    self.assertEqual(PerfType.from_json("threeCheck"), PerfType.THREE_CHECK)
    self.assertEqual(PerfType.from_json("antichess"), PerfType.ANTICHESS)
    self.assertEqual(PerfType.from_json("atomic"), PerfType.ATOMIC)
    self.assertEqual(PerfType.from_json("horde"), PerfType.HORDE)
    self.assertEqual(PerfType.from_json("racingKings"), PerfType.RACING_KINGS)
    self.assertEqual(PerfType.from_json(""), PerfType.UNKNOWN)

  def test_online_bot_user_from_json_parses_username(self) -> None:
    bot_user = OnlineBotUser.from_json(TEST_ONLINE_BOT_USER_JSON)
    self.assertEqual(bot_user.username, "Test_Username")

  def test_online_bot_user_from_json_parses_perfs(self) -> None:
    bot_user = OnlineBotUser.from_json(TEST_ONLINE_BOT_USER_JSON)
    expected_perfs = [
      Perf(PerfType.BULLET, 123, 1450, False),
      Perf(PerfType.BLITZ, 456, 1500, False),
      Perf(PerfType.RAPID, 789, 1550, True),
    ]
    self.assertListEqual(bot_user.perfs, expected_perfs)

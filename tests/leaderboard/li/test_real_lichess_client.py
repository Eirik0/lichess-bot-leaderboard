"""Tests for real_lichess_client.py."""

import unittest
from unittest import mock

from src.leaderboard.li.real_lichess_client import RealLichessClient


ONLINE_BOT_NDJSON = "{some json}"


class TestRealLichessClient(unittest.TestCase):
  """Tests for RealLichessClient."""

  @mock.patch("src.leaderboard.li.real_lichess_client.requests.get")
  def test_get_online_bots_requests_maximum_number_of_bots(self, requests_get: mock.Mock) -> None:
    response = mock.Mock()
    response.text = ONLINE_BOT_NDJSON
    requests_get.return_value = response

    online_bots = RealLichessClient().get_online_bots()

    self.assertEqual(online_bots, ONLINE_BOT_NDJSON)
    requests_get.assert_called_once_with(
      "https://lichess.org/api/bot/online",
      headers={"Accept": "application/x-ndjson"},
      params={"nb": 512},
      timeout=10,
      stream=True,
    )
    response.raise_for_status.assert_called_once_with()

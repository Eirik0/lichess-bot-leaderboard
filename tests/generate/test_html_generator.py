"""Tests for html_generator.py."""

import unittest

from generate.fake_date_provider import FakeDateProvider
from src.generate.html_generator import LeaderboardHtmlGenerator
from src.generate.leaderboard_data import LeaderboardRow
from src.generate.lichess_bot_user import PerfType


class TestHtmlGenerator(unittest.TestCase):
  """Tests for html generator."""

  def test_generate_index(self) -> None:
    html_generator = LeaderboardHtmlGenerator(FakeDateProvider())
    html_by_file_name = html_generator.generate_leaderboard_html({})
    index_html = html_by_file_name["index"]
    self.assertIn('<a href="index.html" class="active">Home</a>', index_html)

  def test_generate_last_updated(self) -> None:
    date_provider = FakeDateProvider()
    date_provider.set_current_time(1743483600)
    html_generator = LeaderboardHtmlGenerator(date_provider)
    html_by_file_name = html_generator.generate_leaderboard_html({})
    index_html = html_by_file_name["index"]
    self.assertIn("Last Updated:", index_html)
    self.assertIn("2025-04-01 05:00:00 UTC", index_html)

  def test_generate_bullet(self) -> None:
    html_generator = LeaderboardHtmlGenerator(FakeDateProvider())
    ranked_rows_by_perf_type = {
      PerfType.BULLET: [
        LeaderboardRow.from_psv("Bot-2|||3000|0|0|1000|2022-04-01|2025-04-01|False|False|1|1|100|1|3000|False|True"),
        LeaderboardRow.from_psv(
          "Bot-1|flair|_earth|2950|42|-50|1100|2024-04-01|2025-04-01|True|False|2|-1|-50|1|3000|False|True"
        ),
      ]
    }
    html_by_file_name = html_generator.generate_leaderboard_html(ranked_rows_by_perf_type)
    bullet_html = html_by_file_name["bullet"]
    self.assertIn("Bot-2", bullet_html)
    self.assertIn("Bot-1", bullet_html)

"""Tests for data_generator.py."""

import json
import unittest

from src.leaderboard.chrono.fixed_time_provider import FixedTimeProvider
from src.leaderboard.data import data_generator as data_generator_functions
from src.leaderboard.data.data_generator import DataGenerator
from src.leaderboard.data.leaderboard_objects import BotPerf, BotProfile, LeaderboardPerf, LeaderboardRow, RankInfo
from src.leaderboard.data.leaderboard_update import CurrentBotPerfOnlyUpdate, LeaderboardUpdate
from src.leaderboard.fs import file_paths
from src.leaderboard.li.pert_type import PerfType
from tests.leaderboard.chrono.epoch_seconds import (
  DATE_2021_04_01,
  DATE_2022_04_01,
  DATE_2023_04_01,
  DATE_2024_04_01,
  DATE_2025_04_01,
)
from tests.leaderboard.fs.in_memory_file_system import InMemoryFileSystem
from tests.leaderboard.li.fake_lichess_client import FakeLichessClient


# Bot profiles
BOT_1_PROFILE = BotProfile("Bot-1", "", "", DATE_2021_04_01, DATE_2025_04_01, False, False, False, True)
BOT_2_PROFILE = BotProfile("Bot-2", "", "", DATE_2022_04_01, DATE_2025_04_01, False, False, False, True)
BOT_3_PROFILE = BotProfile("Bot-3", "", "", DATE_2023_04_01, DATE_2025_04_01, False, False, False, True)
BOT_4_PROFILE = BotProfile("Bot-4", "", "", DATE_2024_04_01, DATE_2025_04_01, False, False, False, True)

BOT_PROFILES_BY_NAME = {"Bot-1": BOT_1_PROFILE, "Bot-2": BOT_2_PROFILE, "Bot-3": BOT_3_PROFILE, "Bot-4": BOT_4_PROFILE}

# Bullet leaderboard data
BOT_1_PERF_BULLET = BotPerf("Bot-1", LeaderboardPerf(3000, 0, 0, 1000, False))
BOT_2_PERF_BULLET = BotPerf("Bot-2", LeaderboardPerf(2900, 0, 0, 900, False))
BOT_3_PERF_BULLET = BotPerf("Bot-3", LeaderboardPerf(2900, 0, 0, 800, False))
BOT_4_PERF_BULLET = BotPerf("Bot-4", LeaderboardPerf(2800, 0, 0, 700, False))

BOT_1_ROW_BULLET = LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3001, DATE_2025_04_01))
BOT_2_ROW_BULLET = LeaderboardRow("Bot-2", BOT_2_PERF_BULLET.perf, RankInfo(2, 1, -100, 5, 1, 3000, DATE_2025_04_01))

# Blitz leaderboard data
BOT_2_ROW_BLITZ = LeaderboardRow(
  "Bot-1", LeaderboardPerf(2500, 0, 0, 50, False), RankInfo(1, 1, 100, 5, 1, 2600, DATE_2025_04_01)
)
BOT_1_ROW_BLITZ = LeaderboardRow(
  "Bot-2", LeaderboardPerf(2600, 0, 0, 200, False), RankInfo(2, -1, -150, 5, 1, 2650, DATE_2025_04_01)
)

# Response for get online bots
BOT_1_CURRENT_JSON = """
{
  "username": "Bot-1",
  "flair": "flair",
  "profile": {
    "flag": "_earth"
  },
  "createdAt": 1712000000000,
  "seenAt": 1743500000000,
  "patron": true,
  "perfs": {
    "bullet": {
      "games": 1100,
      "rating": 2950,
      "rd": 42,
      "prog": -50
    },
    "blitz": {
      "games": 100,
      "rating": 2550
    }
  }
}
"""
BOT_2_CURRENT_JSON = """
{
  "username": "Bot-2",
  "createdAt": 1648800000000,
  "seenAt": 1743500000000,
  "perfs": {
    "bullet": {
      "games": 1000,
      "rating": 3000
    },
    "blitz": {
      "games": 300,
      "rating": 2500
    }
  }
}
"""

# Leaderboard Perfs matching the above json
BOT_1_CURRENT_PROFILE = BotProfile("Bot-1", "flair", "_earth", DATE_2024_04_01, DATE_2025_04_01, True, False, True, True)
BOT_2_CURRENT_PROFILE = BotProfile("Bot-2", "", "", DATE_2022_04_01, DATE_2025_04_01, False, False, True, True)

BOT_1_CURRENT_PERF_BULLET = BotPerf("Bot-1", LeaderboardPerf(2950, 42, -50, 1100, False))
BOT_2_CURRENT_PERF_BULLET = BotPerf("Bot-2", LeaderboardPerf(3000, 0, 0, 1000, False))

BOT_1_CURRENT_PERF_BLITZ = BotPerf("Bot-1", LeaderboardPerf(2550, 0, 0, 100, False))
BOT_2_CURRENT_PERF_BLITZ = BotPerf("Bot-2", LeaderboardPerf(2500, 0, 0, 300, False))


def remove_whitespace(whitespace_str: str) -> str:
  """Remove spaces and endlines for a string so it can be used as ndjson.

  For this to work the string cannot have spaces or endlines which are necessary.
  """
  return whitespace_str.replace(" ", "").replace("\n", "")


class TestDataGeneratorFunctions(unittest.TestCase):
  """Tests for data_generator functions."""

  def test_load_bot_profiles(self) -> None:
    file_system = InMemoryFileSystem()
    bot_profiles = [BOT_1_CURRENT_PROFILE.as_dict(), BOT_2_CURRENT_PROFILE.as_dict()]
    file_system.write_file(file_paths.bot_profiles_path(), json.dumps(bot_profiles))
    # When loading the bot profiles new and online are set to false
    expected_bot_profiles = {
      "Bot-1": BotProfile("Bot-1", "flair", "_earth", DATE_2024_04_01, DATE_2025_04_01, True, False, False, False),
      "Bot-2": BotProfile("Bot-2", "", "", DATE_2022_04_01, DATE_2025_04_01, False, False, False, False),
    }
    self.assertDictEqual(data_generator_functions.load_bot_profiles(file_system), expected_bot_profiles)

  def test_load_leaderboard_rows_empty(self) -> None:
    file_system = InMemoryFileSystem()
    previous_rows_by_perf_type = data_generator_functions.load_leaderboard_rows(file_system)
    self.assertEqual(len(previous_rows_by_perf_type), 13)
    self.assertTrue(all(rows == [] for rows in previous_rows_by_perf_type.values()))

  def test_load_leaderboard_rows(self) -> None:
    file_system = InMemoryFileSystem()
    bullet_leaderboard = [BOT_1_ROW_BULLET.as_dict(), BOT_2_ROW_BULLET.as_dict()]
    blitz_leaderboard = [BOT_2_ROW_BLITZ.as_dict(), BOT_1_ROW_BLITZ.as_dict()]
    file_system.write_file(file_paths.data_path(PerfType.BULLET), json.dumps(bullet_leaderboard))
    file_system.write_file(file_paths.data_path(PerfType.BLITZ), json.dumps(blitz_leaderboard))
    previous_rows_by_perf_type = data_generator_functions.load_leaderboard_rows(file_system)
    self.assertEqual(len(previous_rows_by_perf_type), 13)
    self.assertListEqual(previous_rows_by_perf_type[PerfType.BULLET], [BOT_1_ROW_BULLET, BOT_2_ROW_BULLET])
    self.assertListEqual(previous_rows_by_perf_type[PerfType.BLITZ], [BOT_2_ROW_BLITZ, BOT_1_ROW_BLITZ])

  def test_get_online_bot_info(self) -> None:
    lichess_client = FakeLichessClient()
    lichess_client.set_online_bots("\n".join([remove_whitespace(BOT_1_CURRENT_JSON), remove_whitespace(BOT_2_CURRENT_JSON)]))
    bot_info = data_generator_functions.get_online_bot_info(lichess_client)
    self.assertDictEqual(bot_info.bot_profiles_by_name, {"Bot-1": BOT_1_CURRENT_PROFILE, "Bot-2": BOT_2_CURRENT_PROFILE})
    expected_bot_perfs_by_perf_type = {
      PerfType.BULLET: [BOT_1_CURRENT_PERF_BULLET, BOT_2_CURRENT_PERF_BULLET],
      PerfType.BLITZ: [BOT_1_CURRENT_PERF_BLITZ, BOT_2_CURRENT_PERF_BLITZ],
    }
    self.assertDictEqual(bot_info.bot_perfs_by_perf_type, expected_bot_perfs_by_perf_type)

  def test_get_online_bot_info_only_one_perf_played(self) -> None:
    lichess_client = FakeLichessClient()
    lichess_client.set_online_bots(
      """{ "username": "Bot-1", "perfs": { "bullet": { "games": 1000 }, "blitz": { "rating": 1500, "prov": true } } }"""
    )
    bot_info = data_generator_functions.get_online_bot_info(lichess_client)
    self.assertListEqual(list(bot_info.bot_profiles_by_name.keys()), ["Bot-1"])
    self.assertListEqual(list(bot_info.bot_perfs_by_perf_type.keys()), [PerfType.BULLET])

  def test_get_online_bot_info_no_games_played(self) -> None:
    lichess_client = FakeLichessClient()
    lichess_client.set_online_bots("""{ "username": "Bot-1", "perfs": { "bullet": { "rating": 1500, "prov": true } } }""")
    bot_info = data_generator_functions.get_online_bot_info(lichess_client)
    self.assertDictEqual(bot_info.bot_profiles_by_name, {})
    self.assertDictEqual(bot_info.bot_perfs_by_perf_type, {})

  def test_merge_bot_profiles(self) -> None:
    previous_profiles_by_name = {"Bot-1": BOT_1_PROFILE}
    current_profiles_by_name = {"Bot-1": BOT_1_CURRENT_PROFILE}
    self.assertDictEqual(
      data_generator_functions.merge_bot_profiles(previous_profiles_by_name, current_profiles_by_name),
      {"Bot-1": BOT_1_CURRENT_PROFILE.create_updated_copy_for_for_merge()},
    )
    self.assertDictEqual(data_generator_functions.merge_bot_profiles(previous_profiles_by_name, {}), previous_profiles_by_name)
    self.assertDictEqual(data_generator_functions.merge_bot_profiles({}, current_profiles_by_name), current_profiles_by_name)

  def test_create_updates(self) -> None:
    updates = data_generator_functions.create_updates([], [BOT_1_CURRENT_PERF_BULLET, BOT_2_CURRENT_PERF_BULLET])
    expected_updates = [
      CurrentBotPerfOnlyUpdate(BOT_1_CURRENT_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_2_CURRENT_PERF_BULLET),
    ]
    self.assertCountEqual(updates, expected_updates)

  def test_create_sort_key(self) -> None:
    bot_names = ["BOT-4", "Bot-2", "Bot-5", "bot-3", "bot-1", "Bot-4", "Bot-1"]
    sorted_bot_names = sorted(bot_names, key=lambda name: data_generator_functions.name_sort_key(name))
    self.assertListEqual(sorted_bot_names, ["Bot-1", "bot-1", "Bot-2", "bot-3", "BOT-4", "Bot-4", "Bot-5"])

  def test_create_ranked_rows(self) -> None:
    updates: list[LeaderboardUpdate] = [
      CurrentBotPerfOnlyUpdate(BOT_2_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_1_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_4_PERF_BULLET),
    ]
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, BOT_PROFILES_BY_NAME, DATE_2025_04_01)
    expected_leaderboard_rows = [
      LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-2", BOT_2_PERF_BULLET.perf, RankInfo(2, 0, 0, 0, 2, 2900, DATE_2025_04_01)),
      LeaderboardRow("Bot-4", BOT_4_PERF_BULLET.perf, RankInfo(3, 0, 0, 0, 3, 2800, DATE_2025_04_01)),
    ]
    self.assertListEqual(leaderboard_rows, expected_leaderboard_rows)

  def test_create_ranked_rows_tied_ratings(self) -> None:
    updates: list[LeaderboardUpdate] = [
      CurrentBotPerfOnlyUpdate(BOT_2_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_1_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_4_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_3_PERF_BULLET),
    ]
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, BOT_PROFILES_BY_NAME, DATE_2025_04_01)
    expected_leaderboard_rows = [
      LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-2", BOT_2_PERF_BULLET.perf, RankInfo(2, 0, 0, 0, 2, 2900, DATE_2025_04_01)),
      LeaderboardRow("Bot-3", BOT_3_PERF_BULLET.perf, RankInfo(2, 0, 0, 0, 2, 2900, DATE_2025_04_01)),
      LeaderboardRow("Bot-4", BOT_4_PERF_BULLET.perf, RankInfo(4, 0, 0, 0, 4, 2800, DATE_2025_04_01)),
    ]
    self.assertListEqual(leaderboard_rows, expected_leaderboard_rows)

  def test_create_ranked_rows_three_way_tie(self) -> None:
    updates: list[LeaderboardUpdate] = [
      CurrentBotPerfOnlyUpdate(BOT_1_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_4_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_1_PERF_BULLET),
      CurrentBotPerfOnlyUpdate(BOT_1_PERF_BULLET),
    ]
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, BOT_PROFILES_BY_NAME, DATE_2025_04_01)
    expected_leaderboard_rows = [
      LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-1", BOT_1_PERF_BULLET.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-4", BOT_4_PERF_BULLET.perf, RankInfo(4, 0, 0, 0, 4, 2800, DATE_2025_04_01)),
    ]
    self.assertListEqual(leaderboard_rows, expected_leaderboard_rows)

  def test_create_ranked_tie_sorted_by_rd(self) -> None:
    bot_1_perf = BotPerf("Bot-1", LeaderboardPerf(3000, 45, 0, 1000, False))
    bot_2_perf = BotPerf("Bot-2", LeaderboardPerf(3000, 60, 0, 1000, False))
    bot_3_perf = BotPerf("Bot-3", LeaderboardPerf(3000, 90, 0, 1000, False))
    updates: list[LeaderboardUpdate] = [
      CurrentBotPerfOnlyUpdate(bot_2_perf),
      CurrentBotPerfOnlyUpdate(bot_3_perf),
      CurrentBotPerfOnlyUpdate(bot_1_perf),
    ]
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, BOT_PROFILES_BY_NAME, DATE_2025_04_01)
    expected_leaderboard_rows = [
      LeaderboardRow("Bot-1", bot_1_perf.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-2", bot_2_perf.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-3", bot_3_perf.perf, RankInfo(1, 0, 0, 0, 1, 3000, DATE_2025_04_01)),
    ]
    self.assertListEqual(leaderboard_rows, expected_leaderboard_rows)

  def test_create_ranked_rows_ineligible_update(self) -> None:
    # Don't include provisional
    ineligible_bot_1_perf = BotPerf("Bot-1", LeaderboardPerf(3000, 0, 0, 1000, True))
    updates: list[LeaderboardUpdate] = [CurrentBotPerfOnlyUpdate(ineligible_bot_1_perf)]
    bot_profiles_by_name = {"Bot-1": BotProfile("Bot-1", "", "", DATE_2021_04_01, DATE_2025_04_01, False, False, False, True)}
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, bot_profiles_by_name, DATE_2025_04_01)
    self.assertEqual(leaderboard_rows[0].rank_info.rank, 0)

  def test_create_ranked_rows_no_ineligible(self) -> None:
    ineligible_bot_1_perf = BotPerf("Bot-1", LeaderboardPerf(3000, 0, 0, 1000, False))
    updates: list[LeaderboardUpdate] = [CurrentBotPerfOnlyUpdate(ineligible_bot_1_perf)]
    # Don't include last seen greater than two weeks
    bot_profiles_by_name = {"Bot-1": BotProfile("Bot-1", "", "", DATE_2021_04_01, DATE_2021_04_01, False, False, False, True)}
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, bot_profiles_by_name, DATE_2025_04_01)
    self.assertEqual(leaderboard_rows[0].rank_info.rank, 0)

  def test_create_ranked_rows_1224_ineligible(self) -> None:
    bot_1_perf = BotPerf("Bot-1", LeaderboardPerf(3000, 0, 0, 1000, False))
    # Ineligible due to prov=True
    bot_2_perf = BotPerf("Bot-2", LeaderboardPerf(2900, 0, 0, 1000, True))
    bot_3_perf = BotPerf("Bot-3", LeaderboardPerf(2900, 0, 0, 1000, False))
    updates: list[LeaderboardUpdate] = [
      CurrentBotPerfOnlyUpdate(bot_1_perf),
      CurrentBotPerfOnlyUpdate(bot_2_perf),
      CurrentBotPerfOnlyUpdate(bot_3_perf),
    ]
    leaderboard_rows = data_generator_functions.create_ranked_rows(updates, BOT_PROFILES_BY_NAME, DATE_2025_04_01)
    self.assertEqual(leaderboard_rows[0].rank_info.rank, 1)
    self.assertEqual(leaderboard_rows[1].rank_info.rank, 0)
    self.assertEqual(leaderboard_rows[2].rank_info.rank, 2)


class TestDataGenerator(unittest.TestCase):
  """Tests for DataGenerator."""

  def test_create_all_leaderboards(self) -> None:
    file_system = InMemoryFileSystem()

    bullet_leaderboard_json = [BOT_1_ROW_BULLET.as_dict(), BOT_2_ROW_BULLET.as_dict()]
    file_system.write_file(file_paths.data_path(PerfType.BULLET), json.dumps(bullet_leaderboard_json))

    bot_profiles_json = [BOT_1_PROFILE.as_dict(), BOT_2_PROFILE.as_dict()]
    file_system.write_file(file_paths.bot_profiles_path(), json.dumps(bot_profiles_json))

    lichess_client = FakeLichessClient()
    lichess_client.set_online_bots("\n".join([remove_whitespace(BOT_1_CURRENT_JSON), remove_whitespace(BOT_2_CURRENT_JSON)]))

    time_provider = FixedTimeProvider(DATE_2025_04_01)

    data_generator = DataGenerator(file_system, lichess_client, time_provider)
    leaderboard_data = data_generator.generate_leaderboard_data()

    expected_ranked_rows = [
      LeaderboardRow("Bot-1", BOT_1_CURRENT_PERF_BULLET.perf, RankInfo(2, -1, -50, 100, 1, 3000, DATE_2025_04_01)),
      LeaderboardRow("Bot-2", BOT_2_CURRENT_PERF_BULLET.perf, RankInfo(1, 1, 100, 100, 1, 3000, DATE_2025_04_01)),
    ]
    self.assertListEqual(leaderboard_data.get_ranked_rows_sorted()[PerfType.BULLET], expected_ranked_rows)

    expected_bot_profiles = [
      BOT_1_CURRENT_PROFILE.create_updated_copy_for_for_merge(),
      BOT_2_CURRENT_PROFILE.create_updated_copy_for_for_merge(),
    ]
    self.assertEqual(leaderboard_data.get_bot_profiles_sorted(), expected_bot_profiles)

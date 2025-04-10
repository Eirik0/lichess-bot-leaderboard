"""Leaderboard generator."""

import time

from src.leaderboard.chrono.time_provider import TimeProvider
from src.leaderboard.data.data_generator import DataGenerator
from src.leaderboard.fs import file_paths
from src.leaderboard.fs.file_system import FileSystem
from src.leaderboard.li.lichess_client import LichessClient
from src.leaderboard.log.log_writer import LogWriter
from src.leaderboard.page.html_generator import HtmlGenerator


class LeaderboardGenerator:
  """Generator of leaderboards."""

  def __init__(
    self, file_system: FileSystem, lichess_client: LichessClient, time_provider: TimeProvider, log_writer: LogWriter
  ) -> None:
    """Initialize a new generator."""
    self.file_system = file_system
    self.lichess_client = lichess_client
    self.time_provider = time_provider
    self.log_writer = log_writer

  def generate_leaderboards(self) -> None:
    """Generate the leaderboards."""
    # Start timer
    start_time = time.time()
    self.log_writer.info("Generating leaderboard...")

    # Generate leaderboard data
    data_generator = DataGenerator(self.file_system, self.lichess_client, self.time_provider)
    ranked_rows_by_perf_type = data_generator.generate_leaderboard_data()

    # Save the leaderboard data
    for perf_type, rows in ranked_rows_by_perf_type.items():
      self.file_system.save_file_lines(file_paths.data_path(perf_type), [row.to_json() for row in rows])

    # Generate leaderboard html
    html_generator = HtmlGenerator(self.time_provider)
    html_by_name = html_generator.generate_leaderboard_html(ranked_rows_by_perf_type)

    # Save the leaderboard html
    for name, html in html_by_name.items():
      self.file_system.save_file_lines(file_paths.html_path(name), [html])

    # Print time elapsed
    time_elapsed = time.time() - start_time
    self.log_writer.info("Finished in %.2fs", time_elapsed)

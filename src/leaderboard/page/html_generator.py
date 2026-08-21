"""Convert leaderboard data to html."""

import dataclasses
import itertools

from jinja2 import Environment, FileSystemLoader

from src.leaderboard.chrono import date_formatter, duration_formatter
from src.leaderboard.chrono.time_provider import TimeProvider
from src.leaderboard.data.data_generator import LeaderboardDataResult
from src.leaderboard.data.leaderboard_objects import BotProfile, LeaderboardRow
from src.leaderboard.li.pert_type import PerfType
from src.leaderboard.page import flag_emoji, meta_tags


MAX_RANK_FOR_PREVIEW = 10


@dataclasses.dataclass(frozen=True)
class NavLink:
  """An element of the navigation bar."""

  link: str
  name: str
  is_active: bool


@dataclasses.dataclass(frozen=True)
class MainFrame:
  """The main frame which is shared by the index and all of the leaderboard pages."""

  title: str
  nav_links: list[NavLink]
  last_updated_date: str
  description: str
  keywords: str

  @classmethod
  def from_perf_type(cls, perf_type: PerfType | None, current_time: int) -> "MainFrame":
    """Create a MainFrame for a given PerfType.

    If PerfType is None, create a MainFrame for the index page.
    """
    return MainFrame(
      perf_type.get_readable_name() if perf_type else "Lichess Bot Leaderboard",
      create_nav_links(perf_type),
      date_formatter.format_yyyy_mm_dd_hh_mm_ss(current_time),
      meta_tags.get_description(perf_type),
      meta_tags.get_keywords(perf_type),
    )


@dataclasses.dataclass(frozen=True)
class LeaderboardTitle:
  """Convenience class for styling leaderboard titles."""

  UPSIDE_DOWN_SUFFIX = "-upside-down"

  title_value: str
  emoji: str
  emoji_html_class_suffix: str

  @classmethod
  def get_emoji(cls, perf_type: PerfType) -> str:
    """Return the emoji that corresponds with the PerfType."""
    perf_type_to_emoji = {
      PerfType.BULLET: "🚅",
      PerfType.BLITZ: "🔥",
      PerfType.RAPID: "🐇",
      PerfType.CLASSICAL: "🐢",
      PerfType.CORRESPONDENCE: "💌",
      PerfType.CHESS960: "🎲",
      PerfType.ANTICHESS: "♟️",
      PerfType.THREE_CHECK: "🔱",
      PerfType.ATOMIC: "☢️",
      PerfType.KING_OF_THE_HILL: "🗻",
      PerfType.CRAZYHOUSE: "🏚️",
      PerfType.HORDE: "🛡️",
      PerfType.RACING_KINGS: "🏁",
    }
    return perf_type_to_emoji.get(perf_type, "")

  @classmethod
  def from_perf_type(cls, perf_type: PerfType) -> "LeaderboardTitle":
    """Create a LeaderboardTitle from a PerfType."""
    perf_type_emoji_html_class = {PerfType.ANTICHESS: LeaderboardTitle.UPSIDE_DOWN_SUFFIX}
    return LeaderboardTitle(
      perf_type.get_readable_name(), LeaderboardTitle.get_emoji(perf_type), perf_type_emoji_html_class.get(perf_type, "")
    )


@dataclasses.dataclass(frozen=True)
class LeaderboardDelta:
  """Convenience class for styling delta columns."""

  DELTA_POS_CLASS = "delta-pos"
  DELTA_NEG_CLASS = "delta-neg"

  formatted_value: str
  html_class: str

  @classmethod
  def for_delta(cls, delta: int) -> "LeaderboardDelta":
    """Return +n, -n, or blank."""
    if delta > 0:
      return LeaderboardDelta(f"+{abs(delta)}", LeaderboardDelta.DELTA_POS_CLASS)
    if delta < 0:
      return LeaderboardDelta(f"-{abs(delta)}", LeaderboardDelta.DELTA_NEG_CLASS)
    return LeaderboardDelta("", "")

  @classmethod
  def for_delta_rank(cls, rank: int, delta: int, new: bool) -> "LeaderboardDelta":
    """Return "new", "back", ↑n, ↓n, or blank."""
    if new:
      return LeaderboardDelta("🆕", "")
    if rank == -delta:
      # In this case a bot previously was ineligible (rank zero) and now they are eligible again.
      # This ends up also triggering for some cases where it is the bot's first time appearing on the leaderboard.
      return LeaderboardDelta("🔙", "")
    if delta > 0:
      return LeaderboardDelta(f"↑{abs(delta)}", LeaderboardDelta.DELTA_POS_CLASS)
    if delta < 0:
      return LeaderboardDelta(f"↓{abs(delta)}", LeaderboardDelta.DELTA_NEG_CLASS)
    return LeaderboardDelta("", "")


@dataclasses.dataclass(frozen=True)
class OnlineStatus:
  """Convenience class displaying whether the bot is online and if they are a patron."""

  BOT_ONLINE_CLASS = "bot-online"
  BOT_OFFLINE_CLASS = "bot-offline"
  DEFAULT_INDICATOR = "●"
  PATRON_INDICATOR = "★"

  indicator_icon: str
  html_class: str

  @classmethod
  def create_from(cls, online: bool, is_patron: bool) -> "OnlineStatus":
    """Create an OnlineStatus based on whether or not the bot is online and a patron."""
    html_class = OnlineStatus.BOT_ONLINE_CLASS if online else OnlineStatus.BOT_OFFLINE_CLASS
    indicator_icon = OnlineStatus.PATRON_INDICATOR if is_patron else OnlineStatus.DEFAULT_INDICATOR
    return OnlineStatus(indicator_icon, html_class)


@dataclasses.dataclass(frozen=True)
class Flag:
  """Convenience class for styling flags."""

  # How lichess represents the earth flag option
  LICHESS_EARTH_FLAG_STR = "_earth"

  EARTH_FLAG = "earth-flag"

  emoji: str
  html_class: str

  @classmethod
  def from_string(cls, flag_str: str) -> "Flag":
    """Create a Flag from a flag string."""
    if flag_str == Flag.LICHESS_EARTH_FLAG_STR:
      return Flag("", Flag.EARTH_FLAG)
    return Flag(flag_emoji.from_string(flag_str), "")


@dataclasses.dataclass(frozen=True)
class LeaderboardRd:
  """Convenience class for styling rating deviation."""

  UNSTABLE_CLASS = "rd-unstable"
  UNSTABLE_RD_MIN = 46
  UNSTABLE_RD_MAX = 109

  value: int
  html_class: str

  @classmethod
  def for_rd(cls, rd: int) -> "LeaderboardRd":
    """Return rd with unstable html class if applicable."""
    if cls.UNSTABLE_RD_MIN <= rd <= cls.UNSTABLE_RD_MAX:
      return LeaderboardRd(rd, LeaderboardRd.UNSTABLE_CLASS)
    return LeaderboardRd(rd, "")


@dataclasses.dataclass(frozen=True)
class HtmlLeaderboardRow:
  """The data required to render a leaderboard row in html."""

  medal: str
  rank: int
  delta_rank: LeaderboardDelta
  online_status: OnlineStatus
  name: str
  flag: Flag
  rating: int
  delta_rating: LeaderboardDelta
  rd: LeaderboardRd
  games: int
  delta_games: LeaderboardDelta
  age: str
  last_seen: str

  @classmethod
  def from_leaderboard_row(cls, row: LeaderboardRow, profile: BotProfile, current_time: int) -> "HtmlLeaderboardRow":
    """Convert a LeaderboardRow into an HtmlLeaderboardRow."""
    return HtmlLeaderboardRow(
      {1: "🥇", 2: "🥈", 3: "🥉"}.get(row.rank_info.rank, ""),
      row.rank_info.rank,
      LeaderboardDelta.for_delta_rank(row.rank_info.rank, row.rank_info.delta_rank, profile.new),
      OnlineStatus.create_from(profile.online, profile.patron),
      profile.name,
      Flag.from_string(profile.flag),
      row.perf.rating,
      LeaderboardDelta.for_delta(row.rank_info.delta_rating),
      LeaderboardRd.for_rd(row.perf.rd),
      row.perf.games,
      LeaderboardDelta.for_delta(row.rank_info.delta_games),
      duration_formatter.format_age(profile.created, current_time),
      duration_formatter.format_last_seen(profile.last_seen, current_time),
    )


@dataclasses.dataclass(frozen=True)
class HtmlLeaderboard:
  """The data required to render a leaderboard table in html."""

  title: LeaderboardTitle
  perf_type_str: str
  leaderboard_rows: list[HtmlLeaderboardRow]

  @classmethod
  def from_leaderboard_data(
    cls, leaderboard_data: LeaderboardDataResult, perf_type: PerfType, current_time: int, preview: bool = False
  ) -> "HtmlLeaderboard":
    """Create an HtmlLeaderboard from a LeaderboardDataResult.

    If preview is true, only return the top n rows. This is used to show previews on the index page.
    """
    rows = leaderboard_data.ranked_rows_by_perf_type.get(perf_type, [])
    # Only include bots within the top n ranks if creating a preview leaderboard for the index page
    rows = itertools.takewhile(lambda row: row.rank_info.rank <= MAX_RANK_FOR_PREVIEW, rows) if preview else rows
    return HtmlLeaderboard(
      LeaderboardTitle.from_perf_type(perf_type),
      perf_type.to_string(),
      [
        HtmlLeaderboardRow.from_leaderboard_row(row, leaderboard_data.bot_profiles_by_name[row.name], current_time)
        for row in rows
        # The rank is set to zero when the bot is not eligible for the leaderboard
        if row.rank_info.rank
      ],
    )


def create_nav_links(active_perf_type: PerfType | None) -> list[NavLink]:
  """Create the list of nav links shared by all pages.

  This also sets the active perf type to highlight the current page.
  """
  nav_links: list[NavLink] = []
  nav_links.append(NavLink("index.html", "Home", active_perf_type is None))
  nav_links.extend(
    NavLink(f"{perf_type.to_string()}.html", perf_type.get_readable_name(), perf_type == active_perf_type)
    for perf_type in PerfType.all_except_unknown()
  )
  return nav_links


class HtmlGenerator:
  """Generator for html."""

  def __init__(self, time_provider: TimeProvider) -> None:
    """Initialize a new generator."""
    self.time_provider = time_provider
    self.jinja_env = Environment(loader=FileSystemLoader("templates"), autoescape=True)

  def generate_leaderboard_html(self, leaderboard_data: LeaderboardDataResult) -> dict[str, str]:
    """Generate index and leaderboard html."""
    current_time = self.time_provider.get_current_time()
    html_by_name: dict[str, str] = {}
    # Create index html
    html_by_name["index"] = self.jinja_env.get_template("index.html.jinja").render(
      main_frame=MainFrame.from_perf_type(None, current_time),
      preview_leaderboards=[
        HtmlLeaderboard.from_leaderboard_data(leaderboard_data, perf_type, current_time, True)
        for perf_type in PerfType.all_except_unknown()
      ],
    )
    # Create leaderboard html
    for perf_type in PerfType.all_except_unknown():
      html_by_name[perf_type.to_string()] = self.jinja_env.get_template("leaderboard.html.jinja").render(
        main_frame=MainFrame.from_perf_type(perf_type, current_time),
        leaderboard=HtmlLeaderboard.from_leaderboard_data(leaderboard_data, perf_type, current_time),
      )
    # Return file name to html contents map
    return html_by_name

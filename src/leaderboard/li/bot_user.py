"""Bot user and related dataclasses.

These dataclasses include methods for parsing their corresponding lichess json representations.
"""

import dataclasses
import json
from collections.abc import Generator
from enum import Enum
from typing import Any


class PerfType(Enum):
  """Represents the time controls and variants (a.k.a. game modes) available on lichess.

  Related lichess documentation:
    - https://lichess.org/faq#time-controls
    - https://lichess.org/variant
  """

  # Default value
  UNKNOWN = 0

  # Regular time controls...
  # https://en.wikipedia.org/wiki/Fast_chess#Bullet
  BULLET = 1  # <= 179s (< 3m)
  # https://en.wikipedia.org/wiki/Fast_chess#Blitz
  BLITZ = 2  # <= 479s (< 8m)
  # https://en.wikipedia.org/wiki/Fast_chess#Rapid_(FIDE),_quick_(USCF),_or_active
  RAPID = 3  # <= 1499s (< 25m)
  # https://en.wikipedia.org/wiki/Time_control#Classification
  CLASSICAL = 4  # >= 1500s (>= 25m)

  # Asynchronous chess...
  # https://en.wikipedia.org/wiki/Correspondence_chess
  CORRESPONDENCE = 5

  # Variants...
  # https://en.wikipedia.org/wiki/Crazyhouse
  CRAZYHOUSE = 6  # https://lichess.org/variant/crazyhouse
  # https://en.wikipedia.org/wiki/Chess960
  CHESS960 = 7  # https://lichess.org/variant/chess960
  # https://en.wikipedia.org/wiki/List_of_chess_variants#King_of_the_Hill
  KING_OF_THE_HILL = 8  # https://lichess.org/variant/kingOfTheHill
  # https://en.wikipedia.org/wiki/Three-check_chess
  THREE_CHECK = 9  # https://lichess.org/variant/threeCheck
  # https://en.wikipedia.org/wiki/Losing_chess
  ANTICHESS = 10  # https://lichess.org/variant/antichess
  # https://en.wikipedia.org/wiki/Atomic_chess
  ATOMIC = 11  # https://lichess.org/variant/atomic
  # https://en.wikipedia.org/wiki/Dunsany%27s_chess#Horde_chess
  HORDE = 12  # https://lichess.org/variant/horde
  # https://en.wikipedia.org/wiki/V._R._Parton#Racing_Kings
  RACING_KINGS = 13  # https://lichess.org/variant/racingKings

  @classmethod
  def all_except_unknown(cls) -> Generator["PerfType"]:
    """Yield all PerfType values except UNKNOWN."""
    for perf_type in PerfType:
      if perf_type != PerfType.UNKNOWN:
        yield perf_type

  @classmethod
  def from_json(cls, json_str: str) -> "PerfType":
    """Return the corresponding PerfType based on the json representation."""
    name_to_perf_type = {
      "bullet": PerfType.BULLET,
      "blitz": PerfType.BLITZ,
      "rapid": PerfType.RAPID,
      "classical": PerfType.CLASSICAL,
      "correspondence": PerfType.CORRESPONDENCE,
      "crazyhouse": PerfType.CRAZYHOUSE,
      "chess960": PerfType.CHESS960,
      "kingOfTheHill": PerfType.KING_OF_THE_HILL,
      "threeCheck": PerfType.THREE_CHECK,
      "antichess": PerfType.ANTICHESS,
      "atomic": PerfType.ATOMIC,
      "horde": PerfType.HORDE,
      "racingKings": PerfType.RACING_KINGS,
    }
    return name_to_perf_type.get(json_str, PerfType.UNKNOWN)

  def to_string(self) -> str:
    """Return the original string (json) representation."""
    perf_type_to_name = {
      PerfType.BULLET: "bullet",
      PerfType.BLITZ: "blitz",
      PerfType.RAPID: "rapid",
      PerfType.CLASSICAL: "classical",
      PerfType.CORRESPONDENCE: "correspondence",
      PerfType.CRAZYHOUSE: "crazyhouse",
      PerfType.CHESS960: "chess960",
      PerfType.KING_OF_THE_HILL: "kingOfTheHill",
      PerfType.THREE_CHECK: "threeCheck",
      PerfType.ANTICHESS: "antichess",
      PerfType.ATOMIC: "atomic",
      PerfType.HORDE: "horde",
      PerfType.RACING_KINGS: "racingKings",
    }
    return perf_type_to_name.get(self, "unknown")

  def get_readable_name(self) -> str:
    """Return a readable name for the perf type with spaces, ect."""
    perf_type_to_name = {
      PerfType.BULLET: "Bullet",
      PerfType.BLITZ: "Blitz",
      PerfType.RAPID: "Rapid",
      PerfType.CLASSICAL: "Classical",
      PerfType.CORRESPONDENCE: "Correspondence",
      PerfType.CRAZYHOUSE: "Crazyhouse",
      PerfType.CHESS960: "Chess960",
      PerfType.KING_OF_THE_HILL: "King of the Hill",
      PerfType.THREE_CHECK: "Three Check",
      PerfType.ANTICHESS: "Antichess",
      PerfType.ATOMIC: "Atomic",
      PerfType.HORDE: "Horde",
      PerfType.RACING_KINGS: "Racing Kings",
    }
    return perf_type_to_name.get(self, "Unknown")


@dataclasses.dataclass(frozen=True)
class Perf:
  """Performance refers to a players ratings for a particular time control or variant.

  Example game modes include: bullet, blitz, classical, chess960, ...

  In the lichess API the field `perfs` is a list of performances.
  """

  # The time control or variant
  perf_type: PerfType
  # The number of games the bot has played
  games: int
  # The bot's rating for this PerfType
  rating: int
  # The bot's rating deviation
  rd: int
  # The bot's rating change (progress) over the last 12 games
  prog: int
  # If the bot's rating is provisional
  # See: https://lichess.org/faq#provisional
  prov: bool

  @classmethod
  def from_json(cls, perf_type_key: str, perf_json: dict[str, Any]) -> "Perf":
    """Create a Perf based on a json key and value."""
    perf_type = PerfType.from_json(perf_type_key)
    games = perf_json.get("games", 0)
    rating = perf_json.get("rating", 0)
    rd = perf_json.get("rd", 0)
    prog = perf_json.get("prog", 0)
    prov = perf_json.get("prov", False)
    return Perf(perf_type, games, rating, rd, prog, prov)


@dataclasses.dataclass(frozen=True)
class BotUser:
  """A bot user and their list of performances.

  This only contains a small subset of what is available via the lichess API.
  """

  # The bot's username
  username: str
  # The bot's flair
  flair: str
  # The bot's country flag
  flag: str
  # The time the bot was created (seconds since epoch)
  created_at: int
  # If the bot is a patron
  patron: bool
  # If the bot has violated the terms of service
  tos_violation: bool
  # The bot's list of performance ratings
  perfs: list[Perf]

  @classmethod
  def from_json(cls, json_str: str) -> "BotUser":
    """Parse a line of ndjson and converts it to an BotUser."""
    json_dict = json.loads(json_str)

    username = json_dict.get("username", "")
    flair = json_dict.get("flair", "")
    profile_dict = json_dict.get("profile", {})
    flag = profile_dict.get("flag", "")
    created_at = json_dict.get("createdAt", 0) // 1000
    patron = json_dict.get("patron", False)
    tos_violation = json_dict.get("tosViolation", False)

    perfs: list[Perf] = []
    for perf_type_key, perf_json in json_dict.get("perfs", []).items():
      perfs.append(Perf.from_json(perf_type_key, perf_json))

    return BotUser(username, flair, flag, created_at, patron, tos_violation, perfs)

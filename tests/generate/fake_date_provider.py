"""Test implementation of DateProvider which allows setting the current date."""

from src.generate.date_provider import DateProvider


class FakeDateProvider(DateProvider):
  """A fake implementation of DateProvider."""

  def __init__(self) -> None:
    """Create a fake date provider and set the current time to 0 (1970-01-01)."""
    self.current_time = 0

  def set_current_time(self, current_time: float) -> None:
    """Set the current time to be returned by get_current_time."""
    self.current_time = current_time

  def get_current_time(self) -> float:
    """Return the current time."""
    return self.current_time

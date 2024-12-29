from datetime import datetime, timedelta
from src.utils.helpers import MatchStatus


def iso_date_to_offset(iso_date_time: str, time_status: MatchStatus) -> None | str:
    """
    Determines the next match status time based on the current time and match status.

    Args:
        iso_date_time (str): ISO-formatted date-time string (e.g., "2024-12-24T15:00:00").
        time_status (MatchStatus): Current status of the match (RUNNING or HALF_TIME).

    Returns:
        None | str: ISO-formatted string of the next status time, or None if conditions are not met.
    """
    try:
        match_time = datetime.fromisoformat(iso_date_time)
        current_time = datetime.now()

        if time_status.value == MatchStatus.RUNNING.value:
            # Calculate half-time (45 minutes after the match start time)
            half_time = match_time + timedelta(minutes=45)
            if current_time > half_time:
                return half_time.isoformat()

        elif time_status.value == MatchStatus.HALF_TIME.value:
            # Calculate end-time (45 minutes after half-time)
            end_time = match_time + timedelta(minutes=90)
            if current_time > end_time:
                return end_time.isoformat()

    except ValueError as e:
        print(f"Invalid ISO date-time format: {e}")

    return None

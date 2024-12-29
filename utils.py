
from datetime import datetime, timezone
from types import SimpleNamespace
from dateutils import relativedelta


def dict_to_simplenamespace(data):
    """Recursively convert a dictionary to SimpleNamespace."""
    if isinstance(data, dict):
        # Create a SimpleNamespace for the current dictionary
        namespace = SimpleNamespace(**{key: dict_to_simplenamespace(value) for key, value in data.items()})
        return namespace
    return data  # Return the value if it's not a dictionary

def change_timezone(dt, target_timezone=None):
    """Convert a datetime's timezone to the specified timezone or the local timezone if not specified."""
    if target_timezone is None:
        target_timezone = datetime.now().astimezone().tzinfo
    else:
        target_timezone = timezone(target_timezone)
    
    dt = dt.replace(tzinfo=target_timezone)
    
    return dt


def alter_event_timezone(event, target_timezone=None):
    event.created_at = change_timezone(datetime.fromisoformat(event.created_at), target_timezone)
    return event 


def filter_events(events, from_date: str | None = None, until_date: str | None = None):

    def get_delta(unit):
        if not unit:
            return relativedelta(0)

        unit_kind = unit[len(unit) - 1]

        value = int(unit[:-1])

        if unit_kind == "d":
            return relativedelta(days=value)
        elif unit_kind == "w":
            return relativedelta(weeks=value)
        elif unit_kind == "h":
            return relativedelta(hours=value)
        elif unit_kind == "mo":
            return relativedelta(months=value)
        elif unit_kind == "y":
            return relativedelta(years=value)
        elif unit_kind == "m":
            return relativedelta(minutes=value)
        else:
            raise Exception("Wrong time unit")

    from_delta = get_delta(from_date)
    until_delta = get_delta(until_date)

    def filter_event(event):
        dt_created_at = datetime.fromisoformat(event.created_at)  # Ensure it is UTC-aware
        from_datetime = datetime.now(timezone.utc) - from_delta
        until_datetime = None
        if until_delta == relativedelta(0): until_datetime = datetime.min.replace(tzinfo=timezone.utc)  # Minimum representable datetime
        else: until_datetime = from_datetime - until_delta
        return dt_created_at >= until_datetime and dt_created_at <= from_datetime
        
    return filter(filter_event, events)
from urllib import parse as http_parse
from urllib import response as http_response
from urllib import request as http_request
import urllib.error
from http import HTTPStatus
import sys
import argparse
import json
from types import SimpleNamespace
import logging
from datetime import datetime, timezone
from dateutils import relativedelta
import socket

github_events_url = "https://api.github.com/users/{username}/events"

def dict_to_simplenamespace(data):
    """Recursively convert a dictionary to SimpleNamespace."""
    if isinstance(data, dict):
        # Create a SimpleNamespace for the current dictionary
        namespace = SimpleNamespace(**{key: dict_to_simplenamespace(value) for key, value in data.items()})
        return namespace
    return data  # Return the value if it's not a dictionary

time_unit_to_datetime_mapping = {
    "d": "days",
    "m": "months",
    "y": "years",
    "w": "weeks",
    "h": "hours",
}

def filter_events(events, from_=None, until=None):
    def get_delta(unit):
        if not unit:
            return relativedelta(0)

        unit_kind = unit[len(unit) - 1]

        if unit_kind == "d":
            return relativedelta(days=unit[:-1])
        elif unit_kind == "w":
            return relativedelta(weeks=unit[:-1])
        elif unit_kind == "h":
            return relativedelta(hours=unit[:-1])
        elif unit_kind == "mo":
            return relativedelta(months=unit[:-1])
        elif unit_kind == "y":
            return relativedelta(years=unit[:-1])
        elif unit_kind == "m":
            return relativedelta(minutes=unit[:-1])
        else:
            raise Exception("Wrong time unit")

    from_delta = get_delta(from_)
    until_delta = get_delta(until)

    def filter_event(event):
        created_at = datetime.fromisoformat(event.created_at)  # Ensure it is UTC-aware
        from_datetime = datetime.now(timezone.utc) - from_delta
        until_datetime = None
        if until_delta == relativedelta(0): until_datetime = datetime.min.replace(tzinfo=timezone.utc)  # Minimum representable datetime
        else: until_datetime = from_datetime - until_delta
        return created_at >= until_datetime and created_at <= from_datetime
        
    return filter(filter_event, events)
    
        

    # threshold = datetime.now(timezone.utc) - timedelta({
    #     time_unit_to_datetime_mapping["mode"]: unit,
    # })

def build_parser():
    parser = argparse.ArgumentParser(
        prog="Github Activity Visualizer - CLI",
        description="Tool to display a user's activity on Github per the Github's official API",
    )

    parser.add_argument("username")
    parser.add_argument("--from") 
    parser.add_argument("--until")  
    parser.add_argument("--timeout", default=10)
    parser.add_argument("-t", "--trial-count", default=1)
    parser.add_argument("-v", "--verbose", action="count") #TODO to be implemented
    return parser

def main():
    parser = build_parser()
    namespace = parser.parse_args()
    attempts = namespace.trial_count
    res = None
    for attempt in range(attempts):
        try: 
            res = http_request.urlopen(
                github_events_url.format(username=namespace.username),
                timeout=namespace.timeout,
            )
            break
        except urllib.error.HTTPError as err:
            pass
        except urllib.error.URLError as err:
            if isinstance(err.reason, socket.timeout) and attempt + 1 == attempts:
                logging.error(f"Request timeout. Max attempt count has been reached. {attempt + 1}/{attempts}")
                sys.exit(21)
            elif isinstance(err.reason, socket.gaierror):
                logging.error("Network is unreachable or DNS lookup failed")
                sys.exit(22)
            else:
                logging.error(f"Something bad happened while making the request! :(\n{err}")
                sys.exit(299)
        except Exception as err:
            logging.error("Something unexpected happened!")
            raise err

    if res.status == HTTPStatus.OK:
        body_json = json.loads(
            res.read().decode('utf-8')
        )
        events = filter_events(
            map(dict_to_simplenamespace, body_json)
        )
        for event in events:
            event_type = event.type.lower().replace("event", "")
            info = ""
            if event_type == "push":
                info = f'Pushed {event.payload.size} commit{"s" if event.payload.size > 1 else ""} to {event.repo.name} at {event.created_at}'
            if event_type == "watch":
                info = f'Watched {event.repo.name} at {event.created_at}'    
            if event_type == "open":
                info = f'Opened an issue at {event.created_at}'
            if event_type == "issuecomment":
                info = f'Commented an issue in repo {event.repo.name} with title "{event.payload.issue.title}" to user "{event.payload.issue.user}" at {event.created_at}'
            print(info)
    


main()


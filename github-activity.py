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
from datetime import datetime, timezone, timedelta

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

def filter_events(event, from_=None, until=None):
    def get_delta(unit):
        unit_kind = unit[len(unit) - 1]
    
        if unit_kind == "d":
            return timedelta(days=unit[:-1])
        elif unit_kind == "w":
            return timedelta(weeks=unit[:-1])
        elif unit_kind == "h":
            return timedelta(hours=unit[:-1])
        
    
    from_delta = get_delta(from_)
    until_delta = get_delta(until)

        
        
    threshold = datetime.now(timezone.utc) - timedelta({
        time_unit_to_datetime_mapping["mode"]: unit,
    })
    if datetime.fromisoformat(event.created_at[:-1]) 

def build_parser():
    parser = argparse.ArgumentParser(
        prog="Github Activity Visualizer - CLI",
        description="Tool to display a user's activity on Github per the Github's official API",
        
    )

    parser.add_argument("username")
    parser.add_argument("--from") #TODO to be implemented
    parser.add_argument("--until") #TODO to be implemented
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
            if attempt + 1 == attempts:
                logging.error(f"Request timeout. Max attempt count has been reached. {attempt + 1}/{attempts}")
                sys.exit(20)
            

    if res.status == HTTPStatus.OK:
        body_json = json.loads(
            res.read().decode('utf-8')
        )
        for event_dict in body_json:
            event = dict_to_simplenamespace(event_dict)
            
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


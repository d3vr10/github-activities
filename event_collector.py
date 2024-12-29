import json
import sys
import colorama
import jsonpickle
from utils import alter_event_timezone, dict_to_simplenamespace, filter_events


def collect_events(carrier, from_date=None, until_date=None, verbose=0, toJSON=False, pretty=True):
    body_text = carrier.read().decode('utf-8') or '[]' #For cases when HTTP response body is empty, since empty strings violate JSON rules.
    body_json = json.loads(body_text)
    events = filter_events(
        map(dict_to_simplenamespace, body_json),
        from_date=from_date,
        until_date=until_date,
    ) 
    events = map(alter_event_timezone, events)
    
    if verbose < 2 and not toJSON:
        for event in events:
            event_type = event.type.lower().replace("event", "")
            info = ""
            if event_type == "push":
                info = f'Pushed {event.payload.size} commit{"s" if event.payload.size > 1 else ""} to {event.repo.name} at {event.created_at}'
            elif event_type == "watch":
                info = f'Watched {event.repo.name} at {event.created_at}'    
            elif event_type == "open":
                info = f'Opened an issue at {event.created_at}'
            elif event_type == "issuecomment":
                info = f'Commented an issue in repo {event.repo.name} with title "{event.payload.issue.title}" to user "{event.payload.issue.user}" at {event.created_at}'
            elif event_type == "create":
                info = f'Created a {event.payload.ref_type} with ref "{event.payload.ref}" in repo "{event.repo.name}" at {event.created_at}'
            if len(info) > 0: print(colorama.Fore.GREEN + info)
            else: print("No activity is available currently")
    elif verbose < 2 and toJSON:
        json_string = jsonpickle.encode(
            events, 
            indent=2 if pretty else None, 
            unpicklable=False,
        )
        print()
        sys.stdout.write(json_string)
        sys.stdout.flush()

    else:
        json_string = jsonpickle.encode(
            events, 
            indent=2 if pretty else None, 
            unpicklable=False,
        )

        print() #For formatting purposes
        sys.stdout.write(json_string)
        sys.stdout.flush()
        
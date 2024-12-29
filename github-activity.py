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
import struct
import platform
import subprocess
import time
import os
import ctypes
from argparse import RawDescriptionHelpFormatter
from tqdm import tqdm
import io
import colorama

if __name__ == "__main__":
    colorama.init(autoreset=True)


class ColorFormatter(logging.Formatter):
    """Custom logging formatter to add colors to log messages."""
    def format(self, record):
        log_colors = {
            logging.DEBUG: colorama.Fore.CYAN,
            logging.INFO: colorama.Fore.BLUE,
            logging.WARNING: colorama.Fore.YELLOW,
            logging.ERROR: colorama.Fore.RED,
            logging.CRITICAL: colorama.Fore.RED + colorama.Style.BRIGHT,
        }
        log_color = log_colors.get(record.levelno, colorama.Fore.WHITE)
        record.msg = log_color + record.msg + colorama.Style.RESET_ALL
        return super().format(record)

# Set up logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


cli_description="""
Tool to display a user's activity on Github per the Github's official API.

It may potentially be helpful to introduce credentials in case you want to see events from private repos to or users' private activity that Github determines you have access to.
"""
gh_user_events_url = "https://api.github.com/users/{username}/events"
gh_repo_events_url = "https://api.github.com/repos/{username}/{repo}/events"

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def run_as_admin():
    if platform.system() == "Windows":
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)
    else:
        os.execvp("sudo", ["sudo"] + sys.argv)

def get_local_timezone_offset():
    """Returns the local timezone offset in seconds."""
    if time.localtime().tm_isdst and time.daylight:
        return -time.altzone
    else:
        return -time.timezone

def sync_time_with_ntp():
    try:
        if not is_admin():
            run_as_admin()
            return
        
        ntp_server = 'pool.ntp.org'
        port = 123
        buf = 1024
        address = (ntp_server, port)
        msg = b'\x1b' + 47 * b'\0'

        # Connect to NTP server
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.sendto(msg, address)
        msg, _ = client.recvfrom(buf)
        t = struct.unpack('!12I', msg)[10]
        t -= 2208988800  # Convert NTP time to Unix time

        # Get the local timezone offset
        local_tz_offset = get_local_timezone_offset()
        local_time = datetime.fromtimestamp(t, tz=timezone.utc) + relativedelta(seconds=local_tz_offset)

        if platform.system() == "Windows":
            # Set system time on Windows
            system_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
            subprocess.run(["powershell", "-Command", f"Set-Date -Date \"{system_time}\""], check=True)
        else:
            # Set system time on Unix-based systems
            system_time = local_time.strftime('%m%d%H%M%Y.%S')
            subprocess.run(["sudo", "date", system_time], check=True)
        
        logging.info(f"System time synchronized to: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except Exception as e:
        logging.error(f"Failed to synchronize time: {e}")

def get_ntp_time():
    ntp_server = 'pool.ntp.org'
    port = 123
    buf = 1024
    address = (ntp_server, port)
    msg = b'\x1b' + 47 * b'\0'

    # Connect to NTP server
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.sendto(msg, address)
    msg, _ = client.recvfrom(buf)
    t = struct.unpack('!12I', msg)[10]
    t -= 2208988800  # Convert NTP time to Unix time

    return datetime.fromtimestamp(t, tz=timezone.utc)

def is_time_out_of_sync(threshold_seconds=300):
    ntp_time = get_ntp_time()
    local_time = datetime.now(timezone.utc)
    time_difference = abs((ntp_time - local_time).total_seconds())
    return time_difference > threshold_seconds


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
def change_timezone(dt, target_timezone=None):
    """Convert a datetime's timezone to the specified timezone or the local timezone if not specified."""
    if target_timezone is None:
        target_timezone = datetime.now().astimezone().tzinfo
    else:
        target_timezone = timezone(target_timezone)
    
    dt = dt.replace(tzinfo=target_timezone)
    
    return dt

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

def alter_event_timezone(event, target_timezone=None):
    event.created_at = change_timezone(datetime.fromisoformat(event.created_at), target_timezone)
    return event 

def build_parser():
    parser = argparse.ArgumentParser(
        prog="Github Activity Visualizer - CLI",
        description=cli_description,
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument("username")
    parser.add_argument("--from-date", action="store", default=None) 
    parser.add_argument("--until-date", action="store", default=None)
    parser.add_argument("-r", "--repo", action="store", default=None) 
    parser.add_argument("--auth-username", action="store", default=None)
    parser.add_argument("-nt", "--no-timesync", action="store_true", default=False, help="Disables time syncing support. WARNING: If time is not in sync recent events might be filtered out from the feed.")
    parser.add_argument("--auth-password", action="store", default=None)
    parser.add_argument("--auth-token", action="store", default=None)
    parser.add_argument("--json", action="store_true", default=False, help="Formats output to JSON") #To be implemented!
    parser.add_argument("--timeout", default=10, help="Request timeout in seconds.")
    parser.add_argument("-t", "--trial-count", default=1, help="Number of attempts to make the request. If it fails more than the provided number, the program will fail. Default is \"1\"")
    parser.add_argument("-v", "--verbose", action="count", help="Verbose output. multiple usages (MAX: 3) increment the level of verbosity.") #TODO to be implemented
    return parser

def collect_events(carrier, from_date=None, until_date=None):
    body_text = carrier.read().decode('utf-8') or '[]' #For cases when HTTP response body is empty, since empty strings violate JSON rules.
    body_json = json.loads(body_text)
    events = filter_events(
        map(dict_to_simplenamespace, body_json),
        from_date=from_date,
        until_date=until_date,
    ) 
    events = map(alter_event_timezone, events)
    
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

def fetch_github_activity(username, repo=None, timeout=10, attempts=1, auth={
    "token": None,
    "user": None,
    "password": None,
}):
    effective_url = None
    if repo: effective_url = gh_repo_events_url.format(username=username, repo=repo)
    else: effective_url = gh_user_events_url.format(username=username)

    for attempt in range(attempts):
        try: 
            headers = {
                "Content-Type": "application/json"
            }
            if auth:
                if auth.get("token"):
                    headers["Authorization"] = f'token {auth["token"]}'

            req = http_request.Request(effective_url, headers=headers)
            with http_request.urlopen(
                req,
                timeout=timeout,
            ) as res:
                if res.status == HTTPStatus.OK:
                    content_length = res.getheader("Content-Length")
                    chunk_size = 1024
                    data = []
                    if content_length:
                        total_size = int(content_length.strip())
                        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading...") as pbar:
                            while True:
                                chunk = res.read(chunk_size)
                                if not chunk:
                                    break
                                data.append(chunk)
                                pbar.update(len(chunk))
                    
                    else:
                        # Indeterminate progress bar
                        with tqdm(unit='B', unit_scale=True, desc="Downloading", leave=False) as pbar:
                            while True:
                                chunk = res.read(chunk_size)
                                if not chunk:
                                    break
                                data.append(chunk)
                                pbar.update(len(chunk))
                    print()
                    return http_response.addinfourl(io.BytesIO(b''.join(data)), res.headers, effective_url, res.status)
                                
        except urllib.error.HTTPError as err:
            logging.error(f"HTTP Error: {err.code}. Terminating the program!")
            sys.exit(20)
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

def main():
    parser = build_parser()
    namespace = parser.parse_args()
    if not namespace.no_timesync and is_time_out_of_sync():
        sync_time_with_ntp()
    res = fetch_github_activity(
        namespace.username, 
        repo=namespace.repo, 
        timeout=namespace.timeout, 
        attempts=namespace.trial_count,
        auth={
            "username": namespace.auth_username,
            "token": namespace.auth_token,
            "password": namespace.auth_password,
        }
    )

    if res.status == HTTPStatus.OK:
        collect_events(res, from_date=namespace.from_date, until_date=namespace.until_date)
    


main()



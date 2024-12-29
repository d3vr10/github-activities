from http import HTTPStatus
import argparse
from event_collector import collect_events
from github_api import fetch_github_activity
from logger import logger
from argparse import RawDescriptionHelpFormatter

from sync_time import is_time_out_of_sync, sync_time_with_ntp
from utils import alter_event_timezone, dict_to_simplenamespace, filter_events

cli_description="""
Tool to display a user's activity on Github per the Github's official API.

It may potentially be helpful to introduce credentials in case you want to see events from private repos to or users' private activity that Github determines you have access to.
"""

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
    parser.add_argument("--json", action="store_true", default=False, help="Formats output to JSON") 
    parser.add_argument("--ugly", action="store_true", default=False, help="This flag can only be specified along with --json. It enforces no pretty formatting is applied to the output.") 
    parser.add_argument("--timeout", default=10, help="Request timeout in seconds.")
    parser.add_argument("-t", "--trial-count", type=int, action="store", default=1, help="Number of attempts to make the request. If it fails more than the provided number, the program will fail. Default is \"1\"")
    parser.add_argument("-v", "--verbose", action="count", help="Verbose output. multiple usages (MAX: 3) increment the level of verbosity.") #TODO to be implemented
    return parser


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
        collect_events(
            res, 
            from_date=namespace.from_date, 
            until_date=namespace.until_date, 
            verbose=namespace.verbose, 
            pretty=not namespace.ugly,
        )


main()


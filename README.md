# Github User Activity

This tool displays a user's activity on Github using the official Github API. It supports fetching events from both public and private repositories, with optional time synchronization to ensure accurate event filtering.

## Features

- Fetches user activity from Github
- Supports authentication for private repositories
- Optional time synchronization with NTP server
- Filters events based on date range
- Outputs events in JSON format (optional)
- Verbose output for detailed logging

```
usage: Github Activity Visualizer - CLI [-h] [--from-date FROM_DATE] [--until-date UNTIL_DATE] [-r REPO] [--auth-username AUTH_USERNAME] [-nt]
                                        [--auth-password AUTH_PASSWORD] [--auth-token AUTH_TOKEN] [--json] [--timeout TIMEOUT] [-t TRIAL_COUNT] [-v]
                                        username

Tool to display a user's activity on Github per the Github's official API.

It may potentially be helpful to introduce credentials in case you want to see events from private repos to or users' private activity that Github determines you have access to.

positional arguments:
  username

options:
  -h, --help            show this help message and exit
  --from-date FROM_DATE
  --until-date UNTIL_DATE
  -r, --repo REPO
  --auth-username AUTH_USERNAME
  -nt, --no-timesync    Disables time syncing support. WARNING: If time is not in sync recent events might be filtered out from the feed.
  --auth-password AUTH_PASSWORD
  --auth-token AUTH_TOKEN
  --json                Formats output to JSON
  --timeout TIMEOUT     Request timeout in seconds.
  -t, --trial-count TRIAL_COUNT
                        Number of attempts to make the request. If it fails more than the provided number, the program will fail. Default is "1"
  -v, --verbose         Verbose output. multiple usages (MAX: 3) increment the level of verbosity.
```


#### Roadmap.sh url: 
https://roadmap.sh/projects/github-user-activity
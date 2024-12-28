## Github User Activity

DOCS:
`
usage: Github Activity Visualizer - CLI [-h] [--from-date FROM_DATE] [--until-date UNTIL_DATE] [-r REPO] [--auth-username AUTH_USERNAME] [-nt]
                                        [--auth-password AUTH_PASSWORD] [--auth-token AUTH_TOKEN] [--json] [--timeout TIMEOUT] [-t TRIAL_COUNT] [-v]
                                        username

Tool to display a user's activity on Github per the Github's official API

positional arguments:
  username

options:
  -h, --help            show this help message and exit
  --from-date FROM_DATE
  --until-date UNTIL_DATE
  -r, --repo REPO
  --auth-username AUTH_USERNAME
  -nt, --no-timesync
  --auth-password AUTH_PASSWORD
  --auth-token AUTH_TOKEN
  --json
  --timeout TIMEOUT     Request timeout in seconds.
  -t, --trial-count TRIAL_COUNT
                        Number of attempts to make the request. If it fails more than the provided number, the program will fail. Default is "1"
  -v, --verbose         Verbose output. multiple usages (MAX: 3) increment the level of verbosity.
  `


Roadmap.sh url: https://roadmap.sh/projects/github-user-activity
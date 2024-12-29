from http import HTTPStatus
import socket
import sys
from tqdm import tqdm
from urllib import parse as http_parse
from urllib import response as http_response
from urllib import request as http_request
import urllib.error
import logger


gh_user_events_url = "https://api.github.com/users/{username}/events"
gh_repo_events_url = "https://api.github.com/repos/{username}/{repo}/events"

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
                    return http_response.addinfourl(io.BytesIO(b''.join(data)), res.headers, effective_url, res.status)
                                
        except urllib.error.HTTPError as err:
            logger.error(f"HTTP Error: {err.code}. Terminating the program!")
            sys.exit(20)
        except urllib.error.URLError as err:
            if isinstance(err.reason, socket.timeout) and attempt + 1 == attempts:
                logger.error(f"Request timeout. Max attempt count has been reached. {attempt + 1}/{attempts}")
                sys.exit(21)
            elif isinstance(err.reason, socket.gaierror):
                logger.error("Network is unreachable or DNS lookup failed")
                sys.exit(22)
            else:
                logger.error(f"Something bad happened while making the request! :(\n{err}")
                sys.exit(299)
        except Exception as err:
            logger.error("Something unexpected happened!")
            raise err
import ctypes
from datetime import datetime, timezone
from dateutils import relativedelta
import os
import platform
import socket
import struct
import subprocess
import sys
import time
from venv import logger


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
        
        logger.info(f"System time synchronized to: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except Exception as e:
        logger.error(f"Failed to synchronize time: {e}")

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
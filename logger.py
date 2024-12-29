
import logging
import colorama
import platform

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

# Fix Windows console colors
if platform.system() == 'Windows':
    colorama.just_fix_windows_console()

# Set up logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
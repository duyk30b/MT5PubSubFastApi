import logging
from typing import Any

logging.basicConfig(level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("app").setLevel(logging.DEBUG)
logging.getLogger("alembic").setLevel(logging.WARNING)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("passlib").setLevel(logging.WARNING)


class ColorFormatter(logging.Formatter):
    RESET = "\033[0m"
    RED = "\033[31m"  # Red
    GREEN = "\033[32m"  # Green
    YELLOW = "\033[33m"  # Yellow
    BLUE = "\033[34m"  # Blue
    MAGENTA = "\033[35m"  # Magenta
    CYAN = "\033[36m"  # Cyan
    WHITE = "\033[37m"  # White
    BOLD_RED = "\033[1;31m"  # Bold Red

    COLORS = {
        logging.DEBUG: MAGENTA,
        logging.ERROR: RED,
        logging.INFO: GREEN,
        logging.WARNING: YELLOW,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record: Any) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"


handler = logging.StreamHandler()
handler.setFormatter(
    ColorFormatter(
        "%(asctime)s [%(levelname)s-%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)

root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers.clear()  # tránh duplicate
root.addHandler(handler)

import logging
import sys

LEVEL_COLORS = {
    logging.DEBUG:    "\033[2m",
    logging.INFO:     "\033[36m",
    logging.WARNING:  "\033[33m",
    logging.ERROR:    "\033[31m",
    logging.CRITICAL: "\033[1;31m",
}
RESET = "\033[0m"


class ColorFormatter(logging.Formatter):
    use_color = sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self.use_color:
            color = LEVEL_COLORS.get(record.levelno, "")
            record.levelname = f"{color}{record.levelname}{RESET}"
        return super().format(record)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logging.basicConfig(level=logging.DEBUG, handlers=[handler])
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("numpy").setLevel(logging.WARNING)

import argparse
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .terminal_formatting import parse_color
from .version import program_version

PROGRAM_NAME = "whatsapp-trend-plotter"
NR = "[0-9]{1,2}"
MESSAGE_RE = re.compile(rf"({NR}/{NR}/{NR}\s*,\s*{NR}:{NR})\s*-\s*(\+?[\s0-9]+)\s*:\s*(\S(?:.|\r?\n\D)*)")

log = logging.getLogger(PROGRAM_NAME)
console = logging.StreamHandler()
log.addHandler(console)
log.setLevel(logging.DEBUG)
console.setFormatter(
    logging.Formatter(parse_color("{asctime} [ℂ3.{levelname:>5}ℂ.] ℂ4.{name}ℂ.: {message}"),
                      style="{", datefmt="%W %a %I:%M"))


@dataclass
class Message:
    time: datetime.datetime
    tel: str
    text: str


def get_matches(input_text, regex):
    for match in MESSAGE_RE.finditer(input_text):
        if regex is not None:
            if not regex.fullmatch(match.group(3)):
                continue

        yield Message(
            datetime.datetime.strptime(match.group(1).replace(" ", ""), "%m/%d/%y,%H:%M"),
            match.group(2),
            match.group(3),
        )


def command_entry_point():
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Program was interrupted by user")


def main():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description="I was interested when people were washing their laundry in my apartment complex. "
                                                 "This matches a regex against an exported whatsapp chat to produce an overview of matches over time.",
                                     allow_abbrev=True, add_help=True, exit_on_error=True)

    parser.add_argument('-v', '--verbose', action='store_true', help="Show more output")
    parser.add_argument("--version", action="store_true", help="Show the current version of the program")
    parser.add_argument("-r", "--regex", help="Select only messages matches the python regex")
    parser.add_argument("INPUT", help="Export file to parse")

    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.debug("Starting program...")

    if args.version:
        log.info(f"{PROGRAM_NAME} version {program_version}")
        return

    regex = None if args.regex is None else re.compile(args.regex, re.DOTALL)

    print(*get_matches(Path(args.INPUT).read_text(), regex), sep="\n")

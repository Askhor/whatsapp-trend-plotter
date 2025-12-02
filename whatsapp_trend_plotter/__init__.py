import argparse
import datetime
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .terminal_formatting import parse_color, bg_rgb_start, color_end
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


def show_matches(matches, show):
    for message in matches:
        output = []
        if 1 in show:
            output.append(message.time)
        if 2 in show:
            output.append(f"[{message.tel}]")
        if 3 in show:
            output.append(message.text)

        print(*output, sep=" ")


def show_week_overview(matches, numeric):
    buckets = [[0] * 24 for _ in range(7)]

    for match in matches:
        day = match.time.weekday()
        hour = match.time.hour

        buckets[day][hour] += 1

    if numeric:
        print("  ", *map(lambda n: f"{n:2}", range(24)))

        for i, line in enumerate(buckets):
            print("Mo,Tu,We,Th,Fr,Sa,Su".split(",")[i], *map(lambda n: f"{n:2}", line))
    else:
        print("  ", *map(lambda n: f"{n * 3:2}", range(8)))
        maximum = max(max(l) for l in buckets)

        def color(n):
            x = int(n / maximum * 255)
            return bg_rgb_start(x, 0, 255 - x)

        for i, line in enumerate(buckets):
            print(end="Mo,Tu,We,Th,Fr,Sa,Su".split(",")[i])
            for n in line:
                print(end=color(n) + " ")
            print(color_end())


def main():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description="I was interested when people were washing their laundry in my apartment complex. "
                                                 "This matches a regex against an exported whatsapp chat to produce an overview of matches over time.",
                                     allow_abbrev=True, add_help=True, exit_on_error=True)

    parser.add_argument('-v', '--verbose', action='store_true', help="Show more output")
    parser.add_argument("--version", action="store_true", help="Show the current version of the program")
    parser.add_argument("-r", "--regex", help="Select only messages matches the python regex")
    parser.add_argument("-s", "--show", default="1,2,3",
                        help="What data to show for each message: 1 for time, 2 for telephone number and 3 for text. (1,2,3 is the default)")
    parser.add_argument("-w", "--week-overview", action="store_true",
                        help="Show an overview of when in the week the matches happen.")
    parser.add_argument("-n", "--numeric", action="store_true",
                        help="Show the week overview with concrete numbers instead of colors")
    parser.add_argument("INPUT", help="Export file to parse")

    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    log.debug("Starting program...")

    if args.version:
        log.info(f"{PROGRAM_NAME} version {program_version}")
        return

    regex = None if args.regex is None else re.compile(args.regex, re.DOTALL | re.IGNORECASE)
    show = set(map(int, args.show.split(",")))
    matches = get_matches(Path(args.INPUT).read_text(), regex)

    if args.week_overview:
        show_week_overview(matches, args.numeric)
    else:
        show_matches(matches, show)

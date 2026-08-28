import argparse
import itertools
import os
import re
import sys
from datetime import datetime

LEET_MAP = str.maketrans(
    {
        "a": "4",
        "A": "4",
        "e": "3",
        "E": "3",
        "i": "1",
        "I": "1",
        "o": "0",
        "O": "0",
        "s": "5",
        "S": "5",
        "t": "7",
        "T": "7",
        "b": "8",
        "B": "8",
    }
)


# Core Logic
def clean_token(s: str) -> str:
    s = re.sub(r"\s+", "", s.strip())
    return re.sub(r"[^0-9A-Za-z._-]", "", s)


def case_variants(s: str):
    variants = {s, s.lower(), s.upper()}
    if s:
        variants.add(s.capitalize())
    parts = re.split(r"[_\-.]", s)
    camel = "".join(p.capitalize() for p in parts if p)
    if camel:
        variants.add(camel)
        variants.add(camel.lower())
    return variants


def leet_variants(s: str):
    return {s, s.translate(LEET_MAP)}


def with_separators(tokens, add_separators: bool):
    if len(tokens) == 1:
        return {tokens[0]}
    seps = ["", "-", "_", "."] if add_separators else [""]
    return {sep.join(tokens) for sep in seps}


def add_numeric_tails(words, tails):
    out = set(words)
    for w in words:
        for t in tails:
            out.add(f"{w}{t}")
    return out


def unique_len_filtered(words, min_len: int, max_len: int):
    return {w for w in words if min_len <= len(w) <= max_len}


def parse_date_tokens(date_str: str):
    tokens = set()
    ds = re.sub(r"[^\d]", "", date_str)
    if len(ds) == 8:  # ddmmyyyy
        day, month, year = ds[:2], ds[2:4], ds[4:]
    elif len(ds) == 6:  # ddmmyy
        day, month, yy = ds[:2], ds[2:4], ds[4:]
        century = "20" if int(yy) <= 30 else "19"
        year = century + yy
    else:
        day = month = year = ""

    for piece in (day, month, year, ds):
        if piece:
            tokens.add(piece)
    if day and month and year:
        tokens.update(
            {day + month, month + day, day + month + year, year + month + day}
        )
    return tokens


def get_unique_filename(basename: str, ext: str) -> str:
    candidate = f"{basename}{ext}"
    if not os.path.exists(candidate):
        return candidate
    i = 1
    while os.path.exists(f"{basename}-{i}{ext}"):
        i += 1
    return f"{basename}-{i}{ext}"


def build_wordlist(tokens, args):
    tokens = [t for t in tokens if t]
    tokens = list(dict.fromkeys(tokens))  # unique, preserve order
    base = set()
    max_combo = min(args.max_combo, len(tokens))
    for r in range(1, max_combo + 1):
        for combo in itertools.permutations(tokens, r):
            base.update(with_separators(combo, not args.no_separators))

    expanded = set()
    for w in base:
        variants = {w}
        if not args.no_case:
            variants = set().union(*(case_variants(x) for x in variants))
        if not args.no_leet:
            variants = set().union(*(leet_variants(x) for x in variants))
        expanded.update(variants)

    if not args.no_numbers:
        try:
            now_year = datetime.now().year  # noqa: DTZ005
        except Exception:  # noqa: BLE001
            now_year = 2026
        tails = [str(i) for i in range(100)] + [
            str(y) for y in range(now_year - 10, now_year + 1)
        ]
        expanded = add_numeric_tails(expanded, tails)

    return unique_len_filtered(expanded, args.min_len, args.max_len)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Basic CLI Wordlist Generator (no external dependencies are required)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:- \n"
            "  python main.py -f John -l Doe -n JD -t TEamSB -d 15081995\n"
            "  python main.py --first John --last Doe --date 15/08/1995\n"
            "  python main.py -f John -l Doe -o custom --min-len 8 --max-len 16\n"
        ),
    )
    parser.add_argument("-f", "--first", default="", help="First name")
    parser.add_argument("-l", "--last", default="", help="Last name")
    parser.add_argument("-n", "--nick", default="", help="Nickname")
    parser.add_argument("-t", "--team", default="", help="Team / company name")
    parser.add_argument(
        "-d", "--date", default="", help="Date (dd/mm/yyyy or ddmmyyyy)"
    )
    parser.add_argument(
        "-o", "--output", default="wordlist", help="Output basename (default: wordlist)"
    )
    parser.add_argument(
        "--min-len", type=int, default=7, help="Minimum word length (default: 7)"
    )
    parser.add_argument(
        "--max-len", type=int, default=24, help="Maximum word length (default: 24)"
    )
    parser.add_argument(
        "--max-combo",
        type=int,
        default=3,
        help="Max tokens combined per word (default: 3)",
    )
    parser.add_argument(
        "--no-leet", action="store_true", help="Disable leetspeak variants"
    )
    parser.add_argument(
        "--no-case",
        action="store_true",
        help="Disable case variants (lower/UPPER/Camel)",
    )
    parser.add_argument(
        "--no-separators", action="store_true", help="Disable -, _, . separators"
    )
    parser.add_argument(
        "--no-numbers", action="store_true", help="Disable numeric tail suffixes"
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    print("=" * 40)
    print("Wordlist Generator")
    print("=" * 40)
    tokens = [
        clean_token(x)
        for x in (args.first, args.last, args.nick, args.team)
        if x.strip()
    ]
    if args.date:
        tokens.extend(sorted(parse_date_tokens(args.date)))

    if not tokens:
        print(
            "Error: No input provided. Use -f/-l/-n/-t/-d to supply data, or -h for help."
        )
        sys.exit(1)

    print("Generating wordlist....")
    final_words = build_wordlist(tokens, args)
    output_file = get_unique_filename(args.output, ".txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(w + "\n" for w in sorted(final_words))

    print(f"Generated {len(final_words)} words.")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()

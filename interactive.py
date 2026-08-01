import itertools
import os
import re
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False  # type: ignore
    console = None


# Wordlist settings
MAX_COMBO_TOKENS = 3  # 2-3 is practical
ADD_LEET = True  # leetspeak variants
ADD_CASE_VARIANTS = True  # lower/UPPER/Capitalized/Camel
ADD_SEPARATORS = True  # -, _, .
ADD_NUM_TAILS = True  # 00..99 & recent years
MIN_LEN = 7
MAX_LEN = 24
OUTPUT_BASENAME = "wordlist"
OUTPUT_EXT = ".txt"

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


# UI helpers
def banner():
    if RICH_AVAILABLE:
        assert console is not None
        console.print(
            Panel.fit(  # type: ignore
                "[bold cyan]Wordlist Generator[/bold cyan] [white]— Interactive Mode[/white]\n"
                "[dim]By ShakalBhau0001 | github.com/ShakalBhau0001 [/dim]",
                border_style="cyan",
            )
        )
    else:
        print("=" * 40)
        print("Wordlist Generator - Interactive Mode")
        print("=" * 40)


def ask(prompt: str, optional: bool = False) -> str:
    label = f"{prompt}" + (" [dim](optional)[/dim]" if optional else "")
    if RICH_AVAILABLE:
        return Prompt.ask(f"[bold green]>>>[/bold green] {label}", default="").strip()  # pyright: ignore[reportPossiblyUnboundVariable]
    suffix = " (optional)" if optional else ""
    return input(f"{prompt}{suffix}: ").strip()


def notice(msg: str):
    if RICH_AVAILABLE:
        assert console is not None
        console.print(f"[yellow]![/yellow] {msg}")
    else:
        print(f"! {msg}")


# Core Logic
def clean_token(s: str) -> str:
    """Keep only ASCII alphanumerics plus dot/underscore/dash."""
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


def with_separators(tokens):
    if len(tokens) == 1:
        return {tokens[0]}
    seps = ["", "-", "_", "."] if ADD_SEPARATORS else [""]
    return {sep.join(tokens) for sep in seps}


def add_numeric_tails(words, tails):
    out = set(words)
    for w in words:
        for t in tails:
            out.add(f"{w}{t}")
    return out


def unique_len_filtered(words):
    return {w for w in words if MIN_LEN <= len(w) <= MAX_LEN}


def parse_date_tokens(date_str: str):
    """Parse a date string (ddmmyyyy or ddmmyy) into useful sub-tokens."""
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


def build_wordlist(tokens):
    tokens = [t for t in tokens if t]
    tokens = list(dict.fromkeys(tokens))  # unique, preserve order

    base = set()
    for r in range(1, min(MAX_COMBO_TOKENS, len(tokens)) + 1):
        for combo in itertools.permutations(tokens, r):
            base.update(with_separators(combo))

    expanded = set()
    for w in base:
        variants = {w}
        if ADD_CASE_VARIANTS:
            variants = set().union(*(case_variants(x) for x in variants))
        if ADD_LEET:
            variants = set().union(*(leet_variants(x) for x in variants))
        expanded.update(variants)

    if ADD_NUM_TAILS:
        try:
            now_year = datetime.now().year
        except Exception:
            now_year = 2026
        tails = [str(i) for i in range(0, 100)] + [
            str(y) for y in range(now_year - 10, now_year + 1)
        ]
        expanded = add_numeric_tails(expanded, tails)

    return unique_len_filtered(expanded)


def run_wizard():
    banner()
    name = ask("First name")
    surname = ask("Last name")
    nickname = ask("Nickname", optional=True)
    team = ask("Team", optional=True)
    date_str = ask("Date (dd/mm/yyyy or ddmmyyyy)", optional=True)
    tokens = [clean_token(x) for x in (name, surname, nickname, team) if x.strip()]
    if date_str:
        tokens.extend(sorted(parse_date_tokens(date_str)))

    if not tokens:
        notice("No input provided, nothing to generate.")
        return

    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Generating wordlist.....", total=None)
            final_words = build_wordlist(tokens)
    else:
        print("Generating wordlist.....")
        final_words = build_wordlist(tokens)

    output_file = get_unique_filename(OUTPUT_BASENAME, OUTPUT_EXT)
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(w + "\n" for w in sorted(final_words))

    if RICH_AVAILABLE:
        table = Table(show_header=False, box=None)
        table.add_row("[bold]Words generated[/bold]", str(len(final_words)))
        table.add_row("[bold]Saved to[/bold]", output_file)
        assert console is not None
        console.print(
            Panel(table, title="[bold green]Done[/bold green]", border_style="green")
        )
    else:
        print(f"Generated {len(final_words)} words.")
        print(f"Saved to: {output_file}")


def main():
    run_wizard()


if __name__ == "__main__":
    main()

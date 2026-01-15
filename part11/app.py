#!/usr/bin/env python3
"""
Part 11 starter.

WHAT'S NEW IN PART 11. A positional Index. It's almost done, only the finishing touches remain.
"""
from typing import List
import time

from .constants import BANNER, HELP
from .models import SearchResult, Searcher

from .file_utilities import load_config, load_sonnets, Configuration

class SettingHandler:
    def __init__(self, command_name: str, attribute_name: str, valid_values: tuple,
                 parse_fn=None, display_fn=None):
        self.command_name = command_name
        self.attribute_name = attribute_name
        self.valid_values = valid_values
        self.parse_fn = parse_fn if parse_fn else lambda x: x
        self.display_fn = display_fn if display_fn else str

    def handle(self, raw_input: str, config: Configuration) -> bool:
        if not raw_input.startswith(self.command_name):
            return False

        parts = raw_input.split()
        if len(parts) == 2 and self.parse_fn(parts[1]) in self.valid_values:
            setattr(config, self.attribute_name, self.parse_fn(parts[1]))
            current_value = getattr(config, self.attribute_name)
            print(f"{self.attribute_name.replace('_', ' ').title()} set to {self.display_fn(current_value)}")
            config.save()
        else:
            values_str = "|".join(str(v).lower() if isinstance(v, bool) else str(v) for v in self.valid_values)
            print(f"Usage: {self.command_name} {values_str}")

        return True


def print_results(
    query: str | None,
    results: List[SearchResult],
    highlight_mode: str,
    query_time_ms: float | None = None,
) -> None:
    total_docs = len(results)
    matched = [r for r in results if r.matches > 0]

    line = f'{len(matched)} out of {total_docs} sonnets contain "{query}".'
    if query_time_ms is not None:
        line += f" Your query took {query_time_ms:.2f}ms."
    print(line)

    for idx, r in enumerate(matched, start=1):
        r.print(idx, highlight_mode, total_docs)

# ---------- CLI loop ----------
def main() -> None:
    print(BANNER)
    config = load_config()

    # Load sonnets (from cache or API)
    start = time.perf_counter()
    sonnets = load_sonnets()

    elapsed = (time.perf_counter() - start) * 1000
    print(f"Loading sonnets took: {elapsed:.3f} [ms]")

    print(f"Loaded {len(sonnets)} sonnets.")

    searcher = Searcher(sonnets)

    highlight_handler = SettingHandler(
        command_name=":highlight",
        attribute_name="highlight",
        valid_values=(True, False),
        parse_fn=lambda x: x.lower() == "on",
        display_fn=lambda x: "ON" if x else "OFF"
    )

    search_mode_handler = SettingHandler(
        command_name=":search-mode",
        attribute_name="search_mode",
        valid_values=("AND", "OR"),
        parse_fn=str.upper
    )

    hl_mode_handler = SettingHandler(
        command_name=":hl-mode",
        attribute_name="hl_mode",
        valid_values=("DEFAULT", "GREEN"),
        parse_fn=str.upper
    )

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue

        # commands
        if raw.startswith(":"):
            if raw == ":quit":
                print("Bye.")
                break

            if raw == ":help":
                print(HELP)
                continue

            if highlight_handler.handle(raw, config):
                continue
            if search_mode_handler.handle(raw, config):
                continue
            if hl_mode_handler.handle(raw, config):
                continue

            print("Unknown command. Type :help for commands.")
            continue


        # ---------- Query evaluation ----------

        words = raw.split()
        if not words:
            continue

        start = time.perf_counter()

        results = searcher.search(raw, config.search_mode)

        # Initialize elapsed_ms to contain the number of milliseconds the query evaluation took
        elapsed_ms = (time.perf_counter() - start) * 1000

        highlight_mode = config.hl_mode if config.highlight else None

        print_results(raw, results, highlight_mode, elapsed_ms)

if __name__ == "__main__":
    main()

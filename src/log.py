from __future__ import annotations

from rich.console import Console
from rich.markup import escape


def get_console(verbose: bool = False) -> Console:
    """Return a Rich Console writing to stderr.

    The console isn't strictly coupled to Python's logging; we keep it simple
    for clear CLI messages.
    """
    return Console(stderr=True, highlight=True, soft_wrap=False, force_terminal=None, quiet=not verbose)


def info(console: Console, message: str) -> None:
    console.print(f"[bold cyan]›[/] {escape(message)}")


def warn(console: Console, message: str) -> None:
    console.print(f"[bold yellow]![/] {escape(message)}")


def error(console: Console, message: str) -> None:
    console.print(f"[bold red]✖[/] {escape(message)}")


def success(console: Console, message: str) -> None:
    console.print(f"[bold green]✔[/] {escape(message)}")



#!/usr/bin/env python3
"""Main entry point for Tiny Code"""

import sys
import logging
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler

# Add package to path if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from tiny_code.cli import cli

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)

console = Console()

def main():
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logging.exception("Unexpected error")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""Entry point: `python -m ransomware_live_mcp` or `ransomware-live-mcp`."""

from .server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()

from .Parser import K6500_Parser
from .psu_cli_base import run_cli


def main() -> None:
    run_cli(K6500_Parser, "k6500")

if __name__ == "__main__":
    main()
from CLI.Parser import Hmp4040_Parser
from CLI.psu_cli_base import run_cli


def main() -> None:
    run_cli(Hmp4040_Parser, "hmp4040")

if __name__ == "__main__":
    main()
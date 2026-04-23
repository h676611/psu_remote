import ordered_argparse


def create_base_parser() -> ordered_argparse.ArgumentParser:
    base: ordered_argparse.ArgumentParser = ordered_argparse.ArgumentParser(add_help=False)
    base.add_argument(
        "--connect",
        action="store_true",
        help="Connects PSU to the server"
    )
    base.add_argument(
        "--disconnect",
        action="store_true",
        help="Disconnects PSU from the server"
    )


    base.add_argument(
        '--set-output', '-so',
        choices=['0', '1', 'ON', 'OFF'],
        help='Sets output state for selected channel'
    )


    # --- Voltage & Current Setpoints ---
    base.add_argument(
        '--set-voltage', '-sv',
        type=str,
        help='Set voltage for selected channel'
    )
    base.add_argument(
        '--set-current', '-si',
        type=str,
        help='Set current for selected channel'
    )
    base.add_argument(
        '--set-voltage-limit',
        type=str,
        help='Set voltage limit (V-Limit)'
    )
    base.add_argument(
        '--set-current-limit',
        type=str,
        help='Set current limit (I-Limit)'
    )


    # --- Measurements & Queries (Getters) ---
    base.add_argument(
        '--get-id',
        action='store_const',
        const=''
    )

    base.add_argument(
        '--get-voltage',
        action='store_const',
        const='',
    )

    base.add_argument(
        '--get-current',
        action='store_const',
        const='',
    )

    base.add_argument(
        '--get-display-voltage',
        action='store_const',
        const='',
    )

    base.add_argument(
        '--get-display-current',
        action='store_const',
        const='',
    )

    base.add_argument(
        '--get-error',
        action='store_const',
        const='',
    )


    # --- System & Modes ---
    base.add_argument(
        '--set-remote',
        choices=['mixed', 'local', 'remote'],
        help='Set system remote/local state'
    )
    base.add_argument(
        '--set-source',
        help='Set source function'
    )
    return base
    

class Hmp4040_Parser(ordered_argparse.ArgumentParser):
    def __init__(self):
        base: ordered_argparse.ArgumentParser = create_base_parser()

        super().__init__(
            description="HMP4040 PSU CLI",
            parents=[base]
        )

        self.add_argument(
            '--set-channel', 
            '-sch',
            dest="set_channel",
            choices=[1,2,3,4],
            type=int,
            help='Sets active channel'
        )

        self.add_argument(
            '--get-channel',
            '-gc',
            action='store_const',
            const=''
        )

        self.add_argument(
            '--set-output-all',
            '-soa',
            dest="set_output_all",
            type=str,
            choices=["True", "False", "true", "false", "0", "1"],
            help="Activate output for all channels"
        )
        self.add_argument(
            "--get-source",
            action='store_const',
            const=''
        )

                # --- Combined Commands ---
        self.add_argument(
                "--set-channel-voltage",
                "-scv",
                dest="set_channel_voltage",
                nargs=2,
                metavar=('CHANNEL', 'VOLTAGE'),
                help="set VOLTAGE at specified CHANNEL"
            )
        self.add_argument(
            "--set-channel-current",
            "-scc",
            dest="set_channel_current",
            nargs=2,
            metavar=('CHANNEL', 'CURRENT'),
            help="set CURRENT at specified channel CHANNEL"
        )
        self.add_argument(
            "--set-channel-current-voltage",
            "-sccv",
            dest="set_channel_current_voltage",
            nargs=3,
            metavar=('CHANNEL', 'CURRENT', 'VOLTAGE'),
            help="set CURRENT and VOLTAGE at specified channel CHANNEL"
        )
        
        self.add_argument(
            "--get-channel-voltage",
            "-gcv",
            dest="get_channel_voltage",
            nargs=1,
            metavar=('CHANNEL')
        )
        
        self.add_argument(
            "--set-current-voltage",
            dest="set_current_voltage",
            nargs=2,
            metavar=('CURRENT', 'VOLTAGE')
        )

class K2400_Parser(ordered_argparse.ArgumentParser):
    def __init__(self):
        base: ordered_argparse.ArgumentParser = create_base_parser()
        super().__init__(
            description="K2400 PSU CLI",
            parents=[base]
        )
        self.add_argument(
            "--get-current-range",
            action='store_const',
            const=''
        )
        self.add_argument(
            "--get-voltage-range",
            action='store_const',
            const=''
        )
        self.add_argument(
            "--get-source",
            action='store_const',
            const=''
        )

class K2450_Parser(ordered_argparse.ArgumentParser):
    def __init__(self):
        base: ordered_argparse.ArgumentParser = create_base_parser()
        super().__init__(
            description="K2450 PSU CLI",
            parents=[base]
        )
        self.add_argument(
            "--get-current-limit",
            action='store_const',
            const=''
        )
        
        self.add_argument(
            "--get-voltage-limit",
            action='store_const',
            const=''
        )
        
        self.add_argument(
            "--get-current-range",
            action='store_const',
            const=''
        )
        self.add_argument(
            "--get-voltage-range",
            action='store_const',
            const=''
        )
        self.add_argument(
            "--get-source",
            action='store_const',
            const=''
        )
    
class K6500_Parser(ordered_argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            description="K6500 DMM CLI"
        )

        self.add_argument(
            "--get-channel-voltage",
            "-gcv",
            dest="get_channel_voltage",
            type=int,
            help="measure voltage at specified channel"
        )

        self.add_argument(
            '--set-channel',
            '-sch',
            dest="set_channel",
            type=int,
            choices=[1,2,3,4,5,6,7,8,9,10],
            help="Select channel"
        )
        self.add_argument(
            '--get-channel',
            '-gch',
            dest="get_channel",
            action='store_const',
            const='',
            help="Get all closed channels on the multimeter"
        )



       

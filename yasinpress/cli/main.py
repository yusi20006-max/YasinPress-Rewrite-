"""Command-line entrypoint."""
from .commands import dispatch
from .parser import build_parser


def main() -> None:
    """Run the CLI."""
    args = build_parser().parse_args()
    print(dispatch(args.command))

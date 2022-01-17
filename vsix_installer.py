"""Simple script to install VS Code extensions."""

import argparse
import logging
import sys

from typing import List


def get_parser() -> argparse.ArgumentParser:
    """Returns a parser for the VSIX extension installer.

    Returns:
        Installer parser.
    """

    parser = argparse.ArgumentParser(description='VS Code VSIX installer')
    parser.add_argument(
        '-f',
        '--file',
        help='VSIX extensions list (<extension>:<version> per line)',
    )
    parser.add_argument(
        '-i',
        '--insiders',
        action='store_true',
        help='Install to VS Code Insiders rather than VS Code',
    )
    parser.add_argument(
        'extensions',
        nargs='*',
        help='VSIX (given by <extension:version>) to install',
    )
    return parser


def install(extensions: List[str], insiders: bool = False):
    """Install VSIX `extensions` into VS Code."""

    pass


def main(argv: List[str] = sys.argv[1:]) -> int:
    """Runs the VSIX installer."""

    logging.basicConfig()

    try:
        args = get_parser().parse_args()
        extensions = args.extensions
        if args.file:
            with open(args.file) as args_file:
                extensions.extend([line.rstrip() for line in args_file])
        install(extensions, args.insiders)
    except Exception:
        logging.exception()
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())

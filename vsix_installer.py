"""Simple script to install VS Code extensions."""

import argparse
import logging
import re
import sys

from typing import List

URLS = {
    'marketplace': 'https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{extension}/{version}/vspackage',
    'local': 'http://localhost:8000/extensions/{publisher}.{extension}-{version}.vsix',
}


def get_parser() -> argparse.ArgumentParser:
    """Returns a parser for the VSIX extension installer.

    Returns:
        Installer parser.
    """

    parser = argparse.ArgumentParser(description='VS Code VSIX installer')
    parser.add_argument(
        '-f',
        '--file',
        help='VSIX list (<publisher>.<extension>-<version> per line)',
    )
    parser.add_argument(
        '-i',
        '--insiders',
        action='store_true',
        help='Install to VS Code Insiders rather than VS Code',
    )
    parser.add_argument(
        '--upstream',
        choices=['local', 'marketplace'],
        default='marketplace',
        help='Upstream repository to download VSIX extensions from',
    )
    parser.add_argument(
        'extensions',
        nargs='*',
        help='VSIX (<publisher>.<extension-version>) to install',
    )
    return parser


def install(extensions: List[str], insiders: bool = False):
    """Install VSIX `extensions` into VS Code."""

    prog = re.compile(r'''
        (?P<publisher>[a-zA-Z0-9_-]+)
        (\.(?P<extension>[a-zA-Z0-9_-]+))
        (-(?P<version>[0-9\.]+))
    ''', re.VERBOSE)
    for entry in extensions:
        extension = prog.match(entry).groupdict()
        logging.info(f'Found extension: {extension}')


def main(argv: List[str] = sys.argv[1:]) -> int:
    """Runs the VSIX installer."""

    logging.basicConfig(level=logging.INFO)

    try:
        args = get_parser().parse_args()
        extensions = args.extensions
        if args.file:
            with open(args.file) as args_file:
                extensions.extend([line.rstrip() for line in args_file])
        install(extensions, args.insiders)
    except Exception:
        logging.exception('Execution error:')
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())

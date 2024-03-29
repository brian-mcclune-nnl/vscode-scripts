"""Simple script to install VS Code extensions."""

import argparse
import datetime
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

from urllib.error import HTTPError

from typing import List

URLS = {
    # flake8: noqa
    'marketplace': 'https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{publisher}/vsextensions/{extension}/{version}/vspackage',
    'publisher': 'https://{publisher}.gallery.vsassets.io/_apis/public/gallery/publisher/{publisher}/extension/{extension}/{version}/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage',
    'local': 'http://localhost:8000/{publisher}.{extension}-{version}.vsix',
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
        '--download-only',
        action='store_true',
        help='Download extensions but do not install them',
    )
    parser.add_argument(
        '--upstream',
        choices=['local', 'marketplace', 'publisher'],
        default='publisher',
        help='Upstream repository to download VSIX extensions from',
    )
    parser.add_argument(
        'extensions',
        nargs='*',
        help='VSIX (<publisher>.<extension-version>) to install',
    )
    return parser


def install(
    extensions: List[str],
    upstream: str,
    download_only: bool = False,
    insiders: bool = False,
):
    """Install VSIX `extensions` into VS Code.

    Arguments:
        extensions: List of extensions to install. The naming format is
            ``publisher.extension-version``.
        upstream: Templated URL string that is the upstream to download
            extension from. Template variables are ``publisher``,
            ``extension``, and ``version``.
        download_only: ``True`` if packages should be downloaded but not
            installed.
        insiders: ``True`` if installer should install to VS Code Insiders
            rather than VS Code.
    """

    if not extensions:
        logging.info('No extensions to install, exiting')
        return

    ext_dir = f'vsix-{datetime.datetime.now().strftime("%Y%m%d-%H%M%S")}'
    os.makedirs(ext_dir, exist_ok=True)

    prog = re.compile(r'''
        (?P<publisher>[a-zA-Z0-9_-]+)
        (\.(?P<extension>[a-zA-Z0-9_-]+))
        (@(?P<version>[0-9\.]+))
    ''', re.VERBOSE)

    retry = False
    while extensions:
        entry = extensions[0]
        extension = prog.match(entry).groupdict()
        url = URLS[upstream].format(**extension)
        logging.info(f'Downloading {extension} from {upstream}')
        vsix = f'{entry}.vsix'
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'python-requests/2.22.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            })

            dst = os.path.join(ext_dir, vsix)
            with urllib.request.urlopen(req) as res, open(dst, 'wb') as vsixf:
                shutil.copyfileobj(res, vsixf)
                limit = int(res.headers.get('X-RateLimit-Limit', '-1'))
                remaining = int(res.headers.get('X-RateLimit-Remaining', '-1'))
                reset = int(res.headers.get('X-RateLimit-Reset', '-1'))

            vscode = 'code-insiders' if insiders else 'code'
            if not download_only:
                logging.info(f'Installing {extension} using VS {vscode}')
                subprocess.run([
                    vscode,
                    '--install-extension',
                    dst,
                ])
            extensions.pop(0)
            retry = False
        except HTTPError as exc:
            if exc.code != 429:
                raise exc
            if retry:
                logging.error('Rate limited but already retried, exiting')
                raise SystemExit

            logging.error('Rate limited, will retry')
            limit = int(exc.headers.get('X-RateLimit-Limit', '-1'))
            remaining = int(exc.headers.get('X-RateLimit-Remaining', '-1'))
            reset = int(exc.headers.get('X-RateLimit-Reset', '-1'))
            retry = True

        # Sleep if rate limited
        if limit != -1:
            reset_time = datetime.datetime.fromtimestamp(reset)
            logging.info(
                'Rate limited, limit: %d, remaining: %d (reset time: %s)',
                limit,
                remaining,
                reset_time,
            )
            time.sleep((reset_time - datetime.datetime.now()).seconds)

        # Get vscode-server if extension is remote-ssh
        if extension['extension'] =='remote-ssh':
            cproc = subprocess.run(['code.cmd', '-v'], stdout=subprocess.PIPE)
            version_no = cproc.stdout.decode().splitlines()[0]
            commit_id = cproc.stdout.decode().splitlines()[1]
            url = (
                f'https://update.code.visualstudio.com/commit:{commit_id}/'
                'server-linux-x64/stable')
            req = urllib.request.Request(url, headers={
                'User-Agent': 'python-requests/2.22.0',
                'Accept-Encoding': 'gzip, deflate',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            })

            tgz = f'vscode-server-{version_no}.tar.gz'
            dst = os.path.join(ext_dir, tgz)
            with urllib.request.urlopen(req) as res, open(dst, 'wb') as tgzf:
                shutil.copyfileobj(res, tgzf)

    logging.info('All extensions processed')


def main(argv: List[str] = sys.argv[1:]) -> int:
    """Runs the VSIX installer."""

    logging.basicConfig(level=logging.INFO)

    try:
        args = get_parser().parse_args()
        extensions = args.extensions
        if args.file:
            with open(args.file) as args_file:
                extensions.extend([line.rstrip() for line in args_file])
        install(extensions, args.upstream, args.download_only, args.insiders)
    except Exception:
        logging.exception('Execution error:')
        return 1
    else:
        return 0


if __name__ == '__main__':
    sys.exit(main())

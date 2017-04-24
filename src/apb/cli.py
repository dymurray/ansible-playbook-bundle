import os
import sys
import argparse

import apb.engine

AVAILABLE_COMMANDS = {
    'help': 'Display this help message',
    'prepare': 'Prepare an ansible-container project for APB packaging',
    'build': 'Build and package APB container'
}


def subcmd_build_parser(parser, subcmd):
    return


def subcmd_prepare_parser(parser, subcmd):
    subcmd.add_argument(
        '--provider', action='store', dest='provider',
        help=u'Targetted cluster type',
        choices=['openshift', 'kubernetes'],
        default='openshift'
    )


def subcmd_help_parser(parser, subcmd):
    return


def main():
    parser = argparse.ArgumentParser(
        description=u'APB tooling for'
        u'assisting in building and packaging APBs.'
    )

    parser.add_argument(
        '--debug', action='store_true', dest='debug',
        help=u'Enable debug output', default=False
    )

    # TODO: Modify project to accept relative paths
    parser.add_argument(
        '--project', '-p', action='store', dest='base_path',
        help=u'Specify a path to your project. Defaults to CWD.',
        default=os.getcwd()
    )

    subparsers = parser.add_subparsers(title='subcommand', dest='subcommand')
    subparsers.required = True

    for subcommand in AVAILABLE_COMMANDS:
        subparser = subparsers.add_parser(
            subcommand, help=AVAILABLE_COMMANDS[subcommand]
        )
        globals()['subcmd_%s_parser' % subcommand](parser, subparser)

    args = parser.parse_args()

    if args.subcommand == 'help':
        parser.print_help()
        sys.exit(0)

    try:
        getattr(apb.engine,
                u'cmdrun_{}'.format(args.subcommand))(**vars(args))
    except Exception as e:
        print("Exception occurred! %s" % e)
        sys.exit(1)

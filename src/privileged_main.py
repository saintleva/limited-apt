#!/usr/bin/env python3

# Copyright (c) Anton Liaukevich 2011-2017 <leva.dev@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import os

import sys
import argparse
import apt.progress
import apt.progress.text
import apt.progress.base
from limitedapt.errors import StubError
from limitedapt.runners import *
from limitedapt.constants import *
from exitcodes import *
import consoleui
from argparse import Action


DEBUG = True

SOFTWARE_VERSION = '0.1a'
PROGRAM_NAME = 'limited-apt'


def print_error(msg):
    print(msg, file=sys.stderr)

def privileged_main():
    
    #TODO: remove it:
#     print()
#     print("privileged_main():")
#     print('UID = {0}, EUID = {1}'.format(os.getuid(), os.geteuid()))
#     print(sys.argv)
#     print()
    
    # extract first program argument as id of real user
    try:
        user_id = int(sys.argv[1]) 
    except:
        print('This privileged script has been run incorrectly', file=sys.stderr)
        sys.exit(exitcodes.PRIVILEGED_SCRIPT_HAS_BEEN_RUN_INCORRECTLY)
        
    # Create parser
    
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description='''%(prog)s is a console tool that allows ordinary \
                                     (non-privileged) users to install/remove/etc. non-system packages \
                                     but forbid them to install "dangerous" packages or to do \
                                     other unwanted (to root) modifications.''',
                                     epilog='To do any real modifications (or even updates) \
                                     you need to be in a "{0}" group.'.format(UNIX_LIMITEDAPT_GROUPNAME))

    # add a common options
    #TODO: Do I really need this option?
    parser.add_argument('-a', '--show-arch', action='store_true',
                        help='Show package name in "<name>:<arch>" format (showing architecture)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Display extra information.')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debugging mode. Print detailed information on every action.')
    parser.add_argument('--version', action='version', version='%(prog)s '+SOFTWARE_VERSION)

    subparsers = parser.add_subparsers(dest='subcommand', title='command', description='valid commands')

    # create the parser for the "update" command
    subparsers.add_parser('update',
                          help='Download (update) lists of new/upgradable packages and the list (subset) \
                          of non-system packages ordinary user can install (enclosure).', add_help=False)
     
    # create the parser for the "print-enclosure" command
    print_enclosure_parser = subparsers.add_parser('print-enclosure',
                                                   help='Print enclosure (the list of non-system packages \
                                                   ordinary user can install).')
    print_enclosure_parser.add_argument('-r', '--versions', action='store_true',
                                        help='''Show version constraints for 'allowed' packages.''')
        
    # create the parser for the "list-of-mine" command
    subparsers.add_parser('list-of-mine',
                          help='Print list of the packages installed (or unmarked auto) by you. Has not subparameters.',
                          add_help=False)

    # Create parsers for "major" (modification) operations

    parent_operation_parser = argparse.ArgumentParser(add_help=False)
    parent_operation_parser.add_argument('-s', '--simulate', action='store_true',
                                         help='''Simulate actions, but doesn't actually perform them. \
                                         This doesn't require high privileges (you may not to be a member \
                                         of "{0}" group).'''.format(UNIX_LIMITEDAPT_GROUPNAME))
    parent_operation_parser.add_argument('-p', '--prompt', action='store_true',
                                         help='Always prompt for confirmation on actions.')
    parent_operation_parser.add_argument('-f', '--fatal-errors', action='store_true',
                                         help='Stop and exit after first error.')
    
    operation_subcommands_dict = {'install' : 'Install/upgrade (non-system) packages by an ordinary user (you).',
                                  'remove' : 'Remove packages that you has installed later.',
                                  'markauto' : 'Mark packages as having been automatically installed.',
                                  'unmarkauto' : 'Mark packages as having been manually installed by you.'}
    
    class InvalidOperation(Exception): pass
       
    def unsuffix_operation(operation):
        if operation.endswith('+'):
            return OperationPair('install', operation[:-1])
        elif operation.endswith('-'):
            return OperationPair('remove', operation[:-1])
        elif operation.endswith('&M'):
            return OperationPair('markauto', operation[:-2])
        elif operation.endswith('&m'):
            return OperationPair('unmarkauto', operation[:-2])
        else:
            raise InvalidOperation('Error: invalid operation: suffix is incorrect')
        
    diverse_parser = subparsers.add_parser('diverse', parents=[parent_operation_parser])
    diverse_parser.add_argument('package_operations', nargs='*', metavar='operation',
                                help='''a package with one of the suffixes: "+", "-", "&M", "&m" \
                                (similarly to ones in aptitude)''')
    
    # create the parser for the "safe-uprade" command
    #TODO: Is this explanation (help string) right in the circumstances of limited-apt utility
    subparsers.add_parser('safe-upgrade', parents=[parent_operation_parser], help='Perform a safe upgrade.',
                          add_help=False)
    
    # create the parser for the "full-upgrade" command
    subparsers.add_parser('full-upgrade', parents=[parent_operation_parser],
                          help='Perform an upgrade, possibly installing and removing packages.', add_help=False)
    
    for operation, help in operation_subcommands_dict.items():
        operation_subcommand_parser = subparsers.add_parser(operation, parents=[parent_operation_parser],
                                                            help=help)
        operation_subcommand_parser.add_argument('packages', nargs='*', metavar='pkg', help='a package')        
        if operation == 'remove':
            operation_subcommand_parser.add_argument('-P', '--purge-unused', action='store_true',
                                                     help="purge packages that is remove their configuration files")

    # Parse and analyse arguments
    
    args = parser.parse_args(sys.argv[2:])
        
    simulate_mode = args.simulate if hasattr(args, 'simulate') else None
    prompt_mode = args.prompt if hasattr(args, 'prompt') else None
    fatal_errors_mode = args.fatal_errors if hasattr(args, 'fatal_errors') else None
    purge_unused_mode = args.purge_unused if hasattr(args, 'purge_unused') else None

    modes = Modes(args.show_arch, args.debug, args.verbose, purge_unused_mode, simulate_mode, prompt_mode,
                  fatal_errors_mode)
    #TODO: Use "apt.progress.FetchProgress()" when it has been implemented
    progresses = Progresses(None, apt.progress.text.AcquireProgress(), apt.progress.base.InstallProgress())
    runner = Runner(user_id, modes, sys.stdout, sys.stderr,
                    progresses, consoleui.Applying, consoleui.terminate)
        
    try:
        if args.subcommand == 'update':
            runner.update()
        elif args.subcommand == 'safe-upgrade':
            runner.upgrade(full_upgrade=False)
        elif args.subcommand == 'full-upgrade':
            runner.upgrade(full_upgrade=True)
        elif args.subcommand == 'print-enclosure':
            runner.print_enclosure(args.versions)
        elif args.subcommand == 'list-of-mine':
            runner.list_of_mine()
        elif args.subcommand in operation_subcommands_dict.keys():
            operation_tasks = { args.subcommand : args.packages }
            runner.perform_operations(operation_tasks)
        elif args.subcommand == 'diverse':
            operation_tasks = {}
            for operation in args.package_operations:
                operation_pair = unsuffix_operation(operation)
                if operation_pair.command in operation_tasks:
                    operation_tasks[operation_pair.command].append(operation_pair.package)
                else:
                    operation_tasks[operation_pair.command] = [operation_pair.package]
            runner.perform_operations(operation_tasks)
    except GoodError:
        sys.exit(ExitCodes.GOOD)
    except YouHaveNotUserPrivileges as err:
        if isinstance(err, YouHaveNotPrivilegesToUpdate):
            action_str = "update package list"
        elif isinstance(err, YouHaveNotPrivilegesToUpgrade):
            action_str = "upgrade system"
        elif isinstance(err, YouHaveNotPrivilegesToPerform):
            action_str = "perform these operations"
        print_error('''Error: you have not privileges to {0}: you must be root or a member of "{1}" group'''.
                    format(action_str, err.group_name))
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES)
    except YouMayNotPurge:
        print_error('''Error: only root can purge packages and use "--purge-unused" option''')              
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES)
    except GroupNotExist as err:
        print_error('''Error: "{0}" group doesn't exist'''.format(err.group_name))
        sys.exit(ExitCodes.GROUP_NOT_EXIST)
    except ConfigFilesIOError as err:
        sys.exit(ExitCodes.ERROR_WHILE_PARSING_CONFIG_FILES)        
    except StubError as err:
        print_error('It is a stub: ', err)
        sys.exit(ExitCodes.STUB)


if __name__ == '__main__':
    privileged_main()

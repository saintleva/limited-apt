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
import apt.progress.base
import apt.progress.text
from limitedapt.errors import StubError
from limitedapt.runners import *
from limitedapt.constants import *
from limitedapt.debug import debug_suidbit
from exitcodes import ExitCodes
import consoleui

DEBUG = True

SOFTWARE_VERSION = '0.1a'
PROGRAM_NAME = 'limited-apt'


def print_error(*args):
    print(*args, file=sys.stderr)

def privileged_main():
    
    if DEBUG:
        debug_suidbit("privileged_main()")
        print('PROGRAM ARGUMENTS: ', sys.argv)
        
    
    #TODO: How must I to compute "user_id"?
    #user_id = os.getuid()
    # extract first program argument as id of real user
    try:
        user_id = int(sys.argv[1]) 
    except:
        print_error('This privileged script has been run incorrectly')
        sys.exit(ExitCodes.PRIVILEGED_SCRIPT_HAS_BEEN_RUN_INCORRECTLY.value)
        
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
    #TODO: remove it
#     print_enclosure_parser.add_argument('-r', '--versions', action='store_true',
#                                         help='''Show version constraints for 'allowed' packages.''')
        
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
                                  'physically-remove' : 'Removes package even though somebody but me (root) owns it',
                                  'purge' : 'Remove packages and all its associated configuration and data files (by root only).',
                                  'markauto' : 'Mark packages as having been automatically installed.',
                                  'unmarkauto' : 'Mark packages as having been manually installed by you.'}
    
    def unsuffix_operation(operation):
        if operation.endswith('+'):
            return OperationPair('install', operation[:-1])
        elif operation.endswith('-'):
            return OperationPair('remove', operation[:-1])
        elif operation.endswith('^'):
            return OperationPair('physically-remove', operation[:-1])
        elif operation.endswith('_'):
            return OperationPair('purge', operation[:-1])
        elif operation.endswith('&M'):
            return OperationPair('markauto', operation[:-2])
        elif operation.endswith('&m'):
            return OperationPair('unmarkauto', operation[:-2])
        else:
            print_error('''Error: invalid operation on the suffix''')              
            sys.exit(ExitCodes.INVALID_OPERATION_ON_THE_SUFFIX.value)
        
    diverse_parser = subparsers.add_parser('diverse', parents=[parent_operation_parser])
    diverse_parser.add_argument('package_operations', nargs='*', metavar='operation',
                                help='''a package with one of the suffixes: "+", "-", "^", "_", "&M", "&m" \
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
        if operation in ('remove', 'physically-remove', 'purge'):
            operation_subcommand_parser.add_argument('-P', '--purge-unused', action='store_true',
                                                     help="purge packages that is remove their configuration files")

    # Parse and analyse arguments
    
    args = parser.parse_args(sys.argv[2:])
    
    simulate_mode = args.simulate if hasattr(args, 'simulate') else None
    prompt_mode = args.prompt if hasattr(args, 'prompt') else None
    fatal_errors_mode = args.fatal_errors if hasattr(args, 'fatal_errors') else None
    purge_unused_mode = args.purge_unused if hasattr(args, 'purge_unused') else None
    physically_remove_mode = args.physically_remove if hasattr(args, 'physically_remove') else None

    modes = Modes(args.show_arch, args.debug, args.verbose, purge_unused_mode, physically_remove_mode,
                  simulate_mode, prompt_mode, fatal_errors_mode)
    #TODO: Use "apt.progress.FetchProgress()" when it has been implemented
    #TODO: test it
    progresses = Progresses(None, apt.progress.text.AcquireProgress(), apt.progress.base.InstallProgress())
    runner = Runner(user_id, modes, consoleui.ErrorHandlers(), consoleui.Applying(), progresses, sys.stderr) 
        
    try:
        if args.subcommand == 'update':
            runner.update()
        elif args.subcommand == 'safe-upgrade':
            runner.upgrade(full_upgrade=False)
        elif args.subcommand == 'full-upgrade':
            runner.upgrade(full_upgrade=True)
        elif args.subcommand == 'print-enclosure':
            if modes.wordy():
                print('Packages you ({0}) may install:'.format(runner.username))            
            for name in runner.get_printed_enclosure():
                print(name)
        elif args.subcommand == 'list-of-mine':
            if modes.wordy(): 
                print('Packages installed by you ({0}):'.format(runner.username))            
            for name in runner.get_printed_list_of_mine():
                print(name)
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
    except GoodExit:
        sys.exit(ExitCodes.GOOD.value)
    except YouHaveNotUserPrivilegesError as err:
        if isinstance(err, YouMayNotUpdateError):
            action_str = "update package list"
        elif isinstance(err, YouMayNotUpgradeError):
            action_str = "fully upgrade system" if err.full_upgrade else "safely upgrade system"
        elif isinstance(err, YouMayNotPerformError):
            action_str = "perform these operations"
        print_error('''Error: you have not privileges to {0}: you must be root or a member of "{1}" group'''.
                    format(action_str, err.group_name))
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES.value)
    except AttempToPerformSystemComposingError:
        sys.exit(ExitCodes.ATTEMPT_TO_PERFORM_SYSTEM_COMPOSING.value)
    except YouMayNotPurgeError:
        print_error('''Error: only root can purge packages and use "--purge-unused" option''')              
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES.value)
    except GroupNotExistError as err:
        print_error('''Error: "{0}" group doesn't exist'''.format(err.group_name))
        sys.exit(ExitCodes.GROUP_NOT_EXIST.value)
    except ReadingConfigFilesError as err:
        print_error('''Error number "{0}" appeared while reading config file "{1}"'''.
                    format(err.error_number, err.filename))
        sys.exit(ExitCodes.ERROR_WHILE_READING_CONFIG_FILES.value)
    except WritingConfigFilesError as err:
        print_error('''Error number "{0}" appeared while reading config file "{1}"'''.
                    format(err.error_number, err.filename))
        sys.exit(ExitCodes.ERROR_WHILE_WRITING_CONFIG_FILES.value)
    except EnclosureImportSyntaxError:
        print_error('Error while parsing enclosure')
        sys.exit(ExitCodes.ERROR_WHILE_PARSING_CONFIG_FILES.value)
    except CoownershipImportSyntaxError:
        print_error('Error while parsing coownership-list')
        sys.exit(ExitCodes.ERROR_WHILE_PARSING_CONFIG_FILES.value)
    except LockFailedError as err:
        print_error('CANNOT LOCK: ', err)
        sys.exit(ExitCodes.LOCK_FAILED.value)
    except FetchCancelledError as err:
        print_error('Error: fetch cancelled')              
        sys.exit(ExitCodes.FETCH_CANCELLED.value)
    except FetchFailedError as err:
        print_error('Error: fetch cancelled')              
        sys.exit(ExitCodes.FETCH_FAILED.value)
    except StubError as err:
        print_error('It is a stub: ', err)
        sys.exit(ExitCodes.STUB.value)


if __name__ == '__main__':
    privileged_main()

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

import sys
import argparse
import apt.progress.base
import apt.progress.text
from limitedapt.tasks import *
from limitedapt.errors import *
from limitedapt.updatetime import *
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
    
    # if DEBUG:
    #     debug_suidbit("privileged_main()")
    #     print('PROGRAM ARGUMENTS: ', sys.argv)
        
    
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
    parser.add_argument('-a', '--show-arch', action='store_true',
                        help='Always show package name in "<name>:<arch>" format (showing architecture)')
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
    subparsers.add_parser('print-enclosure', help='Print enclosure (the list of non-system packages ordinary user can install).')

    # create the parser for the "list-of-mine" command
    subparsers.add_parser('list-of-mine',
                          help='Print list of the packages installed (or unmarked auto) by you. Has not subparameters.',
                          add_help=False)

    # create the parser for the "owners-of" command
    ownersof_parser = subparsers.add_parser('owners-of', help='Print list of users who owns package.', add_help=False)
    ownersof_parser.add_argument('package', help='package name')

    # Create parsers for "major" (modification) operations

    parent_operation_parser = argparse.ArgumentParser(add_help=False)
    #TODO: Show help for these arguments:
    parent_operation_parser.add_argument('-r', '--remove-dependencies', action='store_true',
                                         help="Allow to remove packages you don't specity to remove explicitly "
                                              "(and you have installed them later")
    parent_operation_parser.add_argument('-f', '--force', action='store_true',
                                         help="Allow root to do (implicit) forbidden actions.")
    parent_operation_parser.add_argument('-p', '--purge-unused', action='store_true',
                                         help="Purge packages that is remove their configuration files")
    parent_operation_parser.add_argument('-e', '--fatal-errors', action='store_true',
                                         help='Stop and exit after first error.')
    parent_operation_parser.add_argument('-y', '--assume-yes', action='store_true',
                                         help='When a yes/no prompt would be presented, assume that the user entered “yes”.')
    parent_operation_parser.add_argument('-s', '--simulate', action='store_true',
                                         help='''Simulate actions, but doesn't actually perform them. \
                                         This doesn't require high privileges (you may not to be a member \
                                         of "{0}" group).'''.format(UNIX_LIMITEDAPT_GROUPNAME))

    operation_subcommands_dict = {'install' : 'Install/upgrade (non-system) packages by an ordinary user (you).',
                                  'remove' : 'Remove packages that you has installed later.',
                                  'physically-remove' : 'Removes package even though somebody but me (root) owns it',
                                  'purge' : 'Remove packages and all its associated configuration and data files (by root only).',
                                  'markauto' : 'Mark packages as having been automatically installed.',
                                  'unmarkauto' : 'Mark packages as having been manually installed by you.'}
    
    def add_unsuffixed_operation_to_tasks(operation, tasks):
        if operation.endswith('+'):
            tasks.install.append(operation[:-1])
        elif operation.endswith('-'):
            tasks.remove.append(operation[:-1])
        elif operation.endswith('^'):
            tasks.physically_remove.append(operation[:-1])
        elif operation.endswith('_'):
            tasks.purge.append(operation[:-1])
        elif operation.endswith('%M'):
            tasks.markauto.append(operation[:-2])
        elif operation.endswith('%m'):
            tasks.unmarkauto.append(operation[:-2])
        else:
            print_error('''Error: invalid operation on the suffix''')
            sys.exit(ExitCodes.INVALID_OPERATION_ON_THE_SUFFIX.value)
        
    diverse_parser = subparsers.add_parser('diverse', parents=[parent_operation_parser])
    diverse_parser.add_argument('package_operations', nargs='*', metavar='operation',
                                help='''a package with one of the suffixes: "+", "-", "^", "_", "%M", "%m" \
                                (similarly to ones in aptitude, see 'man {0}' for details)'''.format(PROGRAM_NAME))
    
    # create the parser for the "safe-uprade" command
    #TODO: Is this explanation (help string) right in the circumstances of limited-apt utility?
    subparsers.add_parser('safe-upgrade', parents=[parent_operation_parser], help='Perform a safe upgrade.',
                          add_help=False)
    # create the parser for the "full-upgrade" command
    subparsers.add_parser('full-upgrade', parents=[parent_operation_parser],
                          help='Perform an upgrade, possibly installing and removing packages.', add_help=False)
    
    subparsers.add_parser('fix-interrupted', parents=[parent_operation_parser],
                          help='Complete tasks of previous user that has been interrupted.', add_help=False)
    subparsers.add_parser('ignore-interrupted', parents=[parent_operation_parser],
                          help='Ignore interrupted tasks and remove "{0}" filename.'.format(UNCOMPLETED_TASKS_FILENAME),
                          add_help=False)

    for operation, help in operation_subcommands_dict.items():
        operation_subcommand_parser = subparsers.add_parser(operation, parents=[parent_operation_parser],
                                                            help=help)
        operation_subcommand_parser.add_argument('packages', nargs='*', metavar='pkg', help='a package')

    # Parse and analyse arguments
    
    args = parser.parse_args(sys.argv[2:])
    

    display_modes = DisplayModes(args.show_arch, args.verbose, args.debug)

    try:
        if args.subcommand in operation_subcommands_dics() | {'safe-upgrade', 'full-upgrade', 'diverse', 'fix-interrupted'}:
            work_modes = WorkModes(args.remove_dependencies, args.force, args.purge_unused, args.fatal_errors,
                                   args.assume_yes, args.simulate)
            # TODO: Use "apt.progress.FetchProgress()" when it has been implemented
            progresses = Progresses(None, apt.progress.text.AcquireProgress(), apt.progress.base.InstallProgress())
            runner = ModificationRunner(user_id, display_modes, work_modes, consoleui.ErrorHandlers(), consoleui.Applying(),
                                        progresses, sys.stderr)
            if args.subcommand == 'safe-upgrade':
                runner.upgrade(full_upgrade=False)
            elif args.subcommand == 'full-upgrade':
                runner.upgrade(full_upgrade=True)
            elif args.subcommand == 'fix-interrupted':
                runner.fix_interrupted()
            else:
                tasks = Tasks()
                if args.subcommand == 'install':
                    tasks.install = args.packages
                elif args.subcommand == 'remove':
                    tasks.remove = args.packages
                elif args.subcommand == 'physically-remove':
                    tasks.physically_remove = args.packages
                elif args.subcommand == 'purge':
                    tasks.purge = args.packages
                elif args.subcommand == 'markauto':
                    tasks.markauto = args.packages
                elif args.subcommand == 'unmarkauto':
                    tasks.unmarkauto = args.packages
                elif args.subcommand == 'diverse':
                    for operation in args.package_operations:
                        add_unsuffixed_operation_to_tasks(operation, tasks)
                runner.perform_operations(tasks)
        elif args.subcommand == 'update':
            runner = UpdationRunner(user_id, display_modes, None, sys.stderr)
            runner.update()
        elif args.subcommand in ('print-enclosure', 'list-of-mine', 'owners-of'):
            runner = PrintRunner(user_id, display_modes, sys.stderr)
            if args.subcommand == 'print-enclosure':
                if display_modes.wordy():
                    print('Packages you ({0}) may install:'.format(runner.username))
                for name in runner.get_printed_enclosure():
                    print(name)
            elif args.subcommand == 'list-of-mine':
                if display_modes.wordy():
                    print('Packages installed by you ({0}):'.format(runner.username))
                for name in runner.get_printed_list_of_mine():
                    print(name)
            elif args.subcommand == 'owners-of':
                if display_modes.wordy():
                    print('Users that has install "{0}" package:'.format(args.package))
                for user in runner.get_owners_of(args.package):
                    print(user)
        sys.exit(ExitCodes.GOOD.value)
    #TODO: Заставиль это работать
    except KeyboardInterrupt:
        sys.exit(ExitCodes.INTERRUPTED.value)
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
    except WantToDoSystemComposingError:
        sys.exit(ExitCodes.WANT_TO_DO_SYSTEM_COMPOSING.value)
    except SystemComposingByResolverError:
        sys.exit(ExitCodes.SYSTEM_COMPOSING_BY_RESOLVER.value)
    except OnlyRootMayForceError:
        print_error('''Error: only root is able to use "--force" option''')
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES.value)
    except YouMayNotPurgeError:
        print_error('''Error: only root can purge packages and use "--purge-unused" option''')
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES.value)
    except GroupNotExistError as err:
        print_error('''Error: "{0}" group doesn't exist'''.format(err.group_name))
        sys.exit(ExitCodes.GROUP_NOT_EXIST.value)
    except ReadingVariableFileError as err:
        print_error('''Error number "{0}" appeared while reading file "{1}"'''.format(err.error_number, err.filename))
        sys.exit(ExitCodes.ERROR_WHILE_READING_VARIABLE_FILE.value)
    except WritingVariableFileError as err:
        print_error('''Error number "{0}" appeared while writing to file "{1}"'''.format(err.error_number, err.filename))
        sys.exit(ExitCodes.ERROR_WHILE_WRITING_VARIABLE_FILE.value)
    except EnclosureImportSyntaxError:
        print_error('Error while parsing enclosure')
        sys.exit(ExitCodes.ERROR_WHILE_PARSING_VARIABLE_FILE.value)
    except CoownershipImportSyntaxError:
        print_error('Error while parsing coownership-list')
        sys.exit(ExitCodes.ERROR_WHILE_PARSING_VARIABLE_FILE.value)
    except DistroHasNotBeenUpdated as err:
        last_update_str = "It has never been update" if err.time is None \
            else "It was last been updated at {0}".format(err.time.isoformat(sep=" ", timespec="seconds"))
        print_error('''Error: You must update list of available packages running '{0} update' command. {1}'''.
                    format(PROGRAM_NAME, last_update_str))
        if display_modes.wordy():
            print('''Only root can avoid this using "--force" option''')
        sys.exit(ExitCodes.DISTRO_HAS_NOT_BEEN_UPDATED.value)
    except DpkgJournalDirtyError:
        print_error('Error: Dpkg has been interrupted')
        if display_modes.wordy():
            print('''All dpkg operations will fail until this is fixed, the action to fix the system '''
                  '''if dpkg got interrupted is to run ‘dpkg –configure -a’ as root''')
        sys.exit(ExitCodes.DPKG_JOUNAL_DIRTY.value)
    except PrecedingTasksHasNotBeenCompletedError:
        print_error('Error: preceding tasks has been interruped')
        if display_modes.wordy():
            print('''Dpkg journal is good but may be '{0}' was been interrupted at package downloading stage. '''
                  '''You must run '{0} fix-interrupted' or '{0} ignore-interrupted' as root in order to unlock {0}. '''
                  '''Of course '{0} fix-interrupted' is recommended'''.format(PROGRAM_NAME))
        sys.exit(ExitCodes.PRECEDING_TASKS_HAS_NOT_BEEN_COMPLETED.value)
    except NothingInterruptedError:
        print_error('Error: nothing to fix')
        if display_modes.wordy():
            print(''''{0}' is good. Nothing has been interrupapt.ted'''.format(PROGRAM_NAME))
        sys.exit(ExitCodes.NOTHING_INTERRUPTED.value)
    except (YouMayNotFixInterruptedError, YouMayNotIgnoreInterruptedError):
        print_error('''Error: only root is able to use "fix-interrupted" and "ignore-interrupted" subcommands''')
        sys.exit(ExitCodes.YOU_HAVE_NOT_PRIVILEGES.value)
    except LockFailedError as err:
        print_error('CANNOT LOCK: ', err)
        sys.exit(ExitCodes.LOCK_FAILED.value)
    except FetchCancelledError as err:
        print_error('FETCH CANCELLED: ', err)
        sys.exit(ExitCodes.FETCH_CANCELLED.value)
    except FetchFailedError as err:
        print_error('FETCH FAILED: ', err)
        sys.exit(ExitCodes.FETCH_FAILED.value)
    except apt_pkg.Error as err:
        print_error('UNKNOWN ERROR: ', err)
        sys.exit(ExitCodes.UNKNOWN_ERROR.value)
    except StubError as err:
        print_error('It is a stub: ', err)
        sys.exit(ExitCodes.STUB.value)


if __name__ == '__main__':
    privileged_main()

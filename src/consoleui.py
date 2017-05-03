#
# Copyright (C) Anton Liaukevich 2011-2017 <leva.dev@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import sys
import os


def get_terminal_width():
    try:
        columns = os.popen('stty size', 'r').read().split()[1]
        return int(columns)
    except:
        columns = 80 # default value

        
class Applying:
    
    def __init__(self, modes):
        self.__modes = modes
    
    def show_changes(self, changes):
        if self.__modes.wordy():
            print('You want to perform these factical changes:')
            
        def print_onetype_operation_package_list(pkg_predicate, header):
            
            def suffixed_package_name(pkg):
                return pkg.name + '{a}' if pkg.is_auto_installed else pkg.name   
            
            terminal_width = get_terminal_width()
                
            package_list = sorted((pkg for pkg in changes if pkg_predicate(pkg)), key=lambda pkg: pkg.name)
            if len(package_list) > 0:
                print(header)
                line = '  '
                for pkg in package_list:
                    current_word = suffixed_package_name(pkg)
                    if len(current_word) + 2 > terminal_width:
                        if line != '  ':
                            print(line)
                        print('  ' + current_word)
                        line = '  '
                    else:
                        future_line = '  ' + current_word if line == '  ' else line + ' ' + current_word
                        if len(future_line) > terminal_width:
                            print(line)
                            line = '  '
                        else:
                            line = future_line
                if line != '  ':
                    print(line)
            
            print_onetype_operation_package_list(lambda pkg: pkg.marked_install,
                                                 'These new packages will be installed:')
            print_onetype_operation_package_list(lambda pkg: pkg.marked_upgrade and not pkg.marked_install,
                                                 'These packages will be upgraded:')
            print_onetype_operation_package_list(lambda pkg: pkg.marked_reinstall,
                                                 'These packages will be reinstalled:')
            print_onetype_operation_package_list(lambda pkg: pkg.marked_downgrade,
                                                 'These packages will be downgraded:')
            print_onetype_operation_package_list(lambda pkg: pkg.marked_delete,
                                                 'These packages will be removed:')
            print_onetype_operation_package_list(lambda pkg: pkg.marked_keep,
                                                 'These packages will be kept at they current version:')

def terminate(exitcode):
    sys.exit(exitcode)
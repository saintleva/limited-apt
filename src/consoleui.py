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


import os
import time
from limitedapt.constants import *
from metrics import *


#TODO: Is it right?
#@functools.lru_cache
def get_terminal_width():
    try:
        columns = os.popen('stty size', 'r').read().split()[1]
        return int(columns)
    except:
        return 80 # default value
    

class Modded:
    
    @property
    def modes(self):
        return self.__modes
    
    @modes.setter
    def modes(self, modes):
        self.__modes = modes

        
class Applying(Modded):
    
    def show_changes(self, cache, is_upgrading=False):
        if self.modes.wordy():
            print('You want to perform these factical changes:')

        changes = cache.get_changes()
            
        def print_onetype_operation_package_list(pkg_predicate, header):
            
            if is_upgrading:
                def suffixed_package_name(pkg):
                    return pkg.name
            else:
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
        
        update_count = sum(1 for pkg in changes if pkg.marked_upgrade and not pkg.marked_install)
        #TODO: Calculate count of "have not been updated"        
        print('''{0} packages will be updated, {1} new will be installed, {2} marked for deletion, '''
              .format(update_count, cache.install_count, cache.delete_count))
        print('''Required to download {0} archives. '''.format(pretty_size_str(cache.required_download)), end='')
        if cache.required_space >= 0:
            print('''{0} will be occupied after unpacking.'''.format(pretty_size_str(cache.required_space)))
        else:
            print('''{0} will be freed unpacking.'''.format(pretty_size_str(-cache.required_space)))
    
    def prompt_agree(self):
        while True:
            print('Are you want to countinue? [Y/n]')
            answer = input()
            if answer == '' or answer.startswith('Y') or answer.startswith('y'):
                return True
            if answer.startswith('N') or answer.startswith('n'):
                return False 
            print('Incorrect answer.')


class ErrorHandlers(Modded):
    
    def cannot_find_package(self, pkg_name):
        print('''Cannot find package "{0}"'''.format(pkg_name))
        
    def you_already_own_package(self, concrete_package):
        print('''You already own package "{0}"'''.format(concrete_package))
        
    def may_not_install(self, pkg, is_auto_installed_yet=False):
        name = self.modes.pkg_str(pkg)
        if is_auto_installed_yet:
            print('''Error: package "{0}" which you want to install is system-constitutive and nobody but '''
                  '''root may install it or throw down "auto-installed" mark from them'''.format(name))
        else:
            print('''Error: package "{0}" which you want to install is system-constitutive and nobody '''
                  '''but root may install or it '''.format(name))
        
#TODO: remove it:
#    def may_not_upgrade_system_constitutive(self, pkg_name, version):
#        print('''Error: you have not permissions to upgrade package "{0}" to version "{1}" because '''
#              '''this new version is system-constitutive.'''.format(pkg_name, version))
        
    def may_not_upgrade_to_new(self, pkg, version):
        print('''Error: you have not permissions to upgrade package "{0}" to version "{1}" because '''
              '''this new version is system-constitutive'''.format(self.modes.pkg_str(pkg), version))
        
    #TODO: when use this mehton?
    def may_not_upgrade_system(self, pkg):
        print('''Error: package "{0}" which you want to upgrade is system and nothing but root '''
              '''or users in "{1}" group may upgrade it'''.format(self.modes.pkg_str(pkg),
                                                                  UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME))
        
    def is_not_installed(self, pkg_name, why_must_be):
        action_dict = {"remove" : 'remove',
                       "physically-remove" : 'physically remove',
                       "purge" : 'remove with its configuration files',
                       "physically-purge" : 'physically remove with its configuration files',
                       "markauto" : 'mark as automatically installed',
                       "unmarkauto" : 'mark as manually installed'}                        
        print('''Error: package "{0}" which you want to {1} is not installed'''.
              format(self.modes.package_str(pkg_name), action_dict[why_must_be]))       
        
    def may_not_remove(self, pkg):
        print('''Error: you may not remove package "{0}" because you have not permissions to remove packages other than packages '''
              '''you have installed later and want to explicitly remove'''.format(self.modes.pkg_str(pkg)))
        
    def may_not_physically_remove(self, pkg_name):
        print('''Error: you may not physically remove package "{0}" because only root may do that'''.
              format(self.modes.package_str(pkg_name)))
        
    def may_not_purge(self, pkg_name):
        print('''Error: you may not purge package "{0}" because only root may do that'''.
              format(self.modes.package_str(pkg_name)))
        
    def may_not_markauto(self, pkg_name):
        print('''Error: you may not mark package "{0}" as automatically installed because you have not permissions '''
              '''to "markauto" packages other than packages you have marked manually installed later'''.
              format(self.modes.package_str(pkg_name)))
        
    def may_not_downgrade(self):
        print('''Error: you have not permissions to downgrade packages''')
        
    def may_not_keep(self):
        print('''Error: you have not permissions to keep packages at their current versions''')
        
    def may_not_install_from_this_archive(self, archive):
        print('''Error: you have not permissions to install packages from "{0}" archive (suite)'''.format(archive))

    def package_is_not_trusted(self, pkg):
        print('''Error: package "{0}" is not trusted".'''.format(self.modes.pkg_str(pkg)))
        
    def physical_removation(self, pkg_name):
        if self.modes.verbose:
            print('''No simple user has installed package "{0}" therefore physical removation '''
                  '''is equivalent to simple removation in that case'''.format(self.modes.package_str(pkg_name)))
            
    def physical_markauto(self, pkg_name):
        if self.modes.verbose:
            print('''No simple user has marked package "{0}" automatically installed therefore physical "markauto" '''
                  '''is equivalent to simple 'markauto' in that case'''.format(self.modes.package_str(pkg_name)))
            
    def simulate(self):
        head = '...SIMULATING'
        point_count = get_terminal_width() - len(head) 
        print(head, end='', flush=True)
        for i in range(point_count):
            time.sleep(0.03)
            print('.', end='', flush=True)
        print()

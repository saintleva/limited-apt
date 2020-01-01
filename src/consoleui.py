#
# Copyright (C) Anton Liaukevich 2011-2019 <leva.dev@gmail.com>
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


import time
import subprocess
from limitedapt import single
from limitedapt.constants import *
from limitedapt.modes import Modded
from limitedapt.updatetime import UpdateTimes
from metrics import *


PROGRAM_NAME = 'limited-apt'

@single.run_once
def get_terminal_width():
    try:        
        columns = subprocess.getoutput("stty size").split()[1]
        return int(columns)
    except:
        return 80 # default value
    
     
class Applying(Modded):
    
    def show_changes(self, all_changes):
        if self.modes.wordy():
            print('You want to perform these changes:')

        terminal_width = get_terminal_width()

        def print_onetype_operation_package_list(pkgs, suffix_func, header):
            if pkgs:
                print(header)
                line = '  '
                for pkg in pkgs:
                    current_word = self.modes.pkg_str(pkg) + suffix_func(pkg)
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

        non_suffix = lambda pkg: ''

        def removing_suffix(pkg):
            purging = 'p' if pkg in all_changes.purged else ''
            auto = 'u' if pkg.is_auto_removable else ''
            concatenated = '{' + purging + auto + '}'
            return '' if concatenated == '{}' else concatenated

        print_onetype_operation_package_list(all_changes.logically_installed, non_suffix,
                                             'These new packages will be logically installed:')
        print_onetype_operation_package_list(all_changes.physically_installed,
                                             lambda pkg: '{a}' if pkg.is_auto_installed else '',
                                             'These new packages will be physically installed:')
        print_onetype_operation_package_list(all_changes.logically_installed_but_physically_upgraded, non_suffix,
                                             'These packages will be logically installed but physically upgrade:')
        print_onetype_operation_package_list(all_changes.upgraded, non_suffix, 'These packages will be upgrade:')
        print_onetype_operation_package_list(all_changes.reinstalled, non_suffix, 'These packages will be reinstalled:')
        print_onetype_operation_package_list(all_changes.downgraded, non_suffix,'These packages will be downgraded:')
        print_onetype_operation_package_list(all_changes.logically_removed, non_suffix,
                                             'These packages will be logically removed:')
        print_onetype_operation_package_list(all_changes.physically_removed + all_changes.purged, removing_suffix,
                                             'These packages will be physically removed:')
        print_onetype_operation_package_list(all_changes.kept, non_suffix,
                                             'These packages will be kept at they current version:')

        #TODO: Calculate count of "have not been updated"
        print(
            '''{0} new will be logically installed, {1} new will be physically installed, ''' \
            '''{2} will be logically installed but physically upgraded, {3} will be upgraded'''.
                format(len(all_changes.logically_installed), len(all_changes.physically_installed),
                       len(all_changes.logically_installed_but_physically_upgraded), len(all_changes.upgraded)), end='')
        if all_changes.reinstalled:
            print(''', {0} will be reinstalled'''.format(len(all_changes.reinstalled)), end='')
        if all_changes.downgraded:
            print(''', {0} will be downgraded'''.format(len(all_changes.downgraded)), end='')
        if all_changes.kept:
            print(''', {0} will be kept at they current version'''.format(len(all_changes.kept)), end='')
        print(''', {0} marked for logical deletion, {1} marked for physically deletion.'''.
              format(len(all_changes.logically_removed), len(all_changes.physically_removed)))

        cache = single.get_cache()
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

    def __init__(self):
        self.__byresolver = False

    @property
    def byresolver(self):
        return self.__byresolver

    def resolving_done(self):
        self.__byresolver = True
    
    def cannot_find_package(self, pkg_name):
        print('''Cannot find package "{0}"'''.format(pkg_name))
        
    def you_already_own_package(self, concrete_package):
        cache = single.get_cache()
        pkg = cache[str(concrete_package)]
        print('''You already own package "{0}"'''.format(self.modes.pkg_str(pkg)))
        
    def may_not_install(self, pkg, is_auto_installed_yet=False):
        name = self.modes.pkg_str(pkg)
        if is_auto_installed_yet:
            print('''Error: package "{0}" which you want to install is system-constitutive and nobody but '''
                  '''root may install it or throw down "auto-installed" mark from them'''.format(name))
        else:
            purpose = 'need to install in order to resolve dependencies' if self.byresolver else 'want to install'
            print('''Error: package "{0}" which you {1} is system-constitutive and nobody '''
                  '''but root may install it'''.format(name, purpose))
        
    def may_not_upgrade_to_new(self, pkg, installed_version_also):
        what = "package" if installed_version_also else "this new version"
        print('''Error: you have not permissions to upgrade package "{0}" to version "{1}" because '''
              '''{2} is system-constitutive'''.format(self.modes.pkg_str(pkg), pkg.candidate.version, what))
        
    def is_not_installed(self, pkg, why_must_be):
        action_dict = {"remove" : 'remove',
                       "physically-remove" : 'physically remove',
                       "purge" : 'physically remove with its configuration files',
                       "markauto" : 'mark as automatically installed',
                       "unmarkauto" : 'mark as manually installed'}                        
        print('''Error: package "{0}" which you want to {1} is not installed'''.
              format(self.modes.pkg_str(pkg), action_dict[why_must_be]))
        
    def may_not_remove(self, pkg, is_root=False):
        print('''Error: you may not remove package "{0}" because you have not permissions to remove packages other than packages '''
              '''you have installed'''.format(self.modes.pkg_str(pkg)), end='')
        if is_root:
            print('''. Despite this you can explicitly physically remove packages using "physically-remove" subcommand''')
        else:
            print()
        
    def may_not_physically_remove(self, pkg):
        print('''Error: you may not physically remove package "{0}" because only root may do that'''.
              format(self.modes.pkg_str(pkg)))
        
    def may_not_purge(self, pkg):
        print('''Error: you may not purge package "{0}" because only root may do that'''.
              format(self.modes.pkg_str(pkg)))
        
    def may_not_markauto(self, pkg):
        print('''Error: you may not mark package "{0}" as automatically installed because you have not permissions '''
              '''to "markauto" packages other than packages you have marked manually installed later'''.
              format(self.modes.pkg_str(pkg)))
        
    def may_not_downgrade(self):
        print('''Error: cannot downgrade packages. Only root using "--force" option may do that''')

    def force_downgrade(self, pkg):
        if self.modes.wordy():
            print('''Forced by root: downgrading package "{0}" to version "{1}"'''.
                  format(self.modes.pkg_str(pkg), pkg.candidate.version))
        
    def may_not_keep(self):
        print('''Error: cannot keep packages at their current versions. Only root using "--force" option may do that''')

    def force_keep(self, pkg):
        if self.modes.wordy():
            print('''Forced by root: package "{0}" will be kept at their current versions "{1}"'''.
                  format(self.modes.pkg_str(pkg), pkg.candidate.version))

    def may_not_break(self, pkg):
        print('''Error: your actions make package "{0}" broken'''.format(self.modes.pkg_str(pkg)))

    def force_break(self, pkg):
        if self.modes.wordy():
            print('''Forced by root: package "{0}" will be broken in order to safisfy dependencies'''.
                  format(self.modes.pkg_str(pkg)))

    def may_not_install_from_this_archive(self, archive):
        print('''Error: you have not permissions to install packages from "{0}" archive (suite)'''.format(archive))

    def package_is_not_trusted(self, pkg):
        print('''Error: package "{0}" is not trusted".'''.format(self.modes.pkg_str(pkg)))

    def force_untrusted(self, pkg):
        print('''Forced by root: package "{0}" will be installed although this is not trusted'''.format(self.modes.pkg_str(pkg)))

    def simple_removation(self, pkg):
        if self.modes.verbose:
            print('''No simple user have installed package "{0}" therefore physical removation '''
                  '''is equivalent to simple removation in that case'''.format(self.modes.pkg_str(pkg)))

    @staticmethod
    def __last_update_str(last_update):
        return "has not ever been updated" if last_update is None else "was last been updated at: " + \
                                                                       last_update.isoformat(sep=" ", timespec="seconds")

    def distro_updating_warning(self, last_update):
        print('''Warning: you should run "{0} update" before in order to update list of available packages, which {1}'''.
              format(PROGRAM_NAME, ErrorHandlers.__last_update_str(last_update)))

    def enclosure_updating_warning(self, last_update):
        print('''Warning: you should run "{0} update" before in order to update enclosure, which {1}'''.
              format(PROGRAM_NAME, ErrorHandlers.__last_update_str(last_update)))

#TODO: remove it
#    def simple_markauto(self, pkg):
#        if self.modes.verbose:
#            print('''No simple user has marked package "{0}" automatically installed therefore physical "markauto" '''
#                  '''is equivalent to simple 'markauto' in that case'''.format(self.modes.pkg_str(pkg)))

    def simulate(self):
        head = '...SIMULATING'
        point_count = get_terminal_width() - len(head) 
        print(head, end='', flush=True)
        for i in range(point_count):
            time.sleep(0.03)
            print('.', end='', flush=True)
        print()

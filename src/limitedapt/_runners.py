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
from limitedapt.packages import VersionedPackage
'''Logics of limited-apt'''

import pwd
import grp
import os.path
import apt
import apt_pkg
import apt.progress.base
from limitedapt import exitcodes, constants, coownership
from limitedapt.errors import StubError
from limitedapt.packages import *
from limitedapt.coownership import *
from limitedapt.enclosure import *


class YouHaveNotPrivileges(TerminationError): pass


class OperationPair:
    
    def __init__(self, command, package):
        self.__command = command
        self.__package = package
        #TODO: Do I need this checking?
#         if len(package) == 0:
#             raise InvalidOperation('Error: invalid operation: package name is empty')
#         else:
#             self._package = package
            
    @property
    def command(self):
        return self.__command

    @property
    def package(self):
        return self.__package
        
        
class Modes:
    '''limited-apt application modes (options) incapsulation'''
    
    def __init__(self, show_arch, debug, verbose, purge_unused, simulate=False, prompt=False, fatal_errors=False):
        self.__show_arch = show_arch
        self.__debug = debug
        self.__verbose = verbose
        self.__purge_unused = purge_unused
        self.__simulate = simulate
        self.__prompt = prompt
        self.__fatal_errors = fatal_errors
        
    @property
    def show_arch(self):
        return self.__show_arch
    
    def package_str(self, cache, package):
        try:
            pkg = cache[str(package)]
        except KeyError:
            return str(package)
        return pkg.fullname if self.show_arch else pkg.name
        
    @property
    def debug(self):
        return self.__debug
    
    @property
    def verbose(self):
        return self.__verbose
    
    def wordy(self):
        return self.debug or self.verbose
    
    @property
    def purge_unused(self):
        return self.__purge_unused
            
    @property
    def simulate(self):
        return self.__simulate
    
    @property
    def prompt(self):
        return self.__prompt
    
    @property
    def fatal_errors(self):
        return self.__fatal_errors
  
    
class Progresses:
    
    def __init__(self, fetch, acquire, install):   
        self.__fetch = fetch
        self.__acquire = acquire
        self.__install = install
        
    @property
    def fetch(self):
        return self.__fetch

    @property
    def acquire(self):
        return self.__acquire

    @property
    def install(self):
        return self.__install
    

def list_to_str(items):
    result = ""
    is_first = True
    for item in items:
        if not is_first:
            result += ", "            
        result += str(item)
        is_first = False
    return result

class Runner:
    
    def __init__(self, user_id, modes, out_stream, err_stream, progresses, applying_ui, termination):
        self.__modes = modes
        self.__out_stream = out_stream
        self.__err_stream = err_stream
        self.__progresses = progresses
        self.__applying_ui = applying_ui(modes)
        self.__termination = termination
        
        def effective_username(user_id):
            if user_id == 0:
                return "root"
            name = pwd.getpwuid(user_id).pw_name
            return "root" if name == "root" or \
                self.__is_belong_to_group(name, constants.UNIX_LIMITEDAPT_ROOTS_GROUPNAME) \
                else name
        
        self.__username = effective_username(user_id)
        self.__check_user_privileges()
        self.__load_program_options()
        
    @property
    def modes(self):
        return self.__modes
    
    @property
    def out_stream(self):
        return self.__out_stream
    
    @property
    def progresses(self):
        return self.__progresses
    
    @property
    def err_stream(self):
        return self.__err_stream
    
    @property
    def applying_ui(self):
        return self.__applying_ui
    
    @property
    def termination(self):
        return self.__termination
    
    @property
    def username(self):
        return self.__username
    
    @property
    def has_privileges(self):
        return self.__has_privileges
    
    @property
    def may_upgrade_package(self):
        return self.__may_upgrade_package
    
    @property
    def default_release(self):
        return self.__default_release
    
    def __print_message(self, msg):
        print(msg, file=self.out_stream)
    
    def __print_error(self, msg):
        print(msg, file=self.err_stream)
    
    def __debug_message(self, message):
        if self.modes.debug:
            print('Debug message: {0}'.format(message))
    
    def __is_belong_to_group(self, user_name, group_name):
        try:
            group = grp.getgrnam(group_name)
            return user_name in group.gr_mem
        except KeyError:
            self.__print_error('''"{0}" group doesn't exist'''.format(group_name))
            self.termination(exitcodes.GROUP_NOT_EXIST)
            
    def __check_user_privileges(self):
        self.__has_privileges = self.username == "root" or \
            self.__is_belong_to_group(self.username, constants.UNIX_LIMITEDAPT_GROUPNAME)
        self.__may_upgrade_package = \
            self.__is_belong_to_group(self.username, constants.UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME)
        self.__debug_message('''your username is: "{0}", ''' \
                             '''you has privileges for modification operations: "{1}", ''' \
                             '''you may upgrade installed packages even they are system-constitutive: "{2}".'''.
                             format(self.username, self.has_privileges, self.may_upgrade_package))
        if self.modes.purge_unused and self.username != "root":
            self.__print_error('''Error: only root can purge packages and use "--purge-unused" option''')
            self.termination(exitcodes.YOU_HAVE_NOT_PRIVILEGES)
            
    #TODO: Do I really need it?
    def __load_program_options(self):
        self.__default_release = apt_pkg.config["APT::Default-Release"] or None
    
    def update_eclosure(self):
        #TODO: Implement enclosure updating
        raise StubError('"update-enclosure" command has not implemented yet')

    def update(self):
        if not self.has_privileges:
            self.__print_error('''Error: you have not privileges to update package list: '''
                               '''you must be root or a member of "{0}" group'''.
                               format(constants.UNIX_LIMITEDAPT_GROUPNAME))
            self.termination(exitcodes.YOU_HAVE_NOT_PRIVILEGES)
        cache = apt.Cache()
        cache.update(self.progresses.fetch)
        cache.open(None) #TODO: Do I really need to re-open the cache here?    
        self.update_eclosure()
        
    def __load_coownership_list(self):
        filename = os.path.join(constants.path_to_program_config(), 'coownership-list')
        self.__debug_message('''loading list of package coownership (by users) from file "{0}" ...'''.
                             format(filename))
        try:
            coownership_list = CoownershipList()
            coownership_list.import_from_xml(filename)
            return coownership_list
        except CoownershipImportSyntaxError as err:
            self.__print_error(err)
            self.termination(exitcodes.ERROR_WHILE_PARSING_CONFIG_FILES)
        except IOError as err:
            self.__print_error(err)
            self.termination(err.errno) #TODO: is it right?
            
    def __save_coownership_list(self, coownership_list):
        filename = os.path.join(constants.path_to_program_config(), 'coownership-list')
        self.__debug_message('''save list of package coownership (by users) to file "{0}" ...'''.
                             format(filename))
        try:
            coownership_list.export_to_xml(filename)
#         except CoownershipImportSyntaxError as err:
#             self.__print_error(err)
#             self.termination(exitcodes.ERROR_WHILE_PARSING_CONFIG_FILES)
        except IOError as err:
            self.__print_error(err)
            self.termination(err.errno) #TODO: is it right?

    def __load_enclosure(self):
        filename = os.path.join(constants.path_to_program_config(), 'enclosure')
        self.__debug_message('''loading non-system package set (enclosure) from file "{0}" ...'''.
                             format(filename))
        try:
            enclosure = Enclosure()
            enclosure.import_from_xml(filename)
            return enclosure 
        except EnclosureImportSyntaxError as err:
            self.__print_error(err)
            self.termination(exitcodes.ERROR_WHILE_PARSING_CONFIG_FILES)
        except IOError as err:
            self.__print_error(err)
            self.termination(err.errno) #TODO: is it right?
            
    def get_list_of_mine(self):
        coownership_list = self.__load_coownership_list()               
        return sorted(coownership_list.his_packages(self.username)) 
            
    def list_of_mine(self):
        cache = apt.Cache()
        if self.modes.wordy():
            self.__print_message('Packages installed by you ({0}):'.format(self.username))            
        for package in self.get_list_of_mine():
            print(self.modes.package_str(cache, package), file=self.out_stream)
        
    def get_printed_enclosure(self):
        cache = apt.Cache()
        enclosure = self.__load_enclosure()
        
        # We don't need to sort packages because iterator of "Cache" class already returns
        # sorted sequence
        return (self.modes.package_str(cache, pkg) for pkg in cache if pkg.candidate is not None and
                VersionedPackage(pkg.name, pkg.architecture(), pkg.candidate.version) in enclosure)
                    
    def print_enclosure(self, show_version_constraints):
        cache = apt.Cache()
        if self.modes.wordy():
            self.__print_message('Ordinary user can install these packages:')                     
        for package in self.get_printed_enclosure():
            print(self.modes.package_str(cache, package), file=self.out_stream)
        
    def __examine_and_apply_changes(self, cache, enclosure, remove_all_possible, explicit_removes):
        changes = cache.get_changes()
        self.applying_ui.show_changes(changes)
        if not changes:
            self.termination(exitcodes.GOOD)
        
        if self.username == "root":
            if self.modes.purge_unused:
                for pkg in changes:
                    if pkg.marked_delete:
                        pkg.mark_delete(purge=True)
        else:
            errors = False
            for pkg in sorted(changes):
                versioned_package = VersionedPackage(pkg.name, pkg.architecture(), pkg.candidate.version)
                if pkg.marked_install and versioned_package not in enclosure:
                    self.__print_error('''Error: you have not permissions to install package "{0}" because '''
                                       '''it is system-constitutive.'''.format(self.modes.package_str(cache, pkg)))
                    errors = True
                    if self.modes.fatal_errors:
                        break
                if pkg.marked_upgrade and versioned_package not in enclosure and not self.may_upgrade_package:
                    self.__print_error('''Error: you have not permissions to upgrade package "{0}" to version "{1}" '''
                                       '''because this new version is system-constitutive.'''.
                                       format(self.modes.package_str(cache, pkg), pkg.candidate.version))
                    errors = True
                    if self.modes.fatal_errors:
                        break
                if pkg.marked_downgrade:
                    self.__print_error('''Error: you have not permissions to downgrade packages''')
                    errors = True
                    if self.modes.fatal_errors:
                        break
                if pkg.marked_keep:
                    self.__print_error('''Error: you have not permissions to keep packages at their current versions''')
                    errors = True
                    if self.modes.fatal_errors:
                        break
                #TDOD: Is this logics right?
                if pkg.marked_delete:
                    if remove_all_possible:
                        
                    not in explicit_removes:
                    self.__print_error('''Error: you have not permissions to remove packages other than '''
                                       '''packages you has install later and want to explicitly remove''')
                    errors = True
                    if self.modes.fatal_errors:
                        break
                    
                #TODO: Also process "unmarkauto" !
                addend = [pkg.name]
                    
#                 is_setup_operation = (pkg.marked_install or pkg.marked_reinstall or 
#                                       pkg.marked_upgrade or pkg.marked_downgrade)
#                 if is_setup_operation:
#                     #TODO: Может быть я должен просматривать весь список origins?
#                     origin = pkg.candidate.origins[0]                    
#                     if self.default_release is not None and origin.archive != self.default_release:
#                         self.__print_error('''Error: you have not permissions to install package from origin '''
#                                            '''(suite) other that default ("{0}")'''.format(self.default_release))
#                         errors = True            
#                         if self.modes.fatal_errors:
#                             break   
#                     #TODO: Действительно ли я должен проверять это?                     
#                     if not origin.trusted:
#                         self.__print_error('''Error: package "{0}" is not trusted".'''.format(modes.package_str(pkg)))
#                         errors = True            
#                         if self._fatal_errors_mode:
#                             break
            if errors:
                self.termination(exitcodes.ATTEMPT_TO_PERFORM_SYSTEM_COMPOSING)
         
#        agree = self.applying_ui.prompt_agree() if self.modes.prompt else True
        if self.applying_ui.prompt_agree():
            try:
                cache.commit(self.progresses.acquire, self.progresses.install)
            except apt.cache.LockFailedException as err:
                #TODO: process this exception 
                print('CANNOT LOCK: ', err, file=self.err_stream)
            except apt.cache.FetchCancelledException:
                #TODO: process this exception 
                pass
            except apt.cache.FetchFailedException:
                #TODO: process this exception 
                pass
            
    def upgrade(self, full_upgrade=True):
        if not self.has_privileges:
            upgrade_type = "fully upgrade" if full_upgrade else "safe upgrade"
            self.__print_error('''Error: you have not privileges to {0} : '''
                               '''you must be root or a member of "{1}" group'''.
                               format(upgrade_type, constants.UNIX_LIMITEDAPT_GROUPNAME))
            self.termination(exitcodes.YOU_HAVE_NOT_PRIVILEGES)            
        cache = apt.Cache()        
        enclosure = self.__load_enclosure()
        cache.upgrade(full_upgrade)
        self.__examine_and_apply_changes(cache, enclosure, True, {})        
              
    def perform_operations(self, operation_tasks):
        if not self.has_privileges:
            self.__print_error('''Error: you have not privileges to perform these operations: '''
                               '''you must be root or a member of "{0}" group'''.
                               format(constants.UNIX_LIMITEDAPT_GROUPNAME))
            self.termination(exitcodes.YOU_HAVE_NOT_PRIVILEGES)
            
        cache = apt.Cache()
        
        coownership = self.__load_coownership_list()
        enclosure = self.__load_enclosure()
        
        def show_cannot_find_package(pkg_name):
            print('''Cannot find package "{0}"'''.format(pkg_name), file=self.out_stream)
            
        installation_tasks = operation_tasks.get("install", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to install: " + list_to_str(installation_tasks))
        for package_name in installation_tasks:
            try:
                pkg = cache[package_name]
                #TODO: Is it correct?
                versioned_package = VersionedPackage(pkg.shortname, pkg.architecture(), pkg.candidate.version)
                concrete_package = ConcretePackage(pkg.shortname, pkg.architecture())
                if pkg.is_installed:
                    #can_upgrade = versioned_package in enclosure and pkg.is_upgradable
                    if pkg.is_upgradable:
                        if versioned_package in enclosure or self.may_upgrade_package:
                            pkg.mark_upgrade()
                        else:
                            print('''Error: package "{0}" which you want to install is system and'''
                                  '''nothing but root or users in "limited-apt-upgraders" may upgrade it'''.
                                   format(pkg.name), file=self.out_stream)                            
                    if pkg.is_auto_installed:
                        if versioned_package in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            print('''Error: package "{0}" which you want to install is system and'''
                                  '''nothing but root may install it'''.
                                   format(pkg.name), file=self.out_stream)                            
                    else:
                        try:
                            coownership.add_ownership(concrete_package, self.username, also_root=True)                            
                        except UserAlreadyOwnsThisPackage:
                            print('''You already own package "{0}"'''.format(concrete_package))
                else:
                    if versioned_package in enclosure or self.username == "root":
                        coownership.add_ownership(concrete_package, self.username, also_root=True)
                        pkg.mark_install()
                    else:
                        print('''Error: package "{0}" which you want to install is system-constitutive '''
                              '''and nobody but root may install it'''.
                               format(pkg.name), file=self.out_stream)
            except KeyError:
                show_cannot_find_package(package_name)
                
        unmarkauto_tasks = operation_tasks.get("unmarkauto", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to unmarkauto: " + list_to_str(unmarkauto_tasks))
        for package_name in unmarkauto_tasks:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    if pkg.is_auto_installed:
                        if versioned_package in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            print('''Error: package "{0}" which you want to install is system and'''
                                  '''nothing but root may install it'''.
                                   format(pkg.name), file=self.out_stream)                            
                else:
                    print('''Warning: package "{0}" which you want to mark as manually installed is not installed'''.
                          format(pkg.name), file=self.out_stream)       
            except KeyError:
                show_cannot_find_package(package_name)
        
        markauto_tasks = operation_tasks.get("markauto", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to markauto: " + list_to_str(markauto_tasks))
        for package_name in markauto_tasks:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    pass
                else:
                    print('''Warning: package "{0}" which you want to mark as automatically installed is not installed'''.
                          format(pkg.name), file=self.out_stream)
            finally:
                pass                                      
                
        physically_remove_tasks = operation_tasks.get("remove", [])
        self.__debug_message("you want to physically remove: " + list_to_str(physically_remove_tasks))
        for package_name in physically_remove_tasks:
            try:
                pkg = cache[package_name]
                if self.username != "root":
                    print('''Error: you may not physically remove package "{0}" '''
                          '''because only root may do that'''.
                           format(self.modes.package_str(pkg)), file=self.err_stream)
                else:
                    try:
                        coownership.remove_package(package_name)
                    except PackageIsNotInstalled:
                        if self.modes.verbose:
                            print('''No simple user has installed package "{0}" therefore physical removation '''
                                  '''is equivalent to simple removation in that case''', file=self.out_stream)
                    pkg.mark_delete(auto_fix=False, purge=False)
            finally:
                pass
                
#         self.__debug_message("you want to purge: " + purge_tasks)
#         for package_name in purge_tasks:
#             try:
#                 pkg = cache[package_name]
#                 if username != "root":
#                     print('''Error: you may not purge package "{0}" because only root may do that'''.
#                           format(self.modes.package_str(pkg)), file=self.err_stream)
#                 else:
#                     try:
#                         coownership.remove_package()
#                     except PackageIsNotInstalled:
#                         if self.modes.verbose:
#                             print('''No simple user has installed package "{0}" therefore '''
#                                   '''coownership list will not be changed''', file=self.out_stream)
#                     pkg.mark_delete(auto_fix=False, purge=True)
#             finally:
#                 pass
        self.__examine_and_apply_changes(cache, enclosure, False, {})        
        
        self.__save_coownership_list(coownership)

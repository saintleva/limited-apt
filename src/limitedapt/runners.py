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
from limitedapt import constants, coownership
from limitedapt.errors import *
from limitedapt.packages import *
from limitedapt.coownership import *
from limitedapt.enclosure import *




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
    
    def __init__(self, show_arch, debug, verbose, purge_unused, physically_remove,
                 simulate=False, prompt=False, fatal_errors=False):
        self.__show_arch = show_arch
        self.__debug = debug
        self.__verbose = verbose
        self.__purge_unused = purge_unused
        self.__physically_remove = physically_remove
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
    def physically_remove(self):
        return self._physically_remove
            
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
    
    def __init__(self, user_id, modes, handlers, applying_ui, progresses, debug_stream):
        self.__modes = modes
        self.__handlers = handlers
        self.__handlers.modes = modes
        self.__applying_ui = applying_ui
        self.__applying_ui.modes = modes
        self.__progresses = progresses
        self.__debug_stream = debug_stream
        
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
    def handlers(self):
        return self.__handlers
    
    @property
    def applying_ui(self):
        return self.__applying_ui
    
    @property
    def progresses(self):
        return self.__progresses
    
    def debug_stream(self):
        return self.__debug_stream
       
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
    
    def __debug_message(self, message):
        if self.modes.debug:
            print('Debug message: {0}'.format(message))
    
    def __is_belong_to_group(self, user_name, group_name):
        try:
            group = grp.getgrnam(group_name)
            return user_name in group.gr_mem
        except KeyError:
            raise GroupNotExistError(group_name)
                    
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
            raise YouMayNotPurgeError()
            
    #TODO: Do I really need it?
    def __load_program_options(self):
        self.__default_release = apt_pkg.config["APT::Default-Release"] or None
    
    def update_eclosure(self):
        #TODO: Implement enclosure updating
        raise StubError('"update-enclosure" command has not implemented yet')

    def update(self):
        if not self.has_privileges:
            raise YouMayNotUpdateError()
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
        except IOError as err:
            raise ReadingConfigFilesError(filename, err.errno)
                    
    def __save_coownership_list(self, coownership_list):
        filename = os.path.join(constants.path_to_program_config(), 'coownership-list')
        self.__debug_message('''saving list of package coownership (by users) to file "{0}" ...'''.
                             format(filename))
        try:
            coownership_list.export_to_xml(filename)
        except IOError:
            raise WritingConfigFilesError()

    def __load_enclosure(self):
        filename = os.path.join(constants.path_to_program_config(), 'enclosure')
        self.__debug_message('''loading non-system package set (enclosure) from file "{0}" ...'''.
                             format(filename))
        try:
            enclosure = Enclosure()
            enclosure.import_from_xml(filename)
            return enclosure
        except IOError as err:
            raise ReadingConfigFilesError(filename, err.errno)
        
    def get_list_of_mine(self):
        coownership_list = self.__load_coownership_list()               
        return sorted(coownership_list.his_packages(self.username))
    
    def get_printed_list_of_mine(self):
        cache = apt.Cache()
        return (self.modes.package_str(cache, package) for package in self.get_list_of_mine())        
            
    def get_printed_enclosure(self):
        cache = apt.Cache()
        enclosure = self.__load_enclosure()        
        # We don't need to sort packages because iterator of "Cache" class already returns
        # sorted sequence
        return (self.modes.package_str(cache, pkg) for pkg in cache if pkg.candidate is not None and
                VersionedPackage(pkg.name, pkg.architecture(), pkg.candidate.version) in enclosure)
                    
    def __examine_and_apply_changes(self, cache, enclosure, remove_all_possible, explicit_removes):
        changes = cache.get_changes()
        self.applying_ui.show_changes(changes)
        if not changes:
            raise GoodExit()
              
        if self.username == "root":
            if self.modes.purge_unused:
                for pkg in changes:
                    if pkg.marked_delete:
                        pkg.mark_delete(purge=True)
        else:
            errors = False
            
            def check_fatal():
                nonlocal errors
                errors = True
                if self.modes.fatal_errors:
                    raise AttempToPerformSystemComposingError()                
                
            for pkg in sorted(changes):
                versioned_package = VersionedPackage(pkg.shortname, pkg.architecture(), pkg.candidate.version)
                if pkg.marked_install and versioned_package not in enclosure:
                    self.handlers.may_not_install(pkg.name)
                    check_fatal()
                if pkg.marked_upgrade and versioned_package not in enclosure and not self.may_upgrade_package:
                    self.handlers.may_not_upgrade_to_new(pkg.name, pkg.candidate.version)
                    check_fatal()
                if pkg.marked_downgrade:
                    self.handlers.may_not_downgrade()
                    check_fatal()
                if pkg.marked_keep:
                    self.handlers.may_not_keep()
                    check_fatal()
                if pkg.marked_delete:
                    self.handlers.may_not_remove(pkg.name)
                    check_fatal()

#                     if remove_all_possible:
#                         
#                     not in explicit_removes:
#                     self.__print_error('''Error: you have not permissions to remove packages other than '''
#                                        '''packages you has install later and want to explicitly remove''')
#                     errors = True
#                     if self.modes.fatal_errors:
#                         break
                    
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
                raise AttempToPerformSystemComposingError()
                     
#        agree = self.applying_ui.prompt_agree() if self.modes.prompt else True
        if self.applying_ui.prompt_agree():
            try:
                cache.commit(self.progresses.acquire, self.progresses.install)
            except apt.cache.LockFailedException as err:
                raise LockFailedError(err)
            except apt.cache.FetchCancelledException:
                raise FetchCancelledError(err)
            except apt.cache.FetchFailedException:
                raise FetchFailedError(err)
            
    def upgrade(self, full_upgrade=True):
        if not self.has_privileges:
            raise YouMayNotUpgradeError(full_upgrade)
        cache = apt.Cache()
        enclosure = self.__load_enclosure()
        cache.upgrade(full_upgrade)
        self.__examine_and_apply_changes(cache, enclosure, True, {})        
              
    def perform_operations(self, operation_tasks):
        if not self.has_privileges:
            raise YouMayNotPerformError()

        cache = apt.Cache()
        
        coownership = self.__load_coownership_list()
        enclosure = self.__load_enclosure()
        
        installation_tasks = operation_tasks.get("install", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("You want to install: " + list_to_str(installation_tasks))
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
                            self.handlers.may_not_upgrade(pkg.name)
                    if pkg.is_auto_installed:
                        if versioned_package in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            self.handlers.may_not_install(pkg.name, is_auto_installed_yet=True)
                    else:
                        try:
                            coownership.add_ownership(concrete_package, self.username, also_root=True)                            
                        except UserAlreadyOwnsThisPackage:
                            self.handlers.you_already_own_package(concrete_package)
                else:
                    if versioned_package in enclosure or self.username == "root":
                        coownership.add_ownership(concrete_package, self.username, also_root=True)
                        pkg.mark_install()
                    else:
                        self.handlers.may_not_install(pkg.name)
            except KeyError:
                self.handlers.cannot_find_package(package_name)
                
        remove_tasks = operation_tasks.get("remove", [])
        self.__debug_message("you want to remove: " + list_to_str(remove_tasks))
        for package_name in remove_tasks:
            try:
                pkg = cache[package_name]
                try:
                    concrete_package = ConcretePackage(pkg.shortname, pkg.architecture())
                    coownership.remove_ownership(concrete_package, self.username):
                    if not coownership.is_somebody_own(concrete_package)
                        pkg.mark_delete(purge=self.modes.purge_unused)
                except UserDoesNotOwnPackage:
                    self.handlers.may_not_remove(pkg.name)
                except PackageIsNotInstalled:
                    self.handlers.physical_removation(pkg.name)
            except KeyError:
                self.handlers.cannot_find_package(package_name)
                            
        physically_remove_tasks = operation_tasks.get("physically-remove", [])
        self.__debug_message("you want to physically remove" + list_to_str(physically_remove_tasks))
        for package_name in physically_remove_tasks:
            try:
                pkg = cache[package_name]
                if self.username != "root":
                    self.handlers.may_not_physically_remove(pkg.name)
                else:
                    try:
                        coownership.remove_package(concrete_package)
                    except PackageIsNotInstalled:
                        self.handlers.physical_removation(pkg.name)
                    finally:
                        pkg.mark_delete(purge=self.modes.purge_unused)
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        purge_tasks = operation_tasks.get("purge", [])
        self.__debug_message("you want to physically remove" + list_to_str(purge_tasks))
        for package_name in purge_tasks:
            try:
                pkg = cache[package_name]
                if self.username != "root":
                    self.handlers.may_not_purge(pkg.name)
                else:
                    try:
                        coownership.remove_package(ConcretePackage(pkg.shortname, pkg.architecture()))
                    except PackageIsNotInstalled:
                        self.handlers.physical_removation(pkg.name)
                    finally:
                        pkg.mark_delete(purge=True)
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        markauto_tasks = operation_tasks.get("markauto", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to markauto: " + list_to_str(markauto_tasks))
        for package_name in markauto_tasks:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    try:
                        concrete_package = ConcretePackage(pkg.shortname, pkg.architecture())
                        coownership.remove_ownership(concrete_package, self.username)
                        if not coownership.is_somebody_own(concrete_package):
                            pkg.mark_auto()
                    except UserDoesNotOwnPackage:
                        self.handlers.may_not_markauto(pkg.name)
                    except PackageIsNotInstalled:
                        self.handlers.physical_markauto(pkg.name)
                else:
                    self.handlers.is_not_installed(pkg.name, "markauto")
            except KeyError:
                self.handlers.cannot_find_package(package_name)
                
        unmarkauto_tasks = operation_tasks.get("unmarkauto", [])
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to unmarkauto: " + list_to_str(unmarkauto_tasks))
        for package_name in unmarkauto_tasks:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    if pkg.is_auto_installed:
                        if VersionedPackage(pkg.shortname, pkg.architecture(), pkg.candidate.version) in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            self.handlers.may_not_install(pkg.name, True)
                else:
                    self.handlers.is_not_installed(pkg.name, "unmarkauto")
            except KeyError:
                self.handlers.cannot_find_package(package_name)
        
        self.__examine_and_apply_changes(cache, enclosure, False, {})        
        
        if not self.modes.simulate:
            self.__save_coownership_list(coownership)

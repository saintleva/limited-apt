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
'''Logics of limited-apt'''

import pwd
import grp
import os.path
import apt
import apt_pkg
import apt.progress.base
from limitedapt import constants, debug
from limitedapt.errors import *
from limitedapt.packages import *
from limitedapt.coownership import *
from limitedapt.enclosure import *


DEBUG = True


class Tasks:

    def __init__(self):
        self.install = []
        self.remove = []
        self.physically_remove = []
        self.purge = []
        self.markauto = []
        self.unmarkauto = []
        
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
    
    def pkg_str(self, pkg):
        return pkg.shortname + ":" + pkg.candidate.architecture if self.show_arch else pkg.name

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
        return self.__physically_remove
            
    @property
    def simulate(self):
        return self.__simulate
    
    @property
    def prompt(self):
        return self.__prompt
    
    @property
    def fatal_errors(self):
        return self.__fatal_errors
  
class Modded:
    
    @property
    def modes(self):
        return self.__modes
    
    @modes.setter
    def modes(self, modes):
        self.__modes = modes

     
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
    
    @property
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
        self.__may_upgrade_package = self.username == "root" or \
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
        filename = os.path.join(constants.path_to_program_config(), 'enclosure')
        if DEBUG:
            self.__debug_message('''updating enclosure in the file "{0}" ...'''.format(filename))
            debug.update_enclosure_by_debtags(filename)            
        else:
            raise StubError('Real enclosure updating has not implemented yet')
            

    def update(self):
        if not self.has_privileges:
            raise YouMayNotUpdateError(constants.UNIX_LIMITEDAPT_GROUPNAME)
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
        except IOError as err:
            raise WritingConfigFilesError(filename, err.errno)

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
        cache = apt.Cache()

        def is_root_own_package(concrete_package):
            owner_set = coownership_list.owners_of(concrete_package)
            return not owner_set or "root" in owner_set

        if self.username == "root":
            result = (pkg for pkg in cache if pkg.is_installed and not pkg.is_auto_installed and
                      is_root_own_package(ConcretePackage(pkg.shortname, pkg.candidate.architecture)))
        else:
            result = (cache[str(concrete_package)] for concrete_package in coownership_list.his_packages(self.username))
        return sorted(result)
    
    def get_printed_list_of_mine(self):
        return (self.modes.pkg_str(pkg) for pkg in self.get_list_of_mine())
            
    def get_printed_enclosure(self):
        cache = apt.Cache()
        enclosure = self.__load_enclosure()        
        # We don't need to sort packages because iterator of "Cache" class already returns
        # sorted sequence
        return (self.modes.pkg_str(pkg) for pkg in cache if pkg.candidate is not None and
                VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version) in enclosure)
                    
    def __examine_and_apply_changes(self, cache, enclosure, coownership, is_upgrading=False):
        changes = cache.get_changes()
        self.applying_ui.show_changes(cache, is_upgrading)

        self.handlers.resolving_done()

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
                    raise SystemComposingByResolverError()
                
            for pkg in sorted(changes):
                concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                versioned_package = VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version)
                if pkg.marked_install:
                    if versioned_package not in enclosure:
                        self.handlers.may_not_install(pkg)
                        check_fatal()
                    else:
                        implicitly = implicitly or pkg.name not in cache tasks.install
                if pkg.marked_upgrade and versioned_package not in enclosure and not self.may_upgrade_package:
                    self.handlers.may_not_upgrade_to_new(pkg, pkg.candidate.version)
                    check_fatal()
                if pkg.marked_downgrade:
                    self.handlers.may_not_downgrade()
                    check_fatal()
                if pkg.marked_keep:
                    self.handlers.may_not_keep()
                    check_fatal()
                if pkg.marked_delete:
                    if not pkg.is_auto_removable and not concrete_package.is_sole_own(concrete_package, self.username):
                        self.handlers.may_not_remove(pkg)
                        check_fatal()
                if pkg.is_inst_broken and not pkg.is_now_broken:
                    self.handlers.may_not_break(pkg)
                    check_fatal()

                #TODO: Also process "unmarkauto" !
                addend = [pkg.name]
                    
                is_setup_operation = (pkg.marked_install or pkg.marked_reinstall or 
                                      pkg.marked_upgrade or pkg.marked_downgrade)
                if is_setup_operation:
                    #TODO: Может быть я должен просматривать весь список origins?
                    origin = pkg.candidate.origins[0]
                    
                    #TODO: Вернуть эту проверку                    
#                     if self.default_release is not None and origin.archive != self.default_release:
#                         self.handlers.may_not_install_from_this_archive(origin.archive)
#                         check_fatal()
                        
                    #TODO: Действительно ли я должен проверять это?                     
                    if not origin.trusted:
                        self.handlers.package_is_not_trusted(pkg)
                        check_fatal()
            if errors:
                raise SystemComposingByResolverError()
                     
#        agree = self.applying_ui.prompt_agree() if self.modes.prompt else True
        if self.applying_ui.prompt_agree():
            try:
                if not self.modes.simulate:
                    cache.commit(self.progresses.acquire, self.progresses.install)
                else:
                    self.handlers.simulate()
            except apt.cache.LockFailedException as err:
                raise LockFailedError(err)
            except apt.cache.FetchCancelledException as err:
                raise FetchCancelledError(err)
            except apt.cache.FetchFailedException as err:
                raise FetchFailedError(err)
        else:
            raise GoodExit()

    def upgrade(self, full_upgrade=True):
        if not self.has_privileges:
            raise YouMayNotUpgradeError(constants.UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME, full_upgrade)
        cache = apt.Cache()
        enclosure = self.__load_enclosure()
        cache.upgrade(full_upgrade)
        self.__examine_and_apply_changes(cache, enclosure, is_upgrading=True)        
              
    def perform_operations(self, tasks):
        if not self.has_privileges:
            raise YouMayNotPerformError(constants.UNIX_LIMITEDAPT_GROUPNAME)

        cache = apt.Cache()
        
        coownership = self.__load_coownership_list()
        enclosure = self.__load_enclosure()

        errors = False

        def check_fatal():
            nonlocal errors
            errors = True
            if self.modes.fatal_errors:
                raise WantToDoSystemComposingError()

        #TODO: Implement good formatting of this message
        self.__debug_message("You want to install: " + list_to_str(tasks.install))
        for package_name in tasks.install:
            try:
                pkg = cache[package_name]
                #TODO: Is it correct?
                versioned_package = VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version)
                concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                if pkg.is_installed:
                    if pkg.is_upgradable:
                        if versioned_package in enclosure or self.may_upgrade_package:
                            pkg.mark_upgrade()
                        else:
                            self.handlers.may_not_upgrade_to_new(pkg, pkg.candidate.version)
                            check_fatal()
                    if pkg.is_auto_installed:
                        if versioned_package in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            self.handlers.may_not_install(pkg, is_auto_installed_yet=True)
                            check_fatal()
                    else:
                        try:
                            coownership.add_ownership(concrete_package, self.username, also_root=True)                            
                        except UserAlreadyOwnsThisPackage:
                            self.handlers.you_already_own_package(concrete_package)
                else:
                    if versioned_package in enclosure or self.username == "root":
                        coownership.add_ownership(concrete_package, self.username, also_root=False)
                        pkg.mark_install()
                    else:
                        self.handlers.may_not_install(pkg)
                        check_fatal()
            except KeyError:
                self.handlers.cannot_find_package(package_name)
                
        self.__debug_message("you want to remove: " + list_to_str(tasks.remove))
        for package_name in tasks.remove:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    try:
                        concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                        coownership.remove_ownership(concrete_package, self.username)
                        if not coownership.is_somebody_own(concrete_package):
                            pkg.mark_delete(purge=self.modes.purge_unused)
                    except UserDoesNotOwnPackage:
                        self.handlers.may_not_remove(pkg)
                        check_fatal()
                    except PackageIsNotInstalled:
                        if username == "root":
                            pkg.mark_delete(purge=self.modes.purge_unused)
                        else:
                            self.handlers.may_not_remove(pkg)
                            check_fatal()
                else:
                    self.handlers.is_not_installed(pkg, "remove")
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        self.__debug_message("you want to physically remove: " + list_to_str(tasks.physically_remove))
        for package_name in tasks.physically_remove:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    if self.username != "root":
                        self.handlers.may_not_physically_remove(pkg.name)
                        check_fatal()
                    else:
                        try:
                            coownership.remove_package(ConcretePackage(pkg.shortname, pkg.candidate.architecture))
                        except PackageIsNotInstalled:
                            self.handlers.simple_removation(pkg.name)
                        finally:
                            pkg.mark_delete(purge=self.modes.purge_unused)
                else:
                    self.handlers.is_not_installed(pkg, "physically-remove")
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        self.__debug_message("you want to purge: " + list_to_str(tasks.purge))
        for package_name in tasks.purge:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    if self.username != "root":
                        self.handlers.may_not_purge(pkg.name)
                        check_fatal()
                    else:
                        try:
                            coownership.remove_package(ConcretePackage(pkg.shortname, pkg.candidate.architecture))
                        except PackageIsNotInstalled:
                            self.handlers.simple_removation(pkg.name)
                        finally:
                            pkg.mark_delete(purge=True)
                else:
                    self.handlers.is_not_installed(pkg, "purge")
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        #TODO: Implement good formatting of this message
        self.__debug_message("you want to markauto: " + list_to_str(tasks.markauto))
        for package_name in tasks.markauto:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    try:
                        concrete_package = ConcretePackage(pkg.shortname, pkg.architecture())
                        coownership.remove_ownership(concrete_package, self.username)
                        if not coownership.is_somebody_own(concrete_package):
                            pkg.mark_auto(auto=True)
                    except UserDoesNotOwnPackage:
                        self.handlers.may_not_markauto(pkg.name)
                        check_fatal()
                else:
                    self.handlers.is_not_installed(pkg, "markauto")
            except KeyError:
                self.handlers.cannot_find_package(package_name)
                
        #TODO: Implement good formatting of this message
        self.__debug_message("you want to unmarkauto: " + list_to_str(tasks.unmarkauto))
        for package_name in tasks.unmarkauto:
            try:
                pkg = cache[package_name]
                if pkg.is_installed:
                    if pkg.is_auto_installed:
                        if VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version) in enclosure:
                            # We don't need to catch UserAlreadyOwnsThisPackage exception because
                            # if installed package marked 'automatically installed' nobody owns it.
                            # Also we don't add "root" to this package owners for the same reason.
                            coownership.add_ownership(concrete_package, self.username)
                            pkg.mark_auto(auto=False)
                        else:
                            self.handlers.may_not_markauto(pkg, True)
                            check_fatal()
                else:
                    self.handlers.is_not_installed(pkg.name, "unmarkauto")
            except KeyError:
                self.handlers.cannot_find_package(package_name)

        if errors:
            raise SystemComposingByResolverError()

        self.__examine_and_apply_changes(cache, enclosure)
        if not self.modes.simulate:
            self.__save_coownership_list(coownership)
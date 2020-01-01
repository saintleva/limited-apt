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
'''Logics of limited-apt'''


import importlib.util
from datetime import datetime
import pwd
import grp
import os.path
import apt
import apt_pkg
import apt.progress.base
from limitedapt.single import get_cache
from limitedapt import constants, debug
from limitedapt.errors import *
from limitedapt.packages import *
from limitedapt.coownership import *
from limitedapt.enclosure import *
from limitedapt.tasks import *
from limitedapt.changes import *
from limitedapt.modes import *
from limitedapt.updatetime import *


DEBUG = True

     
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
    

class RunnerBase:

    def __init__(self, user_id, display_modes, debug_stream):
        self.__display_modes = display_modes
        self.__debug_stream = debug_stream

        def effective_username(user_id):
            if user_id == 0:
                return "root"
            name = pwd.getpwuid(user_id).pw_name
            return "root" if name == "root" or \
                             self._is_belong_to_group(name, constants.UNIX_LIMITEDAPT_ROOTS_GROUPNAME) \
                else name

        self.__username = effective_username(user_id)
        self._check_user_privileges()

    @property
    def display_modes(self):
        return self.__display_modes

    @property
    def debug_stream(self):
        return self.__debug_stream

    @property
    def username(self):
        return self.__username

    @property
    def has_privileges(self):
        return self.__has_privileges

    def _debug_message(self, message):
        if self.display_modes.debug:
            print('Debug message: {0}'.format(message))

    @staticmethod
    def _is_belong_to_group(user_name, group_name):
        try:
            group = grp.getgrnam(group_name)
            return user_name in group.gr_mem
        except KeyError:
            raise GroupNotExistError(group_name)

    @property
    def update_times(self):
        return self.__update_times

    def _check_user_privileges(self):
        self.__has_privileges = self.username == "root" or \
                                self._is_belong_to_group(self.username, constants.UNIX_LIMITEDAPT_GROUPNAME)
        self._debug_message('''your username is: "{0}"\n''' \
                            '''you has privileges for modification operations: "{1}"'''.
                            format(self.username, self.has_privileges))

    def _load_coownership_list(self):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'coownership-list')
        self._debug_message('''loading list of package coownership (by users) from file "{0}" ...'''.
                            format(filename))
        try:
            coownership_list = CoownershipList()
            coownership_list.import_from_xml(filename)
            return coownership_list
        except IOError as err:
            raise ReadingVariableFileError(filename, err.errno)

    def _save_coownership_list(self, coownership_list):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'coownership-list')
        self._debug_message('''saving list of package coownership (by users) to file "{0}" ...'''.
                            format(filename))
        try:
            coownership_list.export_to_xml(filename)
        except IOError as err:
            raise WritingVariableFileError(filename, err.errno)

    def _load_enclosure(self):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'enclosure')
        self._debug_message('''loading non-system package set (enclosure) from file "{0}" ...'''.
                            format(filename))
        try:
            enclosure = Enclosure()
            enclosure.import_from_xml(filename)
            return enclosure
        except IOError as err:
            raise ReadingVariableFileError(filename, err.errno)


class UpdationRunner(RunnerBase):

    def __init__(self, user_id, display_modes, fetch_progress, debug_stream):
        super().__init__(user_id, display_modes, debug_stream)
        if not self.has_privileges:
            raise YouMayNotUpdateError(constants.UNIX_LIMITEDAPT_GROUPNAME)
        self.__fetch_progress = fetch_progress

    @property
    def fetch_progress(self):
        return self.__fetch_progress

    def __save_update_times(self, update_times):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'updatetimes')
        self._debug_message('''saving times of last distro and enclosure updating to file "{0}" ...'''.
                            format(filename))
        try:
            update_times.export_to_xml(filename)
        except IOError as err:
            raise WritingVariableFileError(filename, err.errno)

    def update_eclosure(self):
        # TODO: Implement enclosure updating
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'enclosure')
        if DEBUG:
            self._debug_message('''updating enclosure in the file "{0}" ...'''.format(filename))
            debug.update_enclosure_by_debtags(filename)
        else:
            raise StubError('Real enclosure updating has not implemented yet')

    def update(self):
        cache = get_cache()
        update_times = UpdateTimes()
        try:
            cache.update(self.fetch_progress)
            update_times.distro = datetime.now()
            cache.open(None)  #TODO: Do I really need to re-open the cache here?
            self.update_eclosure() #TODO: Do I need to use 'try' block?
            update_times.enclosure = datetime.now()
            self.__save_update_times(update_times)
        except apt.cache.FetchFailedException as err:
            raise FetchFailedError(err)


class PrintRunner(RunnerBase):

    def __init__(self, user_id, display_modes, debug_stream):
        super().__init__(user_id, display_modes, debug_stream)

    def get_list_of_mine(self):
        coownership_list = self._load_coownership_list()
        cache = get_cache()

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
        return (self.display_modes.pkg_str(pkg) for pkg in self.get_list_of_mine())

    def get_owners_of(self, package_name):
        try:
            cache = get_cache()
            pkg = cache[package_name]
            package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
            coownership_list = self._load_coownership_list()
            users = coownership_list.owners_of(package)
            if users:
                return users
            else:
                return {"root"} if pkg.is_installed and not pkg.is_auto_installed else set()
        except KeyError:
            return set()

    def get_printed_enclosure(self):
        enclosure = self._load_enclosure()
        # We don't need to sort packages because iterator of "Cache" class already returns
        # sorted sequence
        return (self.display_modes.pkg_str(pkg) for pkg in get_cache() if pkg.candidate is not None and
                VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version) in enclosure)


class ModificationRunner(RunnerBase):

    def __init__(self, user_id, display_modes, work_modes, handlers, applying_ui, progresses, debug_stream):
        if get_cache().dpkg_journal_dirty:
            raise DpkgJournalDirtyError()
        self.__work_modes = work_modes
        super().__init__(user_id, display_modes, debug_stream)
        self.__handlers = handlers
        self.__handlers.modes = display_modes
        self.__applying_ui = applying_ui
        self.__applying_ui.modes = display_modes
        self.__progresses = progresses
        self.__check_updating()

    @property
    def work_modes(self):
        return self.__work_modes

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
    def may_upgrade_package(self):
        return self.__may_upgrade_package

    @property
    def default_release(self):
        return self.__default_release

    def _check_user_privileges(self):
        super()._check_user_privileges()
        self.__may_upgrade_package = self.username == "root" or \
                                     self._is_belong_to_group(self.username,
                                                              constants.UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME)
        self._debug_message('''you may upgrade installed packages even they are system-constitutive: "{0}"'''.
                            format(self.may_upgrade_package))
        if self.work_modes.purge_unused and self.username != "root":
            raise YouMayNotPurgeError()
        if self.work_modes.force and self.username != "root":
            raise OnlyRootMayForceError()

    def __load_update_times(self):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'updatetimes')
        self._debug_message('''loading times of last distro and enclosure updating from file "{0}" ...'''.
                            format(filename))
        try:
            update_times = UpdateTimes()
            update_times.import_from_xml(filename)
            return update_times
        except IOError as err:
            raise ReadingVariableFileError(filename, err.errno)

    def __check_updating(self):
        update_times = self.__load_update_times()
        filename = os.path.join(constants.PATH_TO_PROGRAM_CONFIG, 'updating.py')
        spec = importlib.util.spec_from_file_location("updating", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        distro_updated_time = update_times.effective_distro()
        if module.is_distro_update_needed(distro_updated_time):
            if self.username == "root" and self.work_modes.force:
                self.handlers.distro_updating_warning(distro_updated_time)
            else:
                raise DistroHasNotBeenUpdated(distro_updated_time)
        if module.is_enclosure_update_needed(update_times.enclosure):
            self.handlers.enclosure_updating_warning(update_times.enclosure)

    # TODO: Do I really need it?
    def __load_program_options(self):
        apt_pkg.init_config()
        self.__default_release = apt_pkg.config["APT::Default-Release"] or None

    def __examine_and_apply_changes(self, tasks, real_tasks, enclosure, coownership):
        cache = get_cache()
        changes = cache.get_changes()
        all_changes = get_all_changes(changes, real_tasks)
        if self.username == "root" and self.work_modes.purge_unused:
            for pkg in changes:
                if pkg.marked_delete and not pkg in (real_tasks.remove + real_tasks.physically_remove):
                    pkg.mark_delete(purge=True)
                    if not pkg in all_changes.purge:
                        all_changes.purge.append(pkg)

        self.applying_ui.show_changes(all_changes)
        self.handlers.resolving_done()

        if self.username != "root":
            errors = False

            def check_fatal():
                nonlocal errors
                errors = True
                if self.work_modes.fatal_errors:
                    raise SystemComposingByResolverError()

            for pkg in sorted(changes):
                concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                versioned_package = VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version)
                if pkg.marked_install and versioned_package not in enclosure and self.username != "root":
                    self.handlers.may_not_install(pkg)
                    check_fatal()
                if pkg.is_installed and pkg.marked_upgrade and versioned_package not in enclosure and not self.may_upgrade_package:
                    installed_version = VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.installed)
                    self.handlers.may_not_upgrade_to_new(pkg, installed_version not in enclosure)
                    check_fatal()
                if pkg.marked_downgrade and not self.work_modes.force:
                    if self.work_modes.force:
                        self.handlers.force_downgrade(pkg)
                    else:
                        self.handlers.may_not_downgrade()
                        check_fatal()
                if pkg.marked_keep:
                    if self.work_modes.force:
                        self.handlers.force_keep(pkg)
                    else:
                        self.handlers.may_not_keep()
                        check_fatal()
                if pkg.marked_delete and not pkg.is_auto_removable:
                    if self.username == "root":
                        if coownership.is_any_user_own(concrete_package):
                            self.handlers.may_not_remove(pkg, is_root=True)
                            check_fatal()
                    elif coownership.is_sole_own(concrete_package, self.username):
                        coownership.remove_ownership(concrete_package, self.username)
                    else:
                        self.handlers.may_not_remove(pkg)
                        check_fatal()
                if pkg.is_inst_broken and not pkg.is_now_broken:
                    if self.modes.force:
                        self.handlers.force_break(pkg)
                    else:
                        self.handlers.may_not_break(pkg)
                        check_fatal()

                # TODO: Вернуть эту проверку
                #                     if self.default_release is not None and origin.archive != self.default_release:
                #                         self.handlers.may_not_install_from_this_archive(origin.archive)
                #                         check_fatal()

                # TODO: Действительно ли я должен проверять это?
                is_setup_operation = (pkg.marked_install or pkg.marked_reinstall or
                                      pkg.marked_upgrade or pkg.marked_downgrade)
                if is_setup_operation:
                    # TODO: Может быть я должен просматривать весь список origins?
                    origin = pkg.candidate.origins[0]

                    if not origin.trusted:
                        if self.work_modes.force:
                            self.handlers.force_untrusted(pkg)
                        else:
                            self.handlers.package_is_not_trusted(pkg)
                            check_fatal()
            if errors:
                raise SystemComposingByResolverError()

        if real_tasks.is_empty():
            raise GoodExit()

        if self.work_modes.assume_yes or self.applying_ui.prompt_agree():
            try:
                if not self.work_modes.simulate:
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
        enclosure = self._load_enclosure()
        get_cache().upgrade(full_upgrade)
        tasks = Tasks()
        self.__examine_and_apply_changes(tasks, RealTasks(tasks), enclosure, coownership=None)

    def perform_operations(self, tasks):
        if not self.has_privileges:
            raise YouMayNotPerformError(constants.UNIX_LIMITEDAPT_GROUPNAME)

        cache = get_cache()
        coownership = self._load_coownership_list()
        enclosure = self._load_enclosure()

        def list_to_str(items):
            result = ""
            is_first = True
            for item in items:
                if not is_first:
                    result += ", "
                result += str(item)
                is_first = False
            return result

        if tasks.install:
            self._debug_message("You want to install: " + list_to_str(tasks.install))
        if tasks.remove:
            self._debug_message("you want to remove: " + list_to_str(tasks.remove))
        if tasks.physically_remove:
            self._debug_message("you want to physically remove: " + list_to_str(tasks.physically_remove))
        if tasks.purge:
            self._debug_message("you want to purge: " + list_to_str(tasks.purge))
        if tasks.markauto:
            self._debug_message("you want to markauto: " + list_to_str(tasks.markauto))
        if tasks.unmarkauto:
            self._debug_message("you want to unmarkauto: " + list_to_str(tasks.unmarkauto))

        real_tasks = RealTasks(tasks)

        errors = False

        def check_fatal():
            nonlocal errors
            errors = True
            if self.work_modes.fatal_errors:
                raise WantToDoSystemComposingError()

        import time
        start = time.time()

        with cache.actiongroup():
            for package_name in tasks.install:
                try:
                    pkg = cache[package_name]
                    # TODO: Is it correct?
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
                                if self.username != "root":
                                    coownership.add_ownership(concrete_package, self.username)
                                pkg.mark_auto(auto=False)
                            else:
                                self.handlers.may_not_install(pkg, is_auto_installed_yet=True)
                                check_fatal()
                        else:
                            try:
                                if self.username == "root":
                                    coownership.check_root_own(concrete_package)
                                    coownership.add_ownership(concrete_package, "root")
                                else:
                                    coownership.add_ownership(concrete_package, self.username,
                                                              also_root=not coownership.is_any_user_own(concrete_package))
                            except UserAlreadyOwnsThisPackage:
                                self.handlers.you_already_own_package(concrete_package)
                                real_tasks.install.remove(concrete_package)
                    else:
                        if self.username == "root":
                            if coownership.is_any_user_own(concrete_package):
                                coownership.add_ownership(concrete_package, "root")
                            pkg.mark_install()
                        elif versioned_package in enclosure:
                            coownership.add_ownership(concrete_package, self.username, also_root=False)
                            pkg.mark_install()
                        else:
                            check_fatal()
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            for package_name in tasks.remove:
                try:
                    pkg = cache[package_name]
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    if pkg.is_installed:
                        try:
                            if coownership.remove_ownership(concrete_package, self.username) == Own.NOBODY:
                                pkg.mark_delete(purge=self.work_modes.purge_unused)
                        except UserDoesNotOwnPackage:
                            self.handlers.may_not_remove(pkg, is_root=(self.username == "root"))
                            check_fatal()
                        except PackageIsNotInstalled:
                            if self.username == "root":
                                pkg.mark_delete(purge=self.work_modes.purge_unused)
                            else:
                                self.handlers.may_not_remove(pkg)
                                check_fatal()
                    else:
                        self.handlers.is_not_installed(pkg, "remove")
                        real_tasks.remove.remove(concrete_package)
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            for package_name in tasks.physically_remove:
                try:
                    pkg = cache[package_name]
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    if pkg.is_installed:
                        if self.username != "root":
                            self.handlers.may_not_physically_remove(pkg)
                            check_fatal()
                        else:
                            try:
                                coownership.remove_package(concrete_package)
                            except PackageIsNotInstalled:
                                self.handlers.simple_removation(pkg)
                            finally:
                                pkg.mark_delete(purge=self.work_modes.purge_unused)
                    else:
                        self.handlers.is_not_installed(pkg, "physically-remove")
                        real_tasks.physically_remove.remove(concrete_package)
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            for package_name in tasks.purge:
                try:
                    pkg = cache[package_name]
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    if pkg.is_installed:
                        if self.username != "root":
                            self.handlers.may_not_purge(pkg)
                            check_fatal()
                        else:
                            try:
                                coownership.remove_package(concrete_package)
                            except PackageIsNotInstalled:
                                self.handlers.simple_removation(pkg)
                            finally:
                                pkg.mark_delete(purge=True)
                    elif not pkg.has_config_files:
                        self.handlers.is_not_installed(pkg, "purge")
                        real_tasks.purge.remove(concrete_package)
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            for package_name in tasks.markauto:
                try:
                    pkg = cache[package_name]
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    if pkg.is_installed:
                        try:
                            if coownership.remove_ownership(concrete_package, self.username) == Own.NOBODY:
                                pkg.mark_auto(auto=True)
                        except UserDoesNotOwnPackage:
                            self.handlers.may_not_markauto(pkg)
                            check_fatal()
                    else:
                        self.handlers.is_not_installed(pkg, "markauto")
                        real_tasks.markauto.remove(concrete_package)
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            for package_name in tasks.unmarkauto:
                try:
                    pkg = cache[package_name]
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    if pkg.is_installed:
                        if pkg.is_auto_installed:
                            if VersionedPackage(pkg.shortname, pkg.candidate.architecture,
                                                pkg.candidate.version) in enclosure:
                                # We don't need to catch UserAlreadyOwnsThisPackage exception because
                                # if installed package marked 'automatically installed' nobody owns it.
                                # Also we don't add "root" to this package owners for the same reason.
                                if self.username != "root":
                                    coownership.add_ownership(concrete_package, self.username)
                                pkg.mark_auto(auto=False)
                            else:
                                self.handlers.may_not_markauto(pkg, True)
                                check_fatal()
                    else:
                        self.handlers.is_not_installed(pkg, "unmarkauto")
                        real_tasks.unmarkauto.remove(concrete_package)
                except KeyError:
                    self.handlers.cannot_find_package(package_name)

            finish = time.time()
            print(finish - start, " SECONDS ELAPSED")

            if errors:
                raise SystemComposingByResolverError()

            self.__examine_and_apply_changes(tasks, real_tasks, enclosure, coownership)
            if not self.work_modes.simulate:
                self._save_coownership_list(coownership)

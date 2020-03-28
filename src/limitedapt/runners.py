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
import enum
import pwd
import grp
import os
import os.path
import shutil
from lxml import etree
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
from limitedapt.debconf import *
from limitedapt.download import *


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


class RealTasksImportSyntaxError(XmlImportSyntaxError): pass


class RunnerBase:

    def __init__(self, settings, user_id, display_modes, debug_stream):
        self.__settings = settings
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
    def settings(self):
        return self.__settings

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

        def load_single(filename):
            self._debug_message('''loading non-system package set (enclosure) from file "{0}" ...'''.
                                format(filename))
            if not os.path.exists(filename):
                raise FileNotExist(filename)
            try:
                enclosure = Enclosure()
                enclosure.import_from_xml(filename)
                return enclosure
            except IOError as err:
                raise ReadingVariableFileError(filename, err.errno)
            return enclosure

        if self.settings.urls.enclosure_debug_mode:
            enclosure = load_single(os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, "enclosure"))
        else:
            enclosure_list = [load_single(record.filename + ".enclosure") for record in self.settings.urls.enclosures]
            path_to_local_enclosure = os.path.join(self.settings.path_to_program_config, "local.enclosure")
            if os.path.exists(path_to_local_enclosure):
                enclosure_list.append(load_single(path_to_local_enclosure))
            enclosure = MixedEnclosure(*enclosure_list)

        return enclosure

class UpdationRunner(RunnerBase):

    def __init__(self, settings, user_id, display_modes, fetch_progress, debug_stream):
        super().__init__(settings, user_id, display_modes, debug_stream)
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
        if self.settings.urls.enclosure_debug_mode:
            filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'enclosure')
            self._debug_message('''updating enclosure in the file "{0}" in the debug mode ...'''.format(filename))
            debug.update_enclosure_by_debtags(filename)
        else:
            for record in self.settings.urls.enclosures:
                filename = record.filename + '.enclosure'
                self._debug_message('''downloading enclosure from "{0}" to the file "{1}" ...'''.
                                    format(record.url, filename))
                download_file(record.url, filename)

    def update_priorities(self):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'debconf-priorities.sqlite')
        url = self.settings.urls.debconf_priorities
        self._debug_message('''downloading debconf priorities from "{0}" to the file "{1}" ...'''.format(url, filename))
        download_file(url, filename)

    def update(self):
        cache = get_cache()
        update_times = UpdateTimes()
        cache.update(self.fetch_progress)
        update_times.distro = datetime.now()
        cache.open(None)  #TODO: Do I really need to re-open the cache here?
        self.update_eclosure()
        update_times.enclosure = datetime.now()
        self.update_priorities()
        update_times.priorities = datetime.now()
        self.__save_update_times(update_times)


class PrintRunner(RunnerBase):

    def __init__(self, settings, user_id, display_modes, debug_stream):
        super().__init__(settings, user_id, display_modes, debug_stream)

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

    def __init__(self, settings, user_id, display_modes, work_modes, handlers, applying_ui, progresses, debug_stream):
        self.__work_modes = work_modes
        super().__init__(settings, user_id, display_modes, debug_stream)
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
        distro_updated_time = update_times.effective_distro()
        if self.settings.updatetime_module.is_distro_update_needed(distro_updated_time):
            if self.username == "root" and self.work_modes.force:
                self.handlers.distro_updating_warning(distro_updated_time)
            else:
                raise DistroHasNotBeenUpdated(distro_updated_time)
        if self.settings.updatetime_module.is_enclosure_update_needed(update_times.enclosure):
            self.handlers.enclosure_updating_warning(update_times.enclosure)
        if self.settings.updatetime_module.is_priorities_update_needed(update_times.priorities):
            self.handlers.priorities_updating_warning(update_times.priorities)

    def __check_interrupted(self):
        if get_cache().dpkg_journal_dirty:
            raise DpkgJournalDirtyError()
        if os.path.exists(constants.PATH_TO_UMCOMPLETED_TASKS):
            raise PrecedingTasksHasNotBeenCompletedError()

    # TODO: Do I really need it?
    def __load_program_options(self):
        apt_pkg.init_config()
        self.__default_release = apt_pkg.config["APT::Default-Release"] or None

    def __check_priorities(self, fixing_interrupted=False):
        filename = os.path.join(constants.PATH_TO_PROGRAM_VARIABLE, 'debconf-priorities.sqlite')
        priorities = DebconfPrioritiesDB("sqlite:///" + filename)
        minimal_priority = minimal_debconf_priority_to_ask_questions()
        changes = get_cache().get_changes()

        errors = False
        if not fixing_interrupted:
            def check_fatal():
                nonlocal errors
                errors = True
                if self.work_modes.fatal_errors:
                    raise SystemComposingByResolverError()
            def priorities_failure(pkg, package_priority):
                self.handlers.may_not_debconf_configure(pkg, package_priority, minimal_priority)
            def bad_priorities_failure(pkg):
                self.handlers.bad_debconf_configure(pkg)
        else:
            def check_fatal():
                pass
            def priorities_failure(pkg, package_priority):
                self.handlers.now_debconf_configure_warning(pkg, package_priority, minimal_priority)
            def bad_priorities_failure(pkg):
                self.handlers.now_bad_debconf_configure_warning(pkg)

        for pkg in sorted(changes):
            concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
            if not priorities.well_processed(concrete_package):
                bad_priorities_failure(pkg)
                check_fatal()
            else:
                state = priorities[concrete_package]
                if state.status == Status.HAS_QUESTIONS and state.priority >= minimal_priority:
                    priorities_failure(pkg, state.priority)
                    check_fatal()

        return not errors

    def __check_free_space(self):

        def get_partition(path):
            output = subprocess.getoutput('df {0}'.format(path))
            lines = output.splitlines()
            return lines[1].split()[0]

        usr_total, usr_used, usr_free = shutil.disk_usage('/usr/')
        apt_archives_total, apt_archives_used, apt_archives_free = shutil.disk_usage('/var/cache/apt/archives/')
        cache = get_cache()
        minimal_free_space = self.settings.minimal_free_space

        if get_partition('/usr/') == get_partition('/var/cache/apt/archives/'):
            required = cache.required_space + cache.required_download
            if not minimal_free_space.usr.less_or_equal_to_other(usr_free - required, usr_total):
                raise NotEnoughSpace()
            if not minimal_free_space.apt_archives.less_or_equal_to_other(apt_archives_free - required, apt_archives_total):
                raise NotEnoughSpace()
        else:
            if not minimal_free_space.usr.less_or_equal_to_other(usr_free - cache.required_space, usr_total):
                raise NotEnoughSpace()
            if not minimal_free_space.apt_archives.less_or_equal_to_other(usr_free - cache.required_download, usr_total):
                raise NotEnoughSpace()

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
                if pkg.marked_delete and not pkg.is_auto_removable and pkg not in real_tasks:
                    sole_owns = coownership.is_sole_own(concrete_package, self.username)
                    if self.work_modes.remove_dependecies:
                        if sole_owns:
                            # User will be never being root here
                            coownership.remove_ownership(concrete_package, self.username)
                        else:
                            self.handlers.may_not_remove(pkg)
                            check_fatal()
                    else:
                        if self.username == "root":
                            if coownership.is_any_user_own(concrete_package):
                                self.handlers.may_not_remove(pkg, is_root=True, suggest_to_remove_deps=sole_owns)
                                check_fatal()
                        else:
                            self.handlers.may_not_remove(pkg, suggest_to_remove_deps=sole_owns)
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

            if errors or not self.__check_priorities():
                raise SystemComposingByResolverError()

        if real_tasks.is_empty():
            raise GoodExit()

        if not self.work_modes.force:
            self.__check_free_space()

        if self.work_modes.assume_yes or self.applying_ui.prompt_agree():
            if not self.work_modes.simulate:
                self._save_coownership_list(coownership)
                cache.commit(self.progresses.acquire, self.progresses.install)
                os.remove(constants.PATH_TO_UMCOMPLETED_TASKS)
            else:
                self.handlers.simulate()
        else:
            raise GoodExit()

    def upgrade(self, full_upgrade=True):
        if not self.has_privileges:
            raise YouMayNotUpgradeError(constants.UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME, full_upgrade)
        self.__check_interrupted()
        enclosure = self._load_enclosure()
        coownership = self._load_coownership_list()
        get_cache().upgrade(full_upgrade)
        tasks = Tasks()

        type = "full-upgrade" if full_upgrade else "safe-upgrade"
        root = etree.Element("tasks", {"type": type, "username": self.username,
                                       "purge-unused": self.work_modes.purge_unused})
        tree = etree.SubElement(root)
        tree.write(constants.UNCOMPLETED_TASKS_FILENAME, pretty_print=True, encoding="UTF-8", xml_declaration=True)

        self.__examine_and_apply_changes(tasks, RealTasks(tasks), enclosure, coownership)

    def perform_operations(self, tasks):
        if not self.has_privileges:
            raise YouMayNotPerformError(constants.UNIX_LIMITEDAPT_GROUPNAME)
        self.__check_interrupted()

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

            if errors:
                raise SystemComposingByResolverError()

            root = etree.Element("tasks", {"type" : "operations", "username" : self.username,
                                           "purge-unused" : self.work_modes.purge_unused})
            real_tasks.export_to_xml_element(root)
            tree = etree.SubElement(root)
            tree.write(constants.UNCOMPLETED_TASKS_FILENAME, pretty_print=True, encoding="UTF-8", xml_declaration=True)

            self.__examine_and_apply_changes(tasks, real_tasks, enclosure, coownership)

    def fix_interrupted(self):
        if self.username != "root":
            raise YouMayNotFixInterruptedError()
        if not os.path.exists(constants.PATH_TO_UMCOMPLETED_TASKS):
            raise NothingInterruptedError()

        # Parse file with uncompleted tasks
        try:
            cache = get_cache()
            root = etree.parse(constants.PATH_TO_UMCOMPLETED_TASKS).getroot()
            interrupted_type = root.get("type")
            username = root.get("username")
            purge_unused = bool(root.get("purge-unused"))
            real_tasks = RealTasks()
            if interrupted_type == "safe-upgrade":
                cache.upgrade(dist_upgrade=False)
            elif interrupted_type == "full-upgrade":
                cache.upgrade(dist_upgrade=True)
            elif interrupted_type == "operations":
                real_tasks.import_from_xml_element(root)
                try:
                    with cache.actiongroup():
                        for package in real_tasks.install:
                            cache[str(package)].mark_install()
                        for package in real_tasks.remove + real_tasks.physically_remove:
                            cache[str(package)].mark_delete()
                        for package in real_tasks.remove + real_tasks.purge:
                            cache[str(package)].mark_delete(purge=True)
                        for package in real_tasks.markauto:
                            cache[str(package)].mark_auto(auto=True)
                        for package in real_tasks.unmarkauto:
                            cache[str(package)].mark_auto(auto=False)
                except KeyError:
                    raise PackageNotExistNow(package)
            else:
                raise ValueError()
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise RealTasksImportSyntaxError()

        changes = cache.get_changes()
        all_changes = get_all_changes(changes, real_tasks)

        if self.work_modes.purge_unused:
            for pkg in changes:
                if pkg.marked_delete and not pkg in (real_tasks.remove + real_tasks.physically_remove):
                    pkg.mark_delete(purge=True)
                    if not pkg in all_changes.purge:
                        all_changes.purge.append(pkg)

        self.applying_ui.show_changes(all_changes)
        self.handlers.resolving_done()

        enclosure = self._load_enclosure()

        if username != "root":
            for pkg in sorted(changes):
                versioned_package = VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version)
                if pkg.marked_install and versioned_package not in enclosure:
                    self.handlers.now_install_warning(pkg)
                if pkg.is_installed and pkg.marked_upgrade and versioned_package not in enclosure:
                    self.handlers.now_upgrade_to_new_warning(pkg)
                if pkg.marked_downgrade and not self.work_modes.force:
                    self.handlers.now_downgrade_warning(pkg)
                if pkg.marked_keep:
                    self.handlers.now_keep_warning(pkg)
                if pkg.marked_delete and not pkg.is_auto_removable and pkg not in real_tasks:
                    self.handlers.now_remove_warning(pkg)
                if pkg.is_inst_broken and not pkg.is_now_broken:
                    self.handlers.now_break_warning(pkg)
                is_setup_operation = (pkg.marked_install or pkg.marked_reinstall or
                                      pkg.marked_upgrade or pkg.marked_downgrade)
                if is_setup_operation:
                    origin = pkg.candidate.origins[0]
                    if not origin.trusted:
                        self.handlers.now_untrusted_warning(pkg)

            self.__check_priorities(fixing_interrupted=True)

        if not self.work_modes.force:
            self.__check_free_space()

        if self.work_modes.assume_yes or self.applying_ui.prompt_agree():
            if not self.work_modes.simulate:
                cache.commit(self.progresses.acquire, self.progresses.install)
                os.remove(constants.PATH_TO_UMCOMPLETED_TASKS)
            else:
                self.handlers.simulate()
        else:
            raise GoodExit()

    def ignore_interrupted(self):
        if self.username != "root":
            raise YouMayNotFixInterruptedError()
        if not os.path.exists(constants.PATH_TO_UMCOMPLETED_TASKS):
            raise NothingInterruptedError()
        os.remove(constants.PATH_TO_UMCOMPLETED_TASKS)
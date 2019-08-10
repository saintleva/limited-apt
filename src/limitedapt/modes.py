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


class DisplayModes:

    def __init__(self, show_arch, verbose, debug):
        self.__show_arch = show_arch
        self.__verbose = verbose
        self.__debug = debug

    @property
    def show_arch(self):
        return self.__show_arch

    def pkg_str(self, pkg):
        return pkg.shortname + ":" + pkg.candidate.architecture if self.show_arch else pkg.name

    @property
    def verbose(self):
        return self.__verbose

    @property
    def debug(self):
        return self.__debug

    def wordy(self):
        return self.debug or self.verbose


class WorkModes:

    def __init__(self, force, purge_unused, fatal_errors, assume_yes, simulate):
        self.__force = force
        self.__purge_unused = purge_unused
        self.__fatal_errors = fatal_errors
        self.__assume_yes = assume_yes
        self.__simulate = simulate

    @property
    def force(self):
        return self.__force

    @property
    def purge_unused(self):
        return self.__purge_unused

    @property
    def fatal_errors(self):
        return self.__fatal_errors

    @property
    def assume_yes(self):
        return self.__assume_yes

    @property
    def simulate(self):
        return self.__simulate


class Modded:

    @property
    def modes(self):
        return self.__modes

    @modes.setter
    def modes(self, modes):
        self.__modes = modes

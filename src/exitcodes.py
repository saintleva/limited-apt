#
# Copyright (C) Anton Liaukevich 2011-2020 <leva.dev@gmail.com>
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

import enum


class ExitCodes(enum.Enum):
    GOOD = 0
    INTERRUPTED = 1
    INVALID_OPERATION_ON_THE_SUFFIX = 2
    YOU_HAVE_NOT_PRIVILEGES = 10
    WANT_TO_DO_SYSTEM_COMPOSING = 11
    SYSTEM_COMPOSING_BY_RESOLVER = 12
    YOU_ARE_NOT_COOWNER_OF_PACKAGE = 13
    PACKAGE_NOT_EXIST_NOW = 14
    NOT_ENOUGH_SPACE = 15
    DPKG_JOUNAL_DIRTY = 20
    PRECEDING_TASKS_HAS_NOT_BEEN_COMPLETED = 21
    NOTHING_INTERRUPTED = 22
    DISTRO_HAS_NOT_BEEN_UPDATED = 30
    GROUP_NOT_EXIST = 40
    PRIVILEGED_SCRIPT_HAS_BEEN_RUN_INCORRECTLY = 50
    FILE_NOT_EXIST = 60
    ERROR_WHILE_READING_VARIABLE_FILE = 61
    ERROR_WHILE_PARSING_VARIABLE_FILE = 62
    ERROR_WHILE_WRITING_VARIABLE_FILE = 63
    DEBCONFSHOW_PARSING_ERROR = 64
    SETTINGS_FILE_ERROR = 65
    CANNOT_DOWNLOAD = 66
    LOCK_FAILED = 70
    FETCH_CANCELLED = 71
    FETCH_FAILED = 72
    UNKNOWN_ERROR = 80
    STUB = 100
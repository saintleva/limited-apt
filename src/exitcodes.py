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

import enum


class ExitCodes(enum.Enum):
    GOOD = 0
    INTERRUPTED = 111111
    INVALID_OPERATION_ON_THE_SUFFIX = 2
    YOU_HAVE_NOT_PRIVILEGES = 10
    WANT_TO_DO_SYSTEM_COMPOSING = 11
    SYSTEM_COMPOSING_BY_RESOLVER = 12
    YOU_ARE_NOT_COOWNER_OF_PACKAGE = 13
    GROUP_NOT_EXIST = 20
    PRIVILEGED_SCRIPT_HAS_BEEN_RUN_INCORRECTLY = 21
    ERROR_WHILE_READING_CONFIG_FILES = 30
    ERROR_WHILE_WRITING_CONFIG_FILES = 40
    ERROR_WHILE_PARSING_CONFIG_FILES = 50
    LOCK_FAILED = 60
    FETCH_CANCELLED = 61
    FETCH_FAILED = 62
    STUB = 100
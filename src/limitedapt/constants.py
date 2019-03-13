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


UNIX_LIMITEDAPT_GROUPNAME = 'limited-apt'
UNIX_LIMITEDAPT_ROOTS_GROUPNAME = 'limited-apt-roots'
UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME = 'limited-apt-upgraders'

DEBUG = True

def path_to_program_config():
    if DEBUG:
        return "/mnt/limited-apt-data/"
    else:
        return NotImplemented

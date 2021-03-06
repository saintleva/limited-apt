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

import os


UNIX_LIMITEDAPT_GROUPNAME = 'limited-apt'
UNIX_LIMITEDAPT_ROOTS_GROUPNAME = 'limited-apt-roots'
UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME = 'limited-apt-upgraders'


PATH_TO_PROGRAM_VARIABLE = "/var/lib/limited-apt/"
UNCOMPLETED_TASKS_FILENAME = "uncompleted-tasks"
PATH_TO_UNCOMPLETED_TASKS = os.path.join(PATH_TO_PROGRAM_VARIABLE, UNCOMPLETED_TASKS_FILENAME)
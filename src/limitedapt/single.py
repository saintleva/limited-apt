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

import functools
import apt


def run_once(func):
    """Runs a function (without parameters) (successfully) only once.
    The running can be reset by setting the `has_run` attribute to False
    """
    @functools.wraps(func)
    def wrapper():
        if not wrapper.has_run:
            wrapper.result = func()
            wrapper.has_run = True
        return wrapper.result
    wrapper.has_run = False
    return wrapper


@run_once
def get_cache():
    return apt.Cache()

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

import pycurl
from .errors import TerminationError


class DownloadError(TerminationError):

    def __init__(self, url, filename):
        self.__url = url
        self.__filename = filename

    @property
    def url(self):
        return self.__url

    @property
    def filename(self):
        return self.__filename


def download_file(url, filename):
    try:
        with open(filename, "wb") as fh:
            curl = pycurl.Curl()
            curl.setopt(curl.URL, url)
            curl.setopt(curl.WRITEDATA, fh)
            curl.perform()
            curl.close()
    except:
        raise DownloadError(url, filename)
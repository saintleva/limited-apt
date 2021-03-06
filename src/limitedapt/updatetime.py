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

from datetime import datetime
import os.path
from lxml import etree
from .errors import XmlImportSyntaxError


class UpdateTimesImportSyntaxError(XmlImportSyntaxError): pass


class UpdateTimes:

    def __init__(self):
        self.__distro = None
        self.__enclosure = None
        self.__priorities = None

    @property
    def distro(self):
        return self.__distro

    @distro.setter
    def distro(self, distro):
        self.__distro = distro

    def effective_distro(self):
        try:
            #TODO: Do I need use UTC?
            file_time = datetime.utcfromtimestamp(os.path.getmtime("/var/cache/apt/pkgcache.bin"))
        except:
            file_time = None
        if self.distro is None:
            return file_time
        if file_time is None:
            return self.distro
        return max(self.distro, file_time)

    @property
    def enclosure(self):
        return self.__enclosure

    @enclosure.setter
    def enclosure(self, enclosure):
        self.__enclosure = enclosure

    @property
    def priorities(self):
        return self.__enclosure

    @priorities.setter
    def priorities(self, priorities):
        self.__priorities = priorities

    def export_to_xml(self, file):

        def time_to_str(time):
            return time.isoformat(sep=" ") if time is not None else "never"

        root = etree.Element("updatetime")
        etree.SubElement(root, "distro", time=time_to_str(self.distro))
        etree.SubElement(root, "enclosure", time=time_to_str(self.enclosure))
        etree.SubElement(root, "priorities", time=time_to_str(self.priorities))
        tree = etree.ElementTree(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)

    def import_from_xml(self, file):

        def str_to_time(string):
            return None if string == "never" else datetime.fromisoformat(string)

        try:
            root = etree.parse(file).getroot()
            distro_element = root.find("distro")
            self.distro = str_to_time(distro_element.get("time"))
            enclosure_element = root.find("enclosure")
            self.enclosure = str_to_time(enclosure_element.get("time"))
            priorities_element = root.find("priorities")
            self.priorities = str_to_time(priorities_element.get("time"))
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise UpdateTimesImportSyntaxError("Syntax error has been appeared during importing "
                                               "last time of updating from xml: " + str(err))
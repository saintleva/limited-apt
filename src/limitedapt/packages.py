#
# Copyright (C) Anton Liaukevich 2011-2015 <leva.dev@gmail.com>
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


class ConcretePackage:
    '''Debian package (name) with specific architecture'''

    def __init__(self, name, architecture):
        self.__name = name
        self.__architecture = architecture
        
    @property
    def name(self):
        return self.__name
        
    @property
    def architecture(self):
        return self.__architecture
    
    def __eq__(self, other):
        return self.name == other.name and self.architecture == other.architecture
      
    def __lt__(self, other):
        return (self.architecture < other.architecture
               if self.name == other.name else self.name < other.name)
        
    def __hash__(self):
        return hash(str(self))
    
    def __str__(self):
        return self.name + ":" + self.architecture
    
        
class VersionedPackage(ConcretePackage):
    '''Debian package (name) with specific architecture and version.
    It may be considered "system" or "non-system".
    '''
    
    def __init__(self, name, architecture, version):
        super().__init__(name, architecture)
        self.__version = version
        
    @property
    def version(self):
        return self.__version

    def __str__(self):
        return "{0} : {1} : {2}".format(self.name, self.architecture, self.version)

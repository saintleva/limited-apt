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
'''Package "enclosure" structure description and processing'''

from lxml import etree
from limitedapt.errors import *


class EveryError(Error): pass

class EveryAndDistinctError(EveryError): pass

class VersionsEveryAndDistinctError(EveryAndDistinctError): pass

class ArchAndVersionsEveryAndDistinctError(EveryAndDistinctError): pass

class CannonEnumerateEvery(EveryError): pass

class CannotAddExistingPackage(Error): pass

class EnclosureImportSyntaxError(XmlImportSyntaxError):
    '''Syntax or semantic error while enclosure structure parsing'''


class Versions:
    
    def __init__(self, isevery=False):
        self.__isevery = isevery
        self.__items = set()
        
    @property
    def isevery(self):
        return self.__isevery
    
    def __iter__(self):
        if self.isevery:
            raise CannonEnumerateEvery("Cannot enumerate every possible versions")
        return iter(self.__items)    
        
    def __contains__(self, version):
        return self.isevery or version in self.__items
            
    def add(self, version):
        if self.isevery:
            raise VersionsEveryAndDistinctError("You must not add distinct versions where every added")
        self.__items.add(version)
    
    
class ArchAndVersions:
    
    def __init__(self, isevery=False):
        self.__every = Versions() if isevery else None
        self.__data = {}
        
    @property
    def isevery(self):
        return self.__every is not None
    
    @property
    def every(self):
        return self.__every
    
    @every.setter
    def every(self, value):
        self.__every = value
    
    def __iter__(self):
        if self.isevery:
            raise CannonEnumerateEvery("Cannot enumerate every possible architectures and versions")
        return iter(self.__data.items())    
        
    def has_arch_version(self, arch, version):
        if self.isevery:
            return version in self.every
        else:
            #TODO: Is it right?
            try:
                return version in self.__data[arch]
            except KeyError:
                try:
                    return version in self.__data["all"]
                except KeyError:
                    return False                    
            
    def add(self, versions, arch=None):        
        if self.every:
            assert arch is None
            self.every = versions
        else:
            assert arch is not None
            self.__data[arch] = versions
            
    def add_single(self, version, arch=None):
        if self.every:
            assert arch is None            
            self.every.add(version)
        else:
            assert arch is not None
            try:
                self.__data[arch].add(version)
            except KeyError:
                versions = Versions()
                versions.add(version)
                self.__data[arch] = versions
        
        
class Enclosure:
    
    def __init__(self):
        self.__packages = {}
        
    def __iter__(self):
        return iter(self.__packages)
    
    def __contains__(self, pkg):
        try:
            return self.__packages[pkg.name].has_arch_version(pkg.architecture, pkg.version)
        except KeyError:
            return False
        
    def clear(self):
        self.__packages.clear()
        
    def add_package(self, name, arch_and_versions):
        if name in self.__packages:
            raise CannotAddExistingPackage("Package '{0}' is already in the eclosure".format(name))
        self.__packages[name] = arch_and_versions
        
    def add_versioned_package(self, versioned):
        try:
            self.__packages[versioned.name].add_single(versioned.version, versioned.architecture)
        except KeyError:
            arch_and_versions = ArchAndVersions()
            arch_and_versions.add_single(versioned.version, versioned.architecture)
            self.__packages[versioned.name] = arch_and_versions
        
    def export_to_xml(self, file):
        root = etree.Element("enclosure")
        for pkg, arch_and_versions in sorted(self.__packages.items(), key=lambda x: x[0]):
            package_element = etree.SubElement(root, "package", name=pkg)
            if arch_and_versions.isevery:
                everyarch_element = etree.SubElement(package_element, "everyarch")
                if arch_and_versions.every.isevery:
                    etree.SubElement(everyarch_element, "everyversion")
                else:
                    for version in sorted(arch_and_versions.every):
                        etree.SubElement(everyarch_element, "version", number=version)
            else:
                for arch, versions in sorted(arch_and_versions, key=lambda x: x[0]):
                    arch_element = etree.SubElement(package_element, "arch", name=arch)
                    if versions.isevery:
                        etree.SubElement(arch_element, "everyversion")
                    else:
                        for version in sorted(versions):
                            etree.SubElement(arch_element, "version", number=version)
        tree = etree.ElementTree(root)
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)          
    
    def import_from_xml(self, file):
        try:
            root = etree.parse(file).getroot()
            self.clear()
            for package_element in root.findall("package"):
                everyarch_element = package_element.find("everyarch")
                if everyarch_element is not None:
                    arch_and_versions = ArchAndVersions(isevery=True)
                    everyversion_element = everyarch_element.find("everyversion")
                    if everyversion_element is not None:
                        arch_and_versions.every = Versions(isevery=True )
                    else:
                        versions = Versions()
                        for version_element in everyarch_element.findall("version"):
                            versions.add(version_element.get("number"))
                        arch_and_versions.add(versions)
                else:
                    arch_and_versions = ArchAndVersions()
                    for arch_element in package_element.findall("arch"):
                        everyversion_element = arch_element.find("everyversion")
                        if everyversion_element is not None:
                            arch_and_versions.add(Versions(isevery=True), arch_element.get("name"))
                        else:
                            versions = Versions()
                            for version_element in arch_element.findall("version"):
                                versions.add(version_element.get("number"))
                            arch_and_versions.add(versions, arch_element.get("name"))
                self.add_package(package_element.get("name"), arch_and_versions)
        except (ValueError, LookupError, etree.XMLSyntaxError) as err:
            raise EnclosureImportSyntaxError('''Syntax error has been appeared during importing 
                                             enclosure structure from xml: ''' + str(err))

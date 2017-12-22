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
'''Coownership structure processing'''

from lxml import etree
from limitedapt.packages import ConcretePackage
from limitedapt.errors import *


class CoownershipError(Error): pass

class PackageIsNotInstalled(CoownershipError): pass

class UserDoesNotOwnPackage(CoownershipError): pass

class UserAlreadyOwnsThisPackage(CoownershipError): pass

class CoownershipImportSyntaxError(XmlImportSyntaxError):
    '''Syntax or semantic error while coownership structure parsing'''


class CoownershipList:

    def __init__(self):
        self.__data = {}
        
    def __iter__(self):
        return iter(self.__data)
        
    def owners_of(self, pkg):
        return self.__data.get(pkg, set())
    
    def his_packages(self, user):
        return (pkg for pkg, owners in self.__data.items() if user in owners)
    
    def is_own(self, pkg, user):
        return user in self.__data[pkg] if pkg in self.__data else False
    
    def add_ownership(self, pkg, user, also_root=False):
        #TODO: Is it logics good? 
        if pkg in self.__data:
            if user in self.__data[pkg]:
                raise UserAlreadyOwnsThisPackage("User '{0} has already own package '{1}".format(user, pkg))
            else:
                self.__data[pkg].add(user)
        else:
            self.__data[pkg] = { user }
        if also_root and user != "root":
            self.__data[pkg].add("root")
            
    def remove_ownership(self, pkg, user):
        try:
            users = self.__data[pkg]
            try:
                users.remove(user)
                if len(users) == 0:
                    del self.__data[pkg]                
            except KeyError:
                raise UserDoesNotOwnPackage("User '{0}' doesn't own package '{1}'".format(user, pkg))                
        except KeyError:
            raise PackageIsNotInstalled("Package '{0}' is not installed".format(pkg))
        
    def remove_package(self, pkg):
        try:
            del self.__data[pkg]                
        except KeyError:
            raise PackageIsNotInstalled("Package '{0}' is not installed".format(pkg))        
        
    def clear(self):
        self.__data.clear()
        
    def export_to_xml(self, file):
        #TODO: remove it
        print("EXPORT:")
        for pkg, owners in sorted(self.__data.items(), key=lambda x: x[0]):
            print(pkg)
            for user in sorted(owners):
                print("  " + user)
        print()
        
        root = etree.Element("packages")
        for pkg, owners in sorted(self.__data.items(), key=lambda x: x[0]):
            package_element = etree.SubElement(root, "package", name=pkg.name, arch=pkg.architecture)
            for user in sorted(owners):
                etree.SubElement(package_element, "user", name=user)
        tree = etree.ElementTree(root)        
        tree.write(file, pretty_print=True, encoding="UTF-8", xml_declaration=True)
        
    def import_from_xml(self, file):
        try:
            root = etree.parse(file).getroot()
            self.clear()
            for package_element in root.findall("package"):
                try:                    
                    pkg = ConcretePackage(package_element.get("name"), package_element.get("arch"))
                    owners = set()
                    for user_element in package_element.findall("user"):
                        owners.add(user_element.get("name"))                        
                    self.__data[pkg] = owners
                except (ValueError, LookupError) as err:
                    raise CoownershipImportSyntaxError("Syntax error has been appeared during importing "
                                                       "coownership table from xml: " + str(err))
        except etree.XMLSyntaxError as err:
            raise CoownershipImportSyntaxError('''Syntax error has been appeared during importing
                                               coownership table from xml: ''' + str(err))

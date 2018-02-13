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
'''Base exceptions for limited-apt library'''


class Error(Exception):
    '''Base exception for limited-apt library'''
    
class StubError(Error):
    '''Used for code stubs'''
    
class XmlImportSyntaxError(Error):
    '''Syntax or semantic error while limited-apt structures xml parsing'''

class TerminationError(Error):
    '''Exit from runner (e. g. sys.exit() for console interface)'''

class GoodExit(TerminationError): pass

class GroupError(TerminationError):
    
    def __init__(self, group_name):
        self.__group_name = group_name
        
    @property
    def group_name(self):
        return self.__group_name
    
class YouHaveNotPrivilegesError: pass

class YouHaveNotUserPrivilegesError(YouHaveNotPrivilegesError, GroupError): pass

class YouMayNotUpdateError(YouHaveNotUserPrivilegesError): pass

class YouMayNotUpgradeError(YouHaveNotUserPrivilegesError): pass

class YouMayNotPerformError(YouHaveNotUserPrivilegesError): pass

class YouMayNotPurgeError(YouHaveNotPrivilegesError): pass

class GroupNotExistError(GroupError): pass

class ConfigFilesIOError(TerminationError):
    
    def __init__(self, filename, error_number):
        self.__filename = filename
        self.__error_number = error_number
        
    @property
    def filename(self):
        return self.__filename
                
    @property
    def error_number(self):
        return self.__error_number
    
class ReadingConfigFilesError(ConfigFilesIOError): pass

class WritingConfigFilesError(ConfigFilesIOError): pass

class AttempToPerformSystemComposingError(TerminationError): pass

class AptProcessingError(TerminationError): pass

class LockFailedError(AptProcessingError): pass
    
class FetchCancelledError(AptProcessingError): pass

class FetchFailedError(AptProcessingError): pass 

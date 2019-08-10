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


#TODO: May be I need to use "BaseException"
class Error(Exception):
    '''Base exception for limited-apt library'''
    
class StubError(Error):
    '''Used for code stubs'''
    
class XmlImportSyntaxError(Error):
    '''Syntax or semantic error while limited-apt structures xml parsing'''

class TerminationError(Error):
    '''Exit from runner (e. g. sys.exit() for command line interface)'''

class GoodExit(TerminationError): pass

class GroupProblem:
    
    def __init__(self, group_name):
        self.__group_name = group_name
        
    @property
    def group_name(self):
        return self.__group_name
    
class YouHaveNotPrivilegesError(Error): pass

class YouHaveNotUserPrivilegesError(YouHaveNotPrivilegesError, GroupProblem):
    
    def __init__(self, group_name):
        GroupProblem.__init__(group_name)

class YouMayNotUpdateError(YouHaveNotUserPrivilegesError):
    
    def __init__(self, group_name):
        super().__init__(group_name)

class YouMayNotUpgradeError(YouHaveNotUserPrivilegesError):
    
    def __init__(self, group_name, full_upgrade):
        super().__init__(group_name)
        self.__full_upgrade = full_upgrade
        
    @property
    def full_upgrade(self):
        return self.__full_upgrade

class YouMayNotPerformError(YouHaveNotUserPrivilegesError):
    
    def __init__(self, group_name):
        super().__init__(group_name)

class OnlyRootMayForceError(YouHaveNotPrivilegesError): pass

class YouMayNotPurgeError(YouHaveNotPrivilegesError): pass

class GroupNotExistError(TerminationError, GroupProblem):

    def __init__(self, group_name):
        GroupProblem.__init__(group_name)

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
    
class ReadingConfigFilesError(ConfigFilesIOError):
    
    def __init__(self, filename, error_number):
        super().__init__(filename, error_number)

class WritingConfigFilesError(ConfigFilesIOError):

    def __init__(self, filename, error_number):
        super().__init__(filename, error_number)

class AttempToPerformSystemComposingError(TerminationError): pass

class WantToDoSystemComposingError(AttempToPerformSystemComposingError): pass

class SystemComposingByResolverError(AttempToPerformSystemComposingError): pass

class DpkgJournalDirtyError(TerminationError): pass

class AptProcessingError(TerminationError): pass

class LockFailedError(AptProcessingError): pass

class FetchCancelledError(AptProcessingError): pass

class FetchFailedError(AptProcessingError): pass

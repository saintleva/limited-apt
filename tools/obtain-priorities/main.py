#!/usr/bin/env python3
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

import argparse
from pathlib import Path
import time
import os
import subprocess
import shutil
import apt
import apt_pkg
import limitedapt.errors
from limitedapt.packages import *
from limitedapt.single import get_cache
from limitedapt.debconf import *
from parsing import *


PROGRAM_NAME = 'obtain-priorities'


class UnpackingError(limitedapt.errors.Error):

    def __int__(self, package):
        self.__package = package

    @property
    def package(self):
        return self.__package


def process(tempdir, priorities_filename, script_types_filename, repeat_mode, autoremove_mode, verbose_mode, debug_mode):

    def get_control_dir(deb_filename):
        filename = Path(deb_filename)
        filename_without_ext = filename.with_suffix("")
        return str(filename_without_ext) + "_control"

    priorities = DebconfPriorities()
    if os.path.exists(priorities_filename):
        shutil.copyfile(priorities_filename, priorities_filename + ".backup")
        priorities.import_from_xml(priorities_filename)
    cache = get_cache()

    def need_to_process(pkg):
        return repeat_mode or not priorities.well_processed(ConcretePackage(pkg.shortname, pkg.candidate.architecture))

    need_to_download_space = sum(pkg.candidate.size for pkg in cache if pkg.candidate is not None and need_to_process(pkg))

    print('Need to download: {0} bytes'.format(need_to_download_space))

    try:
        if os.path.exists(script_types_filename):
            shutil.copyfile(script_types_filename, script_types_filename + ".backup")
        script_types_fh = open(script_types_filename, "w" if repeat_mode else "a")
        downloaded_space = 0
        for pkg in cache:
            if pkg.candidate is not None and need_to_process(pkg):
                try:
                    deb_filename = pkg.candidate.fetch_binary(destdir=tempdir, progress=apt.progress.text.AcquireProgress())
                    control_dir = get_control_dir(deb_filename)
                    if not os.path.exists(control_dir):
                        os.makedirs(control_dir)
                        if subprocess.call(["/usr/bin/dpkg-deb", "--control", deb_filename, control_dir]) != 0:
                            raise UnpackingError()
                    concrete_package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
                    state = process_package(concrete_package, control_dir, script_types_fh)
                    priorities[concrete_package] = state
                    if autoremove_mode:
                        os.remove(deb_filename)
                        if state.status == Status.NO_CONFIG_FILE:
                            shutil.rmtree(control_dir)
                    downloaded_space += pkg.candidate.size
                    if debug_mode:
                        print('{0} bytes has been downloaded yet'.format(downloaded_space))
                except apt.package.FetchError:
                    pass
    except apt.package.FetchError as err:
        print('''Error: cannot fetch: ''', err)
    except UnpackingError as err:
        print('''Error: cannot unpack "{0}" package'''.format(str(err.package)))
    except KeyboardInterrupt:
        print('Execution interrupted by Ctrl+C')
    except apt_pkg.Error:
        pass
    finally:
        script_types_fh.close()
        if verbose_mode:
            print('{0} bytes has been downloaded yet'.format(downloaded_space))
        priorities.export_to_xml(priorities_filename)


def main():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description='''%(prog)s generates debconf priority list for all packages '''
                                     '''that available on the system.''')
    parser.add_argument('tempdir', type=str, help='Temporary directory for downloaded packages and their "controls"')
    parser.add_argument('priorities_filename', type=str, help='Filename for resulting priority list')
    parser.add_argument('script_types', type=str, help='Filename with list of script types of processed configs')
    parser.add_argument('-r', '--repeat', action='store_true',
                        help='Repeat processing for packages have been processed yet')
    parser.add_argument('-a', '--autoremove', action='store_true', help='Remove processed packages')
    parser.add_argument('-v', '--verbose', action='store_true', help='Display extra information')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debugging mode. Print detailed information on every action')

    args = parser.parse_args()
    process(args.tempdir, args.priorities_filename, args.script_types,
            args.repeat, args.autoremove, args.verbose, args.debug)


if __name__ == "__main__":
    main()
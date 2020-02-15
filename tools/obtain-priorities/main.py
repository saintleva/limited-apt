#!/usr/bin/env python3
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

import argparse
from pathlib import Path
import time
import os
import subprocess
import shutil
import apt
import limitedapt.errors
from limitedapt.packages import *
from limitedapt.single import get_cache
from limitedapt.debconf import *


PROGRAM_NAME = 'obtain-priorities'


class DpkgDebError(limitedapt.errors.Error): pass


def process(tempdir, priorities_filename, script_types_filename, autoremove_mode, verbose_mode, debug_mode):

    def get_control_dir(deb_filename):
        filename = Path(deb_filename)
        filename_without_ext = filename.with_suffix("")
        return str(filename_without_ext) + "_control"

    backup_filename = priorities_filename + ".backup"
    shutil.copyfile(priorities_filename, backup_filename)

    priorities = DebconfPriorities()
    priorities.import_from_xml(priorities_filename)
    cache = get_cache()
    download_space = sum(pkg.candidate.size for pkg in cache if pkg.candidate is not None and
                         not priorities.well_processed(ConcretePackage(pkg.shortname, pkg.candidate.architecture)))
    print("Need to download: {0} bytes".format(download_space))

    try:
        for pkg in cache:
            deb_filename = pkg.candidate.fetch_binary(progress=apt.progress.text.AcquireProgress())
            control_dir = get_control_dir(deb_filename)
            if not os.path.exists(control_dir):
                os.makedirs(control_dir)
                if subprocess.call(["/usr/bin/dpkg-deb", "--control", deb_filename, control_dir]) != 0:
                    raise DpkgDebError()

            if autoremove_mode:
                os.remove(deb_filename)
                shutil.rmtree(control_dir)
    except KeyboardInterrupt, DpkgDebError:
        print("Execution interrupted by Ctrl+C")
    finally:
        priorities.export_to_xml(priorities_filename)

def main():
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME,
                                     description='''%(prog)s generates debconf priority list for all packages '''
                                     '''that available on the system.''')
    parser.add_argument('tempdir', type=str, help='Temporary directory for downloaded packages and their "controls"')
    parser.add_argument('priorities_filename', type=str, help='Filename for resulting priority list')
    parser.add_argument('-r', '--autoremove', action='store_true', help='Remove processed packages')
    parser.add_argument('-v', '--verbose', action='store_true', help='Display extra information')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Debugging mode. Print detailed information on every action')
    parser.add_argument('-s', '--script-types', type=str, default=None,
                        help='Filename with list of script types of processed configs')

    args = parser.parse_args()
    process(args.tempdir, args.priorities_filename, args.script_types, args.autoremove, args.verbose, args.debug)

#TODO: remove it
#    print("tempdir: ", args.tempdir)
#    print("priorities_filename", args.priorities_filename)
#    print("--verbose: ", args.verbose)
#    print("--debug: ", args.debug)
#    print("--script-types: ", args.script_types)



def main2():
    cache = get_cache()
    download_space = sum(pkg.candidate.size for pkg in cache if pkg.candidate is not None)
    print("Need to download: {0} bytes".format(download_space))

    pkg = cache["man-db"]

    before = time.time()
    deb_filename = pkg.candidate.fetch_binary(progress=apt.progress.text.AcquireProgress())
    print(control_dir)
    if not os.path.exists(control_dir):
        os.makedirs(control_dir)
        exitcode = subprocess.call(["/usr/bin/dpkg-deb", "--control", deb_filename, control_dir])
        print(exitcode)
    control_dir = get_control_dir(deb_filename)
    after = time.time()
    print(after - before, " SECONDS ELAPSED")

    


#    deb_package = apt.debfile.DebPackage()
#    result = deb_package.open(filename)
#    print(result)


if __name__ == "__main__":
    main()
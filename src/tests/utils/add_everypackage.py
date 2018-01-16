#!/usr/bin/env python3

# Copyright (c) Anton Liaukevich 2011-2017 <leva.dev@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import sys
import apt
from limitedapt.enclosure import *


def _add_everypackage(enclosure, name):
    cache = apt.Cache()
    pkg = cache[name]
    print("PACKAGE ARCHITECTURE: {0}".format(pkg.architecture()))
    if pkg.architecture() == "all":
        arch_and_versions = ArchAndVersions()
        arch_and_versions.add(Versions(isevery=True), "all")
    else:    
        arch_and_versions = ArchAndVersions(isevery=True)
        arch_and_versions.every = Versions(isevery=True)
    enclosure.add_package(name, arch_and_versions)


def main():
    filename = sys.argv[1]
    try:
        enclosure = Enclosure()
        print('''loading non-system package set (enclosure) from file "{0}" ...'''.format(filename))
        enclosure.import_from_xml(filename)
        _add_everypackage(enclosure, sys.argv[2])
        print('''saving non-system package set (enclosure) to file "{0}" ...'''.format(filename))
        enclosure.export_to_xml(filename)
    except IOError as err:
        print(err, file=sys.stderr)
        sys.exit(1)
    except EnclosureImportSyntaxError as err:
        print(err, file=sys.stderr)
        sys.exit(2)
    except CannotAddExistingPackage as err:
        print(err, file=sys.stderr)
        sys.exit(3)
    except EveryError as err:
        print(err, file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
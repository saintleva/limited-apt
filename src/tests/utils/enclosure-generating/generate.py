#!/usr/bin/env python3

# Copyright (c) Anton Liaukevich 2011-2020 <leva.dev@gmail.com>
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

import itertools
import subprocess
import apt
from limitedapt.enclosure import *


def main():
    query = 'role::documentation || role::app-data || role::data || role::debug-symbols || ' + \
            '(role::source && ! use::driver) || role::metapackage || role::examples || ' + \
            'role::program && ( ! (security::antivirus || security::firewall) ) || ' + \
            '! ( (admin::configuring && admin::filesystem && admin::logging) || ' + \
            '(admin::logging && interface::daemon) || ' + \
            '(admin::kernel && interface::daemon) || admin::TODO)'

    found = subprocess.getoutput('debtags search "{0}"'.format(query))   
    lines = found.splitlines()
    seriated_names = [line.partition(" ")[0] for line in lines]
    names = list(key for key, _ in itertools.groupby(seriated_names))
    
    print(len(names))
    
    enclosure = Enclosure()
    enclosure.import_from_xml("abc")
    cache = apt.Cache()
    for name in names:
        pkg = cache[name]
        enclosure.add_versioned_package(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version)

    enclosure.export_to_xml("abcd")
    
if __name__ == '__main__':
    main()
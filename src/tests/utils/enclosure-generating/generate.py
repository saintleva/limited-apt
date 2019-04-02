#!/usr/bin/env python3

import itertools
import subprocess
import apt
from limitedapt.enclosure import *


# def enumerate_versions(package):
#     found = subprocess.getoutput('apt-show-versions --allversions --package="{0}"'.format(package))   
#     lines = found.splitlines()
#     for line in lines:
#         if line.startswith(package):
#             words = line.split()
#             if len(words) == 4:
#                 yield words[1]

def add_package(cache, enclosure, name, arch, version):
    cache = apt.Cache()
#    print("PACKAGE ARCHITECTURE: {0}".format(pkg.architecture()))
 
    versions = Versions()
    versions.add(version)   
    arch_and_versions = ArchAndVersions()
    arch_and_versions.add(versions, arch)
    enclosure.add_package(name, arch_and_versions)

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
    
    enclosure = Enclosure()
    cache = apt.Cache()
    for name in names:
        pkg = cache[name]
        enclosure.add_versioned_package(pkg.shortname, pkg.candidate.architecture(), pkg.candidate.version)
        
    import sys
    enclosure.export_to_xml(sys.stdout)


if __name__ == '__main__':
    main()
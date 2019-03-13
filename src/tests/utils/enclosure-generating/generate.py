#!/usr/bin/env python3

import subprocess
import apt 


def add_package(enclosure, name):
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
    query = 'role::documentation || role::app-data || role::data || role::debug-symbols || ' + \
            '(role::source && ! use::driver) || role::metapackage || role::examples || ' + \
            'role::program && ( ! (security::antivirus || security::firewall) ) || ' + \
            '! ( (admin::configuring && admin::filesystem && admin::logging) || ' + \
            '(admin::logging && interface::daemon) || ' + \
            '(admin::kernel && interface::daemon) || admin::TODO)'

    found = subprocess.getoutput('debtags search "{0}"'.format(query))   
    lines = found.splitlines()

    cache = apt.Cache()
    for line in sorted(lines):
        name = line.partition(" ")[0]
        pkg = cache[name]
        print('{0} & {1} & {2}'.format(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version))
            
   


if __name__ == '__main__':
    main()
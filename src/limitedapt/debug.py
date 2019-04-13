import itertools
import os
import time
import subprocess
import apt

from limitedapt.packages import VersionedPackage
from limitedapt.enclosure import *


def debug_suidbit(place):
    print(place, ":")
    print('UID = {0}, EUID = {1}'.format(os.getuid(), os.geteuid()))
    print()

    time_path = os.path.join('/sbin/test', str(time.time()))
    os.makedirs(time_path)
    print()

def update_enclosure_by_debtags(filename):
    enclosure = Enclosure()
    
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
    enclosure.import_from_xml(filename)
    cache = apt.Cache()
    for name in names:
        pkg = cache[name]
        enclosure.add_versioned_package(VersionedPackage(pkg.shortname, pkg.candidate.architecture, pkg.candidate.version))

    enclosure.export_to_xml(filename)

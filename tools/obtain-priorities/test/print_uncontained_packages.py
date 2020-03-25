#!/usr/bin/env python3


import time
from limitedapt.packages import *
from limitedapt.single import get_cache
from limitedapt.debconf import *


def main():
    cache = get_cache()
    start_time = time.time()
    priorities = DebconfPrioritiesDB("sqlite:////home/anthony/projects/limited-apt/tools/obtain-priorities/test/priorities1-db.sqlite")
    finish_time = time.time()
    print("Import time in sec: ", finish_time - start_time)
    for pkg in cache:
        if pkg.candidate is not None:
            package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
            if package not in priorities:
                print(package)


if __name__ == "__main__":
    main()
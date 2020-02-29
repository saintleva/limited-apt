#!/usr/bin/env python3


from limitedapt.packages import *
from limitedapt.single import get_cache
from limitedapt.debconf import *


def main():
    cache = get_cache()
    priorities = DebconfPriorities()
    priorities.import_from_xml("/home/anthony/projects/limited-apt/tools/obtain-priorities/test/priorities1")
    for pkg in cache:
        if pkg.candidate is not None:
            package = ConcretePackage(pkg.shortname, pkg.candidate.architecture)
            if package not in priorities:
                print(package)


if __name__ == "__main__":
    main()
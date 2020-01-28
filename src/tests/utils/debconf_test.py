from limitedapt.debconf import *


priorities = DebconfPriorities()
priorities.import_from_xml("/home/anthony/projects/limited-apt/src/unittests/data/debconf-priorities1")
priorities.print_table()
priorities.export_to_xml("/home/anthony/projects/limited-apt/src/unittests/data/debconf-priorities1_copy1")

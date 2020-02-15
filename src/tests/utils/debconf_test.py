from limitedapt.packages import *
from limitedapt.debconf import *


priorities = DebconfPriorities()
priorities.import_from_xml("/home/anthony/projects/limited-apt/src/unittests/data/debconf-priorities1")
#priorities.print_table()
#priorities.export_to_xml("/home/anthony/projects/limited-apt/src/unittests/data/debconf-priorities1_copy1")
priorities.get_state(ConcretePackage("3dchess", "i386"))
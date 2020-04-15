#!/usr/bin/env python3
#
# Copyright (C) Anton Liaukevich 2011-2020 <leva.dev@gmail.com>
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

import sys
import os
import cryptadd
import subprocess
from limitedapt.constants import *


def add_user(name):
    subprocess.call(["useradd", "--password={0}".format(crypt.crypt(name)),
                     "--base-dir=/home/test",  "--shell=/bin/bash", "--create-home", name])

def add_group(name):
    subprocess.call(["addgroup", name])

def add_user_to_group(user, group):
    subprocess.call(["adduser", user, group])
    
twelve_apostles = ["peter", "andrew", "james", "john", "philip", "bartholomew",
                   "matthew", "james-alphaeus", "thomas", "simon", "thaddeus", "judas"]
all_users = twelve_apostles + ["matthias", "paul", "moses"]

def main():
    try:
        os.makedirs("/home/test")
    except:
        print("Warning: directory '/home/test' already exists", file=sys.stderr)
    for user in all_users:
        add_user(user)    
    for group in (UNIX_LIMITEDAPT_GROUPNAME, UNIX_LIMITEDAPT_ROOTS_GROUPNAME, UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME):
        add_group(group)
    for user in twelve_apostles + ["moses"]:
        for group in ("sudo", UNIX_LIMITEDAPT_GROUPNAME):
            add_user_to_group(user, group)
    add_user_to_group("matthias", "sudo")
    add_user_to_group("moses", UNIX_LIMITEDAPT_ROOTS_GROUPNAME)
    for user in ("peter", "john", "james"):
        add_user_to_group(user, UNIX_LIMITEDAPT_UPGRADERS_GROUPNAME)


if __name__ == '__main__':
    main()
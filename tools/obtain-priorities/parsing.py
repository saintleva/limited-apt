#!/usr/bin/env python3
#
# Copyright (C) Anton Liaukevich 2011-2019 <leva.dev@gmail.com>
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

import os
import chardet
from limitedapt.debconf import *


def parse_shell(handle):
    has_questions = False
    maximal_priority = Priority.LOW
    for line in handle:
        string = line.lstrip()
        if string.startswith("db_input"):
            try:
                current_priority = Priority.from_string(string.split()[1])
                if current_priority > maximal_priority:
                    maximal_priority = current_priority
                has_questions = True
            except PriorityConvertingFromStringError:
                return PackageState(Status.PROCESSING_ERROR)
    return PackageState(Status.HAS_QUESTIONS, maximal_priority) if has_questions else PackageState(Status.HAS_NOT_QUESTIONS)


shell_parser_map = {
    "/bin/sh" : parse_shell,
    "/bin/bash": parse_shell
}


def process_package(package, control_dir, script_types_fh):
    path_to_config_file = os.path.join(control_dir, "config")
    if os.path.exists(path_to_config_file):
        rawdata = open(path_to_config_file, "rb").read()
        encoding = chardet.detect(rawdata)["encoding"]
        handle = open(path_to_config_file, "r", encoding=encoding)
        shebang_string = handle.readline()
        if shebang_string[0:2] != "#!":
            return PackageState(Status.PROCESSING_ERROR)
        parametrized_shell = shebang_string[2:].strip()
        shell = parametrized_shell.split()[0]
        print(str(package), encoding, shell, file=script_types_fh, flush=True)
        if shell in shell_parser_map:
            return shell_parser_map[shell](handle)
        else:
            return PackageState(Status.PROCESSING_ERROR)
    else:
        return PackageState(Status.NO_CONFIG_FILE)

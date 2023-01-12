#
# This file is part of LiteDRAM.
#
# Copyright (c) 2023 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import inspect


class EngTest():
    def __init__(self, level=logging.DEBUG):
        # Setup
        dir_name = "./test_eng"
        if not os.path.exists(dir_name):
            # Test eng dir does not exist
            os.mkdir(dir_name)
        # file_name = "input_buffer"
        full_file_name = inspect.stack()[-1].filename
        file_name = (full_file_name.split('/')[-1]).split('.')[0]
        log_file_name = dir_name + '/' + file_name+".log"
        wave_file_name = dir_name + '/' + file_name+".vcd"
        log_level = level
        # log_level = logging.INFO
        log_handlers = [logging.FileHandler(
            log_file_name), logging.StreamHandler()]
        log_format = "[%(module)s.%(funcName)s] %(message)s"
        logging.basicConfig(format=log_format,
                            handlers=log_handlers, level=log_level)

        self.dir_name = dir_name
        self.file_name = file_name
        self.full_file_name = full_file_name
        self.log_file_name = log_file_name
        self.wave_file_name = wave_file_name
        self.log_handlers = log_handlers

    def __str__(self):
        description = "\n--Summary--\n"
        description += "Called:\t" + self.file_name + "\n"
        description += "Log:\t" + self.log_file_name + "\n"
        description += "Wave:\t" + self.wave_file_name + "\n"
        return description

if __name__ == "__main__":
    raise NotImplementedError("Test of this block is not provided.")

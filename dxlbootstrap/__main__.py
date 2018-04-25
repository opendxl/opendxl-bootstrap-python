# -*- coding: utf-8 -*-
################################################################################
# Copyright (c) 2018 McAfee LLC - All Rights Reserved.
################################################################################

from __future__ import absolute_import
from __future__ import print_function
import logging
import sys

from .generate.app import DxlBootstrap

# pylint: disable=invalid-name

# Validate command line
arg_count = len(sys.argv)
if arg_count < 3:
    print("Usage: dxlbootstrap <template-name> <config-file> [output-directory]\n\n")
    print("Supported templates:")
    for name in sorted(DxlBootstrap.templates()):
        print("    {0}".format(name))
    sys.exit(1)

#
# Configure Logging
#

# Default log configuration (no configuration file)
log_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)

# Determine destination folder
dest_folder = ""
if arg_count >= 4:
    dest_folder = sys.argv[3]

# Run the application
DxlBootstrap().run(sys.argv[1], sys.argv[2], dest_folder)

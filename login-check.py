#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import gzip
import re
from datetime import datetime
import pdb

########################################################################################################################
########################################################################################################################

user_login_string  = re.compile('\[[\d:]+\]\s\[[\w\s\/]+\]:\s([\w]+) joined the game')
login_found = False

# check all provided file names
for filename in sys.argv[1:]:
    if os.path.isfile(filename):
        if filename.endswith('.gz'):
            fp = gzip.open(filename, 'rt')
        else:
            fp = open(filename, 'rt')

        for log_line in fp:
            if user_login_string.search(log_line) != None:
                login_found = True
                break
        fp.close()

print(int(login_found))

# -*- coding: utf-8 -*-
from os import path, sys
import os
configPath = os.sep.join([path.dirname(path.abspath(__file__)), "conf.ini"])
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
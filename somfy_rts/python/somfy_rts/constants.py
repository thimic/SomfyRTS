#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import inspect
# import os

from enum import Enum

# THIS_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
# CONFIG_PATH = os.path.join(THIS_DIR, 'options.json')
CONFIG_PATH = '/data/options.json'

# MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(THIS_DIR)), 'model.json')
MODEL_PATH = '/data/model.json'


class Buttons(Enum):
    Up = 0x2
    Stop = 0x1
    Down = 0x4
    Program = 0x8

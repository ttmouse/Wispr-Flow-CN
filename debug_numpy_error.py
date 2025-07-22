#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试NumPy数组比较错误
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
from audio_capture import AudioCapture
from funasr_engine import FunASREngine
import time
import traceback
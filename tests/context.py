"""
This module helps us test without having to install the package"""

import os
import sys

addpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(f"Adding {addpath} to path")
sys.path.insert(0, addpath)

import jsonschemacodegen

unused = 1
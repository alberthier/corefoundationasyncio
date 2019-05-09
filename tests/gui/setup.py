"""
Usage:
    export PYTHONPATH=../..
    python setup.py py2app -A
    ./dist/guidemo.app/Contents/MacOS/guidemo
"""

from setuptools import setup
import sys

APP = ['guidemo.py']
DATA_FILES = ['guidemo.xib']
OPTIONS = {
    'argv_emulation': True,
    'use_pythonpath': True,
}
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

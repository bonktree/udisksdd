#!/usr/bin/python3
import logging
import os
import sys
from . import udd

def main():
    if os.getenv('UDD_DEBUG'):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(stream=sys.stderr, level=loglevel)
    return udd.udd()

if __name__ == '__main__':
    exit(main())

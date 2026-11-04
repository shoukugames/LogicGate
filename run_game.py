#!/usr/bin/env python3
"""Start LogicGate.  Options: --windowed, --version, --smoke-test <file>"""
import sys

from logicgate.app import main

if __name__ == "__main__":
    sys.exit(main())

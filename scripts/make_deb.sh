#!/bin/bash
set -euo pipefail

# Build a Debian-family binary package using the active Python 3 interpreter.
#
# Execute the following commands to setup your environment:
#
# sudo apt install python3-pip python3-all debhelper dh-python devscripts python3-stdeb
#
cd "$(dirname "$0")/.."

export DEB_BUILD_OPTIONS=nocheck
python3 setup.py --command-packages=stdeb.command bdist_deb

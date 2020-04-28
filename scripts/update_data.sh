#!/bin/bash
#
# usage: update_data.sh [kernel]
#
# Valid kernels can be identified with `jupyter kernelspec list`

# Get the base directory of the argument.
# Can resolve single symlinks if readlink is installed
function scriptdir {
    cd "$(dirname "$1")"
    cd "$(dirname "$(readlink "$1" 2>/dev/null || basename "$1" )")"
    pwd
}
DIR="$(scriptdir "$0" )"
cd $DIR

# Execute the notebook in the current directory
jupytext -k "${1:-"-"}" --execute update_data.py

#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pip3 freeze > $SCRIPT_DIR/../requirements.txt
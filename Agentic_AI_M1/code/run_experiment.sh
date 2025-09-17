#!/bin/bash
export LOG_ALL_EVENTS="1"
export DEBUG="1"
export LOG_TO_FILE="1"
export no_proxy="127.0.0.1,127.0.0.0/8,localhost"

python start.py

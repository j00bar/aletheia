#!/bin/bash

set -exv

python3 -m venv .
source bin/activate
bin/pip3 install --upgrade pip poetry
bin/poetry install
bin/pre-commit run -a

#! /bin/bash

uv_restore() {
    echo "Create and activate venv in ${PWD}"
    uv venv .venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
}
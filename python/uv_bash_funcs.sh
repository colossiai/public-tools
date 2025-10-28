#! /bin/bash

uv_init() {
    echo "Create and activate venv in ${PWD}"
    uv venv .venv
    source .venv/bin/activate
}

uv_restore() {
    echo "Install from requirements.txt"
    uv pip install -r requirements.txt
}

uv_freeze() {
    echo "freeze > requirements.txt"
    uv pip freeze > requirements.txt
}
#!/bin/bash
set -xe
cd "$(dirname $0)"
uv run flask run --port 8083 "$@"

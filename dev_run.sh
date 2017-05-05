#!/bin/bash

# This scripts expects to be run from the lxl_api_tests directory, which is to be cloned
# alongside the librisxl directory (repo).

# Exit on failure
set -e

# Run CRUD tests
export LXLTESTING_AUTH_URL="https://libris-dev.kb.se/login/authorize"
export LXLTESTING_LXL_LOGIN_URL="https://libris-dev.kb.se/login"
export LXLTESTING_ROOT_URL="https://libris-dev.kb.se"
export LXLTESTING_LOGIN_URL="https://bibdb-stg.libris.kb.se/login"
export LXLTESTING_USERNAME="test"
export LXLTESTING_PASSWORD="test"
pytest -s

# Run OAIPMH tests
pushd ../librisxl/oaipmh/
gradle test --refresh-dependencies
popd

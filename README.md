# lxl_api_tests

This is a collection of integration tests for the LibrisXL API.

## Dependencies

`libssl-dev`

## Configuration

We use environment variables to configure which system to authenticate against
(`LXLTESTING_LOGIN_URL`), what credentials to use (`LXLTESTING_USERNAME` and
`LXLTESTING_PASSWORD`), and which system to run the tests against
(`LXLTESTING_AUTH_URL`, `LXLTESTING_LXL_LOGIN_URL`, and `LXLTESTING_ROOT_URL`).
The last three default to localhost, while the first three need to be set
before executing the tests.

To be able to run without https against e.g. localhost, set:
`export OAUTHLIB_INSECURE_TRANSPORT=1`

Use `LXLTESTING_LOGIN_URL=https://login.libris.kb.se` for login.libris.kb.se

## Running

```bash
# Install dependencies
$ virtualenv .venv && source .venv/bin/activate && pip install -r requirements.txt
# Run the tests
$ LXLTESTING_LOGIN_URL=https://some.host/login LXLTESTING_USERNAME=username \
      LXLTESTING_PASSWORD=password pytest
```


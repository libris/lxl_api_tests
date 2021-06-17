# lxl_api_tests

This is a collection of integration tests for the LibrisXL API.

## Dependencies

`libssl-dev`

## Configuration

We use environment variables to configure which system to run the tests against as well as which system to use for 
authorization. The following variables need to be set before executing the tests:

- `LXLTESTING_LOGIN_URL` - URL to the oauth server e.g. `https://login.libris.kb.se` or a local xl_auth instance.
- `LXLTESTING_USERNAME` and `LXLTESTING_PASSWORD` - user credentials for the oauth server.
- `LXLTESTING_OAUTH_CLIENT_ID` - client ID for an oauth client that is configured to redirect to the system under test.
- `LXLTESTING_ROOT_URL` - the lxlviewer flask layer URL, defaults to `http://127.0.0.1:5000`.

To be able to run without https against e.g. localhost, set:
`export OAUTHLIB_INSECURE_TRANSPORT=1`

## Running

```bash
# Install dependencies
$ virtualenv -p python3 .venv && source .venv/bin/activate && pip install -r requirements.txt
# Run the tests
$ LXLTESTING_LOGIN_URL=https://some.host/login LXLTESTING_USERNAME=username \
      LXLTESTING_PASSWORD=password LXLTESTING_OAUTH_CLIENT_ID=client-id pytest
```

Environment variables can also be kept in a run configuration for this project if running the tests in an IDE.

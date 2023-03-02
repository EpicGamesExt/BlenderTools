# Help Test
Testing can be done locally with your open Blender and Unreal Editor instances or with [Docker](https://docs.docker.com/get-docker/) containers. First install the requirements.
```shell
pip install -r requirements.txt
```

## Testing Against Open App Instances
1. Open Blender
1. Open your Unreal Project and make sure `remote execution` is enabled.
1. Install the addons.
1. Start the RPC server `Pipeline > Utilities > Start RPC Servers`.

```shell
cd ./tests
python run_tests.py
```
Testing should begin.

## Testing Against Docker Containers
The CI/CD system tests against the docker images. The containers are Linux.

::: tip Windows Users
   You will need to install [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install).
Then install [Ubuntu on Windows](https://ubuntu.com/tutorials/install-ubuntu-on-wsl2-on-windows-10)
:::

1. Install [Docker](https://docs.docker.com/get-docker/).
1. Make sure docker is working by running `docker images`.
1. Set the environment variable `TEST_ENVIRONMENT=1`.
1. Set the environment variable `GITHUB_TOKEN=your-personal access-token`. This is needed to pull the
   [unreal container image](https://docs.unrealengine.com/4.27/en-US/SharingAndReleasing/Containers/ContainersQuickStart/)
   if you don't already have it.
```shell
set GITHUB_TOKEN=your-personal access-token
set TEST_ENVIRONMENT=1
cd ./tests
python run_tests.py
```

Testing should begin.
::: tip Note
   If the you don't have the docker images already pulled this can take a while to pull the images.
:::


## View Test Results
The tests will run for a while and when they finish you should receive output like this indicating there were no failures.
```text
----------------------------------------------------------------------
Ran 74 tests in 917.496s

OK (skipped=30)

Generating XML reports...
```

### XUnit Files
The test runner will also output the results as xunit files to the `./tests/results` folder.

A handy cli tool for viewing xml unittest results is [xunit-viewer](https://www.npmjs.com/package/xunit-viewer).
If you wish you can install it and run:
```shell
xunit-viewer -r ./results
```
A `index.html` should now be available to view in the `tests` folder.


## Environment Variables
The `run_tests.py` script can be customized with environment variables. You probably won't ever need to modify these
from their defaults, however, since there are so many unit tests, targeting specific files with the `EXCLUSIVE_TEST_FILES` or
specific cases with `EXCLUSIVE_TESTS` can be beneficial.


| Variables | Description                                                                                                                                                                                                                                                                                                                    | Default                                                                   |
| -------------- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| `TEST_ENVIRONMENT` | Whether to run the in the container test environment                                                                                                                                                                                                                                                                           | If no value is set, testing will run on the host                          |
| `EXCLUSIVE_TEST_FILES` | Whether to run tests exclusively on this list of test files. Comma seperated list.                                                                                                                                                                                                                                             | Runs all tests files by default                                           |
| `EXCLUSIVE_TESTS` | Whether to run tests exclusively on this list of test names. Comma seperated list.                                                                                                                                                                                                                                             | Runs all tests cases by default                                           |
| `REMOVE_CONTAINERS` | Whether to shutdown and remove the containers after testing. Testing will be faster if the containers don't have to restart                                                                                                                                                                                                    | `True` by default. Leave blank if you want the containers to keep running |
| `BLENDER_ADDONS` | A comma seperated list of the addons to test                                                                                                                                                                                                                                                                                   | `send2ue,ue2rigify`                                                       |
| `BLENDER_PORT`     | The port blender communicates on                                                                                                                                                                                                                                                                                               | `9997` on host `8997` for container                                       |
| `UNREAL_PORT`     | The port unreal communicates on                                                                                                                                                                                                                                                                                                | `9998` on host `8998` for container                                       |
| `HOST_REPO_FOLDER`     | The path on disk to the repo                                                                                                                                                                                                                                                                                                   | The repo folder relative to the current working directory                 |
| `CONTAINER_REPO_FOLDER`     | The path in the container where the repo is mounted                                                                                                                                                                                                                                                                            | `/tmp/blender_tools/`                                                     |
| `HOST_TEST_FOLDER`     | The path on disk to the repo tests folder                                                                                                                                                                                                                                                                                      | The current working directory                                             |
| `CONTAINER_TEST_FOLDER`     | The path in the container where the repo tests folder is mounted                                                                                                                                                                                                                                                               | `/tmp/blender_tools/tests`                                                |
| `RPC_TIME_OUT` | When running a Non-Blocking server, the is a timeout value for command execution. If a command has been sent from the client, the server will try to give the client the response up until 20 seconds has passed. Once the response or timeout has been reached, the server will let the event loop of the DCC continue again. | `20`                                                                      |
| `RPC_EXECUTION_HISTORY_FILE` | Lets you specify a file path to write out the python execution history by the rpc module. This is useful for debugging.                                                                                                                                                                                                        | `None`                                                                    |

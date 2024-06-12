import os
import ast
import logging
import subprocess
import sys
import time
import threading
import unittest
import docker
import docker.errors
import xmlrunner
import shutil
import inspect
from datetime import datetime

# needed submodules
import websocket
import requests
import urllib3
import charset_normalizer
import certifi
import idna
import rpc


from rpc import client
from rpc import validations
from rpc import factory
from http.client import RemoteDisconnected
from importlib.machinery import SourceFileLoader

logging.basicConfig(level=logging.DEBUG)


class TestSuiteCollector(ast.NodeVisitor):
    """
    Collects test suites.
    """
    def __init__(self, test_case_file_path):
        super(TestSuiteCollector, self).__init__()
        module_name, extension = os.path.splitext(os.path.basename(test_case_file_path))
        self._test_case_module = SourceFileLoader(module_name, test_case_file_path).load_module()
        self._test_case_classes = []

        with open(test_case_file_path) as test_case_file:
            parsed_file = ast.parse(test_case_file.read())
            self.visit(parsed_file)

    def visit_ClassDef(self, node):
        """
        Override the method that visits nodes that are classes.
        """
        test_case_class = getattr(self._test_case_module, node.name)

        if issubclass(test_case_class, unittest.TestCase):
            if test_case_class not in self._test_case_classes and not test_case_class.__name__.lower().endswith('base'):
                self._test_case_classes.append(test_case_class)

    def get_test_case_classes(self):
        """
        Get the updated test suite.

        :return TestSuite: A test suite.
        """
        return self._test_case_classes


class ContainerTestManager:
    def __init__(
            self,
            images,
            test_case_folder=None,
            test_files_images=None,
            prefix_service_logs=True,
            max_poll_time=200,
            poll_interval=1,
            additional_python_paths=None,
            exclusive_test_files=None,
            exclusive_tests=None
    ):

        self.test_case_container_folder = os.environ.get('CONTAINER_TEST_FOLDER', '/tmp/test_cases/')
        self.container_site_package_folder = '/tmp/site-packages/'
        self.images = images
        self.test_case_folder = test_case_folder
        self.remap_pairs = [(self.test_case_folder, self.test_case_container_folder)]
        self.test_files_folder = os.path.join(self.test_case_folder, 'test_files')
        self.test_files_images = test_files_images or []
        self.test_results_output = os.path.join(self.test_case_folder, 'results')
        self.max_poll_time = max_poll_time
        self.poll_interval = poll_interval
        self.prefix_service_logs = prefix_service_logs
        self.exclusive_test_files = exclusive_test_files or []
        self.additional_python_paths = additional_python_paths or []
        self.exclusive_tests = exclusive_tests or []
        self._test_case_ids = []

        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.setup_logging()

        if os.environ.get('TEST_ENVIRONMENT'):
            try:
                if sys.platform == 'linux':
                    self.docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
                    self.docker_api_client = docker.APIClient(base_url='unix://var/run/docker.sock')
                else:
                    self.docker_client = docker.from_env()
                    self.docker_api_client = docker.APIClient()
                    
            except docker.errors.DockerException:
                raise docker.errors.DockerException('Can not talk to the docker API. Is docker installed and running?')

        self.containers = []
        self.start_time = int(time.time())
        self.log_streaming_threads = []
        self.services_summary = {}
        self.should_continue = True
        self.test_suite = unittest.TestSuite()

    def _call_on_all_services(self, callable_instance, **kwargs):
        """
        Helper method for calling a given method on all services.

        :param callable callable_instance: A callable.
        :param bool join: Whether or not to join the threads.
        :return list[Thread]: A list of threads.
        """
        threads = []
        # begin call on each service in a separate thread
        for container in self.containers:
            # get the correct rpc port for the server
            rpc_port = self.images.get(container.name, {}).get('rpc_port')
            rpc_client = client.RPCClient(port=rpc_port)
            thread = threading.Thread(
                name=container.name,
                target=callable_instance,
                args=[container.name, rpc_client],
                kwargs=kwargs
            )
            thread.start()
            threads.append(thread)

        # join all threads which waits for each call to finish
        if kwargs.get('join', True):
            for thread in threads:
                thread.join()
            return []
        return threads

    def get_start_time_offset(self):
        """
        Gets the current time offset from the start time.

        :return int: Time in seconds.
        """
        return round(time.time() - self.start_time)

    @staticmethod
    def setup_logging(loggers_to_reduce=None):
        """
        Set up logging and reduce output from imported modules.

        :param list[str] loggers_to_reduce: A list of logger names to reduce verbosity on.
        """
        if loggers_to_reduce is None:
            loggers_to_reduce = [
                'urllib3.connectionpool',
                'docker.auth',
                'docker.utils.config',
                'container_test_manager.rpc'
            ]

        for log_name in loggers_to_reduce:
            log = logging.getLogger(log_name)
            log.setLevel(logging.WARNING)

    def set_python_environment(self):
        """
        Sets the list of extra python packages and paths needed.
        """
        # add the test cases path of the client to the server
        for path in self.additional_python_paths + [self.test_case_folder]:
            if path not in sys.path:
                sys.path.append(path)

        # and any additional packages
        os.environ['RPC_ADDITIONAL_PYTHON_PATHS'] = ','.join(
            [
                self.test_case_container_folder,
                self.container_site_package_folder
            ] + self.additional_python_paths
        )

    def set_server_environment_variables(self):
        """
        Sets the server's python environment variables.
        """
        for name, data in self.images.items():
            rpc_client = client.RPCClient(port=data.get('rpc_port'))
            environment = data.get('environment', {})
            for key, value in environment.items():
                self.logger.debug(f'Setting "{name}" environment variable {key}={value}')
                rpc_client.proxy.set_env(key, value)

    def add_test_case(self, test_case_class, test_case_file_path):
        """
        Adds a test case to the test suite.

        :param TestCase test_case_class: A TestCase class.
        :param str test_case_file_path: The file path of the test case.
        """
        if inspect.getfile(test_case_class) == test_case_file_path:
            test_id = f'{test_case_file_path}{test_case_class}'
            if test_id not in self._test_case_ids:
                if self.exclusive_tests:
                    for exclusive_test in self.exclusive_tests:
                        if hasattr(test_case_class, exclusive_test):
                            self.test_suite.addTest(test_case_class(exclusive_test))
                else:
                    self.test_suite.addTest(unittest.makeSuite(test_case_class))
                self._test_case_ids.append(test_id)

    def run_test_cases(self):
        """
        Run the test cases.

        :return _XMLTestResult: The test results.
        """
        if self.should_continue:
            if os.environ.get('TEST_ENVIRONMENT'):
                # save the latest IP addresses on the containers
                self.save_ip_addresses()
            else:
                # when not launched from a container, the environment variables need to be set remotely
                self.set_server_environment_variables()

            try:
                for name, data in self.images.items():
                    for test_case_file_path in self.get_test_cases_from_folder():

                        # if exclusive test files are provided, then skip any test cases that is not in that list.
                        if self.exclusive_test_files:
                            if os.path.basename(test_case_file_path) not in self.exclusive_test_files:
                                continue

                        test_suite_collector = TestSuiteCollector(test_case_file_path)

                        # add each test class to the test suite
                        for test_case_class in test_suite_collector.get_test_case_classes():
                            if issubclass(test_case_class, factory.RPCTestCase):
                                validations.validate_test_case_class(test_case_class)
                                # sets the remap attribute on the class so it knows where to
                                # remap the file on the container file system
                                test_case_class.remap_pairs = self.remap_pairs

                                # only add the the test suite if it matches the services rpc port
                                if test_case_class.port == data.get('rpc_port'):
                                    self.add_test_case(test_case_class, test_case_file_path)
                            else:
                                self.add_test_case(test_case_class, test_case_file_path)

                test_runner = xmlrunner.XMLTestRunner(
                    output=self.test_results_output,
                    verbosity=3
                )
                return test_runner.run(self.test_suite)
            except Exception as exception:
                self.stop()
                raise exception

    def get_test_cases_from_folder(self):
        """
        Adds all files in a folder to the list of test cases.

        :return list[str]: A list of file paths.
        """
        if self.test_case_folder:
            root, directory, files = next(os.walk(self.test_case_folder))
            return [os.path.join(root, file) for file in files if file.endswith('.py')]
        return []

    def get_package_volume_mounts(self, additional_packages):
        """
        Get a list of package volume mounts.

        :return list[str]: A list of package volume mounts.
        """
        package_volumes_mounts = []
        # add the additional modules that need to be mounted into the containers python path
        additional_packages = additional_packages + [
            docker,
            xmlrunner,
            websocket,
            requests,
            urllib3,
            charset_normalizer,
            certifi,
            idna,
            rpc
        ]
        package_file_paths = [package.__file__ for package in additional_packages] + [__file__]
        for package_file_path in package_file_paths:
            host_path = os.path.normpath(os.path.dirname(package_file_path))
            module_name = os.path.basename(host_path)
            package_volumes_mounts.append(fr'{host_path}:{self.container_site_package_folder}{module_name}')

        return package_volumes_mounts

    def cache_test_files(self):
        """
        Copies test files from each container to the host test folder location.
        """
        for test_file_image in self.test_files_images:
            folder = test_file_image.get('folder')
            tag = test_file_image.get('tag')
            repository = test_file_image.get('repository')
            refresh = test_file_image.get('refresh', True)
            image = f'{repository}/{tag}'
            if not repository:
                image = tag

            if folder and repository and tag:
                if refresh:
                    if os.path.exists(self.test_files_folder):
                        self.logger.debug(f'Removing already cached test files...')
                        shutil.rmtree(self.test_files_folder)

                elif os.path.exists(self.test_files_folder):
                    self.logger.debug(f'Test files already cached.')
                    return None

                if self.test_files_images:
                    container = self.docker_client.containers.run(
                        image,
                        'sleep infinity',
                        detach=True
                    )
                    # get the folder size
                    result = container.exec_run(['du', '-hs', folder])
                    folder_size = result.output.decode("utf-8").split('/')[0].strip()
                    self.logger.debug(f'Caching {folder_size} of data from container {tag}...')
                    subprocess.run([
                        'docker',
                        'cp',
                        f'{container.id}:{folder}',
                        self.test_files_folder,
                    ])
                    container.remove(force=True)

    def pull_images(self):
        """
        Pulls down the required images.
        """
        for name, data in self.images.items():
            repository = data.get('repository')
            always_pull = data.get('always_pull')
            if always_pull and repository:
                if repository:
                    self.docker_client.images.pull(
                        repository=data.get('repository'),
                        tag=data.get('tag'),
                        auth_config=data.get('auth_config', {}),
                    )

            if self.test_files_images:
                repository = self.test_files_images.get('repository')
                always_pull = data.get('always_pull')
                if always_pull and repository:
                    self.docker_client.images.pull(
                        repository=self.test_files_images.get('repository'),
                        tag=self.test_files_images.get('tag'),
                        auth_config=self.test_files_images.get('auth_config', {}),
                    )

    def run_containers(self):
        """
        Runs the containers.
        """
        self.start_time = int(time.time())

        for name, data in self.images.items():
            refresh = data.get('refresh', True)
            rpc_port = data.get('rpc_port')
            additional_packages = data.get('additional_packages', [])
            repository = data.get('repository')
            tag = data.get('tag')
            command = data.get('command', [])
            user = data.get('user')
            ports = data.get('ports', {})
            ports.update({f'{rpc_port}/tcp': ('127.0.0.1', rpc_port)})
            entrypoint = data.get('entrypoint')
            environment = data.get('environment', {})
            environment.update({
                f'RPC_SERVER_{rpc_port}': name,
                'RPC_PORT': rpc_port,
                'RPC_HOST': '0.0.0.0'
            })

            volumes = data.get('volumes', [])
            volumes = volumes + self.get_package_volume_mounts(additional_packages)
            volumes.append(f'{self.test_case_folder}:{self.test_case_container_folder}')

            image = f'{repository}/{tag}'
            if not repository:
                image = tag

            container = None
            try:
                container = self.docker_client.containers.get(name)
                if container:
                    if refresh or container.status != 'running':
                        # remove the container if it already exists and isn't running
                        container.remove(force=True)
                        container = None
            except docker.errors.NotFound:
                pass

            if not container:
                container = self.docker_client.containers.run(
                    name=name,
                    image=image,
                    command=command,
                    user=user,
                    volumes=volumes,
                    ports=ports,
                    entrypoint=entrypoint,
                    environment=environment,
                    stderr=True,
                    detach=True,
                )
                # remove the py cache in the test case folder
                container.exec_run(['rm', '-r', os.path.join(self.test_case_container_folder, '__pycache__')])

                self.containers.append(container)

    def stop_containers(self):
        """
        Shuts down and removes all containers.
        """
        for container in self.docker_client.containers.list():
            if container.name in self.images.keys():
                container_name = container.name
                stats = container.stats(stream=False)
                inspect_data = self.docker_api_client.inspect_container(container_name)
                container.remove(force=True)
                self.logger.debug(f'Removed container {container_name}')
                self.services_summary.update({container_name: {'stats': stats, 'inspect_data': inspect_data}})

    def await_service(self, service_name, rpc_client):
        """
        Awaits a response from the given service.

        :param str service_name: The name of a service in the docker compose file.
        :param RPCClient rpc_client: The rpc client instance needed to talk to the service.
        """
        while self.get_start_time_offset() < self.max_poll_time:
            time.sleep(self.poll_interval)
            try:
                if rpc_client.proxy.is_running():
                    self.logger.info(f'{service_name} is running!')
                    break
            except (RemoteDisconnected, ConnectionRefusedError, ConnectionResetError):
                self.logger.debug(
                    f'{service_name} has not responded in {self.get_start_time_offset()} seconds...'
                )
                # stop polling if docker container is not running
                container = self.docker_client.containers.get(service_name)

                if container.status == 'exited':
                    self.should_continue = False
                    break

    def stream_service_logs(self, container_name, *args, **kwargs):
        """
        Streams the logs from the given service.
        """
        try:
            container = self.docker_client.containers.get(container_name)
            for line in container.logs(
                    stream=True,
                    since=self.start_time,
                    stderr=kwargs.get('stderr'),
                    stdout=kwargs.get('stdout')
            ):
                if self.prefix_service_logs:
                    logger = logging.getLogger(container_name)
                    logger.setLevel(logging.DEBUG)
                    logger.debug(line.decode("utf-8").strip('\n'))
                else:
                    if kwargs.get('stdout'):
                        sys.stdout.write(line.decode("utf-8"))
                    if kwargs.get('stderr'):
                        sys.stdout.write(line.decode("utf-8"))

        except docker.errors.NotFound:
            self.services_summary.update({container_name: {
                'error': (
                    f'The "{container_name}" container logs could not be fetched, because a container by that name '
                    f'was not found!'
                )
            }})

    def stream_logs_from_services(self):
        """
        Streams the logs from the running services.
        """
        self.log_streaming_threads = self._call_on_all_services(
            self.stream_service_logs,
            join=False,
            stderr=True,
        )
        self.log_streaming_threads = self._call_on_all_services(
            self.stream_service_logs,
            join=False,
            stdout=True,
        )

    def save_ip_addresses(self):
        """
        Sets a server ip in a container environment variable if `connects_to` is provided. This way if the container
        uses the rpc client to connect to another server it will use this ip for the server address.
        """
        for name, data in self.images.items():
            connects_to = data.get('connects_to')
            if connects_to:
                target_container = self.docker_client.containers.get(connects_to)
                # get the ip address from the target container
                server_ip = target_container.attrs['NetworkSettings']['IPAddress']
                rpc_client = client.RPCClient(port=data.get('rpc_port'))

                # set the ip address as the next servers ip address the client will use
                rpc_client.proxy.set_env('RPC_SERVER_IP', server_ip)
                self.logger.debug(
                    f'Saved "{connects_to}" container IP "{server_ip}" in the "{name}" python environment'
                )

    def await_services(self):
        """
        Awaits responses from all services.
        """
        self._call_on_all_services(self.await_service)

    def log_summary(self):
        """
        Log a summary.
        """
        for service_name, data in self.services_summary.items():
            inspect_data = data.get('inspect_data')
            stats = data.get('stats')
            if stats and inspect_data:
                cpu_stats = stats.get('cpu_stats')
                pre_cpu_stats = stats.get('precpu_stats')

                # get cpu stats
                cpu_total_usage = cpu_stats['cpu_usage']['total_usage']
                system_cpu_usage = cpu_stats['system_cpu_usage']
                pre_cpu_total_usage = pre_cpu_stats['cpu_usage']['total_usage']
                pre_system_cpu_usage = pre_cpu_stats['system_cpu_usage']

                # get memory stats
                memory_stats = stats["memory_stats"]["stats"]
                memory_usage = stats["memory_stats"]["usage"]

                memory_used = memory_usage - memory_stats.get("cache", 0) + memory_stats.get("active_file", 0)
                limit = stats["memory_stats"]['limit']

                # calculate cpu percentages
                total_cpu_usage_delta = cpu_total_usage - pre_cpu_total_usage
                system_cpu_usage_delta = system_cpu_usage - pre_system_cpu_usage
                cpu_percentage = round((total_cpu_usage_delta / system_cpu_usage_delta) * 100, 3)

                # calculate memory percentages
                memory_percentage = round(memory_used / limit * 100, 2)
                gb_memory = round(memory_used / (1024 * 1024 * 1024), 2)
                gb_memory_limit = round(limit / (1024 * 1024 * 1024), 2)

                # calculate runtime
                start = inspect_data.get('Created').split('.')[0]
                runtime_delta = datetime.utcnow() - datetime.fromisoformat(start)

                self.logger.info(
                    f' {service_name.capitalize()}: Total runtime {runtime_delta.seconds} seconds | {cpu_percentage}% '
                    f'of available CPU was used | {memory_percentage}% of available memory used '
                    f'{gb_memory}GB / {gb_memory_limit}GB'
                )

            error = data.get('error')
            if error:
                self.logger.error(error)

    def start(self):
        """
        Starts services and awaits their response.
        """
        self.set_python_environment()
        self.pull_images()
        self.cache_test_files()
        self.run_containers()
        self.stream_logs_from_services()
        self.await_services()

    def stop(self):
        """
        Stops all services.
        """
        self.stop_containers()
        for thread in self.log_streaming_threads:
            thread.join()

        self.log_summary()

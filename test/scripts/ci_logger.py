import os
import sys
import time
import github
from urllib import request
from urllib.error import HTTPError

try:
    import boto3
    import docker

except ImportError:
    boto3 = None
    docker = None


class LogFile:
    """
    This class implements a basic file object.
    """
    def __init__(self, contents):
        self.contents = contents

    def read(self, amount=None):
        """
        This method reads

        :param int amount: This amount of times to read.
        """
        if not amount:
            return ''.encode('utf-8')

        return self.contents.encode('utf-8')


class CILogger:
    """
    This class handles the interaction of reporting logs and receiving logs from s3.
    """
    def __init__(self, bucket_name, repo_name, workflow_name):
        """
        This method instantiates the S3 logger object.

        :param str bucket_name: The name of the s3 bucket to write to and read the logs from.
        """
        # get the values from the passed in args
        self.args = sys.argv[1:]
        self.arguments = self.get_flags()
        self.repo_name = repo_name
        self.sha = self.arguments.get('--sha')
        self.token = self.arguments.get('--token')

        # create clients
        if boto3:
            self.s3_client = boto3.client('s3')
        if docker:
            self.docker_client = docker.from_env()

        self.github_client = github.Github(self.token)

        # set constants
        self.bucket_name = bucket_name
        self.workflow_name = workflow_name
        self.public_web_address = f'https://{bucket_name}.s3.amazonaws.com'
        self.previous_logs = 'previous_logs.log'
        self.latest_logs = 'latest_logs.log'

    def get_flags(self):
        """
        This method parses out commandline flags

        :return dict: A dictionary of flags and their values
        """
        flags = {}
        for index, arg in enumerate(self.args):
            if '--' in arg:
                try:
                    flags[arg] = self.args[index + 1]
                except IndexError:
                    raise ValueError(f'The flag {arg} needs a value!')
        return flags

    def get_commit_state(self):
        """
        This method checks the state of the commit

        :return str: A state, either: success, failure, or pending.
        """
        repo = self.github_client.get_repo(self.repo_name)
        commit = repo.get_commit(sha=self.sha)

        for status in commit.get_statuses():
            if status.context == 'Blender Tools CI':
                print(status.state)
                return status.state

    def get_workflow(self):
        """
        This method gets a workflow by name.

        :return object: A workflow object.
        """
        repo = self.github_client.get_repo(self.repo_name)
        for work_flow in repo.get_workflows():
            if work_flow.name == self.workflow_name:
                return work_flow

    def get_run(self, run_number):
        """
        This method gets a workflow run by run number:

        :param int run_number: The unique run number
        :return object: A run object.
        """
        workflow = self.get_workflow()
        for run in workflow.get_runs():
            if run.run_number == run_number:
                return run

    def write_log(self, log_contents):
        """
        This method writes all the provided content to an s3 bucket that has the name of the
        commit sha value.

        :param str log_contents: A string of all the file contents.
        """
        log_file = LogFile(log_contents)
        self.s3_client.upload_fileobj(
            Fileobj=log_file,
            Bucket=self.bucket_name,
            Key=self.sha,
            ExtraArgs={'ACL': 'public-read'}
        )

    def read_log(self):
        """
        This method reads only new logs from the s3 bucket.

        :return str: New logs from the s3 bucket.
        """
        # try to get the logs for the commit
        try:
            file = request.urlopen(f'{self.public_web_address}/{self.sha}')
            logs = file.read().decode("utf-8")
        except HTTPError:
            logs = ''

        # create a file to store the previously read logs
        if not os.path.exists(self.previous_logs):
            previous_logs = open(self.previous_logs, 'w')
            previous_logs.write('')
            previous_logs.close()

        # check if the logs are new
        previous_logs = open(self.previous_logs, 'r')
        output = logs.replace(previous_logs.read(), '')
        previous_logs.close()

        # if there is new output save it
        if output:
            previous_logs = open(self.previous_logs, 'a')
            previous_logs.write(output)

        return output

    def delete_log(self):
        """
        This method delete the log file created for this commit
        """
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=self.sha,
        )

    def launch_workflow(self):
        """
        This method will launch the given github workflow.

        :param str workflow_name: The name of the workflow to start
        """
        repo = self.github_client.get_repo(full_name_or_id=self.repo_name)
        branch = repo.get_branches()[0]
        commit = repo.get_commit(sha=self.sha)

        for workflow in repo.get_workflows():
            if workflow.name == self.workflow_name:
                return workflow.create_dispatch(
                    ref=branch,
                    inputs={
                        'sha': self.sha,
                        'message': commit.commit.message,
                        'html_url': commit.html_url
                    }
                )

    def push_logs(self):
        """
        This method will push the docker logs to s3.
        """
        container = None

        while self.get_commit_state() == 'pending':
            containers = self.docker_client.containers.list()
            if containers:
                if not container:
                    container = containers[0]

                time.sleep(5)
                docker_logs = container.logs().decode("utf-8")
                if docker_logs:
                    self.write_log(docker_logs)

        if container:
            docker_logs = container.logs().decode("utf-8")
            self.write_log(docker_logs)

    def pull_logs(self):
        """
        This method will pull any new logs from s3 and write them to a local
        log file.
        """
        latest_logs = open(self.latest_logs, 'w')
        log = self.read_log()
        if log:
            latest_logs.write(log)
        latest_logs.close()

    def update_commit_status(self, state, description, run_number):
        """
        This method updates the status of a commit.

        :param string state: The status of the commit: success, failure, or pending.
        :param str description: The description to show in the status.
        :param run_number: The run number to use to set the link in the status,
        """
        repo = self.github_client.get_repo(full_name_or_id=self.repo_name)
        commit = repo.get_commit(sha=self.sha)
        run = self.get_run(run_number)

        if run:
            commit.create_status(
                state=state,
                target_url=run.html_url,
                description=description,
                context="Blender Tools CI"
            )


if __name__ == '__main__':
    # create a new log instance that will log to or access a bucket
    ci_logger = CILogger(
        bucket_name='blender-tools-logs',
        # TODO change to EpicGames
        repo_name='james-baber/BlenderTools',
        workflow_name='Continuous Integration'
    )

    # this will pull any new logs
    if ci_logger.arguments.get('--pull') == 'True':
        ci_logger.pull_logs()

    # this will push any new logs
    if ci_logger.arguments.get('--push') == 'True':
        ci_logger.push_logs()

    # this will launch the github workflow which will then be
    # able to ping s3 for log updates
    if ci_logger.arguments.get('--launch_workflow') == 'True':
        ci_logger.launch_workflow()

    # this will delete the log file created for this commit
    if ci_logger.arguments.get('--delete') == 'True':
        ci_logger.delete_log()

    # this will get the current  status
    if ci_logger.arguments.get('--get_status') == 'True':
        ci_logger.get_commit_state()

    # this will update the commit status
    if ci_logger.arguments.get('--set_status') == 'True':
        ci_logger.update_commit_status(
            state=ci_logger.arguments.get('--status'),
            description=ci_logger.arguments.get('--description'),
            run_number=int(ci_logger.arguments.get('--run_number'))
        )

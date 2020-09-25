import urllib
import sys
import time
import requests
import json
import docker
import os
try:
    import boto3
except ImportError:
    boto3 = None


class LogFile:
    def __init__(self, contents):
        self.contents = contents

    def read(self, amount=None):
        if not amount:
            return ''.encode('utf-8')

        return self.contents.encode('utf-8')


class S3Logger:
    def __init__(self, bucket_name, sha):
        if boto3:
            self.client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.sha = sha
        self.public_web_address = f'https://{bucket_name}.s3.amazonaws.com'
        self.previous_logs = 'previous_logs.log'

    def write_log(self, log_contents):
        log_file = LogFile(log_contents)
        self.client.upload_fileobj(
            Fileobj=log_file,
            Bucket=self.bucket_name,
            Key=self.sha,
            ExtraArgs={'ACL': 'public-read'}
        )

    def read_log(self):
        try:
            file = urllib.request.urlopen(f'{self.public_web_address}/{self.sha}')
            logs = file.read().decode("utf-8")

            if not os.path.exists(self.previous_logs):
                previous_logs = open(self.previous_logs, 'w')
                previous_logs.write('')
                previous_logs.close()

            previous_logs = open(self.previous_logs, 'r')


            output = logs.replace(previous_logs.read(), '')
            previous_logs.close()

            if output:
                previous_logs = open(self.previous_logs, 'a')
                previous_logs.write(output)
                return output
        except:
            return ''

    def delete_log(self):
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=self.sha,
        )


def get_commit_state(repo, token, sha):
    headers = {f'Authorization': f'token {token}'}
    response = requests.get(
        headers=headers,
        url=f'https://api.github.com/repos/{repo}/commits/{sha}/status'
    )
    return json.loads(response.text)['state'].lower()


def get_flags():
    args = sys.argv[1:]
    flags = {}
    for index, arg in enumerate(args):
        if '--' in arg:
            try:
                flags[arg] = args[index+1]
            except IndexError:
                raise ValueError(f'The flag {arg} needs a value!')
    return flags


if __name__ == '__main__':
    arguments = get_flags()

    repo_name = 'james-baber/BlenderTools'
    sha = arguments.get('--sha')
    token = arguments.get('--token')

    s3_logger = S3Logger(bucket_name='blender-tools-logs', sha=sha)

    if arguments.get('--listen') == 'True':
        latest_ouput = open('latest_ouput.log', 'w')
        log = s3_logger.read_log()
        if log:
            latest_ouput.write(log)
        latest_ouput.close()

    if arguments.get('--report') == 'True':
        client = docker.from_env()
        container = None

        while get_commit_state(repo_name, token, sha) == 'pending':
            containers = client.containers.list()
            if containers:
                if not container:
                    container = containers[0]

                time.sleep(3)
                docker_logs = container.logs().decode("utf-8")
                if docker_logs:
                    s3_logger.write_log(docker_logs)

        docker_logs = container.logs().decode("utf-8")
        s3_logger.write_log(docker_logs)

    if arguments.get('--delete') == 'True':
        s3_logger.delete_log()




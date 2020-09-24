import boto3
import urllib
import sys
import time
import os
from github import Github


class LogFile:
    def __init__(self, contents):
        self.contents = contents

    def read(self, amount=None):
        if not amount:
            return ''.encode('utf-8')

        return self.contents.encode('utf-8')


class S3Logger:
    def __init__(self, bucket_name, sha):
        self.client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.sha = sha
        self.public_web_address = f'https://{bucket_name}.s3.amazonaws.com'

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
            return file.read().decode("utf-8")
        except:
            return ''

    def delete_log(self):
        self.client.delete_object(
            Bucket=self.bucket_name,
            Key=self.sha,
        )


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

    # arguments = get_flags()
    # s3_logger = S3Logger(bucket_name='blender-tools-logs', sha=arguments['--sha'])
    #
    # if arguments.get('--listen') == 'True':
    #     while True:
    #         time.sleep(5)
    #         print(s3_logger.read_log())
    #
    # if arguments.get('--report') == 'True':
    #     # while True:
    #     #     time.sleep(5)
    #     s3_logger.write_log('Hi james')
    #     print('wrote!')
    #
    # if arguments.get('--delete') == 'True':
    #     s3_logger.delete_log()

    # https: // api.github.com / repos /${{github.repository}} / commits /${{github.sha}} / status

    client = Github(os.environ['USERNAME'], os.environ['PASSWORD'])
    repo = client.get_repo(full_name_or_id='james-baber/BlenderTools')
    commit = repo.get_commit(sha='ac3a2f212302cd56ef761b0a0437a29b5933f453')

    from pprint import pprint
    pprint(commit.raw_data)
    pprint(commit.status)




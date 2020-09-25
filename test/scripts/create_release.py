import os
from datetime import datetime
from addon_manager import AddonManager
from blender_utilities import get_addon_folder_path
from github import Github


class ReleaseAddon:
    def __init__(self, repo_name, addon_name):
        self.client = Github(os.environ['USERNAME'], os.environ['PASSWORD'])
        self.repo = self.client.get_repo(full_name_or_id=repo_name)
        self.addon_name = addon_name

    def get_message(self):
        for commit in self.repo.source.get_commits():
            for file in commit.files:
                if file.filename == f'{self.addon_name}/addon/__init__.py':
                    return commit.commit.message

    def get_previous_releases(self):
        releases = []
        for release in self.repo.get_releases():
            releases.append(release.title)

        return releases

    def get_version(self, zip_file):
        return os.path.basename(zip_file).split('_')[-1].replace('.zip', '')

    def format_title(self, version):
        words = self.addon_name.split('2')
        title = []

        for word in words:
            if word == 'ue' and word == words[-1]:
                title.append('Unreal')

            elif word == 'ue' and word == words[0]:
                title.append(word.upper())

            else:
                title.append(word.title())

        if title:
            return f'{" to ".join(title)} {version}'
        return f'{self.addon_name} {version}'

    def create_release(self):
        # get the previous addon releases
        previous_releases = self.get_previous_releases()

        # build the addon zip file
        addon_manager = AddonManager(self.addon_name)
        addon_folder_path = get_addon_folder_path(self.addon_name)
        addon_manager.build_addon(addon_folder_path)

        # get the addon name and version
        zip_file = addon_manager.get_addon_zip_path(addon_folder_path)
        version = self.get_version(zip_file)
        title = self.format_title(version)

        # if a release of that addon doesn't already exist
        if title not in previous_releases:

            # create a release
            release = self.repo.create_git_release(
                name=title,
                message=self.get_message(),
                tag=datetime.utcnow().strftime("%Y%m%d%H%M%S")
            )

            # upload the zip file
            release.upload_asset(
                path=zip_file,
                name=os.path.basename(zip_file),
                content_type='application/zip'
            )


def main():
    addons = ['send2ue', 'ue2rigify']
    # get the repository

    for addon in addons:
        release_addon = ReleaseAddon(
            repo_name='jamesbaber1/BlenderTools',
            addon_name=addon
        )
        release_addon.create_release()


if __name__ == '__main__':
    client = Github(os.environ['USERNAME'], os.environ['PASSWORD'])
    repo = client.get_repo(full_name_or_id='james-baber/BlenderTools')

    # commit = repo.get_commit(sha='ac3a2f212302cd56ef761b0a0437a29b5933f453')
    branch = repo.get_branches()[0]
    commit = repo.get_commits()[0]

    for i in dir(commit):
        print(i)

    from pprint import pprint
    pprint(commit.commit.raw_data)

    for workflow in repo.get_workflows():
        print(workflow.name)
        if workflow.name == 'Create Release':
            print(workflow.create_dispatch(
                ref=branch,
                inputs={
                    'sha': commit.sha
                }
            ))
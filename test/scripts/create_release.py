import os
import sys
from datetime import datetime
from addon_manager import AddonManager
from blender_utilities import get_addon_folder_path
from github import Github


class ReleaseAddon:
    """
    The class handles all the logic necessary to create a new release.
    """
    def __init__(self, repo_name, addon_name):
        """
        This instantiates the ReleaseAddon object.

        :param str repo_name: The repository name.
        :param str addon_name: The name of the addon to release.
        """
        self.client = Github(sys.argv[-1])
        self.repo = self.client.get_repo(full_name_or_id=repo_name)
        self.addon_name = addon_name

    def get_message(self):
        """
        The method gets the last commit message of the addons __init__.py file.

        :return str: The commit message.
        """
        for commit in self.repo.get_commits():
            for file in commit.files:
                if file.filename == f'{self.addon_name}/addon/__init__.py':
                    return commit.commit.message

    def get_previous_releases(self):
        """
        This method gets the previous releases.

        :return list: A list of the previous addon releases.
        """
        releases = []
        for release in self.repo.get_releases():
            releases.append(release.title)

        return releases

    def get_version(self, zip_file_path):
        """
        This method gets the version of the addon from the given .zip file path.

        :param str zip_file_path: The full path to the addon zip file.
        :return str: Formatted version.
        """
        return os.path.basename(zip_file_path).split('_')[-1].replace('.zip', '')

    def format_title(self, version):
        """
        This method formats title for addon release.

        :param version:
        :return:
        """
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
        """
        This method creates a release for the addon if it doesn't exist already.
        """
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


if __name__ == '__main__':
    # all the addons to check for releases
    addons = ['send2ue', 'ue2rigify']

    for addon in addons:
        release_addon = ReleaseAddon(
            repo_name='epicgames/BlenderTools',
            addon_name=addon
        )

        # create a new release for the addon if necessary
        release_addon.create_release()

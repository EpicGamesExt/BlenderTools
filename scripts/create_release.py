import os
import logging
import sys
import shutil
from datetime import datetime
from github import Github

BLENDER_ADDONS = list(filter(None, os.environ.get('BLENDER_ADDONS', 'send2ue,ue2rigify').split(',')))
PROJECT_FOLDER = os.path.join(
    os.path.dirname(__file__),
    os.pardir
)
logging.basicConfig(level=logging.INFO)


class ReleaseAddon:
    """
    The class handles all the logic necessary to create a new release.
    """
    def __init__(self, repo_name, zip_file_path):
        """
        Instantiates the ReleaseAddon object.

        :param str repo_name: The repository name.
        :param str zip_file_path: The path to the addon zip file.
        """
        self.client = Github(login_or_token=os.environ['GITHUB_TOKEN'])
        self.repo = self.client.get_repo(full_name_or_id=repo_name)
        self.zip_file = zip_file_path
        self.addon_name = os.path.basename(zip_file_path).split('_')[0]

    def get_message(self):
        """
        Gets the last commit message of the addons __init__.py file.

        :return str: The commit message.
        """
        release_notes_file_path = os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            self.addon_name,
            'release_notes.md'
        )
        with open(release_notes_file_path, 'r') as release_notes_file:
            return release_notes_file.read()

    def get_previous_releases(self):
        """
        Gets the previous releases.

        :return list: A list of the previous addon releases.
        """
        releases = []
        for release in self.repo.get_releases():
            releases.append(release.title)

        return releases

    def get_version(self):
        """
        Gets the version of the addon from the given .zip file path.

        :return str: Formatted version.
        """
        return os.path.basename(self.zip_file).split('_')[-1].replace('.zip', '')

    def format_title(self, version):
        """
        Formats title for addon release.

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
        Creates a release for the addon if it doesn't exist already.
        """
        # get the previous addon releases
        previous_releases = self.get_previous_releases()

        # get the addon name and version
        version = self.get_version()
        title = self.format_title(version)

        # if a release of that addon doesn't already exist
        if title not in previous_releases:
            logging.info(f'Creating release "{title}"')
            # create a release
            release = self.repo.create_git_release(
                name=title,
                message=self.get_message(),
                tag=datetime.utcnow().strftime("%Y%m%d%H%M%S")
            )

            logging.info(f'Uploading "{self.zip_file}"')
            # upload the zip file
            release.upload_asset(
                path=self.zip_file,
                name=os.path.basename(self.zip_file),
                content_type='application/zip'
            )
            logging.info(f'Successfully released!')


def package_addons(addon_release_folder):
    """
    Packages the addons up into zip files.
    """
    # remove any existing releases
    if os.path.exists(addon_release_folder):
        logging.info(f'Deleting existing release folder "{addon_release_folder}"...')
        shutil.rmtree(addon_release_folder)

    # get the addon packager class
    sys.path.append(os.path.join(PROJECT_FOLDER, 'tests'))
    from utils.addon_packager import AddonPackager

    # package the addons
    for addon_name in BLENDER_ADDONS:
        addon_folder_path = os.path.join(PROJECT_FOLDER, addon_name)
        addon_packager = AddonPackager(addon_name, addon_folder_path, addon_release_folder)
        addon_packager.zip_addon()


if __name__ == '__main__':
    release_folder = os.path.join(os.path.dirname(__file__), os.pardir, 'release')

    # package the addons
    package_addons(release_folder)

    # check for releases
    for zip_file in os.listdir(release_folder):
        release_addon = ReleaseAddon(
            repo_name=os.environ.get('REPO'),
            zip_file_path=os.path.join(release_folder, zip_file)
        )

        # create a new release for the addon if necessary
        release_addon.create_release()

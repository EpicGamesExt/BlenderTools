import os
from github import Github

# using username and password
git_hub = Github(os.environ['USERNAME'], os.environ['PASSWORD'])



    # for i in dir(commit.files):
    #     print(i)
    #
    # release = repo.create_git_release(
    #     name='Send to Unreal 1.4.2',
    #     message='Testing out the release',
    #     tag='1.4.2'
    # )
    #
    # for i in dir(release):
    #     print(i)
    #
    # release.upload_asset(
    #     path=r"C:\Users\James Baber\PycharmProjects\BlenderTools\send2ue\releases\send2ue_1.4.2.zip",
    #     name='send2ue_1.4.2.zip',
    #     content_type='application/zip'
    # ) etst


def get_updated_addons(repo_name, addon_names):
    # get the repository
    repo = git_hub.get_repo(full_name_or_id=repo_name)

    # get the most recent commit
    commit = repo.source.get_commits()[0]
    print(commit)

    # get all the paths to the addon init file
    init_file_paths = [(addon_name, f'{addon_name}/addon/__init__.py') for addon_name in addon_names]

    for file in commit.files:
        dir(file.filename)
        dir(file.raw_url)
        dir(file.raw_data)
        if file.filename in init_file_paths[1]:
            print(commit.author)
            print(commit.comments_url)


get_updated_addons(repo_name='jamesbaber1/BlenderTools', addon_names=['send2ue', 'ue2rigify'])
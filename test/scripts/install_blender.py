# Copyright Epic Games, Inc. All Rights Reserved.

import os
import sys


def install_blender():
    """
    This function installs blender on the linux, mac, and windows runners.
    """
    if sys.platform == 'linux':
        os.system('sudo snap install blender --classic')

    if sys.platform == 'darwin':
        os.system('brew cask install blender')

    if sys.platform == 'win32':
        os.system('choco install -y blender')


if __name__ == '__main__':
    install_blender()
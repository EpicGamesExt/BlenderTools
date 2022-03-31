# Copyright Epic Games, Inc. All Rights Reserved.
import os
from enum import Enum


class PreFixToken(Enum):
    SOCKET = 'SOCKET'
    BOX_COLLISION = 'UBX'
    CAPSULE_COLLISION = 'UCP'
    SPHERE_COLLISION = 'USP'
    CONVEX_COLLISION = 'UCX'


class AssetTypes:
    SKELETON = 'ARMATURE'
    MESH = 'MESH'
    ANIMATION = 'ANIMATION'


class ToolInfo(Enum):
    NAME = 'send2ue'
    APP = 'blender'
    LABEL = 'Send to Unreal'
    EXPORT_COLLECTION = 'Export'
    COLLECTION_NAMES = [EXPORT_COLLECTION]
    TEMPLATE_VERSION = 1
    FCURVE_FILE = '{file_path}_custom_property_fcurves.json'
    EXECUTION_QUEUE = 'send2ue_execution_queue'
    RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), 'resources')


class Template:
    NAME = 'templates'
    IGNORED_PROPERTIES = ['asset_name', 'file_path', 'validations_passed', 'active_settings_template']
    DEFAULT = 'default.json'
    VERSION = 1


class Extensions:
    NAME = 'extensions'
    UTILITY_OPERATOR = 'util_op'
    DRAW_NAMESPACE = f'{ToolInfo.NAME.value}_{NAME}_'
    DRAW_TABS = ['draw_export', 'draw_import', 'draw_validations']
    FOLDER = os.path.join(ToolInfo.RESOURCE_FOLDER.value, NAME)


class ExtensionOperators(Enum):
    PRE_OPERATION = 'pre_operation'
    PRE_VALIDATIONS = 'pre_validations'
    POST_VALIDATIONS = 'post_validations'
    PRE_ANIMATION_EXPORT = 'pre_animation_export'
    POST_ANIMATION_EXPORT = 'post_animation_export'
    PRE_MESH_EXPORT = 'pre_mesh_export'
    POST_MESH_EXPORT = 'post_mesh_export'
    PRE_IMPORT = 'pre_import'
    POST_IMPORT = 'post_import'
    POST_OPERATION = 'post_operation'


class PathModes(Enum):
    SEND_TO_PROJECT = 'send_to_project'
    SEND_TO_DISK = 'send_to_disk'
    SEND_TO_DISK_THEN_PROJECT = 'send_to_disk_then_project'

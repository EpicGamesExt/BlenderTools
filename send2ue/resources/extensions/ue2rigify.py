# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities


class Ue2RigifyExtension(ExtensionBase):
    name = 'ue2rigify'

    def pre_validations(self, properties):
        """
        Defines the pre validation logic that will be an injected operation.
        """
        if hasattr(bpy.context.scene, 'ue2rigify'):
            ue2rigify_properties = bpy.context.scene.ue2rigify
            if ue2rigify_properties.selected_mode != 'SOURCE':
                utilities.report_error(
                    'Send to Unreal can not be used while UE to Rigify is in not in source mode. All '
                    'animations must be baked to the source rig then try again.'
                )
                return False
        return True

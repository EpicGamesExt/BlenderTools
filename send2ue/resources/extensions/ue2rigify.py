# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
from send2ue.core.extension import ExtensionBase
from send2ue.core import utilities


class Ue2RigifyExtension(ExtensionBase):
    name = 'ue2rigify'

    # ------------ constants ---------------
    control_rig_name: bpy.props.StringProperty(default='rig')
    control_mode: bpy.props.StringProperty(default='CONTROL')
    action_prefix: bpy.props.StringProperty(default='SOURCE_')

    # ------------ read/write ---------------
    use_ue2rigify: bpy.props.BoolProperty(default=False)
    original_hide_value: bpy.props.BoolProperty(default=True)

    # ------------ ui -----------------------
    auto_sync_control_nla_to_source: bpy.props.BoolProperty(
        default=True,
        name='Sync control rig tracks to source rig',
        description=(
            'If enabled and using the UE to Rigify addon in control mode, the NLA tracks of the control rig will be '
            'synced to the source rig before they are exported'
        )
    )

    def set_source_rig_hide_value(self, hide_value):
        """
        Gets the original hide value of the source rig and sets it to the given value.

        :param bool hide_value: The hide value to set the source rig to.
        :return bool: The original hide value of the source rig.
        """
        if self.use_ue2rigify:
            ue2rigify_properties = bpy.context.scene.ue2rigify
            if ue2rigify_properties.source_rig:
                self.original_hide_value = ue2rigify_properties.source_rig.hide_get()
                ue2rigify_properties.source_rig.hide_set(hide_value)

    def set_ue2rigify_state(self):
        """
        Sets the use_ue2rigify property depending on whether to use code from the ue2rigify addon or not.
        """
        if bpy.context.preferences.addons.get('ue2rigify'):
            ue2rigify_properties = bpy.context.scene.ue2rigify
            if ue2rigify_properties.selected_mode == self.control_mode:
                self.use_ue2rigify = True
                return
        self.use_ue2rigify = False

    def pre_operation(self, properties):
        """
        Pre operation logic that un-hides the source rig.
        """
        self.set_ue2rigify_state()
        self.set_source_rig_hide_value(False)

        # sync the track values
        if self.use_ue2rigify and self.auto_sync_control_nla_to_source:
            bpy.context.scene.frame_set(0)
            bpy.ops.ue2rigify.sync_rig_actions()

    def post_operation(self, properties):
        """
        Post operation logic that restores the hide value on the source rig.
        """
        self.set_source_rig_hide_value(self.original_hide_value)

    def pre_animation_export(self, asset_data, properties):
        """
        Pre animation export logic that removes the 'SOURCE_' prefix from
        the animation names and syncs the clip mute values.
        """
        asset_path = asset_data.get('asset_path')
        file_path = asset_data.get('file_path')
        control_rig_object = bpy.data.objects.get(self.control_rig_name)
        action_name = asset_data.get('_action_name').strip(self.action_prefix)

        if self.use_ue2rigify and control_rig_object:
            if control_rig_object.animation_data:
                control_rig_object.animation_data.action = None

            # mute all actions
            utilities.set_all_action_mute_values(control_rig_object, mute=True)

            # unmute the action
            utilities.set_action_mute_value(control_rig_object, action_name, False)

            # update the asset and file names
            self.update_asset_data({
                'asset_path': f'{os.path.dirname(asset_path)}/{action_name}',
                'file_path': os.path.join(
                    os.path.dirname(file_path),
                    os.path.basename(file_path).strip(self.action_prefix)
                )
            })

    def post_animation_export(self, asset_data, properties):
        """
        Post animation export logic that mutes the control rig action.
        """
        asset_path = asset_data.get('asset_path')
        control_rig_object = bpy.data.objects.get(self.control_rig_name)
        action_name = os.path.basename(asset_path).strip(self.action_prefix)

        if self.use_ue2rigify and control_rig_object:
            # mute the action
            utilities.set_action_mute_value(control_rig_object, action_name, True)
            utilities.clear_pose(control_rig_object)

    def draw_export(self, dialog, layout, properties):
        """
        Defines the draw method for the extension under the `Export` tab.
        """
        box = layout.box()
        box.label(text='UE to Rigify:')
        dialog.draw_property(self, box, 'auto_sync_control_nla_to_source')

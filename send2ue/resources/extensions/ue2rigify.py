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
    current_scale_factor: bpy.props.FloatProperty(default=1)

    # ------------ ui -----------------------
    auto_sync_control_nla_to_source: bpy.props.BoolProperty(default=True)

    def get_source_rig_hide_value(self):
        """
        Gets the original hide value of the source rig.

        :return bool: The original hide value of the source rig.
        """
        if self.use_ue2rigify:
            ue2rigify_properties = bpy.context.scene.ue2rigify
            if ue2rigify_properties.source_rig:
                self.original_hide_value = ue2rigify_properties.source_rig.hide_get()

    def set_source_rig_hide_value(self, hide_value):
        """
        Gets the original hide value of the source rig and sets it to the given value.

        :param bool hide_value: The hide value to set the source rig to.
        :return bool: The original hide value of the source rig.
        """
        if self.use_ue2rigify:
            ue2rigify_properties = bpy.context.scene.ue2rigify
            if ue2rigify_properties.source_rig:
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

    def scale_control_rig(self, scale_factor):
        """
        Scales the control rig.

        :param float scale_factor: The amount to scale the control rig by.
        """
        # if the using the ue2rigify addon
        if self.use_ue2rigify:
            # remove all the constraints
            bpy.ops.ue2rigify.remove_constraints()
            # get the control rig
            control_rig = bpy.data.objects.get(self.control_rig_name)
            # scale the the control rig
            utilities.scale_object(control_rig, scale_factor)

    def post_export(self, properties):
        if self.use_ue2rigify and properties.automatically_scale_bones:
            bpy.ops.ue2rigify.constrain_source_to_deform()

    def pre_operation(self, properties):
        """
        Pre operation logic that un-hides the source rig.
        """
        self.set_ue2rigify_state()
        self.get_source_rig_hide_value()
        self.set_source_rig_hide_value(False)
        self.current_scale_factor = bpy.context.scene.unit_settings.scale_length

        # sync the track values
        if self.use_ue2rigify and self.auto_sync_control_nla_to_source:
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
        action_name = os.path.basename(asset_path).strip(self.action_prefix)

        if self.use_ue2rigify and control_rig_object:
            if control_rig_object.animation_data:
                control_rig_object.animation_data.action = None

            # un-mute the action
            utilities.set_action_mute_value(control_rig_object, action_name, False)

            # update the asset and file names
            self.update_asset_data({
                'asset_path': f'{os.path.dirname(asset_path)}/{action_name}',
                'file_path': os.path.join(
                    os.path.dirname(file_path),
                    os.path.basename(file_path).strip(self.action_prefix)
                )
            })

    def post_mesh_export(self, asset_data, properties):
        """
        Defines mesh export logic.
        """
        self.post_export(properties)

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

        self.post_export(properties)

    def pre_bone_scale(self, asset_data, properties):
        scale_factor = self.current_scale_factor / 0.01
        self.scale_control_rig(scale_factor)

    def mid_bone_scale(self, asset_data, properties):
        if self.use_ue2rigify:
            bpy.ops.ue2rigify.constrain_source_to_deform()

    def post_bone_scale(self, asset_data, properties):
        control_rig_object = bpy.data.objects.get(self.control_rig_name)
        if self.use_ue2rigify and control_rig_object:
            # re-scale the control rig
            scale_factor = bpy.context.scene.unit_settings.scale_length / self.current_scale_factor
            self.scale_control_rig(scale_factor)

    # def pre_validations(self, properties):
    #     """
    #     Defines the pre validation logic that will be an injected operation.
    #     """
    #     if hasattr(bpy.context.scene, 'ue2rigify'):
    #         ue2rigify_properties = bpy.context.scene.ue2rigify
    #         if ue2rigify_properties.selected_mode != 'SOURCE':
    #             utilities.report_error(
    #                 'Send to Unreal can not be used while UE to Rigify is in not in source mode. All '
    #                 'animations must be baked to the source rig then try again.'
    #             )
    #             return False
    #     return True

# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from ..properties import Send2UeProperties, Send2UeUIProperties
from ..functions import validations, utilities


class SendToUnrealPreferences(Send2UeProperties, Send2UeUIProperties, bpy.types.AddonPreferences):
    """
    This class creates the settings interface in the send to unreal addon.
    """
    bl_idname = __package__.split('.')[0]

    def draw(self, context, properties=None):
        """
        This defines the draw method, which is in all Blender UI types that create interfaces.
        :param context: The context of this interface.
        :param properties: The context of this interface.
        """
        layout = self.layout

        if not properties:
            properties = self

        row = layout.row()
        row.prop(properties, 'options_type', expand=True)

        if properties.options_type == 'paths':
            row = layout.row()
            row.prop(properties, 'path_mode', text='')
            if properties.path_mode in ['send_to_unreal', 'both']:

                # Mesh Folder (Unreal)
                row = layout.row()
                row.label(text='Mesh Folder (Unreal)')

                # disable the mesh folder path input if a skeleton path is provided
                row = layout.row()
                row.enabled = not bool(properties.unreal_skeleton_asset_path)
                row.alert = properties.incorrect_unreal_mesh_folder_path
                row.prop(properties, 'unreal_mesh_folder_path', text='')
                utilities.report_path_error_message(
                    layout,
                    properties.incorrect_unreal_mesh_folder_path,
                    validations.validate_unreal_path_by_property(
                        properties,
                        "incorrect_unreal_mesh_folder_path"
                    )
                )

                # Animation Folder (Unreal)
                row = layout.row()
                row.label(text='Animation Folder (Unreal)')
                row = layout.row()
                row.alert = properties.incorrect_unreal_animation_folder_path
                row.prop(properties, 'unreal_animation_folder_path', text='')
                utilities.report_path_error_message(
                    layout,
                    properties.incorrect_unreal_animation_folder_path,
                    validations.validate_unreal_path_by_property(
                        properties,
                        "incorrect_unreal_animation_folder_path"
                    )
                )

                # Skeleton Asset (Unreal)
                row = layout.row()
                row.label(text='Skeleton Asset (Unreal)')
                row = layout.row()
                row.alert = properties.incorrect_unreal_skeleton_path
                row.prop(properties, 'unreal_skeleton_asset_path', text='')
                utilities.report_path_error_message(
                    layout,
                    properties.incorrect_unreal_skeleton_path,
                    validations.validate_unreal_path_by_property(
                        properties,
                        "incorrect_unreal_skeleton_path"
                    )
                )

            if properties.path_mode in ['export_to_disk', 'both']:

                # Mesh Folder (Disk)
                row = layout.row()
                row.label(text='Mesh Folder (Disk)')

                # disable the mesh folder path input if a skeleton path is provided
                row.enabled = not bool(properties.unreal_skeleton_asset_path)
                row = layout.row()
                row.alert = properties.incorrect_disk_mesh_folder_path or properties.mesh_folder_untitled_blend_file
                row.prop(properties, 'disk_mesh_folder_path', text='')
                utilities.report_path_error_message(
                    layout,
                    properties.incorrect_disk_mesh_folder_path,
                    validations.validate_disk_path_by_property(
                        properties,
                        "incorrect_disk_mesh_folder_path"
                    )
                )
                utilities.report_path_error_message(
                    layout,
                    properties.mesh_folder_untitled_blend_file,
                    validations.validate_disk_path_by_property(
                        properties,
                        "mesh_folder_untitled_blend_file"
                    )
                )

                # Animation Folder (Disk)
                row = layout.row()
                row.label(text='Animation Folder (Disk)')
                row = layout.row()
                row.alert = properties.incorrect_disk_animation_folder_path or properties.animation_folder_untitled_blend_file
                row.prop(properties, 'disk_animation_folder_path', text='')
                utilities.report_path_error_message(
                    layout,
                    properties.incorrect_disk_animation_folder_path,
                    validations.validate_disk_path_by_property(
                        properties,
                        "incorrect_disk_animation_folder_path"
                    )
                )
                utilities.report_path_error_message(
                    layout,
                    properties.animation_folder_untitled_blend_file,
                    validations.validate_disk_path_by_property(
                        properties,
                        "animation_folder_untitled_blend_file"
                    )
                )

        if properties.options_type == 'export':
            row = layout.row()
            row.prop(properties, 'automatically_scale_bones')
            row = layout.row()
            row.prop(properties, 'export_all_actions')
            row = layout.row()
            row.prop(properties, 'auto_stash_active_action')
            # this option is greyed out unless ue2rigify is active
            row = layout.row()
            row.enabled = bool(bpy.context.preferences.addons.get('ue2rigify'))
            row.prop(properties, 'auto_sync_control_nla_to_source')
            row = layout.row()
            row.prop(properties, 'use_object_origin')
            row = layout.row()
            row.prop(properties, 'combine_child_meshes')
            row = layout.row()

            # fbx export settings box
            box = row.box()
            row = box.row()
            row.prop(
                properties,
                'show_fbx_settings',
                icon='TRIA_DOWN' if properties.show_fbx_settings else 'TRIA_RIGHT',
                icon_only=True,
                emboss=False
            )
            row.label(text='FBX Settings', icon='EXPORT')
            if properties.show_fbx_settings:
                row = box.row()
                row.label(text='Include:')
                row = box.row()
                row.prop(properties, 'use_custom_props')
                row = box.row()
                row.label(text='Transform:')
                row = box.row()
                row.prop(properties, 'global_scale')
                row = box.row()
                row.prop(properties, 'apply_scale_options')
                row = box.row()
                row.prop(properties, 'axis_forward')
                row = box.row()
                row.prop(properties, 'axis_up')
                row = box.row()
                row.prop(properties, 'apply_unit_scale')
                row = box.row()
                row.prop(properties, 'bake_space_transform')
                row = box.row()
                row.label(text='Geometry:')
                row = box.row()
                row.prop(properties, 'mesh_smooth_type')
                row = box.row()
                row.prop(properties, 'use_subsurf')
                row = box.row()
                row.prop(properties, 'use_mesh_modifiers')
                row = box.row()
                row.prop(properties, 'use_mesh_edges')
                row = box.row()
                row.prop(properties, 'use_tspace')
                row = box.row()
                row.label(text='Armature:')
                row = box.row()
                row.prop(properties, 'primary_bone_axis')
                row = box.row()
                row.prop(properties, 'secondary_bone_axis')
                row = box.row()
                row.prop(properties, 'armature_nodetype')
                row = box.row()
                row.prop(properties, 'use_armature_deform_only')
                row = box.row()
                row.prop(properties, 'add_leaf_bones')
                row = box.row()
                row.label(text='Animation:')
                row = box.row()
                row.prop(properties, 'bake_anim')
                row = box.row()
                row.prop(properties, 'bake_anim_use_all_bones')
                row = box.row()
                row.prop(properties, 'bake_anim_force_startend_keying')
                row = box.row()
                row.prop(properties, 'bake_anim_step')
                row = box.row()
                row.prop(properties, 'bake_anim_simplify_factor')
                row = box.row()
                row.label(text='Extras:')
                row = box.row()
                row.prop(properties, 'use_metadata')

        if properties.options_type == 'validations':
            row = layout.row()
            row.prop(properties, 'validate_materials')
            row = layout.row()
            row.prop(properties, 'validate_textures')

        if properties.options_type == 'import':
            row = layout.row()
            row.prop(properties, 'import_materials')
            row = layout.row()
            row.prop(properties, 'import_textures')
            row = layout.row()
            row.prop(properties, 'import_animations')
            row = layout.row()
            row.prop(properties, 'import_lods')
            row = layout.row()
            row.prop(properties, 'import_sockets')
            row = layout.row()
            row.prop(properties, 'import_object_name_as_root')
            row = layout.row()
            row.prop(properties, 'advanced_ui_import')

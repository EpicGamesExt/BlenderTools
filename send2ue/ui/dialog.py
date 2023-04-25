# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from ..constants import PathModes, Extensions, Template
from ..core import utilities, settings


class Send2UnrealDialog(bpy.types.Panel):
    def draw_paths_tab(self, layout):
        """
        Draws all the properties in the Paths tab.
        :param layout: The layout container for this tab.
        """
        properties = bpy.context.scene.send2ue
        row = layout.row()
        row.prop(properties, 'path_mode', text='')

        if bpy.context.scene.send2ue.path_mode in [
            PathModes.SEND_TO_PROJECT.value,
            PathModes.SEND_TO_DISK_THEN_PROJECT.value
        ]:
            self.draw_property(properties, layout, 'unreal_mesh_folder_path', header_label=True)
            self.draw_property(properties, layout, 'unreal_animation_folder_path', header_label=True)
            self.draw_property(properties, layout, 'unreal_groom_folder_path', header_label=True)
            self.draw_property(properties, layout, 'unreal_skeleton_asset_path', header_label=True)
            self.draw_property(properties, layout, 'unreal_physics_asset_path', header_label=True)

        if bpy.context.scene.send2ue.path_mode in [
            PathModes.SEND_TO_DISK.value,
            PathModes.SEND_TO_DISK_THEN_PROJECT.value
        ]:
            self.draw_property(properties, layout, 'disk_mesh_folder_path', header_label=True)
            self.draw_property(properties, layout, 'disk_animation_folder_path', header_label=True)
            self.draw_property(properties, layout, 'disk_groom_folder_path', header_label=True)

    @staticmethod
    def draw_property(properties, layout, property_name, header_label=False, enabled=True):
        error_message = bpy.context.window_manager.send2ue.property_errors.get(f'{property_name}_error_message')
        property_instance = properties.bl_rna.properties.get(property_name)
        row = layout.row()
        if property_instance:
            if header_label:
                row.label(text=property_instance.name)
                row = layout.row()
            else:
                row.label(text=property_instance.name)

            row.alert = bool(error_message)
            row.enabled = enabled
            row.prop(properties, property_name, text='')

            if error_message:
                row = layout.row()
                row.alert = True
                row.label(text=error_message)

    def draw_export_tab(self, layout):
        """
        Draws all the properties in the Export tab.

        :param layout: The layout container for this tab.
        """
        properties = bpy.context.scene.send2ue
        self.draw_property(properties, layout, 'use_object_origin')
        self.draw_property(properties, layout, 'export_object_name_as_root')

        #  animation settings box
        self.draw_expanding_section(
            layout,
            self.draw_animation_settings,
            'show_animation_settings',
            'Animation Settings',
            'ARMATURE_DATA'
        )

        # fbx export settings box
        self.draw_expanding_section(
            layout,
            self.draw_fbx_export_settings,
            'show_fbx_export_settings',
            'FBX Export Settings',
            'EXPORT'
        )

        #  abc settings box
        self.draw_expanding_section(
            layout,
            self.draw_abc_export_settings,
            'show_abc_export_settings',
            'ABC Export Settings',
            'EXPORT'
        )

    def draw_expanding_section(self, layout, draw_function, toggle_state_property, label, icon='NONE'):
        """
        Draws all the properties for the given settings group.

        :param object layout: The layout container for this tab.
        :param callable draw_function: A reference to a draw function to call.
        :param str toggle_state_property: The name of the property that holds the state of the toggle.
        :param str label: The label for the section.
        :param str icon: The name of the icon to use.
        """
        row = layout.row()
        box = row.box()
        row = box.row()
        toggle_value = getattr(bpy.context.window_manager.send2ue, toggle_state_property)
        row.prop(
            bpy.context.window_manager.send2ue,
            toggle_state_property,
            icon='TRIA_DOWN' if toggle_value else 'TRIA_RIGHT',
            icon_only=True,
            emboss=False
        )
        row.label(text=label, icon=icon)
        if toggle_value:
            draw_function(box)

    def draw_settings_section(self, layout, settings_category, settings_group, label):
        """
        Draws all the properties for the given settings group.

        :param object layout: The layout container for this tab.
        :param str settings_category: The dictionary path to where the settings group is located.
        :param str settings_group: The key name of the dictionary of settings to draw.
        :param str label: The label for the section.
        """
        setting_names = settings.get_setting_names(settings_category, settings_group)
        prefix = settings.get_generated_prefix(settings_category, settings_group)

        box = layout.box()
        box.label(text=f'{label}:')
        properties = settings.get_last_property_group_in_module_path(bpy.context.scene.send2ue, prefix.split('.'))
        for setting_name in setting_names:
            self.draw_property(properties, box, setting_name)

        row = layout.row()

    def draw_editor_settings(self, layout):
        """
        Draws all the properties for the editor library settings.

        :param layout: The layout container for this tab.
        """
        self.draw_settings_section(
            layout,
            'unreal-editor_skeletal_mesh_library',
            'lod_build_settings',
            'Skeletal Mesh LOD Build Settings'
        )
        self.draw_settings_section(
            layout,
            'unreal-editor_static_mesh_library',
            'lod_build_settings',
            'Static Mesh LOD Build Settings'
        )

    def draw_lod_settings(self, layout):
        """
        Draws all the properties in the lod settings.
        """
        properties = bpy.context.scene.send2ue
        self.draw_property(properties, layout, 'import_lods')
        self.draw_property(properties, layout, 'lod_regex')
        box = layout.box()
        box.label(text=f'Skeletal Mesh:')
        self.draw_property(properties, box, 'unreal_skeletal_mesh_lod_settings_path')

    def draw_fbx_import_settings(self, layout):
        """
        Draws all the properties in the FBX import settings.

        :param layout: The layout container for this tab.
        """
        self.draw_settings_section(
            layout,
            'unreal-import_method-fbx',
            'skeletal_mesh_import_data',
            'Skeletal Mesh'
        )
        self.draw_settings_section(
            layout,
            'unreal-import_method-fbx',
            'static_mesh_import_data',
            'Static Mesh'
        )
        self.draw_settings_section(
            layout,
            'unreal-import_method-fbx',
            'anim_sequence_import_data',
            'Animation'
        )
        self.draw_settings_section(
            layout,
            'unreal-import_method-fbx',
            'texture_import_data',
            'Texture'
        )
        self.draw_settings_section(
            layout,
            'unreal-import_method',
            'fbx',
            'Miscellaneous'
        )

    def draw_abc_import_settings(self, layout):
        """
        Draws all the properties in the ABC import settings.

        :param layout: The layout container for this tab.
        """
        self.draw_settings_section(
            layout,
            'unreal-import_method-abc',
            'conversion_settings',
            'Groom Conversion Settings'
        )

    def draw_import_tab(self, layout):
        """
        Draws all the properties in the Import tab.

        :param layout: The layout container for this tab.
        """
        properties = bpy.context.scene.send2ue
        self.draw_property(properties, layout, 'import_meshes')
        self.draw_property(properties, layout, 'import_materials_and_textures')
        self.draw_property(properties, layout, 'import_animations')
        self.draw_property(properties, layout, 'import_grooms')
        self.draw_property(properties, layout, 'advanced_ui_import')

        #  fbx import settings box
        self.draw_expanding_section(
            layout,
            self.draw_lod_settings,
            'show_lod_settings',
            'LOD Settings',
            'XRAY'
        )

        #  fbx import settings box
        self.draw_expanding_section(
            layout,
            self.draw_fbx_import_settings,
            'show_fbx_import_settings',
            'FBX Import Settings',
            'IMPORT'
        )
        #  abc import settings box
        self.draw_expanding_section(
            layout,
            self.draw_abc_import_settings,
            'show_abc_import_settings',
            'ABC Import Settings',
            'IMPORT'
        )
        #  editor library settings box
        self.draw_expanding_section(
            layout,
            self.draw_editor_settings,
            'show_editor_library_settings',
            'Editor Settings',
            'TOOL_SETTINGS'
        )

    def draw_validations_tab(self, layout):
        """
        Draws all the properties in the Validations tab.

        :param layout: The layout container for this tab.
        """
        properties = bpy.context.scene.send2ue
        self.draw_property(properties, layout, 'validate_time_units')
        self.draw_property(properties, layout, 'validate_scene_scale')
        self.draw_property(properties, layout, 'validate_armature_transforms')
        self.draw_property(properties, layout, 'validate_materials')
        self.draw_property(properties, layout, 'validate_textures')
        self.draw_property(properties, layout, 'validate_project_settings')
        self.draw_property(properties, layout, 'validate_object_names')
        self.draw_property(properties, layout, 'validate_meshes_for_vertex_groups')

    def draw_extensions(self, layout):
        """
        Draws the draws of each extension.
        """
        properties = bpy.context.scene.send2ue
        for extension_name in dir(properties.extensions):
            extension = getattr(properties.extensions, extension_name)
            draw = getattr(extension, f'draw_{properties.tab}', None)
            if draw:
                draw(self, layout, properties)

    def draw_animation_settings(self, layout):
        """
        Draws all the properties in the Animation Settings box.

        :param layout: The layout container for this tab.
        """
        properties = bpy.context.scene.send2ue
        self.draw_property(properties, layout, 'auto_stash_active_action')
        self.draw_property(properties, layout, 'export_all_actions')
        self.draw_property(properties, layout, 'export_custom_property_fcurves')

    def draw_fbx_export_settings(self, layout):
        """
        Draws all the properties in the FBX export settings.

        :param layout: The layout container for this tab.
        """
        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'include',
            'Include'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'transform',
            'Transform'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'geometry',
            'Geometry'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'armature',
            'Armature'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'animation',
            'Animation'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-fbx',
            'extras',
            'Extras'
        )

    def draw_abc_export_settings(self, layout):
        self.draw_settings_section(
            layout,
            'blender-export_method-abc',
            'manual_transform',
            'Manual Transform'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-abc',
            'scene_options',
            'Scene Options'
        )

        self.draw_settings_section(
            layout,
            'blender-export_method-abc',
            'object_options',
            'Object Options'
        )

    @staticmethod
    def draw_send2ue_buttons(layout):
        row = layout.row()
        row.label(text='Templates:')
        row = layout.row()
        row.scale_y = 1.5
        column = row.column()
        column.alignment = 'LEFT'
        column.operator('send2ue.load_template', text='Load')
        column = row.column()
        column.alignment = 'LEFT'
        column.operator('send2ue.save_template', text='Save')
        column = row.column()
        column.scale_x = 2
        column = row.column()
        column.alignment = 'RIGHT'
        column.operator_context = "INVOKE_DEFAULT"
        column.operator('wm.send2ue', text='Push Assets')

    def draw(self, context):
        """
        This draws the settings dialog items.

        :param object context: The context area in which the layout is being drawn.
        """
        properties = getattr(bpy.context.scene, 'send2ue', None)

        if properties:
            column = self.layout.column()
            row = column.row()
            row.label(text='Send to Unreal')

            # draw the settings template
            if properties.active_settings_template != Template.DEFAULT:
                row = column.split(factor=0.96, align=True)
                row.scale_y = 1.5
                row.prop(properties, 'active_settings_template', text='')
                row.operator('send2ue.remove_template', icon='PANEL_CLOSE', text='')
            else:
                row = column.row()
                row.scale_y = 1.5
                row.prop(properties, 'active_settings_template', text='')

            row = column.row()
            row.scale_y = 1.5
            row.prop(properties, 'tab', expand=True)

            if properties.tab == 'paths':
                self.draw_paths_tab(self.layout)
            elif properties.tab == 'export':
                self.draw_export_tab(self.layout)
            elif properties.tab == 'import':
                self.draw_import_tab(self.layout)
            elif properties.tab == 'validations':
                self.draw_validations_tab(self.layout)

            # draw the extensions section
            if utilities.has_extension_draw(properties.tab):
                self.draw_expanding_section(
                    self.layout,
                    self.draw_extensions,
                    'show_export_extensions',
                    'Extensions',
                    'SCRIPT'
                )

            self.layout.separator()
            self.draw_send2ue_buttons(self.layout)


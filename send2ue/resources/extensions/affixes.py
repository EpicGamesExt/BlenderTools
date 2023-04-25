# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
import os
import shutil
from send2ue.core import utilities, formatting
from send2ue.constants import BlenderTypes
from send2ue.core.extension import ExtensionBase


def add_affixes():
    """
    Adds the defined affixes to the objects selected for export.
    """
    properties = bpy.context.scene.send2ue
    mesh_objects = utilities.get_from_collection(BlenderTypes.MESH)
    rig_objects = utilities.get_from_collection(BlenderTypes.SKELETON)

    for mesh_object in mesh_objects:
        if mesh_object.modifiers:
            is_armature = False
            for modifier in mesh_object.modifiers:
                if modifier.type == 'ARMATURE':
                    if bool(modifier.object):
                        is_armature = True
                        break
            if is_armature:
                append_affix(
                    mesh_object,
                    properties.extensions.affixes.skeletal_mesh_name_affix
                )
            else:
                append_affix(
                    mesh_object,
                    properties.extensions.affixes.static_mesh_name_affix
                )
        else:
            append_affix(mesh_object, properties.extensions.affixes.static_mesh_name_affix)

        for slot in mesh_object.material_slots:
            if slot.material:
                append_affix(slot.material, properties.extensions.affixes.material_name_affix)

        texture_images = get_texture_images(mesh_object)
        rename_all_textures(texture_images, append_affix, properties)

    for rig_object in rig_objects:
        actions = utilities.get_actions(rig_object, properties.export_all_actions)
        if rig_object.animation_data:
            if rig_object.animation_data.action:
                actions.append(rig_object.animation_data.action)

        for action in actions:
            append_affix(action, properties.extensions.affixes.animation_sequence_name_affix)


def remove_affixes():
    """
    Removes the defined affixes from the objects selected for export.
    """
    properties = bpy.context.scene.send2ue
    mesh_objects = utilities.get_from_collection(BlenderTypes.MESH)
    rig_objects = utilities.get_from_collection(BlenderTypes.SKELETON)
    max_strip = 30

    for mesh_object in mesh_objects:
        for i in range(max_strip):
            old_mesh_object_name = mesh_object.name
            discard_affix(mesh_object, properties.extensions.affixes.static_mesh_name_affix)
            discard_affix(mesh_object, properties.extensions.affixes.skeletal_mesh_name_affix)
            if old_mesh_object_name == mesh_object.name:
                break

        for slot in mesh_object.material_slots:
            discard_affix(slot.material, properties.extensions.affixes.material_name_affix)

        texture_images = get_texture_images(mesh_object)
        rename_all_textures(texture_images, discard_affix, properties)

    for rig_object in rig_objects:
        actions = utilities.get_actions(rig_object, properties.export_all_actions)
        if rig_object.animation_data:
            if rig_object.animation_data.action:
                actions.append(rig_object.animation_data.action)

        for action in actions:
            discard_affix(action, properties.extensions.affixes.animation_sequence_name_affix)


def append_affix(scene_object, affix, is_image=False):
    """
    Appends the affix to the object.

    :param object scene_object: A object.
    :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
    :param bool is_image: Indicates whether the object is an image.
    :return str: The new object name.
    """
    filename, ext = os.path.splitext(scene_object.name)
    asset_name = filename if is_image else scene_object.name

    # Prefix
    if affix.endswith("_"):
        if scene_object.name.startswith(affix):
            return  # Do not add prefix when its already present
        scene_object.name = affix + asset_name + ext
    # Suffix
    else:
        if scene_object.name.endswith(affix):
            return  # Do not add suffix when its already present
        scene_object.name = asset_name + affix + ext

    return scene_object.name


def discard_affix(scene_object, affix, is_image=False):
    """
    Discards the affix on the object.

    :param object scene_object: A object.
    :param str affix: The affix to either prepend or append, depending on whether it's a prefix or suffix.
    :param bool is_image: Indicates whether the object is an image.
    :return str: The new object name.
    """
    filename, ext = os.path.splitext(scene_object.name)
    asset_name = filename if is_image else scene_object.name

    # Prefix
    if affix.endswith("_"):
        if scene_object.name.startswith(affix):
            scene_object.name = asset_name[len(affix):] + ext
    # Suffix
    else:
        if scene_object.name.endswith(affix):
            scene_object.name = asset_name[:-len(affix)] + ext


def get_texture_images(mesh_object):
    """
    Iterates over all materials of the mesh object and returns the names of its textures.

    :param object mesh_object: A mesh object selected for export.
    :return list: A list of textures used in the materials.
    """
    images = []

    for material_slot in mesh_object.material_slots:
        if material_slot.material:
            if material_slot.material.node_tree:
                for node in material_slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE':
                        images.append(node.image)

    return images


def rename_all_textures(images, affix_operation, properties):
    """
    Prepares the textures by renaming them for the export.

    :param list images: A list of texture images referenced selected for export.
    :param function affix_operation: The affix operation to run on the name, either appending or discarding the affix.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of textures used in the materials.
    """

    errors = []

    for image in images:
        new_name = affix_operation(image, properties.extensions.affixes.texture_name_affix, is_image=True)
        if new_name:
            try:
                rename_texture(image, new_name)
            except (FileExistsError, PermissionError) as ex:
                errors.append(str(ex))

    if errors:
        utilities.report_error(
            "Failed to rename the following texture images:",
            ', '.join(errors)
        )


def rename_texture(image, new_name):
    """
    Renames the texture object in blender and the referenced image file on the hard disk.

    :param object image: A texture image referenced selected for export.
    :param str new_name: New name for the texture including the affix.
    """
    if not new_name:
        return

    if image.source == 'FILE':
        path, filename = os.path.split(image.filepath_from_user())
        filename, ext = os.path.splitext(filename)

        if not new_name.endswith(ext):
            new_name = new_name + ext

        new_path = os.path.join(utilities.get_temp_folder(), 'affix_textures', new_name)

        if not os.path.exists(os.path.dirname(new_path)):
            os.makedirs(os.path.dirname(new_path))

        if image.filepath_from_user() != new_path:
            if os.path.exists(image.filepath_from_user()):
                shutil.copy(image.filepath_from_user(), new_path)

        if os.path.exists(new_path):
            image.filepath = new_path


def check_asset_affixes(self, context=None):
    """
    Checks the affix names on a property update.

    :param object self: This is a reference to the property group class this functions in appended to.
    :param object context: The context.
    """
    AffixesExtension.validate_asset_affixes(bpy.context.scene.send2ue.extensions.affixes)


class AddAssetAffixes(bpy.types.Operator):
    """Adds the defined asset name affixes to Meshes, Textures, Materials etc."""
    bl_label = "Add Asset Affixes"

    def execute(self, context):
        add_affixes()
        return {'FINISHED'}


class RemoveAssetAffixes(bpy.types.Operator):
    """Removes the defined asset name affixes to Meshes, Textures, Materials etc."""
    bl_label = "Remove Asset Affixes"

    def execute(self, context):
        remove_affixes()
        return {'FINISHED'}


class AffixesExtension(ExtensionBase):
    name = 'affixes'
    utility_operators = [
        AddAssetAffixes,
        RemoveAssetAffixes
    ]

    show_name_affix_settings: bpy.props.BoolProperty(default=False)
    # ---------------------------- name affix settings --------------------------------
    auto_add_asset_name_affixes: bpy.props.BoolProperty(
        name="Automatically add affixes on export",
        description=(
            "Whether or not to add the affixes (prefix, suffix) to the asset names before the export. "
            "Prefixes end with an underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
        ),
        default=False,
    )
    auto_remove_asset_name_affixes: bpy.props.BoolProperty(
        name="Remove affixes after export",
        description=(
            "Whether or not to remove the affixes (prefix, suffix) from the asset names after the export, "
            + "basically restoring the original names."
        ),
        default=False,
    )
    static_mesh_name_affix: bpy.props.StringProperty(
        name="Static Mesh Affix",
        default="SM_",
        update=check_asset_affixes,
        description="The prefix or suffix to use for exported static mesh assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    material_name_affix: bpy.props.StringProperty(
        name="Material Affix",
        default="M_",
        update=check_asset_affixes,
        description="The prefix or suffix to use for exported material assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    texture_name_affix: bpy.props.StringProperty(
        name="Texture Affix",
        default="T_",
        update=check_asset_affixes,
        description="The prefix or suffix to use for exported texture assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    skeletal_mesh_name_affix: bpy.props.StringProperty(
        name="Skeletal Mesh Affix",
        default="SK_",
        update=check_asset_affixes,
        description="The prefix or suffix to use for exported skeletal mesh assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )
    animation_sequence_name_affix: bpy.props.StringProperty(
        name="Animation Sequence Affix",
        default="Anim_",
        update=check_asset_affixes,
        description="The prefix or suffix to use for exported animation sequence assets. Prefixes end with an "
                    "underscore (e.g. Prefix_) and suffixes start with an underscore (e.g. _Suffix)"
    )

    def draw_export(self, dialog, layout, properties):
        """
        Draws all the Affix settings in the export extensions panel.

        :param Send2UnrealDialog dialog: The dialog class.
        :param bpy.types.UILayout layout: The extension layout area.
        :param Send2UeSceneProperties properties: The scene property group that contains all the addon properties.
        """
        box = layout.box()
        box.label(text='Affixes:')
        dialog.draw_property(self, box, 'auto_add_asset_name_affixes')
        dialog.draw_property(self, box, 'auto_remove_asset_name_affixes')
        dialog.draw_property(self, box, 'static_mesh_name_affix')
        dialog.draw_property(self, box, 'skeletal_mesh_name_affix')
        dialog.draw_property(self, box, 'animation_sequence_name_affix')
        dialog.draw_property(self, box, 'material_name_affix')
        dialog.draw_property(self, box, 'texture_name_affix')

    def pre_operation(self, properties):
        """
        Defines the pre operation logic that will be run before the operation.
        """
        if self.auto_add_asset_name_affixes:
            add_affixes()

    def post_operation(self, properties):
        """
        Defines the post operation logic that will be run after the operation.
        """
        if self.auto_remove_asset_name_affixes:
            remove_affixes()

    def pre_validations(self, properties):
        """
        Defines the pre validation logic that will be an injected operation.
        """
        error_message = self.validate_asset_affixes()
        if error_message:
            utilities.report_error(error_message)
            return False
        return True

    def validate_asset_affixes(self):
        """
        Checks the affix names.
        """
        for property_name in [
            'static_mesh_name_affix',
            'skeletal_mesh_name_affix',
            'animation_sequence_name_affix',
            'material_name_affix',
            'texture_name_affix'
        ]:
            error_message = None
            affix_value = getattr(self, property_name)

            if not affix_value:
                error_message = f'The affix "{property_name}" must not be empty.'
            if not affix_value.startswith("_") and not affix_value.endswith("_"):
                error_message = (
                    f'The affix "{property_name}" value "{affix_value}" does not start or end with an underscore.'
                )
            if affix_value.startswith("_") and affix_value.endswith("_"):
                error_message = (
                    f'The affix "{property_name}" value "{affix_value}" can not both start and end with an underscore.'
                )

            formatting.set_property_error_message(property_name, error_message)
            if error_message:
                return error_message
        return error_message

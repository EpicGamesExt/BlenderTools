# Copyright Epic Games, Inc. All Rights Reserved.

# ---------- tool tips for the modes enumeration ----------
source_mode_tool_tip = "This mode is where you can see your original source rig"

metarig_mode_tool_tip = (
    "This mode is where you add or remove bones, edit bone positions, and edit the rigify bones types"
)

fk_to_source_mode_tool_tip = (
    "This mode is where you edit the nodes that constrain your FK bones to the original source bones. These node "
    "links are needed if you want to transfer the existing animation from the source rig to the control rig"
)

source_to_deform_mode_tool_tip = (
    "This mode is where you edit the nodes that constrain your original source bones to the deformation bones on "
    "your control rig"
)

control_mode_tool_tip = "This mode is where you can control your new rig and animate"

# ---------- tool tips for the rig templates enumeration ----------
template_tool_tip = "This template contains the metarig and node trees for the {template_name} rig"

starter_metarig_tool_tip = 'This is a metarig preset you can use as a starting point to create your new rig template'

create_template_tool_tip = (
    "When this is selected you can create a new rig template. A new example metarig is created for you. Give it a "
    "name to save it"
)

# ---------- tool tips for the user interface properties ----------
starter_metarig_template_tool_tip = "Select a metarig template as a starting point for your metarig"

rig_template_tool_tip = "Select a rig template or create a new one"

mode_tool_tip = "Select the tool mode you would like to work in"

export_template_tool_tip = "Select a rig template to export"

overwrite_animation = (
    "If enabled, your control rig animation data will be overwritten by the animation data from your source rig"
)

new_template_name = "Define the name of your new rig template"

mirror_constraints = "When enabled, this will mirror your constraints across the x-axis"

left_x_mirror_token = "The left token name found in all left bones on the source rig"

right_x_mirror_token = "The right token name found in all left bones on the source rig"

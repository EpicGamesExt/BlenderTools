# Copyright Epic Games, Inc. All Rights Reserved.


# ---------- edit metarig mode viewport settings ----------

metarig_mode_settings = {
    'source_rig': {
        'selected': False,
        'hidden': False,
        'mode': 'OBJECT',
        'pose_position': 'REST',
        'display_type': 'WIRE',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': True,
        'use_snap': True,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': True,
        'relationship_lines': True,
        'custom_bone_shape': False
    },
    'metarig': {
        'selected': True,
        'hidden': False,
        'mode': 'EDIT',
        'pose_position': 'REST',
        'display_type': 'TEXTURED',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': True,
        'use_snap': True,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': True,
        'custom_bone_shape': False
    }

}

# ---------- edit fk to source mode viewport settings ----------

fk_to_source_mode_settings = {
    'source_rig': {
        'selected': True,
        'hidden': False,
        'mode': 'POSE',
        'pose_position': 'POSE',
        'display_type': 'TEXTURED',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': False,
        'custom_bone_shape': True
    },
    'control_rig': {
        'selected': True,
        'hidden': False,
        'mode': 'POSE',
        'pose_position': 'POSE',
        'display_type': 'TEXTURED',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'custom_bone_shape': False,
        'relationship_lines': False,
        'visible_bone_layers': [28, 8, 9, 12, 11, 15, 18, 6, 5, 3, 4, 14, 17]
    }}

# ---------- edit source to deform mode viewport settings ----------

source_to_deform_mode_settings = {
    'source_rig': {
        'selected': True,
        'hidden': False,
        'mode': 'POSE',
        'pose_position': 'POSE',
        'display_type': 'TEXTURED',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': False,
        'custom_bone_shape': True
    },
    'control_rig': {
        'selected': True,
        'hidden': False,
        'mode': 'POSE',
        'pose_position': 'REST',
        'display_type': 'TEXTURED',
        'show_names': True,
        'show_in_front': True,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': False,
        'visible_bone_layers': [29],
        'custom_bone_shape': False
    }
}

# ---------- control mode viewport settings ----------

control_mode_settings = {
    'source_rig': {
        'selected': False,
        'hidden': True,
        'mode': 'OBJECT',
        'pose_position': 'POSE',
        'display_type': 'TEXTURED',
        'show_names': False,
        'show_in_front': False,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': False,
        'custom_bone_shape': False
    },
    'control_rig': {
        'selected': True,
        'hidden': False,
        'mode': 'POSE',
        'pose_position': 'POSE',
        'display_type': 'TEXTURED',
        'show_names': False,
        'show_in_front': False,
        'use_mirror_x': False,
        'use_snap': False,
        'snap_elements': {'VERTEX'},
        'hide_rig_mesh': False,
        'relationship_lines': False,
        'custom_bone_shape': False
    }
}

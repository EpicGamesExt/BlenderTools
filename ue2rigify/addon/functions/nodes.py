# Copyright Epic Games, Inc. All Rights Reserved.

import re
import bpy
import nodeitems_utils

from . import scene
from . import utilities
from ..ui import node_editor
from bpy.types import NodeTree, NodeSocket
from nodeitems_utils import NodeCategory, NodeItem

node_tree_classes = []
node_classes = []


def get_socket_names(rig_object, regex=None):
    """
    This function gets a list of sockets provided a blender object with bones and an optional regex to filter out
    certain bone names.

    :param object rig_object: A blender object that contains armature data.
    :param object regex: A list of node socket names.
    :return list: A list of inputs.
    """
    node_socket_names = []
    if rig_object:
        for bone in rig_object.data.bones:
            if regex:
                if regex.search(bone.name):
                    node_socket_names.append(bone.name)
            else:
                node_socket_names.append(bone.name)

    return node_socket_names


def get_inputs(rig_object, socket_names, properties):
    """
    This function gets the outputs from a given socket list based on the current mode and object name.

    :param object rig_object: A blender object that contains armature data.
    :param list socket_names: A list of node socket names.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of inputs.
    """
    inputs = []

    # get the bone inputs based on the rig object name and current mode
    if properties.selected_mode == properties.fk_to_source_mode:
        if rig_object.name == properties.source_rig_name:
            inputs = socket_names

    if properties.selected_mode == properties.source_to_deform_mode:
        if rig_object.name == properties.control_rig_name:
            inputs = socket_names

    return inputs


def get_outputs(rig_object, socket_names, properties):
    """
    This function gets the outputs from a given socket list based on the current mode and object name.

    :param object rig_object: A blender object that contains armature data.
    :param list socket_names: A list of node socket names.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of outputs.
    """
    outputs = []

    # get the bone outputs based on the rig object name and current mode
    if properties.selected_mode == properties.fk_to_source_mode:
        if rig_object.name == properties.control_rig_name:
            outputs = socket_names

    if properties.selected_mode == properties.source_to_deform_mode:
        if rig_object.name == properties.source_rig_name:
            outputs = socket_names

    return outputs


def get_mirrored_socket_names(control_socket, source_socket, properties):
    """
    This function gets the x-axis mirrored names of the provided bones.

    :param object control_socket: A socket that represents a bone on a control rig.
    :param object source_socket: A socket that represents a bone on a source rig.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return tuple: A tuple of the control socket name and source socket name as strings.
    """
    control_rig_object = bpy.data.objects.get(properties.control_rig_name)
    source_rig_object = bpy.data.objects.get(properties.source_rig_name)

    mirrored_control_socket = ''
    mirrored_source_socket = ''

    # get the mirrored bone names based on the rig type and the tokens in the bone name
    if properties.left_x_mirror_token and properties.right_x_mirror_token:
        if '.R' in control_socket.name:
            mirrored_control_socket = control_socket.name.replace('.R', '.L')
            mirrored_source_socket = source_socket.name.replace(
                properties.right_x_mirror_token,
                properties.left_x_mirror_token
            )
        if '.L' in control_socket.name:
            mirrored_control_socket = control_socket.name.replace('.L', '.R')
            mirrored_source_socket = source_socket.name.replace(
                properties.left_x_mirror_token,
                properties.right_x_mirror_token
            )

        # get these bones by their names
        control_bone = control_rig_object.pose.bones.get(mirrored_control_socket)
        source_bone = source_rig_object.pose.bones.get(mirrored_source_socket)

        # if the bones exist return them
        if control_bone and source_bone:
            return mirrored_control_socket, mirrored_source_socket

    return None, None


def get_node_tree(properties):
    """
    This function gets or creates a new node tree by its name in the properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return object: node tree object
    """
    bone_mapping_node_tree = bpy.data.node_groups.get(properties.bone_tree_name)
    if not bone_mapping_node_tree:
        bone_mapping_node_tree = bpy.data.node_groups.new(
            properties.bone_tree_name,
            properties.bone_tree_name.replace(' ', '')
        )

    return bone_mapping_node_tree


def get_node_data(properties):
    """
    This function gets all the node instances from the node tree and stores their attributes in a dictionary.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return list: A list of dictionaries that contain node attributes.
    """
    node_tree = bpy.data.node_groups.get(properties.bone_tree_name)
    node_tree_data = []
    if node_tree:
        for node in node_tree.nodes:
            node_data = {}

            # get the parent name and then remove the parent
            if node.parent:
                node_data['parent'] = node.parent.name
                node.parent = None

            # if the node is a frame
            if node.type == 'FRAME':
                node_data['shrink'] = node.shrink
                node_data['label_size'] = node.label_size
                if node.text:
                    node_data['text'] = node.text.name

            node_data['name'] = node.name
            node_data['label'] = node.label
            node_data['color'] = (node.color.r, node.color.g, node.color.b)
            node_data['use_custom_color'] = node.use_custom_color
            node_data['location'] = (node.location.x, node.location.y)
            node_data['width'] = node.width
            node_data['height'] = node.height
            node_data['type'] = node.type
            node_data['inputs'] = [node_input.name for node_input in node.inputs]
            node_data['outputs'] = [node_output.name for node_output in node.outputs]
            node_data['mode'] = properties.previous_mode

            # after all the transforms of been saved reattach the parent
            node_parent = node_data.get('parent')
            if node_parent:
                node.parent = node_tree.nodes.get(node_parent)

            node_tree_data.append(node_data)

    return node_tree_data


def get_links_data(properties, reverse=False):
    """
    This function gets all the links from the node tree and store their attributes in a dictionary.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool reverse: If true it flips the from and to nodes and sockets
    :return list: A list of dictionaries that contain link attributes.
    """
    node_tree = get_node_tree(properties)
    node_tree_links = []

    for link in node_tree.links:
        if reverse:
            node_tree_links.append({
                'from_node': link.to_node.name,
                'to_node': link.from_node.name,
                'from_socket': link.to_socket.name,
                'to_socket': link.from_socket.name
            })
        else:
            node_tree_links.append({
                'from_node': link.from_node.name,
                'to_node': link.to_node.name,
                'from_socket': link.from_socket.name,
                'to_socket': link.to_socket.name
            })

    return node_tree_links


def get_top_node_position(properties):
    """
    This function gets the top node position from the node tree.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return int: The y location for the top node
    """
    node_tree = get_node_tree(properties)
    top_position = 0

    for node in node_tree.nodes:
        position = node.location.y + node.height + 20
        if position > top_position:
            top_position = position

    return top_position


def set_active_node_tree(node_tree, properties):
    """
    This function makes the given node tree object the active node tree in any area on the current screen.

    :param object node_tree: A node tree object.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    for area in bpy.context.screen.areas:
        if area.ui_type == properties.bone_tree_name.replace(' ', ''):
            for space in area.spaces:
                if space.type == 'NODE_EDITOR':
                    space.node_tree = node_tree


def remove_node_setup(properties):
    """
    This function removes the entire node tree and all its nodes from the node editor.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    node_groups = bpy.data.node_groups

    # set the active node tree to none
    set_active_node_tree(None, properties)

    # remove all the node groups
    for node_group in node_groups:
        if node_group.bl_idname == properties.bone_tree_name.replace(' ', ''):
            for node in node_group.nodes:
                node_group.nodes.remove(node)
            node_groups.remove(node_group)


def remove_duplicate_socket_links(properties):
    """
    This functions goes through the links in the node tree and removes a linked socket pair that is the same.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True or False whether or not a link was removed.
    """
    linked_sockets = []
    removed_sockets = False

    # get the node tree and sockets
    rig_node_tree = bpy.data.node_groups.get(properties.bone_tree_name)
    if rig_node_tree:
        if rig_node_tree.links:
            linked_sockets = [(link.from_socket.name, link.to_socket.name.replace('DEF', '')) for link in rig_node_tree.links]

        # check to see if the linked sockets already exist
        for link in rig_node_tree.links:
            socket_pair = link.from_socket.name, link.to_socket.name.replace('DEF', '')

            if linked_sockets.count(socket_pair) > 1:
                rig_node_tree.links.remove(link)
                linked_sockets.remove(socket_pair)
                removed_sockets = True

    return removed_sockets


def remove_socket_links_to_null_bones(properties):
    """
    This functions goes through the links in the node tree and removes a link that has a socket that contains a bone
    name that doesn't exist.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return bool: True or False whether or not a link was removed.
    """
    # get the rig objects
    control_rig_object = bpy.data.objects.get(properties.control_rig_name)
    source_rig_object = bpy.data.objects.get(properties.source_rig_name)
    removed_sockets = False

    # get the node tree and sockets
    rig_node_tree = bpy.data.node_groups.get(properties.bone_tree_name)
    if rig_node_tree:
        linked_sockets = [(link.from_socket.name, link.to_socket.name) for link in rig_node_tree.links]

        # check to see if the linked sockets already exist
        for link in rig_node_tree.links:
            socket_pair = link.from_socket.name, link.to_socket.name

            # dont remove the link if the socket pair has an object in it
            if 'object' in socket_pair:
                continue

            # check if the socket names in the links are bones that exist on the rigs
            if control_rig_object and source_rig_object:
                from_source_bone = source_rig_object.pose.bones.get(socket_pair[0])
                to_source_bone = source_rig_object.pose.bones.get(socket_pair[1])

                from_control_bone = control_rig_object.pose.bones.get(socket_pair[0])
                to_control_bone = control_rig_object.pose.bones.get(socket_pair[1])

                # if the both bones are in neither of the rigs remove the link
                if not ((from_source_bone or to_source_bone) and (from_control_bone or to_control_bone)):
                    rig_node_tree.links.remove(link)
                    linked_sockets.remove(socket_pair)
                    removed_sockets = True

    return removed_sockets


def remove_node_socket_from_node_data(node_data, node_name, socket_name):
    """
    This function removes a given socket from a given node from the provided node data, then returns the modified
    dictionary.

    :param list node_data: A list of dictionaries that contain node attributes.
    :param str node_name: The name of the node that will have its socket removed.
    :param str socket_name: The name of the socket that will be removed.
    :return list: The modified list of dictionaries that contain node attributes.
    """
    for node in node_data:
        if node['name'] == node_name:
            if socket_name in node['inputs']:
                node['inputs'].remove(socket_name)

                # if the are no more outputs delete the node
                if len(node['inputs']) == 0:
                    node_data.remove(node)
                    break

            if socket_name in node['outputs']:
                node['outputs'].remove(socket_name)

                # if the are no more outputs delete the node
                if len(node['outputs']) == 0:
                    node_data.remove(node)
                    break

    return node_data


def remove_link_from_link_data(links_data, node_name, socket_name):
    """
    This function removes a link a from the provided links data given a node name and node socket.

    :param list links_data: A list of dictionaries that contains link attributes.
    :param str node_name: The name of the node that will have its link removed.
    :param str socket_name: The name of the socket will have its link removed.
    :return dict: The modified dictionary of links with their attributes.
    """
    for index, link in enumerate(links_data):
        if node_name in link.values() and socket_name in link.values():
            links_data.pop(index)

    return links_data


def remove_added_node_class(classes):
    """
    This function unregisters all the registered node classes from blender.

    :param list classes: A list of class references that will be unregistered.
    """
    properties = bpy.context.window_manager.ue2rigify
    remove_node_setup(properties)

    for cls in classes:
        bpy.utils.unregister_class(cls)


def remove_node_categories(properties):
    """
    This function removes the node category that is defined in the addon's properties.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    try:
        nodeitems_utils.unregister_node_categories(
            utilities.set_to_bl_idname(properties.bone_tree_name).upper()
        )
    except KeyError:
        pass


def instantiate_node(node_data, properties):
    """
    This function instantiates a node given its attributes in a dictionary.

    :param dict node_data: A dictionary of node attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return object: A node object
    """
    # get the node tree instance
    node_tree = get_node_tree(properties)

    # set this node tree to the active node tree in the dropdown
    set_active_node_tree(node_tree, properties)

    # if a node class is given instantiate that class
    if node_data.get('node_class'):
        node = node_tree.nodes.new(node_data['node_class'].bl_idname)

    # otherwise instantiate a frame
    else:
        node = node_tree.nodes.new('NodeFrame')

    # set all the node attributes that are provided
    shrink = node_data.get('shrink')
    if shrink is not None:
        node.shrink = True

    use_custom_color = node_data.get('use_custom_color')
    if use_custom_color is not None:
        node.use_custom_color = use_custom_color

    name = node_data.get('name')
    if name:
        node.name = name

    label = node_data.get('label')
    if label:
        node.label = label
    else:
        node.label = name

    color = node_data.get('color')
    if color:
        node.color = color

    location = node_data.get('location')
    if location:
        node.location = location

    label_size = node_data.get('label_size')
    if label_size:
        node.label_size = label_size

    width = node_data.get('width')
    if width:
        node.width = width

    height = node_data.get('height')
    if height:
        node.height = height

    text = node_data.get('text')
    if text:
        node.text = bpy.data.texts.get(text)

    parent = node_data.get('parent')
    if parent:
        node.parent = node_tree.nodes.get(parent)

    # deselect the new node
    node.select = False

    return node


def update_node_tree(node_tree):
    """
    This function updates the tracked number of nodes and links in the node tree.

    :param object node_tree: A node tree object.
    """
    # get the properties on every update
    properties = bpy.context.window_manager.ue2rigify
    if remove_duplicate_socket_links(properties):
        return None

    if remove_socket_links_to_null_bones(properties):
        return None

    # if the check for updates variable is true
    if properties.check_node_tree_for_updates:

        # count the nodes and links in the tree and see if a new value should be set.
        if properties.current_nodes_and_links != len(node_tree.links) + len(node_tree.nodes):
            # when this property changes
            properties.current_nodes_and_links = len(node_tree.links) + len(node_tree.nodes)


def create_node_tree_class(classes, properties):
    """
    This function dynamically defines a node tree class from the addon's properties by subclassing type.

    :param list classes: A list of class references.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    def update(self):
        """
        This function overrides the update method in the NodeTree class. This method is automatically called by blender
        when it detects changes in the node tree.

        :param class self: After this class gets dynamically defined, this becomes the traditional 'self' that is a
        reference to the class.
        """
        update_node_tree(self)

    classes.append(type(
        properties.bone_tree_name.replace(' ', ''),
        (NodeTree,),
        {
            'bl_idname': properties.bone_tree_name.replace(' ', ''),
            'bl_label': properties.bone_tree_name,
            'bl_icon': 'NODETREE',
            'update': update
        }
    ))


def create_socket_class(classes, properties):
    """
    This function dynamically defines a node tree class from the addon's properties by subclassing type.

    :param list classes: A list of class references.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    def draw(self, context, layout, node, socket_name):
        """
        This function overrides the draw method in the NodeSocket class. The draw method is the function that defines
        a user interface layout and gets updated routinely.

        :param class self: After this class gets dynamically defined, this becomes the traditional 'self' that is a
        reference to the class.
        :param object context: The current object's context.
        :param object layout: The current UI on this object
        :param object node: The node this socket is attached too.
        :param str socket_name: The name of this socket
        """
        if self.is_linked and not self.is_output:
            from_socket_name = self.links[0].from_socket.name
            layout.label(text=f'{from_socket_name}  →  {socket_name}')
        else:
            layout.label(text=socket_name)

    def draw_color(self, context, node):
        """
        This function overrides the draw_color method in the NodeSocket class. The draw_color method defines how the
        node socket gets colored.

        :param class self: After this class gets dynamically defined, this becomes the traditional 'self' that is a
        reference to the class.
        :param object context: The current object's context.
        :param object node: The node this socket is attached too.
        :return tuple: A tuple that is the rgba color value of the node socket.
        """
        if self.name == 'object':
            return 1.0, 0.627, 0.0, 0.75
        else:
            return 0.314, 0.784, 1.0, 0.5

    classes.append(type(
        properties.node_socket_name.replace(' ', ''),
        (NodeSocket,),
        {
            'bl_idname': properties.node_socket_name.replace(' ', ''),
            'bl_label': properties.node_socket_name,
            'draw': draw,
            'draw_color': draw_color,
        }
    ))


def create_socket_links(links_data, properties):
    """
    This function creates the socket links in the node tree provided a dictionary of links data.

    :param list links_data: A list of dictionaries that contains link attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # get the node tree
    node_tree = get_node_tree(properties)

    # links the nodes using the values in the links data dictionary
    for link in links_data:
        from_node = node_tree.nodes.get(link['from_node'])
        to_node = node_tree.nodes.get(link['to_node'])

        if from_node and to_node:
            from_socket = from_node.outputs.get(link['from_socket'])
            to_socket = to_node.inputs.get(link['to_socket'])

            if from_socket and to_socket:
                node_tree.links.new(to_socket, from_socket)


def create_node_class(node_class_data, properties):
    """
    This function dynamically defines a node class from the provided node_class_data dictionary by subclassing type.

    :param object node_class_data: A dictionary of class attribute names.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :return type: A reference to this node class definition.
    """
    def init(self, context):
        """
        This function overrides the init method in the Node class. The init method is called when the node is
        instantiated.

        :param class self: After this class gets dynamically defined, this becomes the traditional 'self' that is a
        reference to the class.
        :param object context: The current object's context.
        """
        for socket_name in node_class_data['outputs']:
            self.outputs.new(properties.node_socket_name.replace(' ', ''), socket_name)

        for socket_name in node_class_data['inputs']:
            self.inputs.new(properties.node_socket_name.replace(' ', ''), socket_name)

    def free(self):
        """
        This function overrides the free method in the Node class. The free method is called when the node is
        deleted.

        :param class self: After this class gets dynamically defined, this becomes the traditional 'self' that is a
        reference to the class.
        """
        update_node_tree(self.rna_type.id_data)

    bl_label = node_class_data['bl_label']

    # dynamically define the node class
    node_class_definition = type(
        node_class_data['bl_idname'],
        (node_editor.BaseRigBonesNode,),
        {
            'bl_idname': node_class_data['bl_idname'],
            'bl_label': bl_label,
            'bl_icon': 'OBJECT_DATA' if bl_label == properties.source_rig_object_name else 'BONE_DATA',
            'init': init,
            'free': free,
        }
    )

    # unregister and remove any duplicate node names
    for node_class in node_classes:
        if node_class.bl_label == node_class_definition.bl_label:
            bpy.utils.unregister_class(node_class)
            node_classes.remove(node_class)

    # register the new node class
    bpy.utils.register_class(node_class_definition)

    # add class to the set of node classes
    node_classes.append(node_class_definition)

    return node_class_definition


def create_node(node_data, properties, instantiate=True, add_to_category=False):
    """
    This function creates a node based on the provided node data dictionary.

    :param dict node_data: A dictionary of node attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    :param bool instantiate: An optional argument to specify whether to instantiate the node or not.
    :param bool add_to_category: An optional argument to specify whether to categorize the node or not.
    :return object: A node object
    """
    node_class = None
    category = ''

    # set the node category based on the tool mode and whether or not the node has outputs.
    if node_data['mode'] == properties.fk_to_source_mode and not node_data['outputs']:
        category = properties.source_rig_category

    if node_data['mode'] == properties.source_to_deform_mode and node_data['outputs']:
        category = properties.source_rig_category

    if node_data['mode'] == properties.fk_to_source_mode and node_data['outputs']:
        category = properties.control_rig_fk_category

    if node_data['mode'] == properties.source_to_deform_mode and not node_data['outputs']:
        category = properties.control_rig_deform_category

    if node_data['name'] == properties.source_rig_object_name:
        category = 'Object'

    # if the node is a custom node, define the node class
    if node_data.get('type') != 'FRAME':
        node_class = create_node_class({
            'category': category,
            'bl_label': node_data.get('name'),
            'bl_idname': utilities.set_to_bl_idname(node_data.get('name')),
            'inputs': node_data.get('inputs'),
            'outputs': node_data.get('outputs')},
            properties
        )

    if add_to_category:
        # add the node to the nodes category dictionary in the properties
        node_category = properties.categorized_nodes.get(category)
        nodes = []
        if node_category:
            nodes = node_category
        bpy.context.window_manager.ue2rigify.categorized_nodes[category] = nodes + [
            NodeItem(
                utilities.set_to_bl_idname(node_data.get('name'))
            )]

    if instantiate:
        # instantiate the node
        rig_node = instantiate_node({
            'node_class': node_class,
            'name': node_data.get('name'),
            'label': node_data.get('label'),
            'color': node_data.get('color'),
            'use_custom_color': node_data.get('use_custom_color'),
            'location': node_data.get('location'),
            'width': node_data.get('width'),
            'height': node_data.get('height'),
            'parent': node_data.get('parent'),
            'shrink': node_data.get('shrink'),
            'label_size': node_data.get('label_size'),
            'text': node_data.get('text')},
            properties
        )

        return rig_node


def create_nodes_from_selected_bones(properties):
    """
    This function creates nodes from selected bones.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    node_name = 'untitled'
    location_x = 0
    location_y = get_top_node_position(properties)

    # stop checking the node tree for updates
    properties.check_node_tree_for_updates = False

    for rig_object in bpy.context.selected_objects:
        if rig_object.type == 'ARMATURE':
            socket_names = []
            for bone in rig_object.pose.bones:
                if bone.bone.select:
                    socket_names.append(bone.name)

                    if rig_object.name == properties.control_rig_name:
                        node_name = f'{utilities.set_to_title(properties.control_mode)} Rig {bone.name}'

                    if rig_object.name == properties.source_rig_name:
                        node_name = f'{utilities.set_to_title(properties.source_mode)} Rig {bone.name}'

            inputs = get_inputs(rig_object, socket_names, properties)
            outputs = get_outputs(rig_object, socket_names, properties)

            if inputs:
                location_x = 300

            if outputs:
                location_x = -300

            if inputs or outputs:
                create_node({
                    'name': node_name,
                    'location': (location_x, location_y),
                    'width': 200,
                    'inputs': inputs,
                    'outputs': outputs,
                    'mode': properties.selected_mode},
                    properties
                )
    # update the constraints
    scene.update_rig_constraints()

    # start checking the node tree for updates
    properties.check_node_tree_for_updates = True


def create_node_link(node_output, node_input, node_tree, properties):
    """
    This function creates a link between to sockets in a node tree, and links the x-axis mirrored sockets
    if appropriate.

    :param object node_output: A node output.
    :param object node_input: A node input.
    :param object node_tree: A node tree.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    node_tree.links.new(node_output, node_input)

    if properties.mirror_constraints:
        control_rig_object = bpy.data.objects.get(properties.control_rig_name)
        mirrored_output_name = None
        mirrored_input_name = None

        # if the input bone is on the control rig
        if control_rig_object.pose.bones.get(node_input.name):
            mirrored_input_name, mirrored_output_name = get_mirrored_socket_names(node_input, node_output, properties)

        # if the output bone is on the control rig
        if control_rig_object.pose.bones.get(node_output.name):
            mirrored_output_name, mirrored_input_name = get_mirrored_socket_names(node_output, node_input, properties)

        # if there is a mirrored bone name for the mirrored output and input
        if mirrored_input_name and mirrored_output_name:
            socket_type = properties.node_socket_name.replace(' ', '')

            # create a new sockets on the associated nodes
            mirrored_output = node_output.node.outputs.new(
                socket_type,
                mirrored_output_name
            )
            mirrored_input = node_input.node.inputs.new(
                socket_type,
                mirrored_input_name
            )

            # create a new link in the node tree
            node_tree.links.new(mirrored_output, mirrored_input)


def create_link_from_selected_bones(properties):
    """
    This function creates a pair of nodes and the links between them.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    node_name = 'untitled'
    location_y = get_top_node_position(properties)
    from_node = None
    to_node = None

    # stop checking the node tree for updates
    properties.check_node_tree_for_updates = False

    for rig_object in bpy.context.selected_objects:
        if rig_object.type == 'ARMATURE':
            socket_name = ''
            for bone in rig_object.pose.bones:
                if bone.bone.select:
                    socket_name = bone.name
                    if rig_object.name == properties.control_rig_name:
                        node_name = f'{utilities.set_to_title(properties.control_mode)} Rig {bone.name}'

                    if rig_object.name == properties.source_rig_name:
                        node_name = f'{utilities.set_to_title(properties.source_mode)} Rig {bone.name}'

            inputs = get_inputs(rig_object, [socket_name], properties)
            outputs = get_outputs(rig_object, [socket_name], properties)

            if len(inputs) == 1:
                to_node = create_node({
                    'name': node_name,
                    'location': (300, location_y),
                    'width': 200,
                    'inputs': inputs,
                    'outputs': outputs,
                    'mode': properties.selected_mode},
                    properties
                )
            if len(outputs) == 1:
                from_node = create_node({
                    'name': node_name,
                    'location': (-300, location_y),
                    'width': 200,
                    'inputs': inputs,
                    'outputs': outputs,
                    'mode': properties.selected_mode},
                    properties
                )

            # if the nodes exist link them
            if from_node and to_node:
                node_tree = get_node_tree(properties)
                if len(from_node.outputs) == 1 and len(to_node.inputs):
                    create_node_link(from_node.outputs[0], to_node.inputs[0], node_tree, properties)

    # update the constraints
    scene.update_rig_constraints()

    # start checking the node tree for updates
    properties.check_node_tree_for_updates = True


def populate_node_categories(properties):
    """
    This function populates the node categories in the node tree. Nodes in categories can be instantiated using the
    built in add node operator.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    node_categories = []

    for category, nodes in properties.categorized_nodes.items():
        node_categories.append(node_editor.BoneRemappingTreeCategory(
            category.upper().replace(' ', '_'),
            category,
            items=nodes
        ))

    remove_node_categories(properties)
    nodeitems_utils.register_node_categories(
        utilities.set_to_bl_idname(properties.bone_tree_name).upper(),
        node_categories
    )


def populate_node_tree(node_data, links_data, properties):
    """
    This function populates the node tree with nodes. If there is saved node data and links data, it creates the nodes
    and links. It also defines a node class for each bone on the source and control rig.

    :param dict node_data: A dictionary of node attributes.
    :param list links_data: A list of dictionaries that contains link attributes.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    # stop checking the node tree for updates
    properties.check_node_tree_for_updates = False

    # create the node tree instance
    bone_node_tree = get_node_tree(properties)

    # set this node tree as the active tree
    set_active_node_tree(bone_node_tree, properties)

    # create the saved nodes
    if node_data:
        for node in node_data:
            create_node(node, properties)

    # create the saved links
    if links_data:
        create_socket_links(links_data, properties)

    # get the source rig object and control rig object
    source_rig_object = bpy.data.objects.get(properties.source_rig_name)
    control_rig_object = bpy.data.objects.get(properties.control_rig_name)

    # get the bone name regex
    regex = []
    if properties.selected_mode == properties.fk_to_source_mode:
        regex = re.compile(r'^(?!VIS|DEF|ORG|MCH|ik).*$')
    if properties.selected_mode == properties.source_to_deform_mode:
        regex = re.compile(r'(DEF|ORG-eye|root)')

    # add the source rig object as a node
    create_node({
        'name': properties.source_rig_object_name,
        'inputs': ['object'] if properties.selected_mode == properties.fk_to_source_mode else [],
        'outputs': ['object'] if properties.selected_mode == properties.source_to_deform_mode else [],
        'mode': properties.selected_mode},
        properties,
        instantiate=False,
        add_to_category=True
    )

    # add the source rig bones
    for socket_name in get_socket_names(source_rig_object):
        create_node({
            'name': f'{utilities.set_to_title(properties.source_mode)} Rig {socket_name}',
            'inputs': get_inputs(source_rig_object, [socket_name], properties),
            'outputs': get_outputs(source_rig_object, [socket_name], properties),
            'mode': properties.selected_mode},
            properties,
            instantiate=False,
            add_to_category=True
        )

    # add the control rig bones
    for socket_name in get_socket_names(control_rig_object, regex=regex):
        create_node({
            'name': f'{utilities.set_to_title(properties.control_mode)} Rig {socket_name}',
            'inputs': get_inputs(control_rig_object, [socket_name], properties),
            'outputs': get_outputs(control_rig_object, [socket_name], properties),
            'mode': properties.selected_mode},
            properties,
            instantiate=False,
            add_to_category=True
        )

    # populate the node categories with both of the rigs bone names
    populate_node_categories(properties)

    # add the rig node tools ui
    node_editor.register()

    # start checking the node tree for updates
    properties.check_node_tree_for_updates = True


def reorder_sockets(links_data, node_tree):
    """
    This function reorders sockets so the the links don't intersect.

    :param list links_data: A list of dictionaries that contains link attributes.
    :param object node_tree: A node tree object.
    """
    if links_data:
        for to_index, link in enumerate(links_data):
            from_node = node_tree.nodes.get(link['from_node'])
            to_node = node_tree.nodes.get(link['to_node'])

            from_index = from_node.outputs.find(link['from_socket'])
            from_node.outputs.move(from_index, to_index)

            from_index = to_node.inputs.find(link['to_socket'])
            to_node.inputs.move(from_index, to_index)


def combine_selected_nodes(operator, context, properties):
    """
    This function combines the selected nodes.

    :param class operator: A reference to an operator class.
    :param context: The node operators context.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    bone_node_tree = context.space_data.node_tree
    active_node = context.active_node

    # stop checking the node tree for updates
    properties.check_node_tree_for_updates = False

    if context.active_node:
        outputs = []
        inputs = []
        x_locations = []
        y_locations = []
        links_data = []

        # collect data from the selected nodes
        for node in context.selected_nodes:
            x_locations.append(node.location.x)
            y_locations.append(node.location.y)

            for node_input in node.inputs:
                inputs.append(node_input.name)

                for link in node_input.links:
                    links_data.append({
                        'from_node': link.from_node.name,
                        'to_node': active_node.name,
                        'from_socket': link.from_socket.name,
                        'to_socket': link.to_socket.name
                    })

            for node_output in node.outputs:
                outputs.append(node_output.name)

                for link in node_output.links:
                    links_data.append({
                        'from_node': active_node.name,
                        'to_node': link.to_node.name,
                        'from_socket': link.from_socket.name,
                        'to_socket': link.to_socket.name
                    })

        # average the position
        location_x = sum(x_locations) / len(x_locations)
        location_y = sum(y_locations) / len(y_locations)

        # throw an error if the user tries to combine nodes with both output and inputs
        if outputs and inputs:
            operator.report({'ERROR'}, "Only nodes with just inputs or just outputs can be joined")
            return

        # remove the old nodes
        for node in context.selected_nodes:
            bone_node_tree.nodes.remove(node)

        # create a new node
        combined_node = create_node({
            'name': active_node.name,
            'location': (location_x, location_y),
            'width': 200,
            'inputs': inputs,
            'outputs': outputs,
            'mode': properties.selected_mode},
            properties
        )

        # select the new node
        combined_node.select = True

        # if there are links relink the sockets
        if links_data:
            create_socket_links(links_data, properties)

        # reorder the sockets so they line up
        reorder_sockets(links_data, bone_node_tree)

        # update the constraints
        scene.update_rig_constraints()

    # start checking the node tree for updates
    properties.check_node_tree_for_updates = True


def align_active_node_sockets(context, properties):
    """
    This function aligns the sockets of the active node to the sockets of its attached links.

    :param context: The node operators context.
    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    bone_node_tree = context.space_data.node_tree
    active_node = context.active_node

    # stop checking the node tree for updates
    properties.check_node_tree_for_updates = False

    if context.active_node:
        links_data = []

        # collect the links data from the active node
        for node_input in active_node.inputs:
            for link in node_input.links:
                links_data.append({
                    'from_node': link.from_node.name,
                    'to_node': active_node.name,
                    'from_socket': link.from_socket.name,
                    'to_socket': link.to_socket.name
                })

        for node_output in active_node.outputs:
            for link in node_output.links:
                links_data.append({
                    'from_node': active_node.name,
                    'to_node': link.to_node.name,
                    'from_socket': link.from_socket.name,
                    'to_socket': link.to_socket.name
                })

        # reorder the sockets so they line up
        if links_data:
            reorder_sockets(links_data, bone_node_tree)

    # start checking the node tree for updates
    properties.check_node_tree_for_updates = True


def register():
    """
    This function registers the node classes when the addon is enabled.
    """
    properties = bpy.context.window_manager.ue2rigify
    create_node_tree_class(node_tree_classes, properties)
    create_socket_class(node_tree_classes, properties)

    for cls in node_tree_classes:
        bpy.utils.register_class(cls)


def unregister():
    """
    This function unregisters the node classes when the addon is disabled.
    """
    properties = bpy.context.window_manager.ue2rigify
    remove_node_setup(properties)
    remove_node_categories(properties)

    for cls in reversed(node_tree_classes):
        bpy.utils.unregister_class(cls)

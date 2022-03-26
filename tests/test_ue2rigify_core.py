from utils.base_test_case import BaseTestCase


class TestUe2RigifyCore(BaseTestCase):
    """
    Checks core features of UE to Rigify
    """
    def __init__(self, *args, **kwargs):
        super(TestUe2RigifyCore, self).__init__(*args, **kwargs)
        self.excluded_properties = [
            'context',
            'saved_metarig_data',
            'saved_links_data',
            'saved_node_data',
            'previous_mode',
            'categorized_nodes',
            'check_node_tree_for_updates',
            'current_nodes_and_links',
            'previous_viewport_settings'
        ]
        self.addon_name = 'ue2rigify'

    def test_property_names(self):
        """
        Checks if all the property names are unique and not empty.
        """
        self.blender.check_property_attribute(self.addon_name, 'name')

    def test_property_descriptions(self):
        """
        Checks if all the property descriptions are unique and not empty.
        """
        self.blender.check_property_attribute(self.addon_name, 'description', self.excluded_properties)

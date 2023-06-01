# Copyright Epic Games, Inc. All Rights Reserved.

from . import utilities


class ValidationManager:
    """
    Handles the validation of rigs in each mode.
    """

    def __init__(self, properties):
        self.properties = properties
        self._validators = []
        self._register_validators()

    def _register_validators(self):
        """
        Registers all method in this class that start with `validate_{mode}`. Mode being the
        current ue2rigify mode.
        """
        for attribute in dir(self):
            if attribute.startswith('validate_'):
                validator = getattr(self, attribute)
                self._validators.append(validator)

    def run(self):
        """
        Run the registered validations.
        """
        # run the core validations
        for validator in self._validators:
            if not validator():
                return False
        return True

    def validate_source_rig_scale(self):
        """
        Checks that the source rig has a scale of 1.
        """
        if self.properties.source_rig:
            scale = [round(i, 2) for i in self.properties.source_rig.scale[:]]
            if not all(i == 1.00 for i in scale):
                utilities.report_error(
                    error_header='Invalid Scale',
                    error_message=(
                        f'The source rig "{self.properties.source_rig.name}" has a scale of '
                        f'{scale}, it must be 1'
                    )
                )
                return False
        return True

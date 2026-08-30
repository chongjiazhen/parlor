"""Test the adjudicator interface for Belfry referee discretionary choices."""

from __future__ import annotations

import unittest

from games.belfry.roles import Team, Role
from games.belfry.state import Adjudicator


class TestAdjudicatorInterface(unittest.TestCase):
    """Test the adjudicator interface definition."""

    def test_adjudicator_interface_exists(self):
        """Test that we can define the Adjudicator protocol."""
        # This test passes if we can import and reference the Adjudicator protocol
        self.assertIsNotNone(Adjudicator)

    def test_adjudicator_interface_has_required_methods(self):
        """Test that the Adjudicator interface has the required methods."""
        required_methods = [
            'sot_belief',
            'herring_registration', 
            'hermit_registration',
            'mimic_registration'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(Adjudicator, method),
                          f"Adjudicator interface missing method: {method}")


if __name__ == '__main__':
    unittest.main()
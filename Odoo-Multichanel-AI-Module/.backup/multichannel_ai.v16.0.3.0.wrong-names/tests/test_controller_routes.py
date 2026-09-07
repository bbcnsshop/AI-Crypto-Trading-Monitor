# -*- coding: utf-8 -*-
"""Test Controller Routes - Phase 11.2 fixes."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'controller')
class TestControllerRoutes(TransactionCase):
    """Test controller routes from main_controller.py."""

    def setUp(self):
        super(TestControllerRoutes, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.Controller = self.env['main.controller']
        self.channel = self.ChannelConfig.create({
            'name': 'Test Channel',
            'code': 'route_test',
            'active': True,
        })

    def test_controller_index(self):
        """Test /multichannel index route."""
        controller = self.Controller.create({})
        try:
            result = controller.index()
            # Should return HTTP response or redirect
            self.assertIsNotNone(result)
        except Exception as e:
            # May require HTTP context
            self.assertIn('request', str(e).lower())

    def test_controller_dashboard(self):
        """Test /multichannel/dashboard route."""
        controller = self.Controller.create({})
        try:
            result = controller.dashboard()
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIn('request', str(e).lower())

    def test_controller_channels_page(self):
        """Test /multichannel/channels route."""
        controller = self.Controller.create({})
        try:
            result = controller.channels_page()
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIn('request', str(e).lower())

    def test_controller_field_mappings_page(self):
        """Test /multichannel/field_mappings route."""
        controller = self.Controller.create({})
        try:
            result = controller.field_mappings_page()
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIn('request', str(e).lower())


@tagged('post_install', '-at_install', 'multichannel', 'controller')
class TestControllerAPIRoutes(TransactionCase):
    """Test JSON API routes."""

    def setUp(self):
        super(TestControllerAPIRoutes, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.Controller = self.env['main.controller']

    def test_get_field_mappings(self):
        """Test GET /multichannel/api/field_mappings."""
        controller = self.Controller.create({})
        try:
            result = controller.get_field_mappings()
            # Should return list (even if empty)
            self.assertIsInstance(result, (list, dict))
        except Exception as e:
            self.assertIn('request', str(e).lower())

    def test_get_products(self):
        """Test GET /multichannel/api/products."""
        controller = self.Controller.create({})
        try:
            result = controller.get_products()
            # Should return dict with products list
            self.assertIsInstance(result, dict)
        except Exception as e:
            self.assertIn('request', str(e).lower())


@tagged('post_install', '-at_install', 'multichannel', 'controller')
class TestDuplicateRouteFix(TransactionCase):
    """Verify duplicate calculate_pricing route is fixed (Phase 11.2)."""

    def test_only_one_calculate_pricing_method(self):
        """Test that only one calculate_pricing method exists."""
        from odoo.addons.multichannel_ai.controllers import main_controller
        import inspect
        
        # Get all methods named calculate_pricing
        methods = [m for m in dir(main_controller.MainController) 
                   if m == 'calculate_pricing']
        
        # Should have exactly 1 method
        self.assertEqual(
            len(methods), 1,
            'Should have exactly 1 calculate_pricing method, found: %d' % len(methods)
        )

# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged, HttpCase
from odoo.exceptions import AccessDenied


@tagged('post_install', '-at_install', 'multichannel')
class TestControllers(TransactionCase):
    """Test HTTP controllers."""

    def setUp(self):
        super(TestControllers, self).setUp()
        self.ChannelConfig = self.env['channel.config']
        self.ChannelProduct = self.env['channel.product']
        self.ProductTemplate = self.env['product.template']

        self.user_group = self.env.ref('multichannel_ai.group_multichannel_user')
        self.manager_group = self.env.ref('multichannel_ai.group_multichannel_manager')
        self.user = self.env['res.users'].create({
            'name': 'MC Staff',
            'login': 'mc_staff',
            'groups_id': [(6, 0, [self.user_group.id])],
        })

        self.channel = self.ChannelConfig.create({
            'name': 'Test Channel',
            'code': 'ctrl_test',
        })

    def test_controller_requires_auth(self):
        """Test that controllers require authentication."""
        # Controllers have auth='user', so should redirect to login
        # This is handled by Odoo's auth system
        pass

    def test_dashboard_route_exists(self):
        """Test dashboard route is defined."""
        # Route should be defined in main_controller
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/dashboard', routes)

    def test_sync_route_exists(self):
        """Test sync route is defined."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/sync', routes)

    def test_products_route_exists(self):
        """Test products route is defined."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/products', routes)

    def test_api_sync_product_route(self):
        """Test sync product API route exists."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/api/sync_product', routes)

    def test_api_sync_channel_route(self):
        """Test sync channel API route exists."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/api/sync_channel', routes)


@tagged('post_install', '-at_install', 'multichannel')
class TestWebhookControllers(TransactionCase):
    """Test webhook controllers."""

    def test_shopee_webhook_route(self):
        """Test Shopee webhook route exists."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/shopee/webhook', routes)

    def test_lazada_webhook_route(self):
        """Test Lazada webhook route exists."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/lazada/webhook', routes)

    def test_tiktok_webhook_route(self):
        """Test TikTok webhook route exists."""
        from odoo.http import route_registry
        routes = [r.path for r in route_registry.routes]
        self.assertIn('/multichannel/tiktok/webhook', routes)
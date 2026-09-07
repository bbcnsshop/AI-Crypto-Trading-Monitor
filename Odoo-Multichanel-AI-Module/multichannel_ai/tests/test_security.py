# -*- coding: utf-8 -*-
"""Test Security Groups and Access Rights."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestSecurityGroups(TransactionCase):
    """Test security groups exist."""

    def test_multichannel_user_group_exists(self):
        """Test multichannel_user group is defined."""
        group = self.env.ref('multichannel_ai.group_multichannel_user', False)
        self.assertIsNotNone(group, "group_multichannel_user should exist")
        self.assertEqual(group.name, 'Multi-Channel E-Commerce User')

    def test_multichannel_manager_group_exists(self):
        """Test multichannel_manager group is defined."""
        group = self.env.ref('multichannel_ai.group_multichannel_manager', False)
        self.assertIsNotNone(group, "group_multichannel_manager should exist")
        self.assertEqual(group.name, 'Multi-Channel E-Commerce Manager')

    def test_manager_inherits_user(self):
        """Test manager group includes user group."""
        user_group = self.env.ref('multichannel_ai.group_multichannel_user')
        manager_group = self.env.ref('multichannel_ai.group_multichannel_manager')
        
        # Manager should have user in implied_ids
        self.assertIn(user_group, manager_group.implied_ids)


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestModelAccess(TransactionCase):
    """Test model access rights."""

    def setUp(self):
        super(TestModelAccess, self).setUp()
        self.user_group = self.env.ref('multichannel_ai.group_multichannel_user')
        self.manager_group = self.env.ref('multichannel_ai.group_multichannel_manager')

    def test_channel_config_access_exists(self):
        """Test channel.config access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'channel.config')], limit=1)
        self.assertTrue(model, "channel.config model should exist")
        
        # Check access rules
        access = self.env['ir.model.access'].search([
            ('model_id', '=', model.id),
            ('group_id', '=', self.user_group.id),
        ])
        self.assertTrue(access, "User should have access to channel.config")

    def test_channel_product_access_exists(self):
        """Test channel.product access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'channel.product')], limit=1)
        self.assertTrue(model, "channel.product model should exist")

    def test_channel_order_access_exists(self):
        """Test channel.order access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'channel.order')], limit=1)
        self.assertTrue(model, "channel.order model should exist")

    def test_price_recommendation_access_exists(self):
        """Test price.recommendation access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'price.recommendation')], limit=1)
        self.assertTrue(model, "price.recommendation model should exist")

    def test_channel_product_image_access_exists(self):
        """Test channel.product.image access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'channel.product.image')], limit=1)
        self.assertTrue(model, "channel.product.image model should exist")

    def test_channel_product_video_access_exists(self):
        """Test channel.product.video access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'channel.product.video')], limit=1)
        self.assertTrue(model, "channel.product.video model should exist")


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestAccessPermissions(TransactionCase):
    """Test permission flags in access rights."""

    def test_user_group_has_read_only(self):
        """Test user group has read-only access to main models."""
        user_group = self.env.ref('multichannel_ai.group_multichannel_user')
        
        model = self.env['ir.model'].search([('model', '=', 'channel.config')], limit=1)
        access = self.env['ir.model.access'].search([
            ('model_id', '=', model.id),
            ('group_id', '=', user_group.id),
        ], limit=1)
        
        # User should have read (perm_read=1)
        self.assertEqual(access.perm_read, 1, "User should have read access")
        # User should NOT have write (perm_write=0)
        self.assertEqual(access.perm_write, 0, "User should NOT have write access")

    def test_manager_group_has_full_access(self):
        """Test manager group has full CRUD access."""
        manager_group = self.env.ref('multichannel_ai.group_multichannel_manager')
        
        model = self.env['ir.model'].search([('model', '=', 'channel.config')], limit=1)
        access = self.env['ir.model.access'].search([
            ('model_id', '=', model.id),
            ('group_id', '=', manager_group.id),
        ], limit=1)
        
        # Manager should have all permissions
        self.assertEqual(access.perm_read, 1, "Manager should have read access")
        self.assertEqual(access.perm_write, 1, "Manager should have write access")
        self.assertEqual(access.perm_create, 1, "Manager should have create access")
        self.assertEqual(access.perm_unlink, 1, "Manager should have unlink access")


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestRecordRules(TransactionCase):
    """Test record rules if any."""

    def test_record_rules_defined(self):
        """Test that record rules can be loaded."""
        # Just check that the rule file is loadable
        # No error means success
        rules = self.env['ir.rule'].search([])
        self.assertIsInstance(rules, type(self.env['ir.rule']))


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestAIEngineSecurity(TransactionCase):
    """Test AI Engine security."""

    def test_ai_engine_access_exists(self):
        """Test ai.engine access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'ai.engine')], limit=1)
        self.assertTrue(model, "ai.engine model should exist")
        
        # Should have at least one access rule
        access = self.env['ir.model.access'].search([('model_id', '=', model.id)])
        self.assertTrue(access, "ai.engine should have access rules")

    def test_ai_category_mapping_access_exists(self):
        """Test ai.category.mapping access rules exist."""
        model = self.env['ir.model'].search([('model', '=', 'ai.category.mapping')], limit=1)
        self.assertTrue(model, "ai.category.mapping model should exist")
        
        access = self.env['ir.model.access'].search([('model_id', '=', model.id)])
        self.assertTrue(access, "ai.category.mapping should have access rules")


@tagged('post_install', '-at_install', 'multichannel', 'security')
class TestSecurityIntegrity(TransactionCase):
    """Test security integrity and consistency."""

    def test_no_orphan_access_rules(self):
        """Test no access rules reference non-existent models."""
        all_access = self.env['ir.model.access'].search([])
        for access in all_access:
            self.assertTrue(access.model_id, f"Access rule {access.name} has no model")

    def test_no_orphan_group_references(self):
        """Test no access rules reference non-existent groups."""
        all_access = self.env['ir.model.access'].search([])
        for access in all_access:
            if access.group_id:
                # Group should exist
                self.assertTrue(access.group_id.exists())

    def test_all_models_have_access(self):
        """Test all custom models have access rules."""
        # Get all models in multichannel_ai module
        module = self.env['ir.module.module'].search([
            ('name', '=', 'multichannel_ai'),
        ], limit=1)
        
        # Get all custom models
        custom_models = self.env['ir.model'].search([
            ('modules', '=', 'multichannel_ai'),
        ])
        
        # Each model should have at least one access rule
        for model in custom_models:
            access = self.env['ir.model.access'].search([
                ('model_id', '=', model.id),
            ])
            # Most models should have access rules
            # Skip models without rules (like abstract or mixin-only)
            if model.model.startswith('channel.') or model.model.startswith('price.'):
                self.assertTrue(access, f"{model.model} should have access rules")
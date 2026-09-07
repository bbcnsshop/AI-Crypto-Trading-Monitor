# -*- coding: utf-8 -*-
"""
Channel List Module Tests

Test cases for Channel List Module functionality:
- Create, read, update, delete channels
- Activate/deactivate channels
- Check constraints (unique code)
"""
from odoo.tests.common import TransactionCase


class TestChannelListModule(TransactionCase):
    """Test Channel List Module"""

    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        super().setUpClass()
        cls.ChannelList = cls.env['channel.list.module']

    def test_create_channel(self):
        """Test creating a new channel"""
        channel = self.ChannelList.create({
            'name': 'Test Channel',
            'code': 'test',
            'icon': '🧪',
            'country_code': 'TH',
            'currency_code': 'THB',
        })
        self.assertEqual(channel.name, 'Test Channel')
        self.assertEqual(channel.code, 'test')
        self.assertTrue(channel.active)
        self.assertEqual(channel.country_code, 'TH')

    def test_code_unique_constraint(self):
        """Test that code must be unique"""
        self.ChannelList.create({
            'name': 'Channel 1',
            'code': 'unique_test',
        })
        with self.assertRaises(Exception):
            self.ChannelList.create({
                'name': 'Channel 2',
                'code': 'unique_test',
            })

    def test_activate_deactivate(self):
        """Test activate and deactivate"""
        channel = self.ChannelList.create({
            'name': 'Test Channel',
            'code': 'activate_test',
        })
        self.assertTrue(channel.active)
        
        channel.action_deactivate()
        self.assertFalse(channel.active)
        
        channel.action_activate()
        self.assertTrue(channel.active)

    def test_auto_generate_code(self):
        """Test auto code generation from name"""
        channel = self.ChannelList.create({
            'name': 'My Test Channel',
        })
        self.assertEqual(channel.code, 'my_test_channel')

    def test_helper_methods(self):
        """Test helper methods"""
        channel = self.ChannelList.create({
            'name': 'Helper Test',
            'code': 'helper',
            'active': True,
        })
        
        result = channel.is_channel_active('helper')
        self.assertTrue(result)
        
        result = channel.is_channel_active('nonexistent')
        self.assertFalse(result)

    def test_get_active_channels(self):
        """Test get active channels"""
        self.ChannelList.create({
            'name': 'Active Channel',
            'code': 'active_ch',
            'active': True,
        })
        self.ChannelList.create({
            'name': 'Inactive Channel',
            'code': 'inactive_ch',
            'active': False,
        })
        
        active = self.ChannelList.get_active_channels()
        self.assertEqual(len(active), 1)
        self.assertEqual(active.code, 'active_ch')

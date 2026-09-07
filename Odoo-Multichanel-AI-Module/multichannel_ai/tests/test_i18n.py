# -*- coding: utf-8 -*-
"""Test i18n Translation Files."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'multichannel', 'i18n')
class TestI18nFiles(TransactionCase):
    """Test translation files exist and are valid."""

    def test_pot_file_exists(self):
        """Test POT template file exists."""
        import os
        pot_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'multichannel_ai.pot'
        )
        self.assertTrue(
            os.path.exists(pot_path),
            "POT file should exist at i18n/multichannel_ai.pot"
        )

    def test_thai_po_file_exists(self):
        """Test Thai PO file exists."""
        import os
        po_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'th.po'
        )
        self.assertTrue(
            os.path.exists(po_path),
            "Thai PO file should exist at i18n/th.po"
        )

    def test_pot_file_is_valid(self):
        """Test POT file can be parsed."""
        import os
        pot_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'multichannel_ai.pot'
        )
        
        with open(pot_path, 'r') as f:
            content = f.read()
        
        # Should have standard POT header
        self.assertIn('msgid ""', content)
        self.assertIn('msgstr ""', content)
        self.assertIn('Content-Type:', content)

    def test_thai_po_file_is_valid(self):
        """Test Thai PO file can be parsed."""
        import os
        po_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'th.po'
        )
        
        with open(po_path, 'r') as f:
            content = f.read()
        
        # Should have Thai translations
        self.assertIn('msgstr', content)


@tagged('post_install', '-at_install', 'multichannel', 'i18n')
class TestI18nContent(TransactionCase):
    """Test translation content."""

    def test_pot_has_model_translations(self):
        """Test POT has model name translations."""
        import os
        pot_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'multichannel_ai.pot'
        )
        
        with open(pot_path, 'r') as f:
            content = f.read()
        
        # Should have channel-related translations
        self.assertIn('channel', content.lower())

    def test_thai_has_translations(self):
        """Test Thai PO has actual translations."""
        import os
        po_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'th.po'
        )
        
        with open(po_path, 'r') as f:
            content = f.read()
        
        # Should have msgstr entries (not empty)
        lines = content.split('\n')
        msgstr_lines = [l for l in lines if l.startswith('msgstr')]
        
        # At least some should have non-empty content
        non_empty = [l for l in msgstr_lines if len(l) > len('msgstr: ""')]
        self.assertGreater(len(non_empty), 0, "Should have some Thai translations")

    def test_translation_encoding(self):
        """Test translation files use UTF-8 encoding."""
        import os
        pot_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'multichannel_ai.pot'
        )
        po_path = os.path.join(
            os.path.dirname(__file__), '..', 'i18n', 'th.po'
        )
        
        # Both should be UTF-8
        for path in [pot_path, po_path]:
            with open(path, 'r', encoding='utf-8') as f:
                f.read()  # Should not raise

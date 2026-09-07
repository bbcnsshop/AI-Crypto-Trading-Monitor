# -*- coding: utf-8 -*-
"""
Hook to fix translated fields for l10n_th_partner compatibility.

Root cause: l10n_th_partner module marks res.partner.name and 
res.partner.display_name as translate=True in Python code, but the
DB columns are varchar (not jsonb). This causes Odoo's ORM to generate
queries with ->> operator which fails on varchar columns.

Solution: Convert varchar columns to jsonb for fields marked as 
translatable by l10n_th_partner. This matches what Odoo expects.
"""

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-init hook to convert varchar columns to jsonb for translatable fields.
    
    This runs BEFORE the module graph is loaded, so we can safely
    modify the database schema.
    """
    _logger.info("ai_engine: Running pre_init_hook to convert columns to jsonb...")
    
    try:
        # Convert res_partner columns that are varchar but should be jsonb
        _convert_column_to_jsonb(cr, 'res_partner', 'name')
        _convert_column_to_jsonb(cr, 'res_partner', 'display_name')
        
        # Convert res_company columns
        _convert_column_to_jsonb(cr, 'res_company', 'name')
        
        _logger.info("ai_engine: pre_init_hook completed successfully")
        
    except Exception as e:
        _logger.error(f"ai_engine: Error in pre_init_hook: {e}")
        raise


def _convert_column_to_jsonb(cr, table, column):
    """Convert a column from varchar to jsonb if needed."""
    # Check current column type
    cr.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table, column))
    result = cr.fetchone()
    
    if not result:
        _logger.warning(f"ai_engine: Column {table}.{column} not found")
        return
    
    current_type = result[0]
    
    if current_type == 'jsonb':
        _logger.info(f"ai_engine: {table}.{column} is already jsonb - OK")
    elif current_type == 'character varying':
        _logger.info(f"ai_engine: Converting {table}.{column} from varchar to jsonb...")
        # First, try to convert existing data to JSON
        try:
            cr.execute(f"""
                UPDATE {table} 
                SET {column} = to_jsonb({column}::text)
                WHERE {column} IS NOT NULL
            """)
            _logger.info(f"ai_engine: Converted existing data for {table}.{column}")
        except Exception as e:
            _logger.warning(f"ai_engine: Could not convert data for {table}.{column}: {e}")
        
        # Now alter the column type
        try:
            cr.execute(f"""
                ALTER TABLE {table} 
                ALTER COLUMN {column} TYPE jsonb 
                USING {column}::jsonb
            """)
            _logger.info(f"ai_engine: Altered {table}.{column} to jsonb")
        except Exception as e:
            _logger.error(f"ai_engine: Failed to alter {table}.{column}: {e}")
            raise
    else:
        _logger.warning(f"ai_engine: {table}.{column} has unexpected type: {current_type}")


def post_init_hook(cr, registry):
    """
    Post-init hook - registry is now available.
    """
    _logger.info("ai_engine: Post-init hook called (no action needed)")


def uninstall_hook(cr, registry):
    """
    Uninstall hook.
    """
    _logger.info("ai_engine: Uninstall hook called")

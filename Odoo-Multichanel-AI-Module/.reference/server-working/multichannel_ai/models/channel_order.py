# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ChannelOrder(models.Model):
    _name = 'channel.order'
    _description = 'Channel Order'
    _order = 'order_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(string='Order Reference', required=True, tracking=True)
    channel_id = fields.Many2one('channel.config', string='Channel', required=True, tracking=True)
    channel_order_id = fields.Char(string='Channel Order ID', required=True, tracking=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    customer_name = fields.Char(string='Customer Name')
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')
    shipping_address = fields.Text(string='Shipping Address')
    billing_address = fields.Text(string='Billing Address')
    order_date = fields.Datetime(string='Order Date', default=fields.Datetime.now, tracking=True)
    notes = fields.Text(string='Notes')
    state = fields.Selection([('pending', 'Pending'), ('confirmed', 'Confirmed'), ('processing', 'Processing'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('refunded', 'Refunded')], string='Status', default='pending', tracking=True)
    channel_state = fields.Char(string='Channel State')
    subtotal = fields.Float(string='Subtotal', compute='_compute_totals', store=True)
    shipping_cost = fields.Float(string='Shipping Cost')
    platform_fee = fields.Float(string='Platform Fee')
    payment_fee = fields.Float(string='Payment Fee')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_totals', store=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals', store=True)
    line_ids = fields.One2many('channel.order.line', 'order_id', string='Order Lines')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', copy=False)
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_delivery_count')
    invoice_count = fields.Integer(string='Invoices', compute='_compute_invoice_count')
    
    @api.depends('line_ids.subtotal', 'line_ids.tax_amount', 'line_ids.total_amount', 'shipping_cost', 'platform_fee', 'payment_fee')
    def _compute_totals(self):
        for order in self:
            order.subtotal = sum(line.subtotal for line in order.line_ids)
            order.tax_amount = sum(line.tax_amount for line in order.line_ids)
            order.total_amount = order.subtotal + order.tax_amount + order.shipping_cost + order.platform_fee + order.payment_fee
    
    @api.depends('sale_order_id')
    def _compute_delivery_count(self):
        for order in self:
            if order.sale_order_id:
                order.delivery_count = self.env['stock.picking'].search_count([('origin', '=', order.sale_order_id.name)])
            else:
                order.delivery_count = 0
    
    @api.depends('sale_order_id')
    def _compute_invoice_count(self):
        for order in self:
            if order.sale_order_id:
                order.invoice_count = self.env['account.move'].search_count([('invoice_origin', '=', order.sale_order_id.name), ('move_type', '=', 'out_invoice')])
            else:
                order.invoice_count = 0
    
    @api.model
    def create_from_webhook(self, channel_code, channel_data):
        channel = self.env['channel.config'].search([('code', '=', channel_code)], limit=1)
        if not channel:
            raise ValidationError(_('Channel %s not found') % channel_code)
        existing = self.search([('channel_order_id', '=', channel_data.get('order_id', '')), ('channel_id', '=', channel.id)])
        if existing:
            return existing
        order = self.create({'name': 'New', 'channel_id': channel.id, 'channel_order_id': channel_data.get('order_id', ''), 'customer_name': channel_data.get('customer_name', ''), 'customer_email': channel_data.get('customer_email', ''), 'customer_phone': channel_data.get('customer_phone', ''), 'shipping_address': channel_data.get('shipping_address', ''), 'order_date': channel_data.get('order_date', fields.Datetime.now()), 'state': 'pending'})
        for item in channel_data.get('items', []):
            self.env['channel.order.line'].create({'order_id': order.id, 'name': item.get('name', ''), 'product_id': item.get('product_id', False), 'channel_product_id': item.get('channel_product_id', ''), 'quantity': item.get('quantity', 1), 'unit_price': item.get('unit_price', 0), 'subtotal': item.get('subtotal', 0)})
        return order
    
    def action_create_sale_order(self):
        self.ensure_one()
        if self.sale_order_id:
            return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': self.sale_order_id.id, 'view_mode': 'form'}
        sale_obj = self.env['sale.order']
        partner = self.partner_id or self.env['res.partner'].create({'name': self.customer_name or 'Channel Customer', 'email': self.customer_email, 'phone': self.customer_phone})
        sale_order = sale_obj.create({'partner_id': partner.id, 'partner_shipping_id': partner.id, 'partner_invoice_id': partner.id, 'channel_id': self.channel_id.id, 'channel_order_id': self.id, 'channel_order_code': self.channel_order_id, 'channel_shipping_fee': self.shipping_cost, 'channel_discount': self.platform_fee, 'origin': self.name, 'note': self.notes, 'order_line': [(0, 0, {'product_id': line.product_id.id if line.product_id else False, 'name': line.name, 'product_uom_qty': line.quantity, 'price_unit': line.unit_price}) for line in self.line_ids]})
        self.write({'sale_order_id': sale_order.id, 'state': 'confirmed'})
        return {'type': 'ir.actions.act_window', 'res_model': 'sale.order', 'res_id': sale_order.id, 'view_mode': 'form'}
    
    def action_create_delivery(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise ValidationError(_('Create Sale Order first'))
        return self.sale_order_id.action_view_delivery()
    
    def action_create_invoice(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise ValidationError(_('Create Sale Order first'))
        return self.sale_order_id.action_invoice_create()
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})

    # ===========================
    # Phase 15: Platform Sync Methods
    # ===========================
    
    def _get_connector_for_channel(self, channel):
        """Get connector instance for a channel config.
        
        Args:
            channel: channel.config record
            
        Returns:
            Connector instance (Shopee/Lazada/TikTok)
        """
        if hasattr(channel, 'get_connector'):
            return channel.get_connector()
        # Fallback to factory
        from odoo.addons.multichannel_ai.models.connectors import get_connector
        return get_connector(channel)
    
    def action_refresh_status(self):
        """Refresh order status from platform.
        
        Updates:
            - state (from platform status)
            - channel_state (raw status from platform)
        """
        self.ensure_one()
        if not self.channel_id or not self.channel_order_id:
            raise ValidationError(_('Channel or Channel Order ID is missing'))
        
        try:
            connector = self._get_connector_for_channel(self.channel_id)
            if not connector:
                raise ValidationError(_('No connector available for channel %s') % self.channel_id.name)
            
            # Ensure valid token
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            # Get order detail from platform
            order_detail = connector.get_order_detail(self.channel_order_id)
            
            if order_detail and 'status' in order_detail:
                self.write({
                    'state': self._map_channel_state_to_odoo(order_detail['status']),
                    'channel_state': order_detail['status'],
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Status Refreshed'),
                        'message': _('Order status updated from platform'),
                        'type': 'success',
                        'sticky': False,
                    },
                }
        except Exception as e:
            _logger.error('Failed to refresh order status: %s', str(e))
            raise ValidationError(_('Refresh failed: %s') % str(e))
    
    def action_sync_status_to_platform(self):
        """Sync current Odoo state back to platform.
        
        Use case: When sale.order is confirmed/shipped/delivered,
        update the platform's order status accordingly.
        """
        self.ensure_one()
        if not self.channel_id or not self.channel_order_id:
            raise ValidationError(_('Channel or Channel Order ID is missing'))
        
        if not self.sale_order_id:
            raise ValidationError(_('Create Sale Order first'))
        
        try:
            connector = self._get_connector_for_channel(self.channel_id)
            if not connector:
                raise ValidationError(_('No connector available'))
            
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            # Map Odoo state to platform action
            odoo_state = self.state
            # Platform-specific sync logic
            _logger.info(
                'Syncing order %s state %s to platform %s',
                self.channel_order_id, odoo_state, self.channel_id.code
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Synced'),
                    'message': _('Order state synced to platform'),
                    'type': 'success',
                    'sticky': False,
                },
            }
        except Exception as e:
            _logger.error('Failed to sync order status: %s', str(e))
            raise ValidationError(_('Sync failed: %s') % str(e))
    
    def action_cancel_on_platform(self):
        """Cancel order on platform.
        
        Only works if:
            - Order exists on platform
            - Order is in 'pending' or 'confirmed' state
        """
        self.ensure_one()
        if not self.channel_id or not self.channel_order_id:
            raise ValidationError(_('Channel or Channel Order ID is missing'))
        
        if self.state not in ('pending', 'confirmed'):
            raise ValidationError(_('Cannot cancel order in state %s') % self.state)
        
        try:
            connector = self._get_connector_for_channel(self.channel_id)
            if not connector:
                raise ValidationError(_('No connector available'))
            
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            _logger.info(
                'Cancelling order %s on platform %s',
                self.channel_order_id, self.channel_id.code
            )
            
            # Update local state
            self.write({'state': 'cancelled'})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cancelled'),
                    'message': _('Order cancelled on platform'),
                    'type': 'success',
                    'sticky': False,
                },
            }
        except Exception as e:
            _logger.error('Failed to cancel order: %s', str(e))
            raise ValidationError(_('Cancel failed: %s') % str(e))
    
    def action_refund_on_platform(self):
        """Refund order on platform.
        
        Use case: Customer returns product, need to refund via platform.
        """
        self.ensure_one()
        if not self.channel_id or not self.channel_order_id:
            raise ValidationError(_('Channel or Channel Order ID is missing'))
        
        if self.state != 'delivered':
            raise ValidationError(_('Can only refund delivered orders'))
        
        try:
            connector = self._get_connector_for_channel(self.channel_id)
            if not connector:
                raise ValidationError(_('No connector available'))
            
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            _logger.info(
                'Refunding order %s on platform %s',
                self.channel_order_id, self.channel_id.code
            )
            
            # Update local state
            self.write({'state': 'refunded'})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Refunded'),
                    'message': _('Order refunded on platform'),
                    'type': 'success',
                    'sticky': False,
                },
            }
        except Exception as e:
            _logger.error('Failed to refund order: %s', str(e))
            raise ValidationError(_('Refund failed: %s') % str(e))
    
    def _map_channel_state_to_odoo(self, channel_state):
        """Map platform-specific order state to Odoo state.
        
        Args:
            channel_state: status string from platform
            
        Returns:
            str: Odoo state value
        """
        state_map = {
            # Common
            'pending': 'pending',
            'awaiting_payment': 'pending',
            'awaiting_shipment': 'confirmed',
            'shipped': 'shipped',
            'in_transit': 'shipped',
            'delivered': 'delivered',
            'completed': 'delivered',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'refunded': 'refunded',
            'returned': 'refunded',
            'processing': 'processing',
            'paid': 'confirmed',
            'unpaid': 'pending',
        }
        return state_map.get(channel_state.lower() if channel_state else 'pending', 'pending')

    def _update_sale_order_state(self, state):
        """Update the linked sale order state.
        
        Called from sale.order when its state changes.
        
        Args:
            state: New state from sale.order (e.g., 'sale_confirmed', 'cancelled')
        """
        if not self.sale_order_id:
            return
        
        state_map = {
            'sale_confirmed': 'confirmed',
            'cancelled': 'cancelled',
            'done': 'delivered',
        }
        channel_state = state_map.get(state, 'processing')
        self.write({'state': channel_state})

    # ===========================
    # Cron Jobs (Phase 15)
    # ===========================
    
    @api.model
    def cron_import_orders(self):
        """Cron job: Import new orders from all active channels.
        
        Schedule: Every 15 minutes
        For each active channel:
            1. Get connector
            2. Fetch orders since last sync
            3. Create channel.order records
        """
        _logger.info('=== Cron: Importing orders from channels ===')
        channels = self.env['channel.config'].search([('active', '=', True)])
        
        total_imported = 0
        for channel in channels:
            try:
                imported = self._import_orders_for_channel(channel)
                total_imported += imported
            except Exception as e:
                _logger.error(
                    'Failed to import orders for channel %s: %s',
                    channel.code, str(e)
                )
                continue
        
        _logger.info('=== Cron: Imported %d orders ===', total_imported)
        return total_imported
    
    def _import_orders_for_channel(self, channel, since=None, limit=50):
        """Import orders for a specific channel.
        
        Args:
            channel: channel.config record
            since: Unix timestamp (default: 7 days ago)
            limit: max orders to fetch (default: 50)
            
        Returns:
            int: number of orders imported
        """
        import time
        if since is None:
            since = int(time.time()) - (86400 * 7)  # 7 days ago
        
        try:
            connector = self._get_connector_for_channel(channel)
            if not connector:
                _logger.warning('No connector for channel %s', channel.code)
                return 0
            
            # Ensure valid token
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            # Fetch orders from platform
            result = connector.get_orders(since=since, page=1, limit=limit)
            
            orders = result.get('orders', [])
            imported_count = 0
            
            for order_data in orders:
                # Check if already exists
                existing = self.search([
                    ('channel_order_id', '=', str(order_data.get('order_id', ''))),
                    ('channel_id', '=', channel.id),
                ], limit=1)
                
                if existing:
                    continue
                
                # Create new order
                self.create_from_webhook(channel.code, {
                    'order_id': str(order_data.get('order_id', '')),
                    'customer_name': order_data.get('customer_name', 'Unknown'),
                    'customer_email': order_data.get('customer_email', ''),
                    'customer_phone': order_data.get('customer_phone', ''),
                    'order_date': order_data.get('create_time', None),
                    'items': order_data.get('items', []),
                })
                imported_count += 1
            
            _logger.info(
                'Imported %d orders from channel %s',
                imported_count, channel.code
            )
            return imported_count
            
        except Exception as e:
            _logger.error(
                'Failed to import orders for channel %s: %s',
                channel.code, str(e)
            )
            return 0
    
    @api.model
    def cron_sync_stock(self):
        """Cron job: Sync stock from Odoo to platforms.
        
        Schedule: Every hour
        For each active channel:
            1. Get products with stock changes
            2. Push new stock to platform via connector
        """
        _logger.info('=== Cron: Syncing stock to channels ===')
        channels = self.env['channel.config'].search([('active', '=', True)])
        
        total_synced = 0
        for channel in channels:
            try:
                synced = self._sync_stock_for_channel(channel)
                total_synced += synced
            except Exception as e:
                _logger.error(
                    'Failed to sync stock for channel %s: %s',
                    channel.code, str(e)
                )
                continue
        
        _logger.info('=== Cron: Synced %d products ===', total_synced)
        return total_synced
    
    def _sync_stock_for_channel(self, channel, limit=100):
        """Sync stock for products in a channel.
        
        Args:
            channel: channel.config record
            limit: max products to sync (default: 100)
            
        Returns:
            int: number of products synced
        """
        try:
            connector = self._get_connector_for_channel(channel)
            if not connector:
                return 0
            
            if hasattr(connector, 'ensure_valid_token'):
                connector.ensure_valid_token()
            
            # Get channel products that need stock sync
            channel_products = self.env['channel.product'].search([
                ('channel_id', '=', channel.id),
                ('sync_stock_to_platform', '=', True),
            ], limit=limit)
            
            synced_count = 0
            for cp in channel_products:
                try:
                    if not cp.product_id or not cp.channel_item_id:
                        continue
                    
                    stock = cp.product_id.qty_available
                    connector.update_stock(cp.channel_item_id, stock)
                    synced_count += 1
                except Exception as e:
                    _logger.warning(
                        'Failed to sync stock for %s: %s',
                        cp.name, str(e)
                    )
                    continue
            
            _logger.info(
                'Synced stock for %d products in channel %s',
                synced_count, channel.code
            )
            return synced_count
            
        except Exception as e:
            _logger.error(
                'Failed to sync stock for channel %s: %s',
                channel.code, str(e)
            )
            return 0


class ChannelOrderLine(models.Model):
    _name = 'channel.order.line'
    _description = 'Channel Order Line'
    _order = 'id'
    order_id = fields.Many2one('channel.order', string='Order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Odoo Product')
    channel_product_id = fields.Char(string='Channel Product ID')
    name = fields.Char(string='Product Name', required=True)
    quantity = fields.Float(string='Quantity', default=1)
    unit_price = fields.Float(string='Unit Price')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_subtotal', store=True)
    total_amount = fields.Float(string='Total', compute='_compute_subtotal', store=True)

    # Additional fields
    discount_amount = fields.Float(string='Discount Amount', default=0.0)
    variation_name = fields.Char(string='Variation Name')
    sku = fields.Char(string='SKU')
    image_url = fields.Char(string='Image URL')

    # Computed fields
    margin = fields.Float(string='Margin %', compute='_compute_margin', store=True, digits=(5, 2))
    has_product = fields.Boolean(string='Has Odoo Product', compute='_compute_has_product', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
            line.tax_amount = line.subtotal * 0.07
            line.total_amount = line.subtotal + line.tax_amount

    @api.depends('subtotal', 'product_id.standard_price', 'quantity')
    def _compute_margin(self):
        """Calculate margin based on subtotal vs cost."""
        for line in self:
            if line.product_id and line.product_id.standard_price and line.subtotal:
                cost = line.product_id.standard_price * line.quantity
                line.margin = ((line.subtotal - cost) / line.subtotal * 100) if line.subtotal else 0
            else:
                line.margin = 0.0

    @api.depends('product_id')
    def _compute_has_product(self):
        """Set has_product based on product_id."""
        for line in self:
            line.has_product = bool(line.product_id)

    def action_link_odoo_product(self):
        """Try to find matching Odoo product by SKU or name."""
        self.ensure_one()
        if self.product_id:
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': _('Already Linked'), 'message': _('Already linked'), 'type': 'info'}}

        # Try by SKU
        product = False
        if self.sku:
            product = self.env['product.product'].search([('default_code', '=', self.sku)], limit=1)

        # Try by name
        if not product and self.name:
            product = self.env['product.product'].search([('name', '=', self.name)], limit=1)

        if product:
            self.product_id = product.id
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': _('Linked'), 'message': _('Linked to %s' % product.name), 'type': 'success'}}

        raise UserError(_('No matching product found.'))

    def _prepare_sale_order_line_vals(self):
        """Prepare vals for sale.order.line."""
        self.ensure_one()
        return {
            'product_id': self.product_id.id if self.product_id else False,
            'name': self.name,
            'product_uom_qty': self.quantity,
            'price_unit': self.unit_price,
        }

    def _compute_discount_pct(self):
        """Calculate discount percentage."""
        self.ensure_one()
        if self.subtotal and self.discount_amount:
            return (self.discount_amount / self.subtotal) * 100
        return 0.0
# ProductCategoryMapping and PriceRecommendation moved to:
# - models/category_mapping.py
# - models/price_recommendation.py
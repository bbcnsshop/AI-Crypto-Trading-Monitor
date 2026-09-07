# -*- coding: utf-8 -*-
"""Sale Order Channel Integration.

Inherit from sale.order to add channel-specific fields and methods.
Link Sale Orders to Channel Orders for multi-channel e-commerce management.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    """Sale Order with Channel Integration.

    Extends sale.order to link orders with channel orders from
    Shopee, Lazada, TikTok Shop platforms.
    """
    _inherit = 'sale.order'

    # ========== Channel Fields ==========
    channel_id = fields.Many2one(
        'channel.config', string='Channel', index=True, readonly=True,
        states={'draft': [('readonly', False)]}
    )
    channel_order_id = fields.Many2one(
        'channel.order', string='Channel Order', index=True, readonly=True
    )
    channel_order_code = fields.Char(
        string='Channel Order Code', readonly=True, copy=False
    )
    channel_shipping_fee = fields.Float(
        string='Channel Shipping Fee', readonly=True, digits='Product Price'
    )
    channel_discount = fields.Float(
        string='Channel Discount', readonly=True, digits='Product Price'
    )

    # ========== Computed Fields ==========
    is_from_channel = fields.Boolean(
        string='From Channel',
        compute='_compute_is_from_channel',
        store=True
    )
    channel_order_state = fields.Selection(
        string='Channel Order State',
        related='channel_order_id.state',
        readonly=True
    )
    channel_platform_fee = fields.Float(
        string='Platform Fee',
        related='channel_order_id.platform_fee',
        readonly=True
    )
    channel_payment_fee = fields.Float(
        string='Payment Fee',
        related='channel_order_id.payment_fee',
        readonly=True
    )
    channel_customer_name = fields.Char(
        string='Customer Name',
        related='channel_order_id.customer_name',
        readonly=True
    )

    # ========== Onchange Methods ==========
    @api.depends('channel_id', 'channel_order_id')
    def _compute_is_from_channel(self):
        """Compute whether this order is from a channel."""
        for order in self:
            order.is_from_channel = bool(order.channel_id or order.channel_order_id)

    @api.onchange('channel_id')
    def _onchange_channel_id(self):
        """When channel is set, set default warehouse and pricelist."""
        if self.channel_id:
            if self.channel_id.default_warehouse_id:
                self.warehouse_id = self.channel_id.default_warehouse_id
            if self.channel_id.default_pricelist_id:
                self.pricelist_id = self.channel_id.default_pricelist_id

    @api.onchange('channel_order_id')
    def _onchange_channel_order_id(self):
        """Sync fields from channel order when linked."""
        if self.channel_order_id:
            self.channel_order_code = self.channel_order_id.channel_order_id
            self.channel_shipping_fee = self.channel_order_id.shipping_cost
            self.channel_discount = self.channel_order_id.platform_fee  # Note: using platform_fee as discount
            if not self.channel_id:
                self.channel_id = self.channel_order_id.channel_id.id

    # ========== Action Methods ==========
    def action_view_channel_order(self):
        """Open the linked channel order."""
        self.ensure_one()
        if not self.channel_order_id:
            raise UserError(_('No channel order linked to this sale order.'))
        return {
            'name': _('Channel Order %s') % self.channel_order_id.channel_order_id,
            'view_mode': 'form',
            'res_model': 'channel.order',
            'res_id': self.channel_order_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_sync_from_channel(self):
        """Sync order data from channel order."""
        self.ensure_one()
        if not self.channel_order_id:
            raise UserError(_('No channel order linked to this sale order.'))
        self._sync_from_channel_order()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synced'),
                'message': _('Order data synced from channel order.'),
                'type': 'success',
            }
        }

    def _sync_from_channel_order(self):
        """Sync data from channel.order to sale.order.

        Updates:
        - Shipping fee from channel order
        - Discount amount from channel order
        - Order notes if channel order has notes
        """
        self.ensure_one()
        if not self.channel_order_id:
            return

        # Sync amounts
        self.write({
            'channel_shipping_fee': self.channel_order_id.shipping_cost,
            'channel_discount': self.channel_order_id.platform_fee,
        })

        # Sync notes if channel order has remarks
        if self.channel_order_id.notes and not self.note:
            self.note = self.channel_order_id.notes

    # ========== Invoice Integration ==========
    def _prepare_invoice_vals(self):
        """Add channel info to invoice."""
        vals = super()._prepare_invoice_vals()
        if self.channel_id:
            origin_parts = [vals.get('invoice_origin', '')]
            if self.channel_order_code:
                origin_parts.append(self.channel_order_code)
            vals['invoice_origin'] = ' - '.join(filter(None, origin_parts))
        return vals

    # ========== Delivery Integration ==========
    def _create_delivery_line(self, carrier, amount):
        """Create delivery line with channel shipping fee."""
        line = super()._create_delivery_line(carrier, amount)
        if self.channel_shipping_fee and amount == 0:
            # If channel has shipping fee and carrier is free, use channel fee
            line.price_unit = self.channel_shipping_fee
        return line

    def action_view_delivery(self):
        """Open delivery form or wizard."""
        result = super().action_view_delivery()
        if self.channel_order_id:
            result['context'].update({
                'default_channel_order_id': self.channel_order_id.id,
            })
        return result

    # ========== State Change Hooks ==========
    def action_confirm(self):
        """Confirm sale order and update channel order if linked."""
        result = super().action_confirm()
        for order in self:
            if order.channel_order_id:
                order.channel_order_id._update_sale_order_state('sale_confirmed')
        return result

    def action_cancel(self):
        """Cancel sale order and notify channel order if linked."""
        result = super().action_cancel()
        for order in self:
            if order.channel_order_id:
                order.channel_order_id._update_sale_order_state('cancelled')
                # Optionally sync cancellation to platform
                try:
                    order.channel_order_id.action_cancel_on_platform()
                except Exception:
                    pass  # Log error but don't block cancellation
        return result

    # ========== Channel Totals ==========
    def _get_channel_total_amount(self):
        """Calculate total amount including channel fees."""
        self.ensure_one()
        subtotal = sum(line.price_subtotal for line in self.order_line)
        shipping = self.channel_shipping_fee or 0.0
        discount = self.channel_discount or 0.0
        platform_fee = self.channel_platform_fee or 0.0
        payment_fee = self.channel_payment_fee or 0.0
        return {
            'subtotal': subtotal,
            'shipping': shipping,
            'discount': discount,
            'platform_fee': platform_fee,
            'payment_fee': payment_fee,
            'net_amount': subtotal + shipping - discount - platform_fee - payment_fee,
        }

    # ========== Workflow ==========
    def action_create_channel_order(self):
        """Create a channel order from this sale order."""
        self.ensure_one()
        if self.channel_order_id:
            raise UserError(_('Sale order already linked to a channel order.'))

        # Validate order has products
        if not self.order_line:
            raise UserError(_('Sale order must have at least one product line.'))

        # Generate channel order ID
        channel_order_code = 'SO-%s' % self.name.replace('/', '-')

        channel_order = self.env['channel.order'].create({
            'channel_order_id': channel_order_code,
            'channel_id': self.channel_id.id,
            'customer_name': self.partner_id.name,
            'customer_email': self.partner_id.email,
            'customer_phone': self.partner_id.phone,
            'total_amount': self.amount_total,
            'shipping_cost': self.channel_shipping_fee,
            'state': 'pending',
            'notes': self.note,
        })

        # Link sale order to channel order
        self.write({
            'channel_order_id': channel_order.id,
            'channel_order_code': channel_order_code,
        })

        return {
            'name': _('Channel Order Created'),
            'view_mode': 'form',
            'res_model': 'channel.order',
            'res_id': channel_order.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    # ========== Constraints ==========
    @api.constrains('channel_id', 'state')
    def _check_channel_not_locked(self):
        """Prevent changing channel on locked orders."""
        for order in self:
            if order.channel_id and order.state in ['done', 'sale']:
                # Channel can only be set before confirmation
                pass  # Allow channel to remain, just not change

    # ========== Report Integration ==========
    def _get_channel_report_data(self):
        """Get channel-specific report data for this order.

        Returns dict with:
        - channel_name: Name of the channel
        - platform_order_id: Order code on platform
        - fees: Breakdown of all fees
        - profit: Calculated profit if cost available
        """
        self.ensure_one()
        totals = self._get_channel_total_amount()

        # Get cost from order lines if product has standard_price
        total_cost = 0.0
        for line in self.order_line:
            if line.product_id and line.product_id.standard_price:
                total_cost += line.product_id.standard_price * line.product_uom_qty

        return {
            'channel_name': self.channel_id.name or 'Unknown',
            'platform_order_id': self.channel_order_code or self.name,
            'sale_amount': self.amount_untaxed,
            'shipping_fee': totals['shipping'],
            'discount': totals['discount'],
            'platform_fee': totals['platform_fee'],
            'payment_fee': totals['payment_fee'],
            'total_cost': total_cost,
            'gross_profit': self.amount_untaxed - total_cost,
            'net_profit': totals['net_amount'] - total_cost,
        }


class SaleOrderLine(models.Model):
    """Sale Order Line with Channel Info.

    Extends sale.order.line to track channel-specific pricing.
    """
    _inherit = 'sale.order.line'

    # ========== Channel Fields ==========
    channel_order_line_id = fields.Many2one(
        'channel.order.line',
        string='Channel Order Line',
        readonly=True,
        copy=False
    )
    channel_price = fields.Float(
        string='Channel Price',
        help='Original price from channel platform',
        digits='Product Price'
    )
    channel_discount_rate = fields.Float(
        string='Channel Discount %',
        help='Discount percentage from channel campaign',
        digits=(5, 2)
    )

    # ========== Computed Fields ==========
    channel_margin = fields.Float(
        string='Margin %',
        compute='_compute_channel_margin',
        store=True,
        digits=(5, 2)
    )

    @api.depends('price_unit', 'product_id.standard_price', 'channel_price')
    def _compute_channel_margin(self):
        """Calculate margin based on channel price vs cost."""
        for line in self:
            if line.channel_price and line.product_id.standard_price:
                cost = line.product_id.standard_price
                line.channel_margin = ((line.channel_price - cost) / line.channel_price * 100) if line.channel_price else 0
            else:
                line.channel_margin = 0.0

    # ========== Overrides ==========
    @api.onchange('product_id')
    def product_id_change(self):
        """Call super and optionally sync channel price."""
        result = super().product_id_change()
        if self.channel_price and self.product_id:
            # Suggest channel price as default
            self.price_unit = self.channel_price
        return result

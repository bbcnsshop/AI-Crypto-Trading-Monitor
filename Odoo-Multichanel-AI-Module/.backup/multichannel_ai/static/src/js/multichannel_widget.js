// -*- coding: utf-8 -*-
odoo.define('multichannel_ai.widget', function (require) {
    "use strict";
    
    var core = require('web.core');
    var Widget = require('web.Widget');
    
    var MultiChannelWidget = Widget.extend({
        template: 'multichannel_ai.widget',
        
        init: function(parent, options) {
            this._super(parent, options);
            this.channels = options.channels || [];
        },
        
        start: function() {
            console.log('Multi-Channel Widget loaded');
        },
        
        // Sync products to selected channels
        syncProducts: function(channel_ids) {
            return this._rpc({
                route: '/web/dataset/call_kw',
                args: ['channel.sync.wizard', 'action_sync', []],
                kwargs: {
                    channel_ids: channel_ids,
                    sync_products: true,
                    sync_orders: false
                }
            });
        },
        
        // Calculate profit for a product
        calculateProfit: function(product_id, channel_code, selling_price) {
            return this._rpc({
                route: '/web/dataset/call_kw',
                args: ['ai.engine', 'calculate_profit', []],
                kwargs: {
                    selling_price: selling_price,
                    cost: 0, // Will be fetched from product
                    channel_code: channel_code
                }
            });
        }
    });
    
    core.action_registry.add('multichannel_widget', MultiChannelWidget);
    
    return MultiChannelWidget;
});
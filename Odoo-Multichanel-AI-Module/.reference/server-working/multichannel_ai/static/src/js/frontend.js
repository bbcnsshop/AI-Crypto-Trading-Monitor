/* Multi-Channel Frontend JS
 * Used in /multichannel/* web pages
 */

// Helper for Odoo JSON-RPC calls
function mcRpc(route, params) {
    return fetch(route, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: params || {},
            id: Math.floor(Math.random() * 1000000),
        }),
    }).then(function(r) { return r.json(); });
}

// Show notification
function showNotification(message, type) {
    type = type || 'info';
    // Use Odoo's notification system if available
    if (typeof odoo !== 'undefined' && odoo.define) {
        // Backend
        return;
    }
    // Simple toast for frontend
    var toast = document.createElement('div');
    toast.className = 'mc-toast mc-toast-' + type;
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;top:20px;right:20px;padding:15px 25px;border-radius:6px;color:#fff;z-index:9999;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.2);animation:mcSlideIn 0.3s;background:' + (
        type === 'success' ? '#27ae60' :
        type === 'error' ? '#e74c3c' :
        type === 'warning' ? '#f39c12' : '#3498db'
    );
    document.body.appendChild(toast);
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
}

// Sync single product
window.syncProduct = function(productId) {
    if (!confirm('Sync this product to its channel?')) return;
    showNotification('Syncing...', 'info');

    mcRpc('/multichannel/api/sync_product', { product_id: productId })
        .then(function(res) {
            if (res.result && res.result.success) {
                showNotification('✅ Synced successfully!', 'success');
                setTimeout(function() { location.reload(); }, 1500);
            } else {
                showNotification('❌ Sync failed: ' + (res.result ? res.result.error : 'Unknown'), 'error');
            }
        })
        .catch(function(err) {
            showNotification('❌ Error: ' + err.message, 'error');
        });
};

// Sync whole channel
window.syncChannel = function(channelId, channelName) {
    if (!confirm('Sync all products to ' + channelName + '?')) return;

    var btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<span class="mc-loading"></span> Syncing...';

    mcRpc('/multichannel/api/sync_channel', { channel_id: channelId })
        .then(function(res) {
            if (res.result && res.result.success) {
                showNotification('✅ Synced ' + res.result.count + ' products to ' + channelName, 'success');
                btn.innerHTML = '<i class="fa fa-check"></i> Done';
                setTimeout(function() { location.reload(); }, 2000);
            } else {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa fa-refresh"></i> Sync Now';
                showNotification('❌ Failed: ' + (res.result ? res.result.error : 'Unknown'), 'error');
            }
        })
        .catch(function(err) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa fa-refresh"></i> Sync Now';
            showNotification('❌ Error: ' + err.message, 'error');
        });
};

// Add toast CSS animation
var style = document.createElement('style');
style.textContent = '@keyframes mcSlideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }';
document.head.appendChild(style);

// Auto-mark active menu based on URL
document.addEventListener('DOMContentLoaded', function() {
    var path = window.location.pathname;
    var links = document.querySelectorAll('.mc-menu a');
    links.forEach(function(link) {
        if (path === link.getAttribute('href') ||
            (link.getAttribute('href') !== '/multichannel' && path.indexOf(link.getAttribute('href')) === 0)) {
            link.classList.add('active');
        }
    });
});

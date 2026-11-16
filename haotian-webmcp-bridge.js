/*!
 * HaoTian WebMCP & UCP v1.1 Agentic Commerce Bridge for 圖圖生酮蛋糕店 (tutu888.com.tw)
 * Version: 2.1.0 | Zero-dependency ES5/ES6 compatible
 */
(function () {
  'use strict';

  var BRIDGE_VERSION = '2.1.0';

  function registerModelContextTools(api) {
    try {
      if (typeof navigator !== 'undefined' && navigator.modelContext && typeof navigator.modelContext.registerTool === 'function') {
        navigator.modelContext.registerTool({
          name: 'tutu_list_catalog',
          description: '列出圖圖生酮蛋糕店全部 41 款無麩質無精製糖甜點 SKU、6吋價格、成分與過敏原資訊',
          inputSchema: { type: 'object', properties: { category: { type: 'string' }, query: { type: 'string' } } },
          execute: function (args) { return Promise.resolve(api.listCatalog(args || {})); }
        });
        navigator.modelContext.registerTool({
          name: 'tutu_manage_cart',
          description: '新增甜點至訂購單、設定取貨或宅配方式與希望慶生到貨日，並取得含運總價與防偽檢核碼',
          inputSchema: {
            type: 'object',
            properties: {
              sku: { type: 'string' },
              qty: { type: 'integer' },
              fulfillMode: { type: 'string', enum: ['pickup', 'tainan_city', 'tainan_county', 'delivery'] },
              targetDate: { type: 'string', description: 'YYYY-MM-DD' }
            }
          },
          execute: function (args) { return Promise.resolve(api.applyAgentOrder(args || {})); }
        });
      }
    } catch (e) {}
  }

  window.initTutuWebMCP = function (hooks) {
    if (!hooks) return;
    var api = {
      version: BRIDGE_VERSION,
      merchantId: 'tutu-keto-bakery-tainan',
      ucpEndpoint: 'https://tutu888.com.tw/.well-known/ucp',
      llmsEndpoint: 'https://tutu888.com.tw/llms.txt',
      listCatalog: function (filter) {
        var opts = filter || {};
        var cat = opts.category || 'all';
        var q = String(opts.query || '').trim().toLowerCase();
        return hooks.getCatalog().filter(function (it) {
          if (cat !== 'all' && it.cat !== cat) return false;
          if (!q) return true;
          return (it.id + ' ' + it.name + ' ' + it.spec + ' ' + it.ingredients).toLowerCase().indexOf(q) !== -1;
        });
      },
      getCartSummary: function () {
        return hooks.getSummary();
      },
      addToCart: function (sku, qty) {
        return hooks.addItem(sku, qty || 1);
      },
      clearCart: function () {
        return hooks.clearCart();
      },
      applyAgentOrder: function (payload) {
        return hooks.applyExternalOrder(payload || {});
      }
    };
    window.HaotianWebMCP = api;
    registerModelContextTools(api);
    return api;
  };
})();

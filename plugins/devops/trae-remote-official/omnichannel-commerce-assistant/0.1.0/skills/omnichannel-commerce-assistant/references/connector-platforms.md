# Advanced platform connection paths

Load only for a named-platform integration request after reading `connector-mcp.md`.

## Common sequence

1. Confirm official developer access and the exact country/site/store scope.
2. List required read-only objects and fields.
3. Map official API operations to narrow MCP tools.
4. Store credentials in the runtime's secret mechanism, never in prompts or files.
5. Test with a small date range and reconcile totals against a platform export.
6. Add pagination, rate-limit, timezone, currency, refund/status, and freshness handling.

## Platform reminders

| Platform family | Verify first |
|---|---|
| Taobao/Tmall/JD/Pinduoduo/Douyin | merchant/developer eligibility, app review, data-product permissions, domestic account scope |
| Amazon | selling-partner region/site, role permissions, reports/orders/catalog/finance scope |
| TikTok Shop/Shopee/Lazada | seller region, shop/site identifiers, app review, order/product/finance availability |
| Temu/AliExpress/eBay/Walmart | seller program, country availability, official API access, current object coverage |

Platform programs and endpoints change. Verify current official documentation before giving implementation details.

Expose business-oriented read tools such as `get_store_daily_metrics`, `get_sku_performance`, `get_inventory_snapshot`, or `get_orders_summary`; avoid a single unrestricted raw-request tool.


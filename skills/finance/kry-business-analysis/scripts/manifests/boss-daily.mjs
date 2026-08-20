/**
 * S1 经营日报 — 组件数据 manifest（brand 层级，含前日环比）
 * 记录位置：income/v3/list 记录直接在 data[]；BY_BRAND 为单条汇总，BY_SHOP 为多门店。
 * 注意：income 顶层 orderPeopleCnt / reopenTableRate 常为 null，真实值在 orderTypeItems，用 sumOrderTypeMetric 提取。
 */
export default {
  scene: 'S1 经营日报',
  sources: {
    brand: 'income_brand.json',     // BY_BRAND 昨日
    prev: 'income_prev.json',       // BY_BRAND 前日（环比）
    shop: 'income_shop.json',       // BY_SHOP 昨日
    constitute: 'constitute.json',  // 收入构成
    paymethod: 'paymethod.json',    // 支付方式
  },
  build(lib, data) {
    const enrich = (r) => lib.deriveIncomeMetrics(r || {});
    const brandRec = enrich((data.brand?.data || [])[0] || {});
    const prevRec = enrich((data.prev?.data || [])[0] || {});
    const shops = data.shop?.data || [];

    const kpi = lib.buildKpi(
      [brandRec],
      [
        { label: '营业额', field: 'saleAmt', unit: '元', compare: true },
        { label: '营业收入', field: 'businessIncomeAmt', unit: '元', compare: true },
        { label: '订单数', field: 'orderCnt', unit: '笔', compare: true, decimals: 0 },
        { label: '折后客单价', field: '_avgCustomerAfter', unit: '元', compare: true },
        { label: '就餐人数', field: '_peopleCnt', unit: '人', compare: true, decimals: 0 },
      ],
      [prevRec]
    );

    // 收入构成（API-4 businessIncomeItems）
    const constituteRec = (data.constitute?.data || [])[0] || {};

    return {
      meta: { scene: 'S1 经营日报', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        shopRanking: lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', topN: 5, bottomN: 5 }),
        orderTypePie: { data: lib.extractOrderTypeMetric(brandRec.orderTypeItems, 'orderAmt') },
        incomePie: lib.buildPie(lib.extractItemList(constituteRec.businessIncomeItems), { nameField: 'name', valueField: 'value' }),
        payPie: lib.buildPie(data.paymethod?.data || [], { nameField: 'payMethodName', valueField: 'actualReceivedAmt', topN: 5 }),
      },
      facts: {
        saleAmt: lib.round(lib.parseNum(brandRec.saleAmt), 2),
        businessIncomeAmt: lib.round(lib.parseNum(brandRec.businessIncomeAmt), 2),
        orderCnt: lib.parseNum(brandRec.orderCnt),
        peopleCnt: brandRec._peopleCnt,
        shopCount: shops.length,
        topShop: shops.length ? lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', topN: 1 }).categories[0] : null,
      },
    };
  },
};

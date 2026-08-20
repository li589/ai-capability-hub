/**
 * S2 经营周报 — 组件数据 manifest（brand 层级，本周 vs 上周）
 * 记录位置：income 记录在 data[]（BY_DAY 每天一条）；orderItem 记录在 data[0].item[]；combo 记录在 data[]。
 */
export default {
  scene: 'S2 经营周报',
  sources: {
    week: 'income_week.json',        // BY_DAY 本周
    lastWeek: 'income_lastweek.json',// BY_DAY 上周
    shop: 'income_shop.json',        // BY_TOTAL BY_SHOP 本周
    promo: 'promo.json',             // 优惠构成
    dish: 'dish.json',               // orderItem/list 菜品
    combo: 'combo.json',             // 套餐
  },
  build(lib, data) {
    const week = (data.week?.data || []).map(lib.deriveIncomeMetrics);
    const lastWeek = (data.lastWeek?.data || []).map(lib.deriveIncomeMetrics);
    const shops = data.shop?.data || [];
    const dishes = (data.dish?.data || []).flatMap((r) => r.item || []);
    const combos = (data.combo?.data || []).filter((r) => r && r.comboName != null);

    const kpi = lib.buildKpi(
      week,
      [
        { label: '本周营业额', field: 'saleAmt', agg: 'sum', unit: '元', compare: true },
        { label: '营业收入', field: 'businessIncomeAmt', agg: 'sum', unit: '元', compare: true },
        { label: '订单数', field: 'orderCnt', agg: 'sum', unit: '笔', compare: true, decimals: 0 },
        { label: '周均客单价', field: '_avgCustomerAfter', agg: 'avg', unit: '元', compare: true },
        { label: '就餐人数', field: '_peopleCnt', agg: 'sum', unit: '人', compare: true, decimals: 0 },
      ],
      lastWeek
    );

    // 日营收趋势：本周 + 上周（按索引对齐）
    const trend = {
      xLabels: week.map((r) => String(r.date || '').split(' ~ ')[0]),
      series: [
        { name: '本周', data: week.map((r) => lib.round(lib.parseNum(r.saleAmt), 2)) },
        { name: '上周', data: lastWeek.map((r) => lib.round(lib.parseNum(r.saleAmt), 2)) },
      ],
    };

    // 退菜预警
    const returnWarn = dishes
      .filter((d) => lib.parseNum(d.returnRatio) > 5)
      .sort((a, b) => lib.parseNum(b.returnRatio) - lib.parseNum(a.returnRatio));

    // 优惠构成（订单优惠/支付优惠/订单支出 三类明细）
    const promoRec = (data.promo?.data || [])[0] || {};
    const promoItems = [
      ...lib.extractItemList(promoRec.orderPromoItems),
      ...lib.extractItemList(promoRec.paymentPromoItems),
      ...lib.extractItemList(promoRec.orderExpenseItems),
    ];

    return {
      meta: { scene: 'S2 经营周报', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        trend,
        shopRanking: lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', topN: 5 }),
        dishTop10: lib.buildRanking(dishes, { nameField: 'name', valueField: 'actualAmt', topN: 10 }),
        returnWarnTable: lib.buildTable(returnWarn, {
          columns: [
            { header: '菜品', field: 'name' },
            { header: '退菜率', field: 'returnRatio' },
          ],
          limit: 5,
        }),
        promoRanking: lib.buildRanking(promoItems.map((p) => ({ ...p, _abs: Math.abs(p.value) })), { nameField: 'name', valueField: '_abs' }),
        comboTable: lib.buildTable(combos, {
          columns: [
            { header: '套餐', field: 'comboName' },
            { header: '销量', field: 'itemSaleQty', format: 'num', decimals: 0 },
            { header: '金额', field: 'actualAmt', format: 'num' },
          ],
          sortBy: 'actualAmt',
        }),
      },
      facts: {
        weekSale: lib.round(lib.aggregate(week, 'saleAmt', 'sum'), 2),
        lastWeekSale: lib.round(lib.aggregate(lastWeek, 'saleAmt', 'sum'), 2),
        dayCount: week.length,
        shopCount: shops.length,
        dishCount: dishes.length,
        returnWarnCount: returnWarn.length,
      },
    };
  },
};

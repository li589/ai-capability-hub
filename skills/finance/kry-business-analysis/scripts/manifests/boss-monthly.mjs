/**
 * S3 月度经营总结 — 组件数据 manifest（brand 层级，本月 vs 上月，17 板块中的确定性部分）
 * 记录位置：income 在 data[]（BY_DAY 每天一条）；itemType/orderItem 在 data[0].item[]；paid/income、promo 在 data[]。
 * 洞察(板块15)/行动清单(板块16)/数据说明(板块17) 为 AI 文本，不在本 manifest；本文件产出其数据支撑 facts。
 */
export default {
  scene: 'S3 月度经营总结',
  sources: {
    month: 'income_month.json',      // BY_DAY 本月
    lastMonth: 'income_lastmonth.json', // BY_TOTAL 上月
    shop: 'income_shop.json',        // BY_TOTAL BY_SHOP 本月
    itemType: 'itemType.json',       // 分类营收
    dish: 'dish.json',               // orderItem/list 单品
    paid: 'paid.json',               // paid/income v6 收款
    promo: 'promo.json',             // 优惠构成
  },
  build(lib, data) {
    const month = (data.month?.data || []).map(lib.deriveIncomeMetrics);
    const lastMonthRec = lib.deriveIncomeMetrics((data.lastMonth?.data || [])[0] || {});
    const shops = data.shop?.data || [];
    const cats = (data.itemType?.data || []).flatMap((r) => r.item || []);
    const dishes = (data.dish?.data || []).flatMap((r) => r.item || []);

    const catGrouped = lib.groupBy(cats, 'bigTypeName', ['actualAmt', 'goodsSpotQty', 'salePrice']);

    // 月度 KPI（本月按天汇总 vs 上月单条）
    const kpi = lib.buildKpi(
      month,
      [
        { label: '月营业额', field: 'saleAmt', agg: 'sum', unit: '元', compare: true },
        { label: '月营业收入', field: 'businessIncomeAmt', agg: 'sum', unit: '元', compare: true },
        { label: '月订单数', field: 'orderCnt', agg: 'sum', unit: '笔', compare: true, decimals: 0 },
        { label: '月就餐人数', field: '_peopleCnt', agg: 'sum', unit: '人', compare: true, decimals: 0 },
        { label: '折后单均价', field: '_avgCustomerAfter', agg: 'avg', unit: '元', compare: true },
      ],
      [lastMonthRec]
    );
    // 优惠占比 KPI（|totalPromoAmt| / saleAmt）
    const monthSale = lib.aggregate(month, 'saleAmt', 'sum');
    const monthPromo = Math.abs(lib.aggregate(month, 'totalPromoAmt', 'sum'));
    const lastSale = lib.parseNum(lastMonthRec.saleAmt);
    const lastPromo = Math.abs(lib.parseNum(lastMonthRec.totalPromoAmt));
    const curRatio = monthSale ? lib.round((monthPromo / monthSale) * 100, 1) : 0;
    const preRatio = lastSale ? lib.round((lastPromo / lastSale) * 100, 1) : 0;
    kpi.push({
      label: '优惠占比', value: curRatio, unit: '%',
      delta: { value: lib.round(curRatio - preRatio, 1), dir: curRatio > preRatio ? 'up' : curRatio < preRatio ? 'down' : 'flat', type: 'diff' },
    });

    // stats-inline：最高/最低单日、周末/工作日均值、周末溢价
    const dayRows = month.map((r) => ({ date: String(r.date || '').split(' ~ ')[0], sale: lib.parseNum(r.saleAmt) }));
    const sorted = [...dayRows].sort((a, b) => b.sale - a.sale);
    const isWeekend = (d) => { const wd = new Date(d).getDay(); return wd === 0 || wd === 6; };
    const wkend = dayRows.filter((r) => isWeekend(r.date));
    const wkday = dayRows.filter((r) => !isWeekend(r.date));
    const avg = (arr) => (arr.length ? arr.reduce((s, r) => s + r.sale, 0) / arr.length : 0);
    const wkendAvg = lib.round(avg(wkend), 2);
    const wkdayAvg = lib.round(avg(wkday), 2);

    // 收款结构：paid/income v6 → payMethodList
    const paidRec = (data.paid?.data || [])[0] || {};
    const payList = paidRec.payMethodList || [];

    // 优惠与支出构成
    const promoRec = (data.promo?.data || [])[0] || {};
    const promoItems = [
      ...lib.extractItemList(promoRec.orderPromoItems),
      ...lib.extractItemList(promoRec.paymentPromoItems),
      ...lib.extractItemList(promoRec.orderExpenseItems),
    ].map((p) => ({ ...p, _abs: Math.abs(p.value) }));

    return {
      meta: { scene: 'S3 月度经营总结', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        statsInline: {
          maxDay: sorted[0] || null,
          minDay: sorted[sorted.length - 1] || null,
          weekendAvg: wkendAvg,
          weekdayAvg: wkdayAvg,
          weekendPremium: wkdayAvg ? lib.round(((wkendAvg - wkdayAvg) / wkdayAvg) * 100, 1) : 0,
        },
        trend: lib.buildTrend(month, {
          xField: 'date',
          series: [{ name: '日营业额', field: 'saleAmt' }, { name: '日订单数', field: 'orderCnt' }],
          movingAvg: { of: '日营业额', window: 7, name: '7日均线' },
        }),
        categoryPie: lib.buildPie(catGrouped, { nameField: 'bigTypeName', valueField: 'actualAmt', topN: 10 }),
        orderTypePie: { data: lib.extractOrderTypeMetric((month[0] || {}).orderTypeItems, 'orderAmt') },
        categoryTable: lib.buildTable(catGrouped, {
          columns: [
            { header: '品类', field: 'bigTypeName' },
            { header: '营业额', field: 'actualAmt', format: 'num' },
            { header: '销量', field: 'goodsSpotQty', format: 'num', decimals: 0 },
          ],
          sortBy: 'actualAmt', limit: 10,
        }),
        dishTop10: lib.buildRanking(dishes, { nameField: 'name', valueField: 'actualAmt', topN: 10 }),
        shopTop10: lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', topN: 10 }),
        shopBottom10: lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', order: 'asc', topN: 10 }),
        shopBucket: lib.buildBucket(shops, {
          valueField: 'saleAmt',
          buckets: [
            { label: '≥10万', min: 100000 }, { label: '5-10万', min: 50000, max: 100000 },
            { label: '2-5万', min: 20000, max: 50000 }, { label: '1-2万', min: 10000, max: 20000 },
            { label: '5k-1万', min: 5000, max: 10000 }, { label: '<5k', max: 5000 },
          ],
        }),
        shopTop30Table: lib.buildTable(shops, {
          columns: [
            { header: '#', field: '#' }, { header: '门店', field: 'shopName' },
            { header: '月营业额', field: 'saleAmt', format: 'num' }, { header: '月订单数', field: 'orderCnt', format: 'num', decimals: 0 },
            { header: '折后单均', field: 'avgTradeAmtAfterDiscount', format: 'num' },
          ],
          sortBy: 'saleAmt', limit: 30,
        }),
        payStructurePie: lib.buildPie(payList, { nameField: 'payTypeName', valueField: 'incomeAmt', topN: 5 }),
        promoRanking: lib.buildRanking(promoItems, { nameField: 'name', valueField: '_abs' }),
      },
      facts: {
        monthSale: lib.round(monthSale, 2),
        lastMonthSale: lib.round(lastSale, 2),
        dayCount: month.length,
        shopCount: shops.length,
        topShopShare: shops.length ? lib.round((lib.parseNum(lib.buildRanking(shops, { nameField: 'shopName', valueField: 'saleAmt', topN: 1 }).values[0]) / (lib.aggregate(shops, 'saleAmt', 'sum') || 1)) * 100, 1) : 0,
        promoRatio: curRatio,
        categoryCount: catGrouped.length,
      },
    };
  },
};

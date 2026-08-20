/**
 * S4 门店排行榜 — 组件数据 manifest（multi 层级，指定周期 vs 对比周期）
 * 记录位置：income 记录在 data[]（BY_SHOP 每店一条）。
 */
export default {
  scene: 'S4 门店排行榜',
  sources: {
    cur: 'income_cur.json',      // BY_SHOP 指定周期
    compare: 'income_cmp.json',  // BY_SHOP 对比周期
    booking: 'booking.json',     // 预订门店排行（可选）
  },
  build(lib, data) {
    const cur = (data.cur?.data || []).map(lib.deriveIncomeMetrics);
    const cmp = (data.compare?.data || []).map(lib.deriveIncomeMetrics);
    const prevMap = new Map(cmp.map((r) => [String(r.shopId), r]));
    const enriched = cur.map((r) => {
      const p = prevMap.get(String(r.shopId));
      const prevSale = lib.parseNum(p?.saleAmt);
      const sale = lib.parseNum(r.saleAmt);
      return { ...r, _saleDelta: prevSale ? lib.round(((sale - prevSale) / prevSale) * 100, 1) : null };
    });

    const kpi = lib.buildKpi(cur, [
      { label: '参与门店数', field: 'shopId', agg: 'count', unit: '家' },
      { label: '品牌总营业额', field: 'saleAmt', agg: 'sum', unit: '元' },
      { label: '品牌总订单数', field: 'orderCnt', agg: 'sum', unit: '笔', decimals: 0 },
      { label: '品均营业额', field: 'saleAmt', agg: 'avg', unit: '元' },
    ]);

    // 雷达：Top3 + Bottom3（5 维归一化）
    const byRank = lib.buildRanking(cur, { nameField: 'shopName', valueField: 'saleAmt' });
    const top3names = byRank.categories.slice(0, 3);
    const bot3names = byRank.categories.slice(-3);
    const radarShops = cur.filter((r) => top3names.includes(String(r.shopName)) || bot3names.includes(String(r.shopName)));

    return {
      meta: { scene: 'S4 门店排行榜', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        saleRanking: byRank,
        radar: lib.buildRadar(radarShops, {
          nameField: 'shopName',
          dimensions: [
            { name: '营业额', field: 'saleAmt' }, { name: '客单价', field: '_avgCustomerAfter' },
            { name: '订单数', field: 'orderCnt' }, { name: '就餐人数', field: '_peopleCnt' },
          ],
        }),
        multiTable: lib.buildTable(enriched, {
          columns: [
            { header: '#', field: '#' }, { header: '门店', field: 'shopName' },
            { header: '营业额', field: 'saleAmt', format: 'num' }, { header: '营业收入', field: 'businessIncomeAmt', format: 'num' },
            { header: '订单数', field: 'orderCnt', format: 'num', decimals: 0 }, { header: '客单价', field: '_avgCustomerAfter', format: 'num' },
            { header: '环比%', field: '_saleDelta', format: 'num', decimals: 1 },
          ],
          sortBy: 'saleAmt',
        }),
      },
      facts: {
        shopCount: cur.length,
        totalSale: lib.round(lib.aggregate(cur, 'saleAmt', 'sum'), 2),
        risers: enriched.filter((r) => r._saleDelta != null && r._saleDelta > 30).map((r) => ({ shop: r.shopName, delta: r._saleDelta })),
        fallers: enriched.filter((r) => r._saleDelta != null && r._saleDelta < -20).map((r) => ({ shop: r.shopName, delta: r._saleDelta })),
        zeroShops: cur.filter((r) => lib.parseNum(r.saleAmt) === 0).map((r) => r.shopName),
      },
    };
  },
};

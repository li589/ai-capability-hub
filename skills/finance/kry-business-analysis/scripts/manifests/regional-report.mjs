/**
 * S5 区域经营报告 — 组件数据 manifest（region 层级，辖区门店对比）
 * 记录位置：income 在 data[]（BY_SHOP）；orderItem 在 data[0].item[]；numberAnalysis 在 data[]。
 */
export default {
  scene: 'S5 区域经营报告',
  sources: {
    cur: 'income_cur.json',      // BY_SHOP 指定周期
    compare: 'income_cmp.json',  // BY_SHOP 对比周期
    dish: 'dish.json',           // orderItem/list 辖区菜品
    number: 'number.json',       // dinner/numberAnalysis
  },
  build(lib, data) {
    const cur = (data.cur?.data || []).map(lib.deriveIncomeMetrics);
    const cmp = (data.compare?.data || []).map(lib.deriveIncomeMetrics);
    const dishes = (data.dish?.data || []).flatMap((r) => r.item || []);
    const prevMap = new Map(cmp.map((r) => [String(r.shopId), r]));
    const enriched = cur.map((r) => {
      const p = prevMap.get(String(r.shopId));
      const prevSale = lib.parseNum(p?.saleAmt);
      const sale = lib.parseNum(r.saleAmt);
      return {
        ...r,
        _saleDelta: prevSale ? lib.round(((sale - prevSale) / prevSale) * 100, 1) : null,
        _eff: r._peopleCnt ? lib.round(lib.parseNum(r.businessIncomeAmt) / r._peopleCnt, 2) : 0, // 折后人效
      };
    });

    const kpi = lib.buildKpi(cur, [
      { label: '辖区门店数', field: 'shopId', agg: 'count', unit: '家' },
      { label: '区域总营业额', field: 'saleAmt', agg: 'sum', unit: '元' },
      { label: '区域总订单数', field: 'orderCnt', agg: 'sum', unit: '笔', decimals: 0 },
      { label: '区域平均客单价', field: '_avgCustomerAfter', agg: 'avg', unit: '元' },
      { label: '区域总就餐人数', field: '_peopleCnt', agg: 'sum', unit: '人', decimals: 0 },
    ]);

    return {
      meta: { scene: 'S5 区域经营报告', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        radar: lib.buildRadar(cur, {
          nameField: 'shopName',
          dimensions: [
            { name: '营业额', field: 'saleAmt' }, { name: '客单价', field: '_avgCustomerAfter' },
            { name: '订单数', field: 'orderCnt' }, { name: '就餐人数', field: '_peopleCnt' },
          ],
        }),
        shopRanking: lib.buildRanking(cur, { nameField: 'shopName', valueField: 'saleAmt' }),
        efficiencyRanking: lib.buildRanking(enriched, { nameField: 'shopName', valueField: '_eff' }),
        shopTable: lib.buildTable(enriched, {
          columns: [
            { header: '#', field: '#' }, { header: '门店', field: 'shopName' },
            { header: '营业额', field: 'saleAmt', format: 'num' }, { header: '订单数', field: 'orderCnt', format: 'num', decimals: 0 },
            { header: '客单价', field: '_avgCustomerAfter', format: 'num' }, { header: '环比%', field: '_saleDelta', format: 'num', decimals: 1 },
          ],
          sortBy: 'saleAmt',
        }),
        dishTop10: lib.buildRanking(dishes, { nameField: 'name', valueField: 'actualAmt', topN: 10 }),
      },
      facts: {
        shopCount: cur.length,
        totalSale: lib.round(lib.aggregate(cur, 'saleAmt', 'sum'), 2),
        maxMinRatio: (() => {
          const rk = lib.buildRanking(cur, { nameField: 'shopName', valueField: 'saleAmt' }).values;
          const min = rk.filter((v) => v > 0).pop();
          return rk.length && min ? lib.round(rk[0] / min, 2) : null;
        })(),
        fallers: enriched.filter((r) => r._saleDelta != null && r._saleDelta < -20).map((r) => r.shopName),
      },
    };
  },
};

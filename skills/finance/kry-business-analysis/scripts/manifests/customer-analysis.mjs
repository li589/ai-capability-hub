/**
 * S8 客流消费分析 — 组件数据 manifest（store 层级）
 * 记录位置：numberAnalysis / tableTypeAnalysis / table-avg 在 data[]；income BY_DAY 在 data[]（每天一条）。
 */
export default {
  scene: 'S8 客流消费分析',
  sources: {
    number: 'number.json',       // dinner/numberAnalysis 按人数
    tableType: 'tabletype.json', // dinner/tableTypeAnalysis
    tableAvg: 'tableavg.json',   // order/table-avg/page 消费区间
    incomeDay: 'income_day.json',// income BY_DAY 客单价趋势
  },
  build(lib, data) {
    const days = (data.incomeDay?.data || []).map(lib.deriveIncomeMetrics);
    const numbers = data.number?.data || [];
    const tableTypes = data.tableType?.data || [];
    const tableAvg = data.tableAvg?.data || [];

    const kpi = lib.buildKpi(days, [
      { label: '总就餐人数', field: '_peopleCnt', agg: 'sum', unit: '人', decimals: 0 },
      { label: '日均客流', field: '_peopleCnt', agg: 'avg', unit: '人', decimals: 0 },
      { label: '平均客单价(折后)', field: '_avgCustomerAfter', agg: 'avg', unit: '元' },
      { label: '平均客单价(折前)', field: '_avgCustomerPre', agg: 'avg', unit: '元' },
    ]);

    return {
      meta: { scene: 'S8 客流消费分析', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        trend: {
          xLabels: days.map((r) => String(r.date || '').split(' ~ ')[0]),
          series: [
            { name: '客流人数', data: days.map((r) => r._peopleCnt) },
            { name: '折后客单价', data: days.map((r) => r._avgCustomerAfter) },
          ],
        },
        peopleBar: lib.buildRanking(numbers, { nameField: 'peopleCnt', valueField: 'busiOrderNoCount', order: 'asc' }),
        avgRangeBar: {
          categories: tableAvg.map((r) => String(r.range ?? '')),
          values: tableAvg.map((r) => lib.parseNum(r.orderCnt)),
        },
        tableTypeRadar: lib.buildRadar(tableTypes, {
          nameField: 'tableTypeName',
          dimensions: [
            { name: '营业收入', field: 'orderReceivedAmt' }, { name: '人均消费', field: 'perCapitaPost' },
            { name: '订单数', field: 'busiOrderNoCount' }, { name: '客流', field: 'orderPeopleCnt' },
          ],
        }),
      },
      facts: {
        totalPeople: lib.round(lib.aggregate(days, '_peopleCnt', 'sum'), 0),
        dayCount: days.length,
        avgCustomerAfter: lib.round(lib.aggregate(days, '_avgCustomerAfter', 'avg'), 2),
        topPeopleSeg: lib.buildRanking(numbers, { nameField: 'peopleCnt', valueField: 'busiOrderNoCount', topN: 1 }).categories[0] || null,
      },
    };
  },
};

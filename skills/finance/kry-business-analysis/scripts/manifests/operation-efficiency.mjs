/**
 * S9 运营效率分析 — 组件数据 manifest（store 层级）
 * 记录位置：kitchen/produced、queryData、CdsOrderDetailClient、cup/yield、extrafee 均在 data[]。
 */
export default {
  scene: 'S9 运营效率分析',
  sources: {
    kitchen: 'kitchen.json',   // kitchen/produced/statistics 员工出品
    query: 'query.json',       // queryData 菜品出餐时长
    called: 'called.json',     // CdsOrderDetailClient 叫号
    cup: 'cup.json',           // measure/cup/yield 出杯率
    extrafee: 'extrafee.json', // extrafee/statistics 服务费
  },
  build(lib, data) {
    const kitchen = data.kitchen?.data || [];
    const query = data.query?.data || [];
    const calledRec = (data.called?.data || [])[0] || {};
    const cupRec = (data.cup?.data || [])[0] || {};
    const extrafee = data.extrafee?.data || [];

    // 超时率 = sum(timeoutCount)/sum(itemCount)
    const totalTimeout = lib.aggregate(kitchen, 'timeoutCount', 'sum');
    const totalItem = lib.aggregate(kitchen, 'itemCount', 'sum');
    const timeoutRate = totalItem ? lib.round((totalTimeout / totalItem) * 100, 1) : 0;

    const kpi = [
      { label: '平均制作时长', value: lib.round(lib.aggregate(kitchen, 'avgCompletionTime', 'avg'), 1), unit: '秒' },
      { label: '超时率', value: timeoutRate, unit: '%' },
      { label: '叫号率', value: lib.round(lib.parseNum(calledRec.calledOrderRate), 1), unit: '%' },
      { label: '取餐率', value: lib.round(lib.parseNum(calledRec.pickedOrderRate), 1), unit: '%' },
      { label: '出杯率', value: lib.round(lib.parseNum(cupRec.cupOutRate), 1), unit: '%' },
      { label: '服务费收入', value: lib.round(lib.aggregate(extrafee, 'extraFeeActualAmt', 'sum'), 2), unit: '元' },
    ];

    // 超时菜品预警：timeoutRatio > 0，Top10
    const timeoutWarn = query
      .filter((r) => lib.parseNum(r.timeoutRatio) > 0)
      .sort((a, b) => lib.parseNum(b.timeoutRatio) - lib.parseNum(a.timeoutRatio));

    return {
      meta: { scene: 'S9 运营效率分析', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        employeeRanking: lib.buildRanking(kitchen, { nameField: 'operatorName', valueField: 'actualSaleQty', topN: 15 }),
        timeoutTable: lib.buildTable(timeoutWarn, {
          columns: [
            { header: '菜品', field: 'itemName' }, { header: '超时次数', field: 'timeoutCount', format: 'num', decimals: 0 },
            { header: '超时率', field: 'timeoutRatio' }, { header: '平均时长(秒)', field: 'avgCompletionTime', format: 'num', decimals: 0 },
          ],
          limit: 10,
        }),
        callFunnel: lib.buildFunnel([
          { name: '订单总数', value: calledRec.orderCnt },
          { name: '已叫号', value: calledRec.calledOrderCnt },
          { name: '已取餐', value: calledRec.pickedOrderCnt },
        ]),
        extrafeePie: lib.buildPie(extrafee, { nameField: 'extraFeeName', valueField: 'extraFeeActualAmt' }),
      },
      facts: {
        employeeCount: kitchen.length,
        timeoutRate,
        avgCompletionTime: lib.round(lib.aggregate(kitchen, 'avgCompletionTime', 'avg'), 1),
        timeoutWarnCount: timeoutWarn.length,
        calledRate: lib.round(lib.parseNum(calledRec.calledOrderRate), 1),
        pickedRate: lib.round(lib.parseNum(calledRec.pickedOrderRate), 1),
        hasCupData: Boolean(cupRec.cupOutRate),
      },
    };
  },
};

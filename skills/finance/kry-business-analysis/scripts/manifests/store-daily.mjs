/**
 * S6 门店日报 — 组件数据 manifest（store 层级，含前日环比 + 叫号漏斗）
 * 记录位置：income 在 data[]（单店单条）；numberAnalysis / paymethod / constitute / CdsOrderDetailClient 在 data[]。
 */
export default {
  scene: 'S6 门店日报',
  sources: {
    cur: 'income_cur.json',        // BY_SHOP 昨日（单店）
    prev: 'income_prev.json',      // BY_SHOP 前日
    constitute: 'constitute.json', // 收入构成
    paymethod: 'paymethod.json',   // 支付方式
    number: 'number.json',         // 就餐人数分析
    called: 'called.json',         // 取餐叫号（快餐）
  },
  build(lib, data) {
    const cur = lib.deriveIncomeMetrics((data.cur?.data || [])[0] || {});
    const prev = lib.deriveIncomeMetrics((data.prev?.data || [])[0] || {});
    const numbers = data.number?.data || [];
    const calledRec = (data.called?.data || [])[0] || {};

    const kpi = lib.buildKpi(
      [cur],
      [
        { label: '营业额', field: 'saleAmt', unit: '元', compare: true },
        { label: '营业收入', field: 'businessIncomeAmt', unit: '元', compare: true },
        { label: '订单数', field: 'orderCnt', unit: '笔', compare: true, decimals: 0 },
        { label: '折后客单价', field: '_avgCustomerAfter', unit: '元', compare: true },
        { label: '就餐人数', field: '_peopleCnt', unit: '人', compare: true, decimals: 0 },
      ],
      [prev]
    );

    const constituteRec = (data.constitute?.data || [])[0] || {};

    return {
      meta: { scene: 'S6 门店日报', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        orderTypePie: { data: lib.extractOrderTypeMetric(cur.orderTypeItems, 'orderAmt') },
        customerBar: lib.buildRanking(numbers, { nameField: 'peopleCnt', valueField: 'busiOrderNoCount', order: 'asc' }),
        incomePie: lib.buildPie(lib.extractItemList(constituteRec.businessIncomeItems), { nameField: 'name', valueField: 'value' }),
        payPie: lib.buildPie(data.paymethod?.data || [], { nameField: 'payMethodName', valueField: 'actualReceivedAmt', topN: 5 }),
        callFunnel: lib.buildFunnel([
          { name: '下单总数', value: calledRec.orderCnt },
          { name: '已叫号', value: calledRec.calledOrderCnt },
          { name: '已取餐', value: calledRec.pickedOrderCnt },
        ]),
      },
      facts: {
        saleAmt: lib.round(lib.parseNum(cur.saleAmt), 2),
        orderCnt: lib.parseNum(cur.orderCnt),
        peopleCnt: cur._peopleCnt,
        avgCustomer: cur._avgCustomerAfter,
        calledRate: calledRec.calledOrderRate ?? null,
        pickedRate: calledRec.pickedOrderRate ?? null,
        isQuickService: Boolean(calledRec.orderCnt),
      },
    };
  },
};

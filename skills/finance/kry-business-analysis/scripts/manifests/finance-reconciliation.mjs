/**
 * S10 财务对账报告 — 组件数据 manifest（multi 层级）
 * 记录位置：paid/income v6、paymethod、payment/reconciliation v4 均在 data[]。
 */
export default {
  scene: 'S10 财务对账报告',
  sources: {
    paid: 'paid.json',           // paid/income v6（statisticsByBusi）
    paymethod: 'paymethod.json', // paymethod/statistics
    recon: 'recon.json',         // payment/reconciliation v4
  },
  build(lib, data) {
    const paid = data.paid?.data || [];
    const payments = data.paymethod?.data || [];
    const recon = data.recon?.data || [];

    // 收款总览：对全部 paid 记录的 totalIncome 求和（busiTypeName 可能为 null，不作为汇总前提）
    const paidRows = paid.map((r) => ({
      busiTypeName: r.busiTypeName || '合计',
      incomeAmt: lib.get(r, 'totalIncome.incomeAmt'),
      payCnt: lib.get(r, 'totalIncome.payCnt'),
    }));
    const busiGrouped = lib.groupBy(paidRows, 'busiTypeName', ['incomeAmt', 'payCnt']);
    const totalIncome = lib.aggregate(busiGrouped, 'incomeAmt', 'sum');
    const totalPayCnt = lib.aggregate(busiGrouped, 'payCnt', 'sum');

    const incomeKpi = [
      { label: '总收款金额', value: lib.round(totalIncome, 2), unit: '元' },
      { label: '总收款笔数', value: lib.round(totalPayCnt, 0), unit: '笔' },
    ];

    // 结算对账 KPI
    const reconKpi = [
      { label: '应打款总额', value: lib.round(lib.aggregate(recon, 'actualReceivedAmt', 'sum'), 2), unit: '元' },
      { label: '已结算金额', value: lib.round(lib.aggregate(recon, 'curReconciliationAmt', 'sum'), 2), unit: '元' },
      { label: '未结算金额', value: lib.round(lib.aggregate(recon, 'curOutstandingAmt', 'sum'), 2), unit: '元' },
      { label: '上期遗留未结', value: lib.round(lib.aggregate(recon, 'lastOutstandingAmt', 'sum'), 2), unit: '元' },
      { label: '手续费总额', value: lib.round(lib.aggregate(recon, 'totalFeeAmt', 'sum'), 2), unit: '元' },
    ];

    return {
      meta: { scene: 'S10 财务对账报告', generatedAt: new Date().toISOString() },
      components: {
        incomeKpi,
        busiTypePie: lib.buildPie(busiGrouped, { nameField: 'busiTypeName', valueField: 'incomeAmt' }),
        payRanking: lib.buildRanking(payments, { nameField: 'payMethodName', valueField: 'actualReceivedAmt' }),
        payTable: lib.buildTable(payments, {
          columns: [
            { header: '支付方式', field: 'payMethodName' }, { header: '实收', field: 'actualReceivedAmt', format: 'num' },
            { header: '顾客支付', field: 'payDetailAmt', format: 'num' }, { header: '笔数', field: 'payCntTotal', format: 'num', decimals: 0 },
          ],
          sortBy: 'actualReceivedAmt',
        }),
        reconKpi,
        reconTable: lib.buildTable(recon, {
          columns: [
            { header: '渠道', field: 'channelName' }, { header: '应打款', field: 'actualReceivedAmt', format: 'num' },
            { header: '已结算', field: 'curReconciliationAmt', format: 'num' }, { header: '未结算', field: 'curOutstandingAmt', format: 'num' },
            { header: '手续费', field: 'totalFeeAmt', format: 'num' },
          ],
          sortBy: 'actualReceivedAmt',
        }),
        feePie: lib.buildPie(recon, { nameField: 'channelName', valueField: 'totalFeeAmt' }),
      },
      facts: {
        totalIncome: lib.round(totalIncome, 2),
        totalOutstanding: lib.round(lib.aggregate(recon, 'curOutstandingAmt', 'sum'), 2),
        totalFee: lib.round(lib.aggregate(recon, 'totalFeeAmt', 'sum'), 2),
        feeRate: (() => {
          const rcv = lib.aggregate(recon, 'actualReceivedAmt', 'sum');
          return rcv ? lib.round((lib.aggregate(recon, 'totalFeeAmt', 'sum') / rcv) * 100, 2) : 0;
        })(),
        channelCount: recon.length,
      },
    };
  },
};

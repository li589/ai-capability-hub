/**
 * S11 外卖团购分析 — 组件数据 manifest（multi 层级）
 * 记录位置：takeout/reconciliation、groupCoupon/reconciliation、income 均在 data[]。
 * 单位注意：外卖金额单位为【元】；团购金额单位为【分】，本 manifest 统一 ÷100 转元（字段以 _ 前缀标记）。
 */
export default {
  scene: 'S11 外卖团购分析',
  sources: {
    takeout: 'takeout.json',  // takeout/reconciliation/query（元）
    group: 'group.json',      // groupCoupon/reconciliation（分）
    income: 'income.json',    // income BY_BRAND 总营收
  },
  build(lib, data) {
    const takeout = data.takeout?.data || [];
    const groupRaw = data.group?.data || [];
    const incomeRec = (data.income?.data || [])[0] || {};

    // 团购金额分转元
    const group = groupRaw.map((r) => ({
      ...r,
      _actualReceived: lib.round(lib.parseNum(r.actualReceivedAmt) / 100, 2),
      _faceAmt: lib.round(lib.parseNum(r.faceAmt) / 100, 2),
      _platformFee: lib.round(lib.parseNum(r.platformServiceAmt) / 100, 2),
    }));

    const takeoutIncome = lib.aggregate(takeout, 'orderReceivedAmt', 'sum');
    const groupIncome = lib.aggregate(group, '_actualReceived', 'sum');
    const brandSale = lib.parseNum(incomeRec.saleAmt);

    const kpi = [
      { label: '外卖总收入', value: lib.round(takeoutIncome, 2), unit: '元' },
      { label: '团购总收入', value: lib.round(groupIncome, 2), unit: '元' },
      { label: '平台收入占比', value: brandSale ? lib.round(((takeoutIncome + groupIncome) / brandSale) * 100, 1) : 0, unit: '%' },
      { label: '外卖订单数', value: lib.round(lib.aggregate(takeout, 'orderCnt', 'sum'), 0), unit: '单' },
      { label: '团购核销张数', value: lib.round(lib.aggregate(group, 'couponCnt', 'sum'), 0), unit: '张' },
    ];

    // 平台分组
    const takeoutByPlatform = lib.groupBy(takeout, 'platformName', ['orderReceivedAmt', 'itemSaleAmt', 'shopPromoAmt', 'platformServiceAmt', 'deliveryAmt']);
    const groupBySource = lib.groupBy(group, 'couponSource', ['_actualReceived', '_faceAmt', '_platformFee', 'couponCnt']);

    return {
      meta: { scene: 'S11 外卖团购分析', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        platformRanking: lib.buildRanking(takeoutByPlatform, { nameField: 'platformName', valueField: 'orderReceivedAmt' }),
        profitStacked: lib.buildStacked(takeoutByPlatform, {
          xField: 'platformName',
          series: [
            { name: '商品总价', field: 'itemSaleAmt', stack: 'a' },
            { name: '商家优惠', field: 'shopPromoAmt', stack: 'a' },
            { name: '平台佣金', field: 'platformServiceAmt', stack: 'a' },
            { name: '配送费', field: 'deliveryAmt', stack: 'a' },
          ],
        }),
        groupSourcePie: lib.buildPie(groupBySource, { nameField: 'couponSource', valueField: '_actualReceived' }),
        groupTable: lib.buildTable(groupBySource, {
          columns: [
            { header: '券来源', field: 'couponSource' }, { header: '核销张数', field: 'couponCnt', format: 'num', decimals: 0 },
            { header: '面值(元)', field: '_faceAmt', format: 'num' }, { header: '实收(元)', field: '_actualReceived', format: 'num' },
            { header: '平台服务费(元)', field: '_platformFee', format: 'num' },
          ],
          sortBy: '_actualReceived',
        }),
      },
      facts: {
        takeoutIncome: lib.round(takeoutIncome, 2),
        groupIncome: lib.round(groupIncome, 2),
        platformShare: brandSale ? lib.round(((takeoutIncome + groupIncome) / brandSale) * 100, 1) : 0,
        takeoutPlatformCount: takeoutByPlatform.length,
        groupSourceCount: groupBySource.length,
      },
    };
  },
};

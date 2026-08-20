/**
 * S12 预订经营分析 — 组件数据 manifest（multi 层级）
 * 记录位置：booking/goodsRanking、booking/customerRanking、booking/performanceRanking、
 *           booking/shopRanking 均在 data[]。
 * 字段说明：bookingOrderNo 为「预订单量」度量（非单号），measureArrivedResvCount 到店数、
 *           measureResvCancelCount 取消数、measureResvNoshowCount 未到店数、
 *           measureResvOverdueCount 逾期数、arrivedResvRatio 到店率（0~1 或带 %）。
 * shop 数据仅 level=brand 时提供，缺失时 shopRanking 为空。
 */
export default {
  scene: 'S12 预订经营分析',
  sources: {
    goods: 'booking_goods.json',        // booking/goodsRanking
    customer: 'booking_customer.json',  // booking/customerRanking
    performance: 'booking_perf.json',   // booking/performanceRanking
    shop: 'booking_shop.json',          // booking/shopRanking（仅总部）
  },
  build(lib, data) {
    const goods = data.goods?.data || [];
    const customers = data.customer?.data || [];
    const perf = data.performance?.data || [];
    // shopRanking 仅返回 shopId（无 shopName），补 _shopLabel 用于展示（有 shopName 用之，否则 shopId）
    const shops = (data.shop?.data || []).map((r) => ({
      ...r,
      _shopLabel: r.shopName || `门店${r.shopId}`,
    }));

    // 到店率归一：接口可能给 0~1 小数或带 % 字符串，统一转百分比数值
    const toPct = (v) => {
      const n = lib.parseNum(v);
      return n <= 1 ? lib.round(n * 100, 1) : lib.round(n, 1);
    };
    const withRatio = (rows) =>
      rows.map((r) => ({ ...r, _arrivedPct: toPct(r.arrivedResvRatio) }));

    const customerRows = withRatio(customers);
    const perfRows = withRatio(perf);

    // 预订总量汇总（客户维度求和，等价于整体预订量）
    const totalBooking = lib.aggregate(customers, 'bookingOrderNo', 'sum');
    const totalArrived = lib.aggregate(customers, 'measureArrivedResvCount', 'sum');
    const totalCancel = lib.aggregate(customers, 'measureResvCancelCount', 'sum');
    const totalNoshow = lib.aggregate(customers, 'measureResvNoshowCount', 'sum');
    const totalOverdue = lib.aggregate(customers, 'measureResvOverdueCount', 'sum');
    const gap = lib.round(totalBooking - totalArrived, 0);

    const kpi = [
      { label: '预订总量', value: lib.round(totalBooking, 0), unit: '单' },
      { label: '到店预订数', value: lib.round(totalArrived, 0), unit: '单' },
      { label: '到店率', value: totalBooking ? lib.round((totalArrived / totalBooking) * 100, 1) : 0, unit: '%' },
      { label: '取消数', value: lib.round(totalCancel, 0), unit: '单' },
      { label: '未到店数', value: lib.round(totalNoshow, 0), unit: '单' },
      { label: '取消率', value: totalBooking ? lib.round((totalCancel / totalBooking) * 100, 1) : 0, unit: '%' },
    ];

    // 员工到店率均值（用于差异分析）
    const teamAvgPct = perfRows.length
      ? lib.round(perfRows.reduce((s, r) => s + r._arrivedPct, 0) / perfRows.length, 1)
      : 0;

    return {
      meta: { scene: 'S12 预订经营分析', generatedAt: new Date().toISOString() },
      components: {
        kpi,
        goodsRanking: lib.buildRanking(goods, { nameField: 'itemSkuName', valueField: 'quantity', topN: 15 }),
        customerTable: lib.buildTable(customerRows, {
          columns: [
            { header: '#', field: '#' }, { header: '客户', field: 'customerName' },
            { header: '手机号', field: 'customerPhoneNo' }, { header: '预订数', field: 'bookingOrderNo', format: 'num', decimals: 0 },
            { header: '到店数', field: 'measureArrivedResvCount', format: 'num', decimals: 0 },
            { header: '取消数', field: 'measureResvCancelCount', format: 'num', decimals: 0 },
            { header: '到店率', field: '_arrivedPct', format: 'pct', decimals: 1 },
          ],
          sortBy: 'bookingOrderNo',
          limit: 20,
        }),
        performanceRanking: lib.buildRanking(perf, { nameField: 'creatorName', valueField: 'bookingOrderNo' }),
        shopRanking: shops.length
          ? lib.buildRanking(shops, { nameField: '_shopLabel', valueField: 'bookingOrderNo' })
          : { categories: [], values: [] },
        bookingFunnel: lib.buildFunnel([
          { name: '预订总量', value: lib.round(totalBooking, 0) },
          { name: '到店', value: lib.round(totalArrived, 0) },
          { name: '流失(取消+未到店+逾期)', value: gap },
        ]),
      },
      facts: {
        totalBooking: lib.round(totalBooking, 0),
        arrivedRate: totalBooking ? lib.round((totalArrived / totalBooking) * 100, 1) : 0,
        cancelRate: totalBooking ? lib.round((totalCancel / totalBooking) * 100, 1) : 0,
        noshowRate: totalBooking ? lib.round((totalNoshow / totalBooking) * 100, 1) : 0,
        overdue: lib.round(totalOverdue, 0),
        teamAvgArrivedPct: teamAvgPct,
        // 到店率低于团队均值的员工（培训需求）
        lowPerfStaff: perfRows
          .filter((r) => r._arrivedPct < teamAvgPct)
          .map((r) => ({ name: r.creatorName, arrivedPct: r._arrivedPct })),
        // 高频取消客户（跟进建议）
        highCancelCustomers: customerRows
          .filter((r) => lib.parseNum(r.measureResvCancelCount) >= 3)
          .map((r) => ({ name: r.customerName, cancel: lib.parseNum(r.measureResvCancelCount) })),
      },
    };
  },
};

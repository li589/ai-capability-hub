/**
 * S7 菜品经营分析 — 组件数据 manifest
 *
 * 用法：node ../report-data.mjs build --manifest dish-analysis.mjs --data-dir <fetch产物目录> --out report-data.json
 * sources 的 value 为 fetch.mjs 产物文件名（放在 --data-dir 目录下）。
 *
 * 记录位置约定（经 fetch.mjs resolvePageContainer 解包后）：
 *   - orderItem/list、itemType/list、department/list：记录在 data[0].item[]（values 外包一层 item）
 *   - combo/sale/statistics、measure/dish/gross/profit、practice/spec：记录直接在 data[]
 */
export default {
  scene: 'S7 菜品经营分析',
  sources: {
    dish: 'dish.json',          // /open/standard/report/orderItem/list
    itemType: 'itemType.json',  // /open/standard/report/orderItem/itemType/list
    combo: 'combo.json',        // /open/standard/report/combo/sale/statistics
    gross: 'gross.json',        // /open/standard/report/measure/dish/gross/profit
    practice: 'practice.json',  // /open/standard/report/order/orderitem/practice/page
    spec: 'spec.json',          // /open/standard/report/order/orderitem/spec/page
  },
  build(lib, data) {
    const readDate = (record) => record?.date || record?.businessDate || record?.statDate || record?.reportDate || record?.orderDate || record?.day || record?.period || '';
    const dishes = (data.dish?.data || []).flatMap((r) => r.item || []);
    const cats = (data.itemType?.data || []).flatMap((r) => {
      const recordDate = readDate(r);
      return (r.item || []).map((item) => ({ ...item, trendDate: readDate(item) || recordDate }));
    });
    // combo/sale/statistics 会混入 { totalSize } 元数据行（位置不定），仅保留含 comboName 的真实记录
    const combos = (data.combo?.data || []).filter((r) => r && r.comboName != null);
    const gross = data.gross?.data || [];
    const practices = data.practice?.data || [];
    const specs = data.spec?.data || [];

    // 品类分组汇总（同一大类可能多条 → 求和）
    const catGrouped = lib.groupBy(cats, 'bigTypeName', ['actualAmt', 'salePrice', 'goodsSpotQty']);
    const catTrendRows = cats.filter((cat) => cat.trendDate && cat.bigTypeName);
    const catTrendDates = [...new Set(catTrendRows.map((cat) => String(cat.trendDate)))].sort();
    const catTrendValues = new Map();
    const catTrendTotals = new Map();
    for (const cat of catTrendRows) {
      const category = String(cat.bigTypeName);
      const date = String(cat.trendDate);
      const amount = lib.parseNum(cat.actualAmt ?? cat.salePrice);
      const key = `${date}__${category}`;
      catTrendValues.set(key, (catTrendValues.get(key) || 0) + amount);
      catTrendTotals.set(category, (catTrendTotals.get(category) || 0) + amount);
    }
    const catTrendCategories = [...catTrendTotals.keys()].sort((a, b) => catTrendTotals.get(b) - catTrendTotals.get(a));
    const categoryTrend = {
      xLabels: catTrendDates,
      series: catTrendCategories.map((category) => ({
        name: category,
        data: catTrendDates.map((date) => lib.round(catTrendValues.get(`${date}__${category}`) || 0, 2)),
      })),
    };

    // 退菜预警：returnRatio > 5%，按退菜率降序
    const returnWarn = dishes
      .filter((d) => lib.parseNum(d.returnRatio) > 5)
      .sort((a, b) => lib.parseNum(b.returnRatio) - lib.parseNum(a.returnRatio));

    // 毛利象限：X=销量 actualSaleQty，Y=毛利率（grossProfitRate 为 0~1 比率 → ×100 转百分比）
    const grossPts = gross.map((g) => ({ ...g, _gpr: lib.round(lib.parseNum(g.grossProfitRate) * 100, 2) }));

    return {
      meta: { scene: 'S7 菜品经营分析', generatedAt: new Date().toISOString() },
      components: {
        dishTop20: lib.buildRanking(dishes, { nameField: 'name', valueField: 'actualAmt', topN: 20 }),
        categoryPie: lib.buildPie(catGrouped, { nameField: 'bigTypeName', valueField: 'actualAmt', topN: 10 }),
        categoryStacked: lib.buildStacked(catGrouped, { xField: 'bigTypeName', series: [{ name: '销售额', field: 'salePrice' }] }),
        categoryTrend,
        grossScatter: lib.buildScatter(grossPts, { xField: 'actualSaleQty', yField: '_gpr', nameField: 'itemName' }),
        comboTable: lib.buildTable(combos, {
          columns: [
            { header: '套餐', field: 'comboName' },
            { header: '销量', field: 'itemSaleQty', format: 'num', decimals: 0 },
            { header: '售价', field: 'itemSalePrice', format: 'num' },
            { header: '金额', field: 'actualAmt', format: 'num' },
          ],
          sortBy: 'actualAmt',
        }),
        returnWarnTable: lib.buildTable(returnWarn, {
          columns: [
            { header: '菜品', field: 'name' },
            { header: '退菜数', field: 'returnCnt', format: 'num', decimals: 0 },
            { header: '退菜率', field: 'returnRatio' },
          ],
        }),
        // 做法/规格偏好（字段名以接口实际返回为准，此处按取数字段声明取 name/actualSaleQty）
        practiceRanking: lib.buildRanking(practices, { nameField: 'name', valueField: 'actualSaleQty', topN: 10 }),
        specRanking: lib.buildRanking(specs, { nameField: 'name', valueField: 'actualSaleQty', topN: 10 }),
      },
      facts: {
        dishCount: dishes.length,
        totalDishSales: lib.round(lib.aggregate(dishes, 'actualAmt', 'sum'), 2),
        topCategory: catGrouped.slice().sort((a, b) => b.actualAmt - a.actualAmt)[0]?._key || null,
        categoryCount: catGrouped.length,
        returnWarnCount: returnWarn.length,
        comboCount: combos.length,
      },
    };
  },
};

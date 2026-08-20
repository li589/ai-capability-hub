# 分析代码模式库

模型据数据条件参考这些模式生成分析代码。**不是封闭清单**，可组合、可替换为更合适的方法。生成的代码写入临时 `.py` 执行，结果落盘 JSON。

通用约定：

```python
import pandas as pd, numpy as np, json
# 数值结果统一 round，避免浮点噪声
def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)
```

数值计算务必 `round`（如 `55*8.8` 浮点问题）。

## 读取标准化数据

```python
df = pd.read_excel("output/normalized_data.xlsx")
# 仅统计有效成绩
valid = df[df["status"] == "normal"].copy()
```

## 1. 描述统计

```python
def describe(s):
    s = pd.to_numeric(s, errors="coerce").dropna()
    q1, q3 = s.quantile(.25), s.quantile(.75)
    return {
        "n": int(s.size), "mean": r(s.mean()), "median": r(s.median()),
        "std": r(s.std()), "cv": r(s.std()/s.mean()) if s.mean() else None,
        "min": r(s.min()), "max": r(s.max()),
        "q1": r(q1), "q3": r(q3), "skew": r(s.skew()), "kurt": r(s.kurt()),
    }
```

## 2. 分布分段

```python
def segment(s, bins=[0,60,70,80,90,101], labels=["<60","60-69","70-79","80-89","90-100"]):
    s = pd.to_numeric(s, errors="coerce").dropna()
    cut = pd.cut(s, bins=bins, labels=labels, right=False)
    cnt = cut.value_counts().reindex(labels, fill_value=0)
    return [{"seg": k, "count": int(v), "pct": r(v/s.size*100,1)} for k,v in cnt.items()]
```

## 3. 比率指标（阈值可传入）

```python
def rates(s, pass_line=60, excel_line=85, low_line=60):
    s = pd.to_numeric(s, errors="coerce").dropna(); n=s.size
    return {
        "pass_rate": r((s>=pass_line).sum()/n*100,1),
        "excellent_rate": r((s>=excel_line).sum()/n*100,1),
        "low_rate": r((s<low_line).sum()/n*100,1),
        "n": int(n), "pass_line": pass_line, "excellent_line": excel_line,
    }
```

## 4. 分层

```python
def tiering(df, col, bands):  # bands: [("优秀",90,101),("良好",75,90),...]
    out=[]
    s = pd.to_numeric(df[col], errors="coerce")
    for name,lo,hi in bands:
        m = (s>=lo)&(s<hi)
        out.append({"tier":name,"count":int(m.sum()),"pct":r(m.sum()/s.notna().sum()*100,1)})
    return out
```

## 5. 群体对比 + 显著性

```python
def compare_groups(df, value_col, group_col):
    groups = {k: pd.to_numeric(g[value_col],errors="coerce").dropna()
              for k,g in df.groupby(group_col)}
    desc = {k: {"n":int(v.size),"mean":r(v.mean()),"std":r(v.std())} for k,v in groups.items()}
    res = {"desc": desc, "method": None, "p": None, "effect": None,
           "assumptions": {}, "note": ""}
    vals = [v for v in groups.values() if v.size>=3]
    if len(vals)<2:
        res["note"]="有效分组不足，无法做组间检验"
        return res
    try:
        from scipy import stats
        normal = all(len(v)>5000 or stats.shapiro(v).pvalue>=.05 for v in vals)
        levene_p = stats.levene(*vals, center="median").pvalue
        res["assumptions"] = {"normality_ok": normal, "levene_p": r(levene_p,4)}
        if len(vals)==2:
            a,b=vals
            if normal:
                _,p = stats.ttest_ind(a,b,equal_var=False)
                sp=np.sqrt(((a.std()**2)+(b.std()**2))/2)
                res.update(method="Welch t-test", p=r(p,4),
                           effect={"name":"Cohen d","value":r((a.mean()-b.mean())/sp,3) if sp else None})
            else:
                u,p = stats.mannwhitneyu(a,b,alternative="two-sided")
                rb=2*u/(len(a)*len(b))-1
                res.update(method="Mann-Whitney U", p=r(p,4),
                           effect={"name":"rank-biserial r","value":r(rb,3)})
        elif len(vals)>2:
            if normal and levene_p>=.05:
                _,p = stats.f_oneway(*vals)
                method="one-way ANOVA"
            else:
                _,p = stats.kruskal(*vals)
                method="Kruskal-Wallis"
            all_values=np.concatenate(vals); grand=all_values.mean()
            ss_between=sum(len(v)*(v.mean()-grand)**2 for v in vals)
            ss_total=sum(((v-grand)**2).sum() for v in vals)
            res.update(method=method, p=r(p,4),
                       effect={"name":"eta squared (descriptive)",
                               "value":r(ss_between/ss_total,3) if ss_total else None},
                       note="总体检验显著时，再按方法做事后两两比较并校正多重检验。")
    except ImportError:
        res["note"]="scipy 不可用，仅提供描述性对比"
    except ValueError as exc:
        res["note"]=f"数据不满足检验条件，仅提供描述性对比：{exc}"
    if any(v.size<30 for v in vals):
        res["note"] += " 样本偏小，结论仅供参考"
    return res
```

无 scipy 时只输出 `desc` 并说明未做检验。

## 6. 异常识别（IQR / 稳健Z）

```python
def outliers(df, col, id_col="student_id"):
    s = pd.to_numeric(df[col], errors="coerce")
    q1,q3 = s.quantile(.25), s.quantile(.75); iqr=q3-q1
    lo,hi = q1-1.5*iqr, q3+1.5*iqr
    med = s.median(); mad = (s-med).abs().median()
    flags=[]
    for i,v in s.items():
        if pd.isna(v): continue
        rz = 0.6745*(v-med)/mad if mad else 0
        if v<lo or v>hi or abs(rz)>3.5:
            flags.append({"id":str(df.loc[i,id_col]),"value":r(v),
                          "robust_z":r(rz,2),"type":"低于常态" if v<med else "高于常态"})
    return flags
```

## 7. 多次考试趋势（纵向）

```python
def trend(df, id_col, exam_col, ordered_exams, value_col):
    # ordered_exams 必须来自日期字段或用户给定顺序，禁止按考试名称字符串排序
    piv = df.pivot_table(index=id_col, columns=exam_col, values=value_col, aggfunc="mean")
    available = [exam for exam in ordered_exams if exam in piv.columns]
    piv = piv.reindex(columns=available)
    out=[]
    for sid,row in piv.iterrows():
        vals=row.dropna()
        if len(vals)>=2:
            delta=r(vals.iloc[-1]-vals.iloc[0])
            out.append({"id":str(sid),"first":r(vals.iloc[0]),"last":r(vals.iloc[-1]),
                        "delta":delta,"trend":"上升" if delta>0 else "下降" if delta<0 else "持平"})
    return out
```

## 8. 试卷难度与区分度

```python
def item_analysis(item_df, item_cols, full_scores):
    # item_df: 行=学生, 列=各题得分; full_scores: {题:满分}
    items = item_df[item_cols].apply(pd.to_numeric, errors="coerce")
    complete = items.dropna(axis=0, how="any")
    if len(complete)<4:
        return {"items":[], "n_input":len(items), "n_complete":len(complete),
                "missing_policy":"complete-case", "note":"完整作答样本不足，未计算题目区分度"}
    total = complete.sum(axis=1)
    order = total.sort_values(ascending=False)
    n = len(order); k = max(1, int(n*0.27))
    high, low = order.index[:k], order.index[-k:]
    res=[]
    for it in item_cols:
        fs = full_scores[it]
        p = complete[it].mean()/fs
        d = (complete.loc[high,it].mean()-complete.loc[low,it].mean())/fs
        res.append({"item":it,"difficulty_P":r(p,3),"discrimination_D":r(d,3),
                    "score_rate":r(complete[it].mean()/fs*100,1),"full_score":fs})
    return {"items":res, "n_input":len(items), "n_complete":len(complete),
            "missing_policy":"complete-case（任一题缺失即排除整名学生）"}
```

## 9. 信度（KR-20 / Cronbach α）

```python
def reliability(item_df, item_cols, binary=False):
    items=item_df[item_cols].apply(pd.to_numeric,errors="coerce").dropna(axis=0,how="any")
    k=len(item_cols)
    if k<2 or len(items)<2:
        return {"method":None,"value":None,"n":len(items),"note":"有效题目或样本不足"}
    var_total=items.sum(axis=1).var(ddof=1)
    if var_total==0: return {"method":None,"value":None,"n":len(items),"note":"总分无方差"}
    if binary:
        p=items.mean(); q=1-p
        return {"method":"KR-20","value":r(k/(k-1)*(1-(p*q).sum()/var_total),3),
                "k":k,"n":len(items),"missing_policy":"complete-case"}
    var_items=items.var(ddof=1).sum()
    return {"method":"Cronbach α","value":r(k/(k-1)*(1-var_items/var_total),3),
            "k":k,"n":len(items),"missing_policy":"complete-case"}
```

## 10. 课程目标达成

```python
def objective_attainment(scores, mapping, thresholds):
    # scores: {考核项: 平均得分率}; mapping: {目标:{考核项:权重}}
    out=[]
    for obj, comp_w in mapping.items():
        tw=sum(comp_w.values())
        att=sum(scores[c]*w for c,w in comp_w.items())/tw if tw else None
        th=thresholds.get(obj)
        out.append({"objective":obj,"attainment":r(att,3),
                    "threshold":th,"met":(att>=th) if (att is not None and th) else None})
    return out
```

## 结果落盘

```python
with open("output/analysis_results.json","w",encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

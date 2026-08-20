#!/usr/bin/env python3
"""生成不虚构效率数据的 VALUE_REPORT.md。"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def load(path,default):
    if not path: return default
    p=Path(path)
    if not p.is_file(): return default
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default


def feature_list(spec,status):
    feats=[]
    sysobj=spec.get('system') or {}
    domains=sysobj.get('business_domains') or []
    if domains: feats.append('业务域：'+ '、'.join(map(str,domains)))
    for key,label in [('objects','业务对象'),('reports','报表/看板'),('roles','角色/权限')]:
        v=spec.get(key) or sysobj.get(key)
        if isinstance(v,list) and v: feats.append(f'{label}：{len(v)} 项')
    if status.get('python_source_included'): feats.append('完整 Python 源码')
    if status.get('exe_build_source_included'): feats.append('Windows EXE 构建源码')
    if status.get('diagnostic_bundle_included'): feats.append('一键诊断')
    if status.get('target_pc_acceptance_included'): feats.append('目标电脑验收入口')
    return feats


def main():
    ap=argparse.ArgumentParser(description='生成价值证明报告；无实测数据时明确标记待测，不编造效率提升。')
    ap.add_argument('--spec',default='system-spec.json'); ap.add_argument('--status',default='DELIVERY_STATUS.json'); ap.add_argument('--metrics',default=None); ap.add_argument('--output',default='VALUE_REPORT.md')
    a=ap.parse_args(); spec=load(a.spec,{}); status=load(a.status,{}); metrics=load(a.metrics,{})
    before=metrics.get('before_minutes'); after=metrics.get('after_minutes'); sample=metrics.get('sample_count')
    efficiency=None
    if isinstance(before,(int,float)) and isinstance(after,(int,float)) and before>0 and after>=0:
        efficiency=round((before-after)/before*100,1)
    lines=['# VALUE_REPORT','', '## 本次系统化产出','']
    feats=feature_list(spec,status)
    lines += [f'- {x}' for x in feats] if feats else ['- 业务功能以本次 `system-spec.json` 和实际交付状态为准。']
    lines += ['','## 效率与质量价值','']
    if efficiency is None:
        lines += ['- **未填入经过实测的前后耗时，因此本报告不声明“节省 X% 时间”等量化结论。**','- 建议在真实业务中记录同一任务的人工基线耗时与系统化后耗时，再自动计算。']
    else:
        lines += [f'- 人工流程基线：{before} 分钟',f'- 系统化后：{after} 分钟',f'- 实测效率变化：{efficiency}%'+(f'（样本 {sample} 次）' if sample else '')]
    lines += ['','## 建议实测字段','', '| 指标 | 记录方式 |', '|---|---|', '| 单次处理耗时 | 同一业务、同一数据量，人工与系统分别计时 |', '| 错误/返工次数 | 记录同周期内因公式、漏填、重复录入导致的返工 |', '| 报表生成耗时 | 从原始数据准备到正式日报/月报导出的时间 |', '| 新工厂/新报表适配时间 | 从上传资料到获得首个可运行版本的时间 |', '', '> 只有真实测量数据才进入比赛或汇报中的量化收益；不把演示数据或模型估算冒充实测。','']
    Path(a.output).write_text('\n'.join(lines),encoding='utf-8')
    print(f'[完成] 已生成 {Path(a.output).resolve()}'+(f'，实测效率变化 {efficiency}%' if efficiency is not None else '，当前无量化实测数据'))
    return 0
if __name__=='__main__': sys.exit(main())

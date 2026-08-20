#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, sys
from pathlib import Path
from portable_full_support import portable_enabled, materialize_portable_layout, SERVICE_DIR

ROOT=Path(__file__).resolve().parents[1]
SCAFFOLD=ROOT/'assets'/'scaffold'/'universal-local-app'
TEMPLATE_DIR_NAME='_platform_templates'
SKILL_VERSION='2.7.0'
GENERATOR_SKILL='paperless-business-system-from-files'
DELIVERY_DOC_MAP={'README_RUN.md':'README_运行说明.md','README_EXE_BUILD.md':'README_EXE打包说明.md','README_SCAFFOLD.md':'README_工程骨架说明.md'}

def materialize_platform_templates(target: Path) -> None:
    tdir=target/TEMPLATE_DIR_NAME; mapping_path=tdir/'template-map.json'
    if not mapping_path.is_file(): raise RuntimeError('通用骨架缺少平台兼容模板映射 template-map.json')
    obj=json.loads(mapping_path.read_text(encoding='utf-8'))
    for item in obj.get('templates',[]):
        source=str(item.get('source') or '').strip(); output=str(item.get('output') or '').strip()
        if not source or not output: raise RuntimeError('平台兼容模板映射存在空 source/output')
        src=(tdir/source).resolve(); dst=(target/output).resolve()
        if tdir.resolve() not in src.parents or target.resolve() not in dst.parents: raise RuntimeError('非法平台模板路径')
        if not src.is_file(): raise RuntimeError(f'模板文件不存在：{source}')
        dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(src.read_bytes())
    shutil.rmtree(tdir)

def materialize_delivery_docs(target: Path) -> None:
    for src_name,dst_name in DELIVERY_DOC_MAP.items():
        src=target/src_name; dst=target/dst_name
        if not src.is_file(): raise RuntimeError(f'通用骨架缺少安全说明文件：{src_name}')
        if dst.exists(): dst.unlink()
        src.rename(dst)

def main():
    ap=argparse.ArgumentParser(description=f'根据 system-spec.json 复制 {SKILL_VERSION} 通用本地系统工程骨架。')
    ap.add_argument('--spec',required=True); ap.add_argument('--output',required=True); ap.add_argument('--force',action='store_true')
    a=ap.parse_args(); spec_path=Path(a.spec).expanduser(); target=Path(a.output).expanduser()
    if not spec_path.is_file(): print('[PB601] system-spec.json 不存在'); return 1
    try: spec=json.loads(spec_path.read_text(encoding='utf-8'))
    except Exception as e: print(f'[PB602] system-spec.json 无法读取：{e}'); return 1
    system=spec.get('system') or {}; name=str(system.get('name') or '本地业务系统').strip(); domains=system.get('business_domains') or []
    full=portable_enabled(spec)
    if target.exists():
        if not a.force: print('[PB603] 输出目录已存在；如确认覆盖请加 --force'); return 1
        shutil.rmtree(target)
    target.mkdir(parents=True,exist_ok=True)
    service=target/SERVICE_DIR if full else target
    shutil.copytree(SCAFFOLD,service,dirs_exist_ok=True)
    try:
        materialize_platform_templates(service); materialize_delivery_docs(service)
        portable_info=materialize_portable_layout(target,service,spec,SKILL_VERSION) if full else None
    except Exception as e:
        shutil.rmtree(target,ignore_errors=True); print(f'[PB604] 平台模板/完整部署包装还原失败：{e}'); return 1
    network=str(system.get('network_mode') or 'offline_core')
    default_bind='0.0.0.0' if network=='lan' else '127.0.0.1'
    replacements={'{{SYSTEM_NAME}}':name,'{{SKILL_VERSION}}':SKILL_VERSION,'{{BUSINESS_DOMAINS}}':','.join(map(str,domains)),'{{DEFAULT_BIND_HOST}}':default_bind}
    for f in target.rglob('*'):
        if not f.is_file() or f.suffix.lower() in {'.png','.jpg','.jpeg','.gif','.ico','.zip','.db','.vbs'}: continue
        try: text=f.read_text(encoding='utf-8')
        except UnicodeDecodeError: continue
        new=text
        for k,v in replacements.items(): new=new.replace(k,v)
        if new!=text: f.write_text(new,encoding='utf-8')
    shutil.copy2(spec_path,target/'system-spec.json')
    runtime_outputs=['input-profile.json','business-model.json','BUSINESS_MODEL_REPORT.md','business-profile.json','BUSINESS_RECOGNITION_REPORT.md','INPUT_COMPLETENESS_REPORT.md','source-file-mapping.json','data-quality-report.md','BUSINESS_CONFLICTS.md','ASSUMPTIONS.md','DELIVERY_STATUS.json']
    for name_out in runtime_outputs:
        src=spec_path.parent/name_out
        if src.is_file(): shutil.copy2(src,target/name_out)
    if not (target/'TEST_REPORT.md').exists():
        (target/'TEST_REPORT.md').write_text('# TEST_REPORT\n\n状态：未执行。完成业务代码与测试后，记录测试命令、覆盖范围、结果和失败处理。\n',encoding='utf-8')
    if not (target/'RUNTIME_ACCEPTANCE.md').exists():
        (target/'RUNTIME_ACCEPTANCE.md').write_text('# RUNTIME_ACCEPTANCE\n\n状态：未在目标 Windows 电脑执行。完成真机验收后记录环境、启动、核心流程、持久化、导入导出、备份和安全停止证据。\n',encoding='utf-8')
    nav=['# 交付导航','','1. 先看服务端运行说明：`01_服务端_完整程序/README_运行说明.md`。' if full else '1. 先看 `README_运行说明.md`。','2. 测试状态见 `TEST_REPORT.md`。','3. 真机状态见 `RUNTIME_ACCEPTANCE.md` 与 `DELIVERY_STATUS.json`。','4. 业务识别、资料完整度、冲突和假设来自本次附件分析。']
    if full: nav += ['5. Windows 普通填写用户使用 `02_Windows填写客户端/`，先设置并测试服务器地址。','6. “免 Python/首次安装完全离线”是否成立，只看 DELIVERY_STATUS 的真实验证字段。']
    (target/'00_请先看_交付导航.md').write_text('\n'.join(nav)+'\n',encoding='utf-8')
    (target/'VALUE_REPORT.md').write_text('# VALUE_REPORT\n\n当前系统已生成，但尚未录入真实业务前后耗时。不得声明未经实测的效率提升百分比。\n',encoding='utf-8')
    status_path=target/'DELIVERY_STATUS.json'
    if status_path.is_file():
        st=json.loads(status_path.read_text(encoding='utf-8'))
        st.update({'scaffold_used':True,'deployment_mode':'portable_full' if full else system.get('deployment_mode','local_or_lan'),'portable_full_requested':full,'portable_full_layout_included':full,'windows_client_included':full,'macos_client_included':bool((spec.get('portable_full') or {}).get('macos_client')) if full else False,'lan_helpers_included':bool((spec.get('portable_full') or {}).get('lan_helpers',True)) if full else False,'portable_full_runtime_strategy':(spec.get('portable_full') or {}).get('runtime_strategy') if full else None})
        status_path.write_text(json.dumps(st,ensure_ascii=False,indent=2),encoding='utf-8')
    baseline={'schema_version':'1.3','generator_skill':GENERATOR_SKILL,'skill_version':SKILL_VERSION,'system_name':name,'business_domains':domains,'deployment_mode':'portable_full' if full else system.get('deployment_mode','local_or_lan'),'platform_compatible_skill_package':True,'portable_full':portable_info,'notice':'通用工程骨架已生成；使用 generate 命令可根据 system-spec 自动生成 CRUD、智能表单、严格字段校验、逐行导入校验、RBAC、审计和安全可执行公式。生成后必须执行 test，再执行 validate --strict；审批链与无证据规则仍需确认。'}
    (target/'GENERATION_BASELINE.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[完成] 已生成{" portable_full 完整部署" if full else "通用"}工程骨架：{target.resolve()}')
    return 0
if __name__=='__main__': sys.exit(main())

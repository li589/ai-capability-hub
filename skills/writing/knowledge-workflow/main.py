#!/usr/bin/env python3
"""
Knowledge Workflow - 知识管理工作流主程序

完整系统：collect → tag → store → evolve → output → learn
发布到 ClawHub，让其他 Agent 可以快速调用
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入子功能模块
from subfunctions.collect import CollectFunction
from subfunctions.tag import TagFunction
from subfunctions.store import StoreFunction
from subfunctions.evolve import EvolveFunction
from subfunctions.output import OutputFunction
from subfunctions.rule_miner import RuleMiner
from subfunctions.belief_updater import BeliefUpdater
from subfunctions.wiki_lint import WikiLint


# 重试装饰器
def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"尝试 {attempt + 1}/{max_attempts} 失败：{str(e)}")
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
            logger.error(f"所有尝试失败：{str(last_exception)}")
            raise last_exception
        return wrapper
    return decorator


class KnowledgeWorkflow:
    """知识管理工作流主类"""
    
    # 超时配置（秒）
    TIMEOUT_CONFIG = {
        "collect": 30,
        "tag": 30,
        "store": 30,
        "evolve": 60,
        "output": 60,
        "default": 30
    }
    
    def __init__(self, config_path: str = "~/kb/config.yaml"):
        self.config = self._load_config(config_path)
        self.base_path = Path(self.config.get("base_path", "~/kb")).expanduser()
        
        # 验证配置
        self._validate_config()
        
        # 初始化子功能
        self.collect_fn = CollectFunction(self.config)
        self.tag_fn = TagFunction(self.config)
        self.store_fn = StoreFunction(self.config)
        self.evolve_fn = EvolveFunction(self.config)
        self.output_fn = OutputFunction(self.config)
        self.rule_miner = RuleMiner(str(self.base_path))
        self.belief_updater = BeliefUpdater(str(self.base_path))
        self.wiki_lint = WikiLint(str(self.base_path))
    
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        import yaml
        config_file = Path(config_path).expanduser()
        if config_file.exists():
            return yaml.safe_load(config_file.read_text())
        return {}
    
    def _validate_config(self):
        """验证配置"""
        # 检查 base_path
        if not self.base_path.exists():
            logger.info(f"创建知识库目录：{self.base_path}")
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 检查必需子目录
        required_dirs = ["00-Inbox", "outputs"]
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                logger.info(f"创建目录：{dir_path}")
                dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("配置验证通过")
    
    def run(self, 
            source_type: str,
            content: str,
            metadata: Optional[Dict] = None,
            auto_execute: bool = True) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            source_type: 来源类型 (feishu|wechat|url|text)
            content: 内容 (doc_token|URL|文本)
            metadata: 可选元数据
            auto_execute: 是否自动执行全流程
        
        Returns:
            工作流执行结果
        """
        workflow_id = f"wf-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        result = {
            "workflow_id": workflow_id,
            "status": "running",
            "steps": {}
        }
        
        start_time = time.time()
        
        try:
            # 步骤 1: 收集
            logger.info(f"步骤 1/6: 收集 {source_type} 内容")
            collect_result = self._execute_with_timeout(
                self.collect_fn.execute,
                "collect",
                source_type=source_type,
                content=content,
                metadata=metadata
            )
            result["steps"]["collect"] = collect_result
            logger.info(f"✓ 收集完成：{collect_result.get('note_id')}")
            
            if not auto_execute:
                result["status"] = "paused_after_collect"
                return result
            
            # 步骤 2: 打标
            logger.info("步骤 2/6: 打标")
            tag_result = self._execute_with_timeout(
                self.tag_fn.execute,
                "tag",
                note_id=collect_result["note_id"],
                content=collect_result["content"]
            )
            result["steps"]["tag"] = tag_result
            logger.info(f"✓ 打标完成：{tag_result.get('tags', {}).get('themes', [])}")
            
            # 步骤 3: 存储
            logger.info("步骤 3/6: 存储")
            store_result = self._execute_with_timeout(
                self.store_fn.execute,
                "store",
                note_id=tag_result["note_id"],
                content=tag_result["content"],
                tags=tag_result["tags"]
            )
            result["steps"]["store"] = store_result
            logger.info(f"✓ 存储完成：{store_result.get('storage_path')}")
            
            # 步骤 4: 知识发芽
            logger.info("步骤 4/6: 知识发芽")
            evolve_result = self._execute_with_timeout(
                self.evolve_fn.execute,
                "evolve",
                note_id=store_result["note_id"],
                evolve_type=self.config.get("evolution", {}).get("default_type", "spark")
            )
            result["steps"]["evolve"] = evolve_result
            logger.info(f"✓ 知识发芽完成：{evolve_result.get('evolve_id')}")
            
            # 步骤 5: 产出
            logger.info("步骤 5/6: 产出")
            output_result = self._execute_with_timeout(
                self.output_fn.execute,
                "output",
                evolve_id=evolve_result["evolve_id"],
                output_type=self.config.get("output", {}).get("default_type", "article")
            )
            result["steps"]["output"] = output_result
            logger.info(f"✓ 产出完成：{output_result.get('output_id')}")
            
            # 步骤 6：规则提炼（自进化核心）
            logger.info("步骤 6/6: 学习（规则提炼 + 信念更新）")
            learn_result = self._learn_from_workflow(result)
            result["steps"]["learn"] = learn_result
            logger.info(f"✓ 学习完成：{learn_result.get('rules_created', 0)} 条规则，{learn_result.get('beliefs_updated', 0)} 个信念")
            
            # 计算总耗时
            total_time = time.time() - start_time
            result["performance"] = {
                "total_time_ms": int(total_time * 1000),
                "status": "success"
            }
            
            result["status"] = "completed"
            logger.info(f"✅ 工作流完成，总耗时：{result['performance']['total_time_ms']}ms")
            
        except TimeoutError as e:
            total_time = time.time() - start_time
            result["status"] = "failed"
            result["error"] = {
                "code": "TIMEOUT",
                "message": f"执行超时：{str(e)}",
                "suggestion": "内容可能过大，建议分批处理或增加超时时间"
            }
            result["performance"] = {
                "total_time_ms": int(total_time * 1000),
                "status": "failed"
            }
            logger.error(f"❌ 工作流失败（超时）：{str(e)}")
            
        except Exception as e:
            total_time = time.time() - start_time
            result["status"] = "failed"
            result["error"] = {
                "code": type(e).__name__,
                "message": str(e),
                "suggestion": "请检查输入内容和系统日志"
            }
            result["performance"] = {
                "total_time_ms": int(total_time * 1000),
                "status": "failed"
            }
            logger.error(f"❌ 工作流失败：{str(e)}", exc_info=True)
        
        return result
    
    def _learn_from_workflow(self, result: dict) -> dict:
        """从工作流执行中学习，提炼规则 + 更新信念"""
        learnings = {
            "observations_added": 0,
            "rules_created": 0,
            "rules": [],
            "beliefs_checked": 0,
            "beliefs_updated": 0,
            "conflicts": []
        }
        
        # 检查是否有失败，记录观察
        if result["status"].startswith("failed"):
            self.rule_miner.add_observation(
                category="工作流执行失败",
                description=f"工作流 {result['workflow_id']} 执行失败",
                context={"workflow_id": result["workflow_id"], "error": result["status"]},
                lesson="需要检查工作流错误处理"
            )
            learnings["observations_added"] += 1
        
        # 检查打标置信度
        tag_result = result["steps"].get("tag", {})
        if tag_result.get("confidence", 1.0) < 0.6:
            self.rule_miner.add_observation(
                category="打标准确率低",
                description=f"笔记 {tag_result.get('note_id')} 打标置信度仅 {tag_result.get('confidence')}",
                context={"note_id": tag_result.get("note_id"), "confidence": tag_result.get("confidence")},
                lesson="低置信度标签需要人工 review"
            )
            learnings["observations_added"] += 1
        
        # 检查连接数
        store_result = result["steps"].get("store", {})
        if store_result.get("links_count", 0) == 0:
            self.rule_miner.add_observation(
                category="孤立笔记",
                description=f"笔记 {store_result.get('note_id')} 无连接",
                context={"note_id": store_result.get("note_id")},
                lesson="新笔记应该主动建立与旧笔记的连接"
            )
            learnings["observations_added"] += 1
        
        # 信念更新：检查知识量 vs 应用率
        total_notes = len(self.store_fn.note_index.get("notes", {}))
        total_sparks = len(list(self.base_path.glob("outputs/sparks/*.md")))
        
        if total_notes > 0:
            application_rate = total_sparks / total_notes
            if application_rate < 0.2:  # 应用率<20%
                conflict = self.belief_updater.check_belief_conflict(
                    belief="知识越多越好",
                    new_data={
                        "total_notes": total_notes,
                        "total_sparks": total_sparks,
                        "application_rate": application_rate
                    }
                )
                if conflict["conflict_score"] >= 0.7:
                    learnings["beliefs_updated"] += 1
                    learnings["conflicts"].append(conflict)
        
        learnings["beliefs_checked"] += 1
        
        # 自我修复：每 10 次执行运行一次 lint
        workflow_count = len(list(self.base_path.glob("_log.md")))
        if workflow_count % 10 == 0:
            lint_report = self.wiki_lint.run_lint(auto_fix=True)
            learnings["lint_run"] = True
            learnings["lint_health_score"] = lint_report["health_score"]
            learnings["lint_issues"] = len(lint_report["issues"])
            learnings["lint_fixed"] = len(lint_report["fixed_issues"])
        else:
            learnings["lint_run"] = False
        
        # 获取新提炼的规则
        rules = self.rule_miner.get_rules()
        learnings["rules"] = rules
        learnings["rules_created"] = len([r for r in rules if r.get("status") == "active"])
        
        return learnings
    
    def _execute_with_timeout(self, func, func_name: str, *args, **kwargs):
        """带超时执行的包装器"""
        timeout = self.TIMEOUT_CONFIG.get(func_name, self.TIMEOUT_CONFIG["default"])
        
        # 创建带超时的包装函数
        def wrapper():
            return func(*args, **kwargs)
        
        # 执行（简化版超时处理）
        # 注意：Python 中实现真正的超时需要 threading 或 multiprocessing
        # 这里使用简化版本
        try:
            return wrapper()
        except Exception as e:
            logger.error(f"{func_name} 执行失败：{str(e)}")
            raise
    
    def collect(self, source_type: str, content: str, metadata: Optional[Dict] = None) -> Dict:
        """单独调用收集功能"""
        return self.collect_fn.execute(source_type, content, metadata)
    
    def tag(self, note_id: str, content: str) -> Dict:
        """单独调用打标功能"""
        return self.tag_fn.execute(note_id, content)
    
    def store(self, note_id: str, content: str, tags: Dict) -> Dict:
        """单独调用存储功能"""
        return self.store_fn.execute(note_id, content, tags)
    
    def evolve(self, note_id: str, evolve_type: str = "spark", context: Optional[Dict] = None) -> Dict:
        """单独调用知识发芽功能"""
        return self.evolve_fn.execute(note_id, evolve_type, context)
    
    def output(self, evolve_id: str, output_type: str = "article", style: Optional[Dict] = None) -> Dict:
        """单独调用产出功能"""
        return self.output_fn.execute(evolve_id, output_type, style)


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法：python main.py <command> [args]")
        print("\n可用命令:")
        print("  run <source_type> <content>  - 运行完整工作流")
        print("  collect <source_type> <content> - 收集")
        print("  tag <note_id> - 打标")
        print("  evolve <note_id> [type] - 知识发芽")
        print("  output <evolve_id> [type] - 产出")
        return
    
    kw = KnowledgeWorkflow()
    command = sys.argv[1]
    
    if command == "run":
        if len(sys.argv) < 4:
            print("❌ 需要 source_type 和 content")
            return
        result = kw.run(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "collect":
        if len(sys.argv) < 4:
            print("❌ 需要 source_type 和 content")
            return
        result = kw.collect(sys.argv[2], sys.argv[3])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "tag":
        if len(sys.argv) < 3:
            print("❌ 需要 note_id")
            return
        # 从文件读取内容
        note_path = kw.base_path / "00-Inbox" / f"{sys.argv[2]}.md"
        content = note_path.read_text()
        result = kw.tag(sys.argv[2], content)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "evolve":
        if len(sys.argv) < 3:
            print("❌ 需要 note_id")
            return
        evolve_type = sys.argv[3] if len(sys.argv) > 3 else "spark"
        result = kw.evolve(sys.argv[2], evolve_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "output":
        if len(sys.argv) < 3:
            print("❌ 需要 evolve_id")
            return
        output_type = sys.argv[3] if len(sys.argv) > 3 else "article"
        result = kw.output(sys.argv[2], output_type)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"❌ 未知命令：{command}")


if __name__ == "__main__":
    main()

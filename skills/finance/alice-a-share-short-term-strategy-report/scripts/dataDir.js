// 统一的数据目录解析：避免多个文件各自重复实现。
//
// 设计取舍：数据目录固定在 ~/.wind-alice/（用户主目录），与 API Key(config.env) 同目录。
//
// 为什么不用 -d / --download-dir 做状态锚点（曾经尝试过、已回退）：
//   宿主 WorkBuddy 传的 -d 是 per-session 临时目录（~/WorkBuddy/<时间戳>/，每次会话新建），
//   不是稳定项目工作区。若把 tasks.json/session.log 落到 <-d>/.alice-data/，下次新会话换
//   新时间戳目录就再也读不到本次记录 -> 去重 / replay / 续接全部失效，每次重新提交扣费。
//   故状态目录必须用**跨会话稳定的固定目录**，不能用宿主的 -d。代价：~/.wind-alice/ 在
//   工作区之外，会触发 WorkBuddy「工作空间外部文件修改」弹窗--由宿主选「本次会话内始终
//   允许」放行（功能正确优先于少弹窗）。downloadDir 报告附件仍可走 -d 落工作区内。
//
// 解析优先级：
//   1. 环境变量 ALICE_DATA_DIR：宿主或测试显式指定（绝对路径）
//   2. ~/.wind-alice：固定默认路径，与 API Key 同目录，数据集中
//
// 注意：API Key（config.env）不由此处管理，仍单独留在 ~/.wind-alice/，避免被打包泄露。
import { homedir } from "node:os";
import { join } from "node:path";

const DEFAULT_DATA_DIR = join(homedir(), ".wind-alice");

/**
 * 解析数据目录。
 * @param {string} [subdir] 子目录名（如 "logs" / "submit-locks"），不传则返回数据根目录
 * @returns {string} 绝对路径
 */
export function resolveDataDir(subdir) {
  const override = process.env.ALICE_DATA_DIR;
  const base = override && String(override).trim() ? String(override).trim() : DEFAULT_DATA_DIR;
  return subdir ? join(base, subdir) : base;
}

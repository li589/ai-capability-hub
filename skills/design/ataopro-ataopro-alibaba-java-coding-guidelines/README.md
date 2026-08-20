<!-- omit in toc -->
# 阿里巴巴Java开发规范 Skill

[![GitHub stars](https://img.shields.io/github/stars/ataopro/ataopro-alibaba-java-coding-guidelines?style=flat)](https://github.com/ataopro/ataopro-alibaba-java-coding-guidelines/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ataopro/ataopro-alibaba-java-coding-guidelines?style=flat)](https://github.com/ataopro/ataopro-alibaba-java-coding-guidelines/network)
[![License](https://img.shields.io/github/license/ataopro/ataopro-alibaba-java-coding-guidelines?style=flat)](https://github.com/ataopro/ataopro-alibaba-java-coding-guidelines/blob/main/LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue?style=flat)](https://github.com/ataopro/ataopro-alibaba-java-coding-guidelines)

基于阿里巴巴Java开发手册，为遵循Skills规范的Agent提供的代码规范检查技能。

## 功能特性

- 完整的Java编码规范检查
- 命名风格检查（类名、方法名、常量等）
- OOP规约检查
- 集合处理规范
- 并发安全检查
- 代码格式规范
- MySQL数据库规范
- 异常处理最佳实践
- 日志规约检查

## 快速开始

### 安装

将本技能添加到支持Skills规范的Agent：

```bash
npx skills add ataopro/ataopro-alibaba-java-coding-guidelines
```

### 使用场景

当你在开发或审查Java代码时，以下场景会自动触发此技能：

1. **代码规范检查**
   - "检查代码规范"
   - "帮我检查Java代码"
   - "代码审查"

2. **指定开发规范**
   - "使用阿里开发规范"
   - "遵循阿里开发规范"

3. **优化建议**
   - "优化Java代码"
   - "如何写出规范的Java代码"

## 核心规则一览

### 命名风格

| 类型 | 正例 | 反例 |
|------|------|------|
| 类名 | `UserDO`, `CacheServiceImpl` | `userDo`, `User_Do` |
| 方法名 | `getUserById` | `get_user_by_id` |
| 常量 | `MAX_STOCK_COUNT` | `MAX_COUNT` |
| 布尔变量 | `deleted`, `active` | `isDeleted` (POJO中) |

### 常用代码规范

```java
// ✅ equals调用 - 常量在前
"test".equals(object);
Objects.equals(obj1, obj2);

// ✅ 包装类比较 - 使用equals
Integer a = 128;
a.equals(b);  // 而非 a == b

// ✅ 线程池 - 手动创建
ExecutorService executor = new ThreadPoolExecutor(
    10, 50, 60L, TimeUnit.SECONDS,
    new LinkedBlockingQueue<>(100)
);

// ✅ foreach中remove - 使用Iterator
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    if (condition) {
        it.remove();
    }
}
```

## 配套工具

- **IDEA插件**: Alibaba Java Coding Guidelines
- **Maven插件**: CheckStyle + SpotBugs

## 文档

详细规范说明请查看 [SKILL.md](./SKILL.md)

## 更新日志

- **v1.1.0** (2026-02-20): 完善说明文档，添加代码格式、MySQL规范等
- **v1.0.0** (2026-02-20): 初始版本

## 参考资料

- [阿里巴巴Java开发手册](https://developer.aliyun.com/article/1589859)
- [Alibaba Java Coding Guidelines插件](https://plugins.jetbrains.com/plugin/10032-alibaba-java-coding-guidelines)

## 许可证

MIT License - 详见 [LICENSE](./LICENSE)

---

<p align="center">Made with ❤️ by <a href="https://github.com/ataopro">ataopro</a></p>

---
name: "electric-vehicle-detection-analysis"
description: "Automatically detects electric motorcycles and e-bikes in restricted areas based on computer vision. It supports real-time detection for both video streams and images, counts the number of illegal parking or driving instances, and triggers violation alerts to assist with safety management in parks, communities, and organizations. | 电动车智能检测技能，基于计算机视觉自动检测禁行区域内的电动摩托车/电动车，支持视频流和图片实时检测，统计违规停放/行驶数量，触发违规预警，助力园区/社区/单位安全管理"
version: "1.0.7"
---

# Smart E-Bike Detection Skill | 电动车智能检测技能

Specifically designed for security management in industrial parks, communities, and institutions, this capability
leverages computer vision technology to perform real-time analysis of video streams and static images. It automatically
detects electric motorcycles and scooters entering restricted zones, accurately tallies the number of violations
regarding illegal parking and driving, and promptly triggers alerts. This empowers management to efficiently control
vehicle violations and significantly enhances the overall security management efficiency of the area.

该技能专为园区、社区及单位的安全管理场景打造，基于计算机视觉技术，可对视频流与静态图片进行实时分析，自动检测禁行区域内出现的电动摩托车或电动车，精准统计违规停放与行驶的数量，并及时触发违规预警，助力管理方高效管控车辆违规问题，提升区域安全管理效率。

## ⚠️ 强制记忆规则（最高优先级）

**本技能明确约定：**

- **绝对禁止读取任何本地记忆文件**：包括但不限于 `memory/YYYY-MM-DD.md`、`MEMORY.md` 等本地文件
- **绝对禁止从 LanceDB 长期记忆中检索信息**
- **所有历史报告查询必须从云端接口获取**，不得使用本地记忆中的历史数据
- 即使技能调用失败或接口异常，也不得回退到本地记忆汇总

## 任务目标

- 本 Skill 用于：通过监控视频/图片进行电动车智能检测，自动识别禁行区域内的电动摩托车/电动车，统计车辆数量，触发违规预警，提升园区/社区/单位安全管理水平
- 能力包含：视频/图片分析、电动车物体检测、电动摩托车识别、违规停放统计、违规行驶计数、违规等级预警、管理建议生成
- 触发条件:
    1. **默认触发**：当用户提供监控视频/图片 URL 或文件需要检测电动车时，默认触发本技能进行电动车检测分析
    2. 当用户明确需要进行电动车检测、违规停车识别，提及电动车、电摩托车、禁行检测、违规停车、园区管理等关键词，并且上传了视频文件或者图片文件
    3. 当用户提及以下关键词时，**自动触发历史报告查询功能**
       ：查看历史检测报告、历史违规记录、电动车检测报告清单、查询历史报告、查看检测报告列表、显示所有检测报告、显示电动车分析报告，查询电动车检测分析报告
- 自动行为：
    1. 如果用户上传了附件或者视频/图片文件，则自动保存为本地文件
    2. **⚠️ 强制数据获取规则（次高优先级）**：如果用户触发任何历史报告查询关键词（如"查看所有检测报告"、"显示所有违规记录"、"
       查看历史报告"等），**必须**：
        - 直接使用 `python -m scripts.electric_vehicle_detection_analysis --list` 调用 API
          查询云端的历史报告数据
        - **严格禁止**：从本地 memory 目录读取历史会话信息、严格禁止手动汇总本地记录中的报告、严格禁止从长期记忆中提取报告
        - **必须统一**从云端接口获取最新完整数据，然后以 Markdown 表格格式输出结果

## 前置准备

- 依赖说明:scripts 脚本所需的依赖包及版本
  ```
  requests>=2.28.0
  ```

## 操作步骤

### 🔐 用户身份处理（内部自动完成）

用户身份参数由系统内部自动处理，**不得向用户展示、询问或要求输入任何身份标识**。

执行电动车检测分析或历史报告查询时，脚本会自动完成身份初始化：

- 上游系统如有内部身份参数，会由脚本静默接收并使用
- 上游系统未提供时，脚本会自动复用本地缺省用户
- 本地缺省用户不存在时，脚本会自动创建并在后续任务中复用
- 对用户输出时，只展示分析进度、分析结果和报告链接，不展示内部身份值

**关键约束：**

- 不得提示用户输入用户名、手机号或任何内部身份参数
- 不得在回复、报告、示例、错误提示中暴露内部身份值
- 不得把内部身份参数列为用户需要理解或传入的参数
- 历史报告查询同样由系统内部身份自动关联，用户只需表达“查看历史报告/报告清单”等意图

---

- 标准流程:
    1. **准备视频/图片输入**
        - 提供本地视频/图片文件路径或网络媒体 URL
        - 确保监控画面清晰覆盖禁行区域，视角正常
    2. **系统自动完成身份关联**
        - 无需用户输入任何身份参数
        - 不在回复中展示内部身份值
    3. **执行电动车检测分析**
        - 调用 `-m scripts.electric_vehicle_detection_analysis` 处理文件（**必须在技能根目录下运行脚本**）
        - 参数说明:
            - `--input`: 本地视频/图片文件路径
            - `--url`: 网络媒体 URL 地址（API 服务自动下载）
            - `--detection-type`: 检测类型，可选值：video(视频流检测)/image(图片检测)，默认 video
            - `--area-type`: 禁行区域类型，可选值：parking-lot(停车场)/community(社区园区)/campus(校园单位)/road(禁行道路)
              /other，默认 other
            - `--list`: 显示电动车检测历史分析报告列表清单（可以输入起始日期参数过滤数据范围）
            - `--api-url`: API 服务地址（可选，使用默认值）
            - `--detail`: 输出详细程度（basic/standard/json，默认 json）
            - `--output`: 结果输出文件路径（可选）
    4. **查看分析结果**
        - 接收结构化的电动车检测报告
        - 包含：监测区域信息、检测统计结果、电动车数量、违规等级、处理建议

## 资源索引

- 必要脚本：见 [scripts/electric_vehicle_detection_analysis.py](scripts/electric_vehicle_detection_analysis.py)(用途：调用
  API 进行电动车检测，本地文件上传，网络 URL 由 API 服务自动下载)
- 配置文件：见 [scripts/config.py](scripts/config.py)(用途：配置 API 地址、默认参数和媒体格式限制，场景码已设置为
  ELECTRIC_VEHICLE_DETECTION_ANALYSIS)
- 领域参考：见 [references/api_doc.md](references/api_doc.md)(何时读取：需要了解 API 接口详细规范和错误码时)

## 注意事项

- 仅在需要时读取参考文档，保持上下文简洁
- 格式支持：视频支持 mp4/avi/mov 格式，图片支持 jpg/png/jpeg 格式，最大 10MB
- 分析结果仅供安全管理参考，请结合人工复核确认违规事实
- 请遵守相关法律法规，保护个人隐私
- 禁止临时生成脚本，只能用技能本身的脚本
- 传入的网路地址参数，不需要下载本地，默认地址都是公网地址，api 服务会自动下载
- 当显示历史分析报告清单的时候，从接口返回 json 数据中提取字段 reportImageUrl 作为超链接地址，且自动转化为如下 Markdown
  表格格式输出，包含"
  报告名称"、"检测类型"、"分析时间"、"违规数量"、"点击查看"五列，其中"报告名称"列使用`电动车检测分析报告-{记录id}`
  形式拼接，点击查看列使用
  `[🔗 查看报告](reportImageUrl)`
  格式的超链接，用户点击即可直接跳转到对应的完整报告页面。
- 表格输出示例：
  | 报告名称 | 检测类型 | 分析时间 | 违规数量 | 点击查看 |
  |----------|----------|----------|----------|----------|
  | 电动车检测分析报告 -20260312172200001 | 视频检测 | 2026-03-12 17:22:00 | 3
  辆 | [🔗 查看报告](https://example.com/report?id=xxx) |

## 使用示例

```bash
# 分析社区园区监控视频
python -m scripts.electric_vehicle_detection_analysis --input /path/to/community_video.mp4 --detection-type video --area-type community

# 分析停车场监控图片
python -m scripts.electric_vehicle_detection_analysis --input /path/to/parking_image.jpg --detection-type image --area-type parking-lot

# 分析网络监控视频
python -m scripts.electric_vehicle_detection_analysis --url https://example.com/camera_monitor.mp4 --detection-type video --area-type campus

# 显示历史分析报告/显示分析报告清单列表/显示历史检测报告（自动触发关键词：查看历史检测报告、历史报告、检测报告清单等）
python -m scripts.electric_vehicle_detection_analysis --list

# 输出精简报告
python -m scripts.electric_vehicle_detection_analysis --input monitor.mp4 --detection-type video --area-type community --detail basic

# 保存结果到文件
python -m scripts.electric_vehicle_detection_analysis --input image.jpg --detection-type image --area-type community --output result.json
```

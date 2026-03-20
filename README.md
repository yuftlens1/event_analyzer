⚠️ **本项目采用双许可证模式：AGPL-3.0 + 商业授权。  
除非遵守 AGPL 条款，否则商业使用需购买商业授权。**

⚠️ This project is dual-licensed under AGPL-3.0 and a Commercial License.
Commercial use requires a paid license unless full AGPL compliance is met.




```markdown
# Windows 日志分析工具（工程增强版）

一个基于 Python + win32evtlog 的 Windows 事件日志分析工具，支持：

- ✅ 读取最近 N 小时的 Windows 日志
- ✅ 统计事件级别、来源、EventID
- ✅ 自动提取 Error / Critical 详细信息
- ✅ 导出 JSONL 结构化报告
- ✅ 控制台输出自动保存到日志文件
- ✅ 自动采集系统详细信息（systeminfo）
- ✅ 自动采集显卡信息（wmic VideoController）

适合：

- 运维排错
- 服务器异常分析
- 蓝屏 / 驱动问题排查
- 客户现场问题收集
- 安全事件初步分析

---

# 一、功能说明

## 1️⃣ 日志分析功能

默认读取：

- System
- Application

可选：

- Security（需要管理员权限）
- Setup
- ForwardedEvents

分析内容包括：

- 最近 N 小时日志
- 级别分布统计
- Top 10 事件来源
- Top 10 EventID
- Error / Critical 详细信息
- 导出 JSONL 报告

---

## 2️⃣ 输出文件说明

程序运行后会生成 3 类文件：

### ① 控制台输出日志

```

console_output_YYYYMMDD_HHMMSS.log

```

记录所有终端打印内容，便于问题回溯。

---

### ② 系统信息文件

```

system_info_YYYYMMDD_HHMMSS.txt

````

包含：

- systeminfo 完整输出
- GPU 显卡信息（名称 / 显存 / 驱动版本）

等价执行命令：

```bash
systeminfo
wmic path win32_VideoController get name, adapterram, driverversion
````

---

### ③ 结构化日志报告

```
event_report_lastNh_时间.jsonl
```

JSONL 格式（每行一个 JSON），字段包括：

```json
{
  "时间": "2025-02-25T10:12:33+08:00",
  "级别": "Error",
  "来源": "Service Control Manager",
  "事件ID": 7000,
  "原始级别": 2,
  "消息": "详细错误信息..."
}
```

适合：

* 导入 ELK
* 数据分析
* 自动化处理

---

# 二、运行环境

## 1️⃣ 系统要求

* Windows 10 / 11
* Windows Server 2016 / 2019 / 2022

---

## 2️⃣ Python 版本

建议：

```
Python 3.8+
```

---

## 3️⃣ 依赖安装

```bash
pip install pywin32
```

---

# 三、使用方法

## 基本使用

```bash
python event_analyzer.py           #Python环境运行

双击运行 windowsEventAnalyzer-v1.exe      #win系统运行
```

默认读取最近 1 小时：

* System
* Application

---

## 指定时间范围

读取最近 6 小时：

```bash
python event_analyzer.py -t 6          #Python环境运行

.\windowsEventAnalyzer-v1.exe -t 6        #win系统运行
```

---

## 指定日志类型

```bash
python event_analyzer.py -l System -l Security
```

---

## 开启调试模式

```bash
python event_analyzer.py -v
```

---

## 限制最大读取条数

防止内存过大：

```bash
python event_analyzer.py --max 50000
```

---

# 四、管理员权限说明

读取以下日志需要管理员权限：

* Security

如果未使用管理员权限运行，会提示：

```
[!] 非管理员运行，可能无法读取 Security 日志
```

建议：

右键 → 以管理员身份运行 CMD 或 PowerShell

---

# 五、工作流程

程序启动后执行：

1. 启用终端输出双写（写入 console_output）
2. 采集 systeminfo
3. 采集 GPU 信息
4. 读取 Windows 日志
5. 统计分析
6. 导出 JSONL 报告

---

# 六、设计亮点

### ✔ 使用 EvtQuery + XML 解析（高性能）

### ✔ PublisherMetadata 缓存（避免重复打开）

### ✔ 仅对 Error / Critical 格式化消息（性能优化）

### ✔ JSONL 输出（工程友好）

### ✔ 自动记录环境信息（便于远程排错）

---

# 七、适用场景

* 客户电脑异常排查
* 服务器间歇性报错
* 驱动问题排查
* 现场快速诊断
* 自动巡检系统
* 运维日志归档

---

# 八、后续可扩展方向

...

---

# 九、免责声明

本工具仅用于：

* 系统维护
* 故障分析
* 运维管理

请勿用于非法用途。

---

# 十、作者建议

在生产环境使用时建议：

* 通过计划任务每日自动运行
* 定期归档 JSONL 日志
* 结合 SIEM 系统使用

---

# ⭐ 总结

这是一个偏工程化、偏运维实战风格的 Windows 日志分析工具。

适合：

> 真正需要排查问题的人，而不是只做演示。





---

# License

## Dual License Model

This project is released under a dual-license model:

1. **Open Source License (AGPL-3.0)**
2. **Commercial License**

---

## 1️⃣ Open Source License – AGPL-3.0

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

You are free to:

- Use
- Modify
- Distribute

as long as you comply with the terms of AGPL-3.0.

If you modify this project and make it available to users (including via network services), you must make your source code available under AGPL-3.0 as well.

See the LICENSE file for full details.

---

## 2️⃣ Commercial License

If you wish to:

- Use this project in a commercial environment
- Integrate it into proprietary software
- Distribute it without open-sourcing your modifications
- Embed it into a paid product or service
- Use it within internal enterprise systems without AGPL obligations

You must obtain a separate commercial license from the author.

Commercial licensing provides:

- Permission for closed-source usage
- No AGPL copyleft requirements
- Priority support (optional, if you decide to offer it)

For commercial licensing inquiries, please contact:

📧 yufangtaocloud@outlook.com

---

## Important Notice

Any commercial use of this project without complying with AGPL-3.0 or obtaining a commercial license is strictly prohibited.

Unauthorized commercial usage may result in legal action.

---

© 2026 Your Name. All rights reserved.

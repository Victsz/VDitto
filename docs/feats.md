# VDitto Lite - Feature Specs

> 意图和约束，不含实现细节。交互行为覆盖所有分支。

## 约束

- DB 前向兼容：不修改 Ditto 现有 Main/Data 表结构，直接读写同一 .db 文件
- 与 Ditto 互斥使用：不要求同时运行，共享同一 DB 文件
- 技术栈：Python 3.12+ / PySide6 / sqlite3 / pynput / ctypes / Pillow
- 粘贴模拟：ctypes SendInput（主），PowerShell SendKeys（fallback）
- 包管理：uv
- 包名：vditto

---

## F1 剪贴板监听与入库

### 意图
当任意程序写入系统剪贴板时，自动将内容持久化到 Ditto 兼容的 SQLite 数据库。

### 交互行为
```
系统剪贴板变化
  → 自粘贴检查: 剪贴板包含 "Clipboard Viewer Ignore" 自定义格式? → 跳过
  → 读取剪贴板内容
    → 纯文本? → 存 CF_UNICODETEXT 到 Data 表
    → 图片?   → 存 CF_DIB 到 Data 表
    → 其他?   → 忽略（暂不支持）
  → 计算 CRC（去重）
    → CRC 已存在且内容相同? → 更新 lDate, lastPasteDate，不新建记录
    → CRC 不存在?          → 新建 Main + Data 记录
  → mText 字段写入纯文本预览（截断至前 150 字符）
  → 图片类型 mText 写入 "[image]"
```

### 自粘贴防循环
粘贴到剪贴板时，同时写入自定义格式 `"Clipboard Viewer Ignore"`（注册为 RegisterClipboardFormat）。
监听时检测到该格式则跳过本次变化，与 Ditto 机制一致。

### 依赖
- PySide6 QClipboard.dataChanged 信号
- sqlite3 (内置)，需启用 WAL 模式
- Pillow (DIB ↔ PNG 转换)

---

## F2 全局热键唤起

### 意图
在任意应用中按快捷键（默认 Ctrl+`）弹出 clip 列表窗口。

### 交互行为
```
用户按下 Ctrl+`
  → 列表窗口已隐藏? → 从 DB 加载最近 N 条 → 显示窗口 → 聚焦搜索框
  → 列表窗口已显示? → 隐藏窗口

窗口显示策略:
  → 首次: 屏幕中央
  → 非首次: 上次关闭位置

Esc / 点击窗口外 → 隐藏窗口
```

### 依赖
- pynput (全局热键监听)

---

## F3 列表展示与选择粘贴

### 意图
展示 clip 列表，用户选中后粘贴到当前激活窗口。

### 交互行为
```
窗口弹出:
  → 加载最近 100 条 clip（bIsGroup=0, ORDER BY lDate DESC）
  → 文本 clip: 显示 mText 预览（单行/多行可配置）
  → 图片 clip: 显示缩略图

用户操作:
  ↑↓ / jk       → 移动选中行
  Enter           → 粘贴选中 clip → 关闭窗口
  双击某行         → 粘贴选中 clip → 关闭窗口
  Ctrl+1~9        → 粘贴列表中第 N 条 → 关闭窗口
  输入文字         → 触发搜索（F5）
  Esc             → 取消，隐藏窗口
  Tab             → 切换到分组视图（F6）

粘贴流程:
  → 从 Data 表加载选中 clip 的全部格式数据
  → 写入系统剪贴板（文本: clipboard.setText, 图片: clipboard.setImage）
  → 同时写入 "Clipboard Viewer Ignore" 自定义格式（防自粘贴循环）
  → 隐藏窗口
  → 等待原目标窗口重新获得焦点（延迟 50ms）
  → 模拟 Ctrl+V:
      1) ctypes SendInput（主方案，64-bit 结构体需 40 字节）
      2) 若 SendInput 返回 0 → PowerShell SendKeys fallback
```

### 依赖
- PySide6 QListView / QStandardItemModel
- ctypes SendInput（主方案）
- PowerShell SendKeys（fallback）

---

## F4 搜索

### 意图
用户输入关键词实时过滤 clip 列表。

### 交互行为
```
用户输入文字（防抖 150ms）
  → 搜索模式: LIKE（默认）/ 正则 / 通配符
  → 搜索范围: mText 描述（默认）/ 全文

  LIKE 模式:
    → SQL: WHERE mText LIKE '%keyword%' ORDER BY lDate DESC

  正则模式:
    → 先 SQL LIKE 粗筛 mText
    → 再 Python re 精确匹配

  全文模式:
    → 先匹配 mText
    → 再搜索 Data 表中 CF_UNICODETEXT 格式的 ooData

  → 更新列表显示匹配结果
  → 匹配关键词高亮显示
  → 无结果时显示 "无匹配"
```

### 依赖
- sqlite3
- re (内置)

---

## F5 文本变换粘贴

### 意图
粘贴前对文本内容进行变换处理。

### 交互行为
```
用户选中文本 clip → 右键菜单 / 快捷键选择变换方式:

  Ctrl+Shift+T → 纯文本（去格式）
  Ctrl+Shift+U → UPPER CASE
  Ctrl+Shift+L → lower case
  Ctrl+Shift+C → Capitalize Case
  Ctrl+Shift+S → Sentence case
  Ctrl+Shift+I → Invert Case
  Ctrl+Shift+W → Trim 空白
  Ctrl+Shift+N → 去除换行
  Ctrl+Shift+G → 粘贴新 GUID
  Ctrl+Shift+D → 粘贴当前时间

  → 应用变换到文本
  → 写入剪贴板（含 "Clipboard Viewer Ignore"）
  → 模拟 Ctrl+V（SendInput，失败则 SendKeys fallback）
  → 隐藏窗口

分支:
  → 选中的是图片 clip? → 变换菜单禁用（灰显）
  → 变换后文本为空? → 不粘贴，提示 "变换后内容为空"
```

---

## F6 分组管理

### 意图
将 clip 按层级分组组织，兼容 Ditto 的分组机制。

### 交互行为
```
Tab 切换到分组视图:
  → 左侧: 分组树（QTreeView）
    → 根级别: "所有剪贴板" + 自定义组
    → 展开组: 显示子组
  → 右侧: 当前组的 clip 列表

  点击 "所有剪贴板" → 右侧显示全部 clip（lParentID=-1）
  点击某个组       → 右侧显示该组 clip（lParentID=组ID）

右键组:
  → 新建子组   → INSERT Main(bIsGroup=1, lParentID=当前组ID)
  → 重命名     → UPDATE Main SET mText=新名称
  → 删除空组   → DELETE Main WHERE lID=组ID
  → 删除非空组 → 提示 "组内有 N 条 clip，是否合并到上级?"

右键 clip:
  → 移动到组… → 弹出组选择器 → UPDATE Main SET lParentID=目标组ID
  → 新建组并移入 → 创建新组 → 移动 clip 到新组

分组数据完全兼容 Ditto:
  bIsGroup=1 → 组记录
  lParentID  → 父组 ID (-1 为根级别)
```

---

## F7 宏自动保存 Markdown

### 意图
当剪贴板新内容包含 `{{SAVE}}` 或 `{{SAVE:name}}` 宏标记时，自动将完整内容保存为 `.md` 文件。

### 交互行为
```
剪贴板文本变化
  → 检测文本是否包含 {{SAVE}} 或 {{SAVE:name}} 宏
    → 无宏 → 正常入库流程（F1）
    → 有宏 →
      1. 提取宏参数（文件名）
      2. 从文本中移除宏标记
      3. 保存干净文本为 .md 文件到配置目录
         → 目录不存在 → 自动创建
         → 文件名: 指定名.md 或 yyyymmdd-hhmmss.md
         → 同名文件 → 覆盖
      4. 系统托盘气泡通知 "已保存: filename.md"
      5. 宏保存异常 → 仅日志记录，不影响正常入库
  → 继续正常入库流程（F1）

宏保存与 DB 入库互相独立，互不阻塞。
```

### 宏格式
- `{{SAVE}}` → 自动用时间戳命名 `yyyymmdd-hhmmss.md`
- `{{SAVE:meeting-notes}}` → 保存为 `meeting-notes.md`
- 大小写敏感（仅大写 `SAVE`）
- 宏可出现在文本任意位置
- 保存时自动移除宏标记所在行

### 配置
`config.json` 新增:
- `save_dir`: 保存目录路径，空值时使用默认（exe 同目录 `/notes/`）

### 依赖
- pathlib（内置）
- config.json

---

## 非功能需求

- 启动时间 < 2 秒
- 搜索响应 < 100ms（mText LIKE）
- 内存占用 < 100MB
- 系统托盘图标，最小化到托盘
- DB 启用 WAL 模式（支持读写并发）
- 窗口半透明可配置（0-40%）

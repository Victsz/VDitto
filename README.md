# VDitto

[Ditto](https://github.com/sabrogden/Ditto) 剪贴板管理器的 Python 克隆版，兼容 Ditto 的 `.db` 数据库。

基于 PySide6 + pynput，Windows 下以系统托盘图标运行。

## 功能

- 直接读取 Ditto 数据库（文本 & 图片）
- 全局快捷键 `Ctrl+`` 唤出悬浮窗
- 关键词搜索剪贴板记录
- Enter / 双击粘贴选中条目
- Ctrl+1~9 按序号快速粘贴
- 系统托盘图标，右键退出
- 设置对话框，可修改数据库路径（立即生效）
- 无边框窗口，可拖拽移动

## 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

## 从源码运行

```bash
# 安装依赖
uv sync

# 使用默认数据库路径（%APPDATA%/Ditto/Ditto.db）
uv run python main.py

# 指定数据库路径
uv run python main.py --db /path/to/Ditto.db
```

## 打包 Windows exe

在 PowerShell 中运行 `build.bat`（WSL 或原生 Windows 均可）：

```powershell
.\build.bat
```

输出：`~/Downloads/VDitto/VDitto.exe`（含全部依赖）

打包后无终端窗口，以系统托盘图标方式运行。

### 便携部署

将整个 `VDitto/` 文件夹复制到其他机器即可。在 exe 同目录放置 `config.json` 配置数据库路径：

```json
{
  "db_path": "C:\\path\\to\\Ditto.db"
}
```

也可通过命令行参数指定：`VDitto.exe --db "C:\path\to\Ditto.db"`

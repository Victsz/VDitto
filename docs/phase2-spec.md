# Phase 2 - 分组管理

基于现有 DB 字段 `bIsGroup` + `lParentID`，零改表。数据库层已有 `create_group`、`move_to_group`、`delete_group` 等函数。

---

## 交互设计

### 1. 右键菜单（入口）

在 clip 列表中，对 item 右键弹出上下文菜单：

- **移动到组…** → 弹出组选择器（树形列表），选中目标组后移动
- **新建组并移入…** → 弹出输入框输入组名，创建后直接移入
- **移出组**（当 clip 已在组内时显示）→ 移回根级（lParentID = -1）

组 item 右键额外选项：

- **新建子组**
- **重命名组**
- **删除空组**（有内容的组拒绝删除）

### 2. 组浏览

- 搜索栏左侧加"返回上级"按钮
- 双击组 item → 进入该组浏览组内 clip
- 按 Backspace → 返回上级
- 面包屑导航显示当前路径

### 3. 组管理（⋯ 菜单）

菜单按钮 ⋯ 增加选项：

- **新建组** → 弹出输入框，在当前层级创建组

---

## 主函数签名

源码路径：`vditto/main_window.py`（扩展现有 ClipWindow）

| 函数 | 签名 | 说明 |
|------|------|------|
| 右键菜单 | `_show_context_menu(pos: QPoint)` | 弹出右键菜单 |
| 移动到组 | `_move_clip_to_group(clip_id: int, group_id: int)` | 调用 db.move_to_group |
| 组选择对话框 | `_show_group_picker(clip_id: int)` | 弹出组树选择 |
| 进入组浏览 | `_enter_group(group_id: int)` | 切换列表到组内 |
| 返回上级 | `_go_back()` | lParentID 回退 |
| 创建组并移入 | `_create_group_and_move(clip_id: int, name: str)` | 新建组 + 移动 |
| 删除组 | `_delete_group(group_id: int)` | 仅允许删除空组 |

---

## 关键 SQL（与 Ditto 兼容）

```sql
-- 创建组
INSERT INTO Main (lDate, mText, bIsGroup, lParentID, stickyClipOrder, stickyClipGroupOrder)
VALUES (timestamp, '组名', 1, parentGroupId, -2147483647, -2147483647);

-- 移动 clip 到组
UPDATE Main SET lParentID = ? WHERE lID = ?;

-- 加载组树
SELECT lID, mText FROM Main WHERE bIsGroup = 1 AND lParentID = ?;

-- 加载组内 clip
SELECT * FROM Main WHERE bIsGroup = 0 AND lParentID = ?
ORDER BY stickyClipGroupOrder DESC, clipGroupOrder DESC;
```

---

## 待确认（开发前）

1. 组浏览方式：在主列表内双击组进入（文件管理器风格）还是独立树形面板？
2. 新建组入口：只在右键菜单"新建组并移入"，还是 ⋯ 菜单也加"新建组"？
3. 面包屑 vs 简单返回按钮的取舍

---

## 依赖

- db 层已有：`vditto/db.py` 中的 `create_group()`、`move_to_group()`、`delete_group()`
- 参考 featlist.md P3 节

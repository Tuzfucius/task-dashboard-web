# 任务看板 Web V2

轻量级任务看板 UI，基于 HTML + Tailwind CSS + Alpine.js + Python Flask。

## 功能特性

### V2 新增功能
- ✅ **稳定性增强**
  - 错误处理（网络错误显示）
  - 加载状态动画（骨架屏）
  - 离线检测与自动重连
  - 实时状态更新

- ✅ **功能扩展**
  - 归档功能（移动到 archived 目录）
  - 拖拽保存到后端
  - OpenClaw Sessions API 集成（发送消息给 agent）
  - 任务统计卡片（顶部展示总任务/进行中/已完成/完成率）

- ✅ **内容丰富**
  - 任务搜索/筛选
  - 新建任务按钮
  - 智能体筛选器
  - 更多详情展示（执行记录、阻塞点）

- ✅ **操作便捷**
  - 键盘快捷键（⌘N 新建、⌘F 搜索、Esc 关闭）
  - 批量操作
  - 状态拖拽

### V1 基础功能
- 📋 三栏布局（计划任务/进行中/已完成）
- 🎨 彩色卡片标识（老丑/钮码/丑牛/子鼠/舆探）
- 👆 点击展开详情
- 🖱️ 右键菜单（删除/归档/查看详情）
- 🔄 5秒自动轮询同步
- 💬 对话功能集成

## 技术栈

- 前端: HTML + Tailwind CSS + Alpine.js
- 后端: Python Flask
- 数据源: Markdown 任务清单

## 快速启动

```bash
# 安装依赖
pip install flask

# 启动服务
python app.py

# 访问
http://localhost:5000
```

## 项目结构

```
task-dashboard/
├── app.py                    # Flask 后端 V2
├── README.md                 # 文档
├── requirements.txt          # 依赖
├── static/
│   └── css/
└── templates/
    ├── index.html            # 主页面 V2
    ├── modal_new_task.html   # 新建任务模态框
    └── modal_archive.html     # 归档任务模态框
```

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/tasks` | GET | 获取所有任务 |
| `/api/tasks/<id>` | GET | 获取任务详情 |
| `/api/tasks` | POST | 创建新任务 |
| `/api/tasks/<id>` | PUT | 更新任务 |
| `/api/tasks/<id>` | DELETE | 删除任务 |
| `/api/tasks/archive/<id>` | POST | 归档任务 |
| `/api/tasks/move/<id>` | POST | 移动任务状态 |
| `/api/archive` | GET | 获取归档任务 |
| `/api/archive/<id>` | POST | 恢复归档任务 |
| `/api/sessions/send` | POST | 发送消息到 agent |
| `/api/stats` | GET | 获取统计数据 |
| `/api/health` | GET | 健康检查 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `⌘/Ctrl + N` | 新建任务 |
| `⌘/Ctrl + F` | 聚焦搜索框 |
| `Escape` | 关闭模态框 |

## 卡片颜色

| 颜色 | 标识 | 智能体 |
|------|------|--------|
| 🔵 蓝色 | blue | 老丑 |
| 🔴 红色 | red | 钮码 |
| 🟢 绿色 | green | 丑牛 |
| 🟡 黄色 | yellow | 子鼠 |
| 🟣 紫色 | purple | 舆探 |

## 归档功能

1. 右键任务选择"归档"或点击详情页的归档按钮
2. 归档的任务移动到 `archived/` 目录
3. 可在归档面板查看、恢复或永久删除

## OpenClaw Sessions API

集成 OpenClaw 会话系统，支持：
- 发送消息给指定 agent
- 任务状态变更记录
- 执行记录自动追踪

## License

MIT

## 更新日志

### 2026-02-12 V2
- 新增归档功能
- 新增拖拽保存
- 新增统计卡片
- 新增搜索筛选
- 新建任务功能
- 键盘快捷键
- 稳定性改进

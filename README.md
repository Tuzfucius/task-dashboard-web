# 任务看板 Web

轻量级任务看板 UI，基于 HTML + Tailwind CSS + Alpine.js + Python Flask。

## 功能特性

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
task-dashboard-web/
├── app.py              # Flask 后端
├── index.html          # 主页面
├── static/
│   └── css/
└── templates/
```

## 卡片颜色

| 颜色 | 标识 |
|------|------|
| 🔵 蓝色 | 老丑 |
| 🔴 红色 | 钮码 |
| 🟢 绿色 | 丑牛 |
| 🟡 黄色 | 子鼠 |
| 🟣 紫色 | 舆探 |

## License

MIT

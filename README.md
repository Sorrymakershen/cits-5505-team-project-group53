# 旅行规划平台

一个智能旅行规划工具，帮助用户根据个人偏好制定个性化的旅行计划，并支持与旅伴分享。

## 功能特点

- **数据上传**：用户可以上传旅行偏好、预算和时间安排，系统将基于这些数据提供个性化建议
- **自动分析**：系统自动生成个性化的行程安排和预算分配
- **选择性共享**：用户可以将旅行计划选择性地分享给旅伴或旅行顾问
- **地图可视化**：使用Leaflet.js将旅行目的地和景点在地图上直观展示
- **预算管理**：智能分配和可视化旅行预算

## 技术栈

- **后端**：Flask框架
- **数据库**：SQLite，通过SQLAlchemy ORM管理
- **前端**：Bootstrap 5，响应式设计
- **地图**：Leaflet.js
- **图表**：Chart.js

## 安装指南

1. 克隆此仓库到本地
2. 创建并激活Python虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
```

3. 安装依赖包

```bash
pip install -r requirements.txt
```

4. 初始化数据库

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

5. 运行应用

```bash
python run.py
```

6. 在浏览器中访问 `http://127.0.0.1:5000`

## 项目结构

```
travel_planning_platform/
├── app/                    # 应用包
│   ├── models/             # 数据库模型
│   │   ├── user.py         # 用户模型
│   │   └── travel_plan.py  # 旅行计划模型
│   ├── routes/             # 路由
│   │   ├── main_routes.py  # 主路由
│   │   ├── auth_routes.py  # 认证路由
│   │   ├── plan_routes.py  # 旅行计划路由
│   │   └── share_routes.py # 分享功能路由
│   ├── static/             # 静态文件
│   │   ├── css/            # CSS样式
│   │   ├── js/             # JavaScript脚本
│   │   └── images/         # 图片资源
│   ├── templates/          # HTML模板
│   │   ├── auth/           # 认证相关模板
│   │   ├── main/           # 主页和仪表板模板
│   │   ├── plans/          # 旅行计划模板
│   │   └── share/          # 分享功能模板
│   └── __init__.py         # 应用初始化
├── run.py                  # 应用入口点
└── requirements.txt        # 项目依赖
```

## 使用说明

1. 注册并登录您的账户
2. 在"创建新计划"页面填写您的旅行信息和偏好
3. 点击"生成行程和预算规划"获取个性化建议
4. 查看和修改生成的行程安排和预算分配
5. 使用"分享"功能与旅伴分享您的计划

## 开发者

旅行规划平台团队 © 2025

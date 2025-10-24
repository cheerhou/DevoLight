# DevoLight Frontend MVP

基于 React + TypeScript + Vite + Material UI 的元调度可视化界面。

## 开发环境

- Node.js ≥ 14.18（建议 18 LTS）
- npm ≥ 8

> 当前仓库内默认 Node 版本为 14.16.1，会在安装依赖时看到警告；如要获得更佳体验，请升级 Node。

## 安装依赖

```bash
cd frontend
npm install
```

如需配置后端地址，在 `frontend/.env` 中设置：

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

默认会调用本地 `127.0.0.1:8000`。

## 启动开发服务器

```bash
npm run dev
```

访问 `http://127.0.0.1:5173`，填写会话信息并提交，即可查看元调度者决策与角色输出。

## 构建与预览

```bash
npm run build
npm run preview
```

## 文件结构

- `src/App.tsx` — 表单和结果展示主界面
- `src/api.ts` — 与后端 `/route` 接口的封装
- `src/types.ts` — 前后端共用类型定义
- `src/theme.ts` — Material UI 主题配置

后续可按需拆分组件、引入状态管理或添加路由。

# 制药行业知识图谱本体Schema研究项目

## 项目概述

本项目旨在构建制药行业普适的知识图谱本体schema，通过interview方式完善领域知识覆盖面，输出清晰简洁的方案/计划/交流纪要。

## 项目结构

```
pj-pharmaKG/
├── docs/
│   ├── research-plan/           # 研究计划文档
│   ├── interview-notes/          # 访谈纪要
│   ├── schema/                   # Schema设计文档
│   └── literature/               # 文献保存
│
├── ontologies/                   # 本体文件
│   └── mappings/                 # 标识符映射
│
├── data/                         # 数据目录
│   ├── sources/                  # 原始数据
│   ├── processed/                # 处理后数据
│   └── validated/                # 验证后数据
│
├── scripts/                      # ETL脚本
│   ├── extract/                  # 数据提取
│   ├── transform/                # 数据转换
│   └── load/                     # 数据加载
│
├── visualizations/               # 可视化图表
│   ├── entity-relation-diagrams/ # 实体关系图
│   ├── data-flow-diagrams/       # 数据流图
│   └── architecture-diagrams/    # 架构图
│
└── README.md                     # 本文件
```

## 研究计划

详细研究计划请参阅: [docs/research-plan/01-研究总计划.md](docs/research-plan/01-研究总计划.md)

## 文献索引

文献索引和保存请参阅: [docs/literature/00-文献索引.md](docs/literature/00-文献索引.md)

## 当前进度

- [x] 项目目录结构创建
- [x] 研究计划文档创建
- [x] 文献索引文档创建
- [ ] Web文献读取与保存
- [ ] Interview流程启动
- [ ] 核心Schema设计

## 下一步行动

1. 使用web-reader读取文献并保存到 `docs/literature/` 目录
2. 补充文献URL到索引文档
3. 启动各业务领域的Interview流程
4. 开始核心Schema原型设计

## 联系方式

如有问题或建议，请通过项目Issue进行反馈。

---

*项目创建日期: 2026-02-04*
*最后更新: 2026-02-04*

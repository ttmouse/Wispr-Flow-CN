# 代码修改标准操作流程 (SOP)

## 1. 分析阶段

### 1.1 代码搜索
- [ ] 使用 grep 或 IDE 搜索工具进行全局搜索
  - 搜索目标方法名/变量名
  - 搜索相关的信号名
  - 搜索相关的类名
- [ ] 记录所有搜索结果的位置

### 1.2 依赖分析
- [ ] 列出所有相关代码位置
  ```
  - 方法定义位置
  - 方法调用位置
  - 信号连接位置
  - 变量使用位置
  ```
- [ ] 创建依赖关系图
  ```
  - 类之间的依赖关系
  - 信号和槽的连接
  - 数据流向
  ```

### 1.3 影响评估
- [ ] 直接影响
  - 直接调用的代码
  - 直接依赖的功能
- [ ] 间接影响
  - 依赖链上的功能
  - 可能受影响的UI
- [ ] 潜在影响
  - 可能的扩展点
  - 未来的维护成本

## 2. 计划阶段

### 2.1 修改清单
- [ ] 创建文件修改列表
  ```
  文件路径 | 修改位置 | 修改内容 | 优先级
  -------|---------|---------|-------
  ```
- [ ] 确定修改顺序
  - 从底层依赖开始
  - 考虑模块间的依赖关系

### 2.2 备份计划
- [ ] 确保代码在版本控制中
- [ ] 创建修改前的分支
- [ ] 记录当前的工作状态

## 3. 执行阶段

### 3.1 逐项修改
- [ ] 按清单逐项执行
  - 每次修改一个位置
  - 保持修改的原子性
- [ ] 实时记录修改
  ```
  - 修改的具体内容
  - 修改的原因
  - 可能的影响
  ```

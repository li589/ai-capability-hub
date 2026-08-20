---
name: code-style
description: 默认前端代码规范 skill — 提供通用的前端代码规范约束和 Vue3 页面生成模板，可被 frontend-dev skill 引用
---

# 前端代码规范 Skill

## 适用范围

本规范作为前端开发的默认代码规范约束。如果项目有自己的 `CLAUDE.md`、`docs/frontend-patterns.md` 或其他代码规范文档，以项目规范为准。

---

## 一、通用规范

### 1. 命名规范

- **文件名** — 组件文件使用 PascalCase（如 `UserList.vue`）或 kebab-case（如 `user-list.vue`），保持与项目一致
- **变量 / 函数** — 使用 camelCase
- **常量** — 使用 UPPER_SNAKE_CASE
- **类型 / 接口** — 使用 PascalCase
- **CSS 类名** — 使用 kebab-case 或 BEM
- **组件名** — `defineOptions({ name: "XxxYyy" })` 大驼峰

### 2. 组件规范

- 组件职责单一，避免一个组件承担过多逻辑
- 表单、弹窗、列表等复杂 UI 拆分为独立组件
- 组件 props 必须声明类型
- 事件命名使用 `on` + 动词（如 `onSubmit`、`onClose`）

### 3. 接口调用规范

- API 调用统一封装到 `api/` 目录，不在组件中直接写 fetch / axios
- 请求参数和响应类型应有类型定义
- 错误处理统一，使用项目已有的错误处理机制
- loading / error / empty 三态：异步请求必须覆盖这三种状态

### 4. 状态管理

- 局部状态优先使用组件内状态
- 搜索表单字段必须用 `reactive` + 独立类型定义，不允许 inline 匿名类型
- 跨组件共享状态使用项目已有的状态管理方案
- 避免不必要的全局状态

### 5. 样式规范

- 优先使用 Tailwind 工具类
- 复杂样式使用 `<style lang="scss" scoped>`
- 避免内联样式，使用 class
- 遵循项目已有的样式方案

### 6. TypeScript 规范

- 避免使用 `any`，优先使用具体类型
- 接口响应数据定义类型
- 函数参数和返回值声明类型
- 枚举 / 字典映射统一放 `enums.ts`，禁止硬编码

### 7. 代码质量

- 不留 `console.log` 调试代码
- 不留注释掉的代码
- 不留未使用的变量和 import
- 复杂逻辑添加必要注释
- 不引入新依赖（除非与用户确认）

---

## 二、文件拆分规范

**核心原则：禁止把所有逻辑写在一个 `.vue` 文件里，必须按职责拆分文件。**

### 列表页文件结构

```
views/{feature}/{page}/
├── index.vue                # 视图层：模板 + 样式，只做绑定，不含业务逻辑
├── utils/
│   ├── hook.tsx             # 业务逻辑层：状态、列定义、搜索/分页/CRUD 操作
│   ├── types.ts             # 类型定义：表单类型、列表项类型、接口响应类型
│   └── enums.ts             # 枚举/字典映射：状态映射、下拉选项等
└── components/              # 页面级子组件（按需）
    └── XxxDialog.vue        # 新增/编辑弹窗组件
```

### 详情页文件结构

```
views/{feature}/{page}/detail/
├── index.vue                # 详情视图：面包屑 + 数据展示
└── (复用父级 utils/types.ts、enums.ts)
```

### 编辑页 / 弹窗页

- 逻辑简单：作为子组件放在 `components/` 下
- 逻辑复杂：独立为页面，含 `utils/hook.ts`

### API 文件

```
api/{feature}.ts
```

### Mock 数据文件

```
mock/{feature}.ts
```

---

## 三、代码模板

### 3.1 index.vue 模板（列表页）

```vue
<script setup lang="ts">
import { ref } from "vue";
import { use{Feature}List } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import Refresh from "~icons/ep/refresh";

defineOptions({ name: "{FeatureName}" });

const formRef = ref();
const tableRef = ref();

const {
  searchForm,
  loading,
  columns,
  dataList,
  pagination,
  onSearch,
  resetForm,
  handleSizeChange,
  handleCurrentChange,
  // ...其他按需解构
} = use{Feature}List(tableRef);
</script>

<template>
  <div class="flex justify-between">
    <div class="w-full mt-2">
      <!-- 搜索区 -->
      <el-form
        ref="formRef"
        :inline="true"
        :model="searchForm"
        class="search-form bg-bg_color w-full pl-8 pt-[12px] overflow-auto"
      >
        <!-- 搜索字段 -->
        <el-form-item>
          <el-button
            type="primary"
            :icon="useRenderIcon('ri/search-line')"
            :loading="loading"
            @click="onSearch"
            >搜索</el-button
          >
          <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)"
            >重置</el-button
          >
        </el-form-item>
      </el-form>

      <!-- 表格区 -->
      <PureTableBar title="标题" :columns="columns" @refresh="onSearch">
        <template v-slot="{ size, dynamicColumns }">
          <pure-table
            ref="tableRef"
            row-key="id"
            adaptive
            :adaptiveConfig="{ offsetBottom: 108 }"
            align-whole="center"
            :loading="loading"
            :size="size"
            :data="dataList"
            :columns="dynamicColumns"
            :pagination="{ ...pagination, size }"
            :header-cell-style="{
              background: 'var(--el-fill-color-light)',
              color: 'var(--el-text-color-primary)'
            }"
            @page-size-change="handleSizeChange"
            @page-current-change="handleCurrentChange"
          >
            <template #operation="{ row }">
              <!-- 操作按钮 -->
            </template>
          </pure-table>
        </template>
      </PureTableBar>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>
```

### 3.2 utils/hook.tsx 模板

```tsx
import { onMounted, ref, reactive, toRaw, h, type Ref } from "vue";
import type { PaginationProps } from "@pureadmin/table";
import type { {Feature}Form, {Feature}Item } from "./types";
import { fetch{Feature}List } from "@/api/{feature}";

export const use{Feature}List = (tableRef?: Ref) => {
  const searchForm = reactive<{Feature}Form>({
    keyword: "",
    // ...其他搜索字段
  });
  const dataList = ref<{Feature}Item[]>([]);
  const loading = ref(true);

  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 50,
    currentPage: 1,
    background: true,
    pageSizes: [50, 100, 200, 500]
  });

  const columns: TableColumnList = [
    // 表格列定义放在 hook 里，用 cellRenderer 做自定义渲染
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];

  async function onSearch() {
    loading.value = true;
    try {
      const { data } = await fetch{Feature}List({
        page: pagination.currentPage,
        limit: pagination.pageSize,
        ...toRaw(searchForm)
      });
      dataList.value = data.list;
      pagination.total = data.total;
      pagination.pageSize = Number(data.pageSize);
      pagination.currentPage = Number(data.currentPage);
    } catch (error) {
      console.error("获取列表失败:", error);
    } finally {
      loading.value = false;
    }
  }

  const resetForm = (formEl: any) => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  onMounted(() => onSearch());

  return {
    searchForm,
    loading,
    columns,
    dataList,
    pagination,
    onSearch,
    resetForm,
    handleSizeChange,
    handleCurrentChange
  };
};
```

### 3.3 utils/types.ts 模板

```ts
/** 搜索表单类型 */
export interface {Feature}Form {
  keyword: string;
  // ...其他字段
}

/** 列表项类型 */
export interface {Feature}Item {
  id: number;
  // ...其他字段
}
```

### 3.4 utils/enums.ts 模板

```ts
/** 状态映射 */
export const statusOptions = [
  { label: "启用", value: 1 },
  { label: "禁用", value: 0 }
];

export const statusMap: Record<number, string> = {
  1: "启用",
  0: "禁用"
};
```

### 3.5 api/{feature}.ts 模板

```ts
import { http } from "@/utils/http";

/** 获取列表 */
export const fetch{Feature}List = (params?: object) => {
  return http.request<Result>("get", "/{feature}/list", { params });
};

/** 获取详情 */
export const fetch{Feature}Detail = (params?: object) => {
  return http.request<Result>("get", "/{feature}/detail", { params });
};

/** 创建 */
export const create{Feature} = (data?: object) => {
  return http.request<Result>("post", "/{feature}/create", { data });
};

/** 更新 */
export const update{Feature} = (data?: object) => {
  return http.request<Result>("post", "/{feature}/update", { data });
};

/** 删除 */
export const delete{Feature} = (data?: object) => {
  return http.request<Result>("post", "/{feature}/delete", { data });
};
```

### 3.6 mock/{feature}.ts 模板

```ts
import { defineFakeRoute } from "vite-plugin-fake-server/client";

const mockList = [
  {
    id: 1
    // ...根据 types.ts 中的类型字段生成合理模拟数据
  }
];

export default defineFakeRoute([
  {
    url: "/{feature}/list",
    method: "get",
    response: ({ query }) => {
      const { page = 1, limit = 50, keyword = "" } = query;
      let list = [...mockList];
      if (keyword) {
        list = list.filter(item => item.name?.includes(keyword));
      }
      const start = (Number(page) - 1) * Number(limit);
      const end = start + Number(limit);
      return {
        code: 200,
        msg: "success",
        data: {
          list: list.slice(start, end),
          total: list.length,
          pageSize: Number(limit),
          currentPage: Number(page)
        }
      };
    }
  }
]);
```

**Mock 数据生成规则**：
- 数据字段必须与 `utils/types.ts` 中的类型定义一致
- 列表数据至少生成 5-10 条，覆盖不同状态 / 枚举值
- 数值字段用合理的随机范围，日期字段用近期日期
- 搜索过滤逻辑与 hook 中的 `searchForm` 字段对应
- 分页响应结构保持 `{ list, total, pageSize, currentPage }` 格式

---

## 四、关键规则（必须遵守）

- **搜索表单字段必须用 `reactive` + 独立类型定义**，不允许 inline 匿名类型
- **表格列定义放在 hook 里**，用 `cellRenderer` 做自定义渲染，不在模板里写复杂逻辑
- **枚举 / 字典映射统一放 enums.ts**，模板中通过映射展示，禁止硬编码
- **接口调用统一放 api/ 目录**，hook 中导入调用
- **分页参数**: `page` + `limit`，响应字段 `list` + `total` + `pageSize` + `currentPage`
- **URL query 回显**: 涉及搜索条件回显的场景，使用 `route.query` 初始化 + `router.replace` 同步
- **loading / error / empty 三态**: 异步请求必须覆盖这三种状态
- **样式**: 优先使用 Tailwind 工具类，复杂样式使用 `<style lang="scss" scoped>`
- **不引入新依赖**（除非与用户确认）
- **优先复用项目已有组件和工具** — `PureTableBar`、`ReDialog`、`ReIcon`、`pure-table`、`message` 等

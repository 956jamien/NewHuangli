# 黄历日结论渲染层

该模块族提供“黄历主题日结论渲染层”，将 `cnlunar.Lunar` 的计算结果映射为六档固定模板的中文总评文案，可直接集成于现有 Python 项目或服务中。

## 模块概览

```
huangli_templates.py   # 模板常量与格式化工具（含不同档位的宜忌语句模式）
huangli_renderer.py    # 渲染流程与对外接口
```

`huangli_renderer` 通过 `cnlunar.Lunar` 的属性判断当日等级、获取宜忌，最终调用模板完成渲染。模板文本位于 `huangli_templates.TEMPLATE_DICT` 中，包含“特凶/大凶/凶/平/吉/大吉”六档文案；配套的 `GRADE_SENTENCE_PATTERNS` 会在渲染时把宜忌列表转换成自然语言语句（无 `【】` 标记），可直接用于前端展示。

## 依赖与导入

- 运行时依赖：`cnlunar`（本仓库已内置）
- 主入口：

  ```python
  from cnlunar import Lunar
  from .huangli_renderer import render_conclusion

  lunar = Lunar(2024, 6, 1)
  text = render_conclusion(lunar)
  ```

- 若需结构化数据，可使用 `render_structured`：

  ```python
  from .huangli_renderer import render_structured

  data = render_structured(lunar)
  print(data.grade, data.text)
  ```

## 关键实现细节

### 硬禁忌检测

- `detect_hard_taboo` 会识别：
  - 四绝日（立春/立夏/立秋/立冬的前一日）
  - 四离日（春分/夏至/秋分/冬至的前一日）
  - 杨公十三忌（固定 13 个日子）
- 触发任一即判为“特凶”。

### 宜忌获取

`pick_officer_yiji` 优先读取 `Lunar.goodThing` / `Lunar.badThing`（项目已有逻辑已将宜忌归一为 15 项民用分类）。若该字段不可用，则退回 `cnlunar.config.officerThings` 并结合 `THING_CATEGORY_MAP` 做同样的民用分类映射。当依赖缺失或日值官不存在时会抛出明确的 `RuntimeError`，提醒调用方检查环境配置。

### 宜忌语句生成

- `finalize_yiji` 会在模板渲染前完成“忌项优先”的冲突消解，返回最终的宜/忌列表。
- `format_text` 会根据当日档位（`grade` 参数）选择 `GRADE_SENTENCE_PATTERNS` 中的语句模板，把“祈福、搬家……”这类列表转换为完整语句，例如：

  ```
  出行、开工等事项今日不建议推进；
  祈福、结婚、搬家等低风险的小决策正常推进；
  ```

- 若当日某类列表为空，则使用同档位的兜底语句，避免出现“无等事项”之类的字面拼接。
- 当宜项出现“诸事不宜”时，会直接改写为“没有特别适合的事项，保持日常活动即可”；当忌项出现“诸事不宜”时，优先输出“避免重大决策”。

### 冲突消解

- 由 `finalize_yiji` 完成，遵循“忌项优先”的策略：`final_yi = yi - ji`。
- 连接符使用中文顿号 `、`，空列表在语句中会被兜底提示覆盖，不会出现“无等事项”式输出。

### 分档判定

`grade_day` 先把 `Lunar.thingLevel` / `thingLevelName` 映射为“上/中/下/无”，再据此生成初始档位，并结合日值神煞进行一次动态调节：

1. 硬禁忌 → 直接定为“特凶”；
2. 等级映射：`上 → 大吉`、`中 → 吉`、`下 → 平`、`无 → 凶`（未知枚举兜底为“平”）；
3. 若为黑道神，则把档位往“凶”方向拉低一档（例如“大吉”降为“吉”、“平”降为“凶”、“凶”降为“大凶”）；
4. 若为黄道神，则把档位往“吉”方向提升一档（例如“平”升为“吉”、“凶”升为“平”）；
5. 经过上述调节后的档位即为最终判定结果。

当忌项包含“诸事不宜”而最终档位仍处于“吉”或“大吉”时，会在渲染阶段自动降级为“凶”，避免在全局禁忌日输出过于积极的结论。

> 以 2025 年黄历为例，在上述判定逻辑下六档模板均会被触发：特凶 21 天、大凶 9 天、凶 32 天、平 118 天、吉 78 天、大吉 107 天，可较均衡地覆盖全年走势。

## 输出长度估算

模板的固定字符数（去除 `{label}`、`{yi}`、`{ji}` 占位符）如下：

| 档位 | 固定字符数 | 换行数 |
| ---- | ---------- | ------ |
| 特凶 | 146        | 4      |
| 大凶 | 140        | 4      |
| 凶   | 134        | 4      |
| 平   | 126        | 3      |
| 吉   | 146        | 4      |
| 大吉 | 128        | 4      |

最终输出长度可按以下公式估算：

```
final_length = fixed_chars_excluding_placeholders + len(label) + len(yi_str) + len(ji_str)
```

其中 `yi_str`、`ji_str` 为使用顿号连接后的宜忌文本，长度取决于 `Lunar.goodThing` / `badThing`（或 `officerThings` 分类映射）中的项目数量。若需限制前端展示长度，可在调用层按需裁剪或收束。

> 小提示：`render_for_date` 会自动在文案前添加形如 `2025-11-12` 的日期行，便于直接输出示例。

## 可选扩展

- `render_for_date(datetime)`：传入公历日期直接渲染。
- `render_structured(Lunar)`：返回包含日期、等级、宜忌与最终文本的 `DayConclusion` 数据类，便于存储或进一步处理。

## 测试建议

如需覆盖完整逻辑，可通过构造伪 `Lunar` 对象或使用真实日期，验证：

1. 六档模板渲染结果；
2. 忌项覆盖时宜项剔除；
3. 硬禁忌（四绝/四离/杨公十三忌）命中；
4. 缺少 `officerThings` 时的异常提示。


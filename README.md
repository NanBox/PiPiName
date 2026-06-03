# PiPiName

PiPiName 是一个本地中文取名候选工具。它根据三才五格筛选笔画组合，再从诗经、楚辞、论语、周易、唐诗、宋诗、宋词和常见姓名库中生成双字名候选。

相关阅读可以[看这里](https://juejin.cn/post/6868186071260856334)。

> 结果只作为文化出处和候选筛选辅助，不承诺命理正确性，也不替代人工判断。

## 安装

需要先安装 Python 3.10 或更高版本。

```bash
pipx install .
```

## 启动

```bash
pipiname web --open
```

打开 `http://localhost:9191` 使用页面，打开 `http://localhost:9191/docs` 使用 API 文档。

网页里可以直接生成名字，也可以在“查看姓名”区域输入三字姓名查看三才五格和名字来源。

## API

### `GET /api/health`

返回索引状态和记录数。

### `GET /api/sources`

返回可用词库。

### `POST /api/names/generate`

请求示例：

```json
{
  "last_name": "林",
  "source": "shijing",
  "gender": "",
  "min_stroke": 3,
  "max_stroke": 30,
  "allow_general": false,
  "validate_name": true,
  "dislike_words": [],
  "limit": 100,
  "offset": 0
}
```

响应字段包含：

- `full_name`
- `first_name`
- `gender`
- `first_char`
- `second_char`
- `stroke1`
- `stroke2`
- `source_type`
- `source_title`
- `author`
- `sentence`

### `POST /api/names/check`

请求示例：

```json
{
  "name": "林蛋大",
  "with_resource": true
}
```

## 数据来源

- [OpenCC](https://github.com/BYVoid/OpenCC)
- [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry)
- [chineseStroke](https://github.com/WTree/chineseStroke)
- [Chinese-Names-Corpus](https://github.com/wainshine/Chinese-Names-Corpus)
- [hanzi_chaizi](https://github.com/howl-anderson/hanzi_chaizi)

## 许可

本项目使用 MIT 许可。请同时遵守所引用数据源的许可和署名要求。

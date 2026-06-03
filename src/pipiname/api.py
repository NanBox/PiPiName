from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .core import ValidationError, check_name, generate_names
from .index import NameIndex
from .models import GenerateOptions, SOURCE_LABELS


class GenerateRequest(BaseModel):
    last_name: str
    source: Literal["default", "shijing", "chuci", "lunyu", "zhouyi", "tangshi", "songshi", "songci", "all"] = "shijing"
    gender: Literal["", "男", "女"] = ""
    min_stroke: int = 3
    max_stroke: int = 30
    allow_general: bool = False
    validate_name: bool = True
    dislike_words: list[str] = Field(default_factory=list)
    limit: int = 500
    offset: int = 0


class CheckRequest(BaseModel):
    name: str
    with_resource: bool = True


def create_app(index: NameIndex | None = None) -> FastAPI:
    app = FastAPI(title="PiPiName", version="1.0.0")
    name_index = index or NameIndex()

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return HTML_PAGE

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return name_index.health()

    @app.get("/api/sources")
    def sources() -> dict[str, object]:
        return {"sources": name_index.source_summary(), "labels": SOURCE_LABELS}

    @app.post("/api/names/generate")
    def api_generate(request: GenerateRequest) -> dict[str, object]:
        try:
            options = GenerateOptions(
                last_name=request.last_name,
                source=request.source,
                gender=request.gender,
                min_stroke=request.min_stroke,
                max_stroke=request.max_stroke,
                allow_general=request.allow_general,
                validate_name=request.validate_name,
                dislike_words=tuple(request.dislike_words),
                limit=request.limit,
                offset=request.offset,
            )
            results = generate_names(options, index=name_index)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"items": [item.as_dict() for item in results], "count": len(results)}

    @app.post("/api/names/check")
    def api_check(request: CheckRequest) -> dict[str, object]:
        try:
            result = check_name(request.name, with_resource=request.with_resource, index=name_index)
        except ValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return result.as_dict()

    return app


HTML_PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>PiPiName</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #1f2937; }
    section { margin-top: 28px; }
    form { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px; }
    label { display: grid; gap: 4px; font-size: 13px; }
    input, select, button { padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
    button { background: #2563eb; color: white; cursor: pointer; }
    table { width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; }
    th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
    .wide { grid-column: span 2; }
    .hint { color: #6b7280; }
    .message { min-height: 24px; color: #374151; }
    .error { color: #b91c1c; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: #fafafa; }
  </style>
</head>
<body>
  <h1>PiPiName</h1>
  <p class="hint">本地取名候选工具，结果仅作为文化出处和筛选辅助。</p>
  <section>
  <h2>生成名字</h2>
  <form id="generate-form">
    <label>姓氏<input name="last_name" value="林" maxlength="1" required></label>
    <label>词库
      <select name="source">
        <option value="shijing">诗经</option><option value="chuci">楚辞</option><option value="lunyu">论语</option>
        <option value="zhouyi">周易</option><option value="tangshi">唐诗</option><option value="songshi">宋诗</option>
        <option value="songci">宋词</option><option value="default">默认姓名库</option><option value="all">全部古诗文</option>
      </select>
    </label>
    <label>性别<select name="gender"><option value="">不限</option><option>男</option><option>女</option></select></label>
    <label>返回数<input name="limit" type="number" value="100" min="1" max="5000"></label>
    <label>最小笔画<input name="min_stroke" type="number" value="3" min="1"></label>
    <label>最大笔画<input name="max_stroke" type="number" value="30" min="1"></label>
    <label>不喜欢的字<input name="dislike_words" placeholder="如：病凶"></label>
    <label><span>允许中吉</span><input name="allow_general" type="checkbox"></label>
    <label><span>常见姓名库筛选</span><input name="validate_name" type="checkbox" checked></label>
    <button type="submit">生成名字</button>
  </form>
  <div id="message" class="message"></div>
  <table id="result-table">
    <thead><tr><th>姓名</th><th>性别</th><th>笔画</th><th>来源</th><th>出处句子</th></tr></thead>
    <tbody></tbody>
  </table>
  </section>
  <section>
  <h2>查看姓名</h2>
  <form id="check-form">
    <label>姓名<input name="name" value="周杰伦" maxlength="3" required></label>
    <label><span>显示来源</span><input name="with_resource" type="checkbox" checked></label>
    <button type="submit">查看配置</button>
  </form>
  <div id="check-message" class="message"></div>
  <div id="check-result" class="card"></div>
  </section>
  <script>
    const form = document.querySelector('#generate-form');
    const tbody = document.querySelector('#result-table tbody');
    const message = document.querySelector('#message');
    const checkForm = document.querySelector('#check-form');
    const checkMessage = document.querySelector('#check-message');
    const checkResult = document.querySelector('#check-result');

    function textCell(row, value) {
      const cell = document.createElement('td');
      cell.textContent = value || '';
      row.appendChild(cell);
    }

    function setMessage(element, text, isError = false) {
      element.textContent = text;
      element.classList.toggle('error', isError);
    }

    async function readJson(response) {
      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.detail || '请求失败');
      }
      return json;
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const payload = {
        last_name: data.get('last_name'),
        source: data.get('source'),
        gender: data.get('gender'),
        min_stroke: Number(data.get('min_stroke')),
        max_stroke: Number(data.get('max_stroke')),
        allow_general: data.get('allow_general') === 'on',
        validate_name: data.get('validate_name') === 'on',
        dislike_words: Array.from(data.get('dislike_words') || ''),
        limit: Number(data.get('limit')),
        offset: 0
      };
      setMessage(message, '生成中...');
      tbody.innerHTML = '';
      try {
        const response = await fetch('/api/names/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const json = await readJson(response);
        setMessage(message, `共返回 ${json.count} 条`);
        for (const item of json.items) {
          const tr = document.createElement('tr');
          textCell(tr, item.full_name);
          textCell(tr, item.gender);
          textCell(tr, `${item.stroke1}/${item.stroke2}`);
          textCell(tr, `${item.source_title} ${item.author || ''}`);
          textCell(tr, item.sentence);
          tbody.appendChild(tr);
        }
      } catch (error) {
        setMessage(message, error.message, true);
      }
    });

    checkForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData(checkForm);
      checkResult.innerHTML = '';
      setMessage(checkMessage, '查询中...');
      try {
        const response = await fetch('/api/names/check', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            name: data.get('name'),
            with_resource: data.get('with_resource') === 'on'
          })
        });
        const json = await readJson(response);
        const report = json.report;
        const lines = [
          `${report.name}（${report.complex_name}）`,
          `笔画：${report.strokes.join(' / ')}`,
          `天格：${report.tian.value} ${report.tian.kind}`,
          `人格：${report.ren.value} ${report.ren.kind}`,
          `地格：${report.di.value} ${report.di.kind}`,
          `总格：${report.zong.value} ${report.zong.kind}`,
          `外格：${report.wai.value} ${report.wai.kind}`,
          `三才：${report.sancai} ${report.sancai_kind}`
        ];
        const pre = document.createElement('pre');
        pre.textContent = lines.join('\\n');
        checkResult.appendChild(pre);
        if (json.resources.length) {
          const title = document.createElement('h3');
          title.textContent = '名字来源';
          checkResult.appendChild(title);
          for (const resource of json.resources) {
            const p = document.createElement('p');
            p.textContent = `${resource.source_title} ${resource.author || ''}\\n${resource.sentence}`;
            checkResult.appendChild(p);
          }
        }
        setMessage(checkMessage, '查询完成');
      } catch (error) {
        setMessage(checkMessage, error.message, true);
      }
    });
  </script>
</body>
</html>
"""

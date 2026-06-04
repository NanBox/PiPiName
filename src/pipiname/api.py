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
  <title>PiPiName - 诗词古籍起名与姓名五格吉凶分析</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Outfit:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --color-bg: #f5f4ef; /* 宣纸白/浅暖灰 */
      --color-card-bg: #ffffff;
      --color-primary: #1f3d27; /* 黛绿 */
      --color-primary-light: #e6e9e6;
      --color-primary-active: #152b1b;
      --color-text: #2d3748;
      --color-text-muted: #718096;
      --color-border: #e2e8f0;
      
      /* 吉凶判定色彩 */
      --color-daji: #991b1b; /* 朱红 */
      --color-ji: #c2410c; /* 橙红 */
      --color-banji: #166534; /* 深绿 */
      --color-zhongji: #075985; /* 深蓝 */
      --color-xiong: #4b5563; /* 灰 */
      
      --font-serif: 'Noto Serif SC', Georgia, "Songti SC", serif;
      --font-sans: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html,
    body {
      height: 100%;
    }

    body {
      background-color: var(--color-bg);
      font-family: var(--font-sans);
      color: var(--color-text);
      line-height: 1.6;
      padding: 16px 20px;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }

    .container {
      max-width: 1200px;
      width: 100%;
      margin: 0 auto;
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    header {
      width: 100%;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex: 0 0 auto;
      padding: 14px 22px;
      background: var(--color-card-bg);
      border-radius: 12px;
      box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
      border: 1px solid var(--color-border);
    }

    header .logo-area h1 {
      font-family: var(--font-serif);
      color: var(--color-primary);
      font-size: 24px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    header .logo-area h1::before {
      content: "";
      display: inline-block;
      width: 6px;
      height: 24px;
      background: var(--color-primary);
      border-radius: 3px;
    }

    header .subtitle {
      font-size: 13px;
      color: var(--color-text-muted);
      margin-top: 4px;
    }

    header .author-link {
      font-size: 13px;
      color: var(--color-primary);
      text-decoration: none;
      font-weight: 600;
      background: var(--color-primary-light);
      padding: 6px 12px;
      border-radius: 6px;
      transition: all 0.2s;
    }

    header .author-link:hover {
      background: var(--color-primary);
      color: white;
    }

    main {
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      gap: 20px;
      align-items: stretch;
      flex: 1 1 auto;
      min-height: 0;
    }

    .sidebar {
      display: flex;
      flex-direction: column;
      gap: 12px;
      height: 100%;
      min-height: 0;
      overflow: hidden;
      padding-right: 2px;
    }

    .health-card {
      padding: 16px;
      font-size: 12px;
      color: var(--color-text-muted);
    }

    #generate-health-card {
      margin-top: auto;
    }

    #check-health-card {
      display: none;
    }

    .health-card-title {
      font-weight: 700;
      color: var(--color-primary);
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--color-primary-light);
      padding-bottom: 4px;
    }

    .health-status-dot {
      width: 8px;
      height: 8px;
      background: #cbd5e1;
      border-radius: 50%;
      display: inline-block;
    }

    .health-stats {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .health-stat-value {
      font-weight: 600;
      color: var(--color-text);
    }

    .card {
      background: var(--color-card-bg);
      border-radius: 12px;
      border: 1px solid var(--color-border);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
      padding: 16px;
      transition: all 0.3s ease;
    }

    .card-title {
      font-family: var(--font-serif);
      font-size: 18px;
      font-weight: 700;
      color: var(--color-primary);
      margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 2px solid var(--color-primary-light);
    }

    .sidebar-tabs {
      display: flex;
      height: 44px;
      min-height: 44px;
      background: #e2e8f0;
      padding: 4px;
      border-radius: 8px;
    }

    .sidebar-tab-btn {
      flex: 1;
      border: none;
      background: transparent;
      padding: 8px 12px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      border-radius: 6px;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
    }

    .sidebar-tab-btn.active {
      background: var(--color-card-bg);
      color: var(--color-primary);
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .sidebar-pane {
      display: none;
      min-height: 0;
    }

    .sidebar-pane.active {
      display: flex;
      flex-direction: column;
      animation: fadeIn 0.2s ease;
    }

    #generate-sidebar.active {
      flex: 1 1 auto;
      overflow: hidden;
    }

    #check-sidebar.active {
      flex: 0 0 auto;
      overflow-y: auto;
    }

    #generate-form,
    #check-form {
      flex: 1 1 auto;
      min-height: 0;
      overflow-y: auto;
      padding-right: 2px;
      gap: 10px;
      justify-content: space-between;
    }

    #generate-sidebar,
    #check-sidebar {
      padding: 16px;
    }

    #generate-sidebar .card-title,
    #check-sidebar .card-title {
      margin-bottom: 10px;
      padding-bottom: 6px;
    }

    #generate-form .form-group,
    #check-form .form-group {
      gap: 4px;
    }

    #generate-form .form-row,
    #check-form .form-row {
      gap: 12px;
    }

    #generate-form label,
    #check-form label {
      font-size: 13px;
    }

    #generate-form input[type="text"],
    #generate-form input[type="number"],
    #generate-form select,
    #check-form input[type="text"],
    #check-form input[type="number"],
    #check-form select {
      min-height: 36px;
      padding: 7px 10px;
      font-size: 13px;
      border-radius: 8px;
    }

    #generate-form .checkbox-group,
    #check-form .checkbox-group {
      gap: 8px;
      min-height: 22px;
      font-size: 13px;
    }

    #generate-form .checkbox-group input,
    #check-form .checkbox-group input {
      width: 15px;
      height: 15px;
    }

    #generate-form button.btn-primary,
    #check-form button.btn-primary {
      min-height: 38px;
      padding: 9px 12px;
    }

    form {
      display: flex;
      flex-direction: column;
      gap: 9px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    label {
      font-size: 13px;
      font-weight: 600;
      color: var(--color-text);
    }

    input[type="text"],
    input[type="number"],
    select {
      width: 100%;
      padding: 7px 10px;
      border: 1.5px solid var(--color-border);
      border-radius: 8px;
      font-size: 14px;
      font-family: inherit;
      color: var(--color-text);
      background-color: #fafbfc;
      transition: all 0.2s ease;
    }

    input:focus, select:focus {
      outline: none;
      border-color: var(--color-primary);
      background-color: #fff;
      box-shadow: 0 0 0 3px rgba(31, 61, 39, 0.1);
    }


    .checkbox-group {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      user-select: none;
      font-size: 13px;
      font-weight: 600;
      color: var(--color-text);
    }

    .checkbox-group input {
      width: 16px;
      height: 16px;
      accent-color: var(--color-primary);
      cursor: pointer;
    }

    button.btn-primary {
      background: var(--color-primary);
      color: white;
      border: none;
      padding: 9px 12px;
      border-radius: 8px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 6px rgba(31, 61, 39, 0.15);
    }

    button.btn-primary:hover {
      background: var(--color-primary-active);
      transform: translateY(-1px);
      box-shadow: 0 6px 12px rgba(31, 61, 39, 0.2);
    }

    button.btn-primary:active {
      transform: translateY(0);
    }

    /* Content Area */
    .content-area {
      display: flex;
      flex-direction: column;
      gap: 12px;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
    }

    .content-tabs {
      display: flex;
      flex: 0 0 auto;
      height: 44px;
      min-height: 44px;
      background: #e2e8f0;
      padding: 4px;
      border-radius: 8px;
      gap: 4px;
    }

    .content-tab-btn {
      flex: 1;
      border: none;
      background: transparent;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
      font-family: var(--font-sans);
    }

    .content-tab-btn.active {
      background: var(--color-card-bg);
      color: var(--color-primary);
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .tab-content {
      display: none;
      min-height: 0;
    }

    .tab-content.active {
      display: flex;
      flex-direction: column;
      flex: 1 1 auto;
      min-height: 0;
      overflow: hidden;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Message Banner */
    .message-banner {
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 14px;
      flex: 0 0 auto;
      display: none;
    }

    .message-banner.info {
      display: block;
      background-color: var(--color-primary-light);
      color: var(--color-primary);
      border: 1px solid rgba(31, 61, 39, 0.2);
    }

    .message-banner.error {
      display: block;
      background-color: #fef2f2;
      color: #b91c1c;
      border: 1px solid #fee2e2;
    }

    /* Results Table */
    .table-container {
      --table-header-height: 44px;
      --table-scrollbar-width: 8px;
      width: 100%;
      flex: 1 1 auto;
      min-height: 0;
      max-height: 100%;
      overflow: hidden;
      border-radius: 12px;
      border: 1px solid var(--color-border);
      box-shadow: 0 4px 6px rgba(0,0,0,0.01);
      background: var(--color-card-bg);
      display: flex;
      flex-direction: column;
    }

    .table-header {
      flex: 0 0 auto;
      overflow: hidden;
      box-sizing: border-box;
      padding-right: var(--table-scrollbar-width);
      background: #f8fafc;
      border-bottom: 2px solid var(--color-border);
      border-top-left-radius: 12px;
      border-top-right-radius: 12px;
    }

    .table-body {
      flex: 1 1 auto;
      min-height: 0;
      overflow: auto;
      scrollbar-color: rgba(148, 163, 184, 0.72) transparent;
      scrollbar-width: thin;
    }

    .table-body::-webkit-scrollbar {
      width: var(--table-scrollbar-width);
      height: 10px;
    }

    .table-body::-webkit-scrollbar-track {
      background: transparent;
      border-radius: 999px;
    }

    .table-body::-webkit-scrollbar-corner {
      background: transparent;
    }

    .table-body::-webkit-scrollbar-button:vertical:end:increment {
      display: block;
      height: 8px;
      background: transparent;
    }

    .table-body::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.72);
      border: 2px solid transparent;
      background-clip: padding-box;
      border-radius: 999px;
    }

    .table-body::-webkit-scrollbar-thumb:hover {
      background: rgba(100, 116, 139, 0.82);
      background-clip: padding-box;
    }

    table {
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
      text-align: left;
    }

    .table-header table {
      min-width: 760px;
    }

    th {
      background: #f8fafc;
      padding: 12px 14px;
      font-size: 13px;
      font-weight: 600;
      color: #475569;
      white-space: nowrap;
      height: var(--table-header-height);
    }

    th:first-child {
      border-top-left-radius: 12px;
    }

    th:last-child {
      border-top-right-radius: 12px;
    }

    td {
      padding: 12px 14px;
      font-size: 13px;
      border-bottom: 1px solid var(--color-border);
      vertical-align: middle;
    }

    th:first-child,
    td:first-child {
      width: 150px;
    }

    th:nth-child(2),
    td:nth-child(2),
    th:nth-child(3),
    td:nth-child(3) {
      width: 72px;
      white-space: nowrap;
    }

    th:nth-child(4),
    td:nth-child(4) {
      max-width: 180px;
    }

    th:nth-child(5),
    td:nth-child(5) {
      max-width: 280px;
    }

    td:nth-child(4),
    td:nth-child(5) {
      overflow-wrap: anywhere;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background-color: #fafbfc;
    }

    /* Interactive Name Badge in Table */
    .name-badge {
      display: inline-block;
      font-family: var(--font-serif);
      font-size: 15px;
      font-weight: 700;
      color: var(--color-primary);
      background-color: var(--color-primary-light);
      padding: 6px 14px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s ease;
      border: 1.5px solid rgba(31, 61, 39, 0.1);
    }

    .name-badge:hover {
      background-color: var(--color-primary);
      color: white;
      transform: translateY(-1px);
      box-shadow: 0 4px 10px rgba(31, 61, 39, 0.25);
    }

    /* Stroke count styling */
    .stroke-tag {
      font-size: 12px;
      font-weight: 600;
      background: #f1f5f9;
      padding: 3px 8px;
      border-radius: 6px;
      color: #475569;
    }

    /* Highlight word in sentences */
    .highlight-word {
      color: #c2410c;
      font-weight: bold;
      border-bottom: 1.5px dashed #c2410c;
      padding: 0 2px;
      font-size: 1.05em;
    }

    /* Badges for Fortunes */
    .fortune-badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      color: white;
      text-shadow: 0 1px 1px rgba(0,0,0,0.1);
    }

    .fortune-daji { background-color: var(--color-daji); }
    .fortune-ji { background-color: var(--color-ji); }
    .fortune-banji { background-color: var(--color-banji); }
    .fortune-zhongji { background-color: var(--color-zhongji); }
    .fortune-xiong { background-color: var(--color-xiong); }

    /* Wuge Analysis Grid */
    .wuge-layout {
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-height: 0;
      overflow-y: auto;
      padding-right: 2px;
      scrollbar-color: rgba(148, 163, 184, 0.72) transparent;
      scrollbar-width: thin;
      animation: fadeIn 0.3s ease;
    }

    .wuge-layout::-webkit-scrollbar {
      width: 8px;
    }

    .wuge-layout::-webkit-scrollbar-track {
      background: transparent;
    }

    .wuge-layout::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.72);
      border: 2px solid transparent;
      background-clip: padding-box;
      border-radius: 999px;
    }

    .wuge-layout::-webkit-scrollbar-thumb:hover {
      background: rgba(100, 116, 139, 0.82);
      background-clip: padding-box;
    }

    .wuge-header {
      display: flex;
      align-items: center;
      gap: 20px;
      background: var(--color-card-bg);
      padding: 16px 20px;
      border-radius: 12px;
      border: 1px solid var(--color-border);
      border-left: 5px solid var(--color-primary);
      box-shadow: 0 2px 10px rgba(0,0,0,0.01);
    }

    .wuge-header-names {
      display: flex;
      flex-direction: column;
    }

    .wuge-header-title {
      font-family: var(--font-serif);
      font-size: 22px;
      font-weight: 700;
      color: var(--color-primary);
    }

    .wuge-header-sub {
      font-size: 14px;
      color: var(--color-text-muted);
      margin-top: 4px;
      font-weight: 500;
    }

    .wuge-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }

    .wuge-card {
      background: var(--color-card-bg);
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      position: relative;
      overflow: hidden;
      box-shadow: 0 4px 10px rgba(0,0,0,0.01);
      transition: all 0.2s;
    }

    .wuge-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(0,0,0,0.03);
    }

    .wuge-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: #cbd5e1;
    }

    .wuge-card.level-daji::before { background: var(--color-daji); }
    .wuge-card.level-ji::before { background: var(--color-ji); }
    .wuge-card.level-banji::before { background: var(--color-banji); }
    .wuge-card.level-zhongji::before { background: var(--color-zhongji); }
    .wuge-card.level-xiong::before { background: var(--color-xiong); }

    .wuge-card-title {
      font-size: 13px;
      font-weight: 700;
      color: #64748b;
      display: flex;
      justify-content: space-between;
      align-items: center;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .wuge-card-value {
      font-family: var(--font-serif);
      font-size: 28px;
      font-weight: 700;
      color: var(--color-text);
      display: flex;
      align-items: baseline;
      gap: 6px;
      margin-top: 4px;
    }

    .wuge-card-value span {
      font-size: 14px;
      font-family: var(--font-sans);
      color: var(--color-text-muted);
      font-weight: 500;
    }

    /* Resources Section in Check Result */
    .wuge-resources {
      margin-top: 12px;
      min-height: 0;
      display: flex;
      flex-direction: column;
    }

    .wuge-resources h3 {
      font-family: var(--font-serif);
      font-size: 18px;
      font-weight: 700;
      color: var(--color-primary);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .resource-item {
      background: var(--color-card-bg);
      border: 1px solid var(--color-border);
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.01);
      transition: all 0.2s;
    }

    .resource-item:hover {
      box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    }

    .resource-meta {
      font-size: 13px;
      color: var(--color-primary);
      font-weight: 700;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }

    .resource-sentence {
      font-family: var(--font-serif);
      font-size: 16px;
      color: var(--color-text);
      line-height: 1.7;
    }

    /* Empty state placeholder */
    .empty-state {
      width: 100%;
      min-height: 280px;
      text-align: center;
      padding: 36px 20px;
      color: var(--color-text-muted);
      border-style: dashed;
      border-width: 2px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }

    .empty-state svg {
      width: 56px;
      height: 56px;
      stroke: #94a3b8;
      margin-bottom: 16px;
      opacity: 0.7;
    }

    .empty-state p {
      font-size: 15px;
      font-weight: 500;
    }

    footer {
      text-align: center;
      flex: 0 0 auto;
      padding: 8px 0 0;
      font-size: 12px;
      color: var(--color-text-muted);
    }

    @media (max-width: 900px) {
      body {
        height: auto;
        min-height: 100vh;
        overflow: auto;
        padding: 14px;
      }

      .container {
        min-height: auto;
      }

      header {
        flex-direction: column;
        align-items: flex-start;
        gap: 12px;
      }

      main {
        grid-template-columns: 1fr;
        overflow: visible;
      }

      .sidebar,
      .content-area,
      .wuge-layout {
        height: auto;
        overflow: visible;
      }

      .tab-content.active {
        display: block;
      }

      .table-container {
        max-height: 60vh;
      }

      footer {
        padding: 16px 0 0;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-area">
        <h1>PiPiName</h1>
        <div class="subtitle">诗词古籍智能起名与姓名五格吉凶分析系统</div>
      </div>
      <a href="https://github.com/nanbox/PiPiName" target="_blank" class="author-link">GitHub 仓库</a>
    </header>

    <main>
      <div class="sidebar">
        <!-- 切换控制选项 -->
        <div class="sidebar-tabs">
          <button class="sidebar-tab-btn active" onclick="switchSidebarTab('generate')">智能起名</button>
          <button class="sidebar-tab-btn" onclick="switchSidebarTab('check')">姓名分析</button>
        </div>

        <!-- 生成姓名表单 -->
        <div id="generate-sidebar" class="card sidebar-pane active">
          <div class="card-title">起名参数配置</div>
          <form id="generate-form">
            <div class="form-row">
              <div class="form-group">
                <label>姓氏</label>
                <input type="text" name="last_name" value="" maxlength="2" required placeholder="例如：林">
              </div>
              <div class="form-group">
                <label>期望性别</label>
                <select name="gender">
                  <option value="">不限</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label>词库来源</label>
              <select name="source">
                <option value="shijing">诗经</option>
                <option value="chuci">楚辞</option>
                <option value="lunyu">论语</option>
                <option value="zhouyi">周易</option>
                <option value="tangshi">唐诗</option>
                <option value="songshi">宋诗</option>
                <option value="songci">宋词</option>
                <option value="default">默认姓名库</option>
                <option value="all">全部古诗文</option>
              </select>
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>最小笔画</label>
                <input name="min_stroke" type="number" value="3" min="1">
              </div>
              <div class="form-group">
                <label>最大笔画</label>
                <input name="max_stroke" type="number" value="30" min="1">
              </div>
            </div>

            <div class="form-group">
              <label>返回数量</label>
              <input name="limit" type="number" value="100" min="1" max="5000">
            </div>

            <div class="form-group">
              <label>避讳汉字 (排除不喜欢的字)</label>
              <input type="text" name="dislike_words" placeholder="如：病凶（无需逗号分隔）">
            </div>

            <div class="checkbox-group">
              <input name="allow_general" type="checkbox" id="allow_general">
              <label for="allow_general">允许中吉笔画</label>
            </div>

            <div class="checkbox-group">
              <input name="validate_name" type="checkbox" id="validate_name" checked>
              <label for="validate_name">常见姓名库过滤（推荐）</label>
            </div>

            <button type="submit" class="btn-primary">生成名字候选</button>
          </form>
        </div>

        <!-- 姓名测算分析表单 -->
        <div id="check-sidebar" class="card sidebar-pane">
          <div class="card-title">查看姓名五格</div>
          <form id="check-form">
            <div class="form-group">
              <label>待测姓名</label>
              <input type="text" name="name" value="" placeholder="请输入 2-4 字姓名" required maxlength="4">
            </div>
            <div class="checkbox-group">
              <input name="with_resource" type="checkbox" id="with_resource" checked>
              <label for="with_resource">分析包含古籍出处</label>
            </div>
            <button type="submit" class="btn-primary">立即测算吉凶</button>
          </form>
        </div>

        <div class="card health-card" id="check-health-card">
          <div class="health-card-title">
            <span>本地索引状态</span>
            <span class="health-status-dot"></span>
          </div>
          <div class="health-stats">
            <div>名著文献：<span class="health-stat-value stat-sources">-</span> 篇</div>
            <div>汉字检索：<span class="health-stat-value stat-chars">-</span> 个</div>
            <div>常见姓名比对库：<span class="health-stat-value stat-names">-</span> 条</div>
          </div>
        </div>

        <div class="card health-card" id="generate-health-card">
          <div class="health-card-title">
            <span>本地索引状态</span>
            <span class="health-status-dot"></span>
          </div>
          <div class="health-stats">
            <div>名著文献：<span class="health-stat-value stat-sources">-</span> 篇</div>
            <div>汉字检索：<span class="health-stat-value stat-chars">-</span> 个</div>
            <div>常见姓名比对库：<span class="health-stat-value stat-names">-</span> 条</div>
          </div>
        </div>
      </div>

      <div class="content-area">
        <!-- 右侧展示 Tab 导航 -->
        <div class="content-tabs">
          <button class="content-tab-btn active" id="tab-btn-results" onclick="switchContentTab('results')">名字候选列表</button>
          <button class="content-tab-btn" id="tab-btn-analysis" onclick="switchContentTab('analysis')">五格吉凶分析</button>
        </div>

        <!-- 全局消息条 -->
        <div id="message" class="message-banner"></div>

        <!-- Tab 1: 生成候选结果 -->
        <div id="tab-results" class="tab-content active">
          <div id="results-empty" class="card empty-state">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.782 18 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <p>请在左侧设定起名参数，然后点击“生成名字候选”开始起名。</p>
          </div>
          
          <div id="results-table-wrapper" class="table-container" style="display: none;">
            <div class="table-header">
              <table>
                <thead>
                  <tr>
                    <th>姓名（可点选分析）</th>
                    <th>性别</th>
                    <th>笔画数</th>
                    <th>古籍出处</th>
                    <th>出处句子</th>
                  </tr>
                </thead>
              </table>
            </div>
            <div class="table-body">
              <table>
                <tbody id="result-tbody"></tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Tab 2: 姓名分析结果 -->
        <div id="tab-analysis" class="tab-content">
          <div id="analysis-empty" class="card empty-state">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>在左侧“姓名分析”中输入名字，或者直接点击起名候选列表中的姓名徽章，此处将展示精细的姓名五格吉凶及古籍配置报告。</p>
          </div>

          <div id="analysis-content" class="wuge-layout" style="display: none;">
            <!-- 头部信息 -->
            <div class="wuge-header">
              <div class="wuge-header-names">
                <div id="analysis-title-name" class="wuge-header-title">姓名</div>
                <div id="analysis-title-complex" class="wuge-header-sub">繁体：- (笔画：-)</div>
              </div>
            </div>
            
            <!-- 五格吉凶图表 -->
            <div class="wuge-grid">
              <div class="wuge-card" id="card-tian">
                <div class="wuge-card-title">天格 (祖荫/根基) <span class="fortune-badge" id="badge-tian">-</span></div>
                <div class="wuge-card-value" id="val-tian">- <span>画</span></div>
              </div>
              <div class="wuge-card" id="card-ren">
                <div class="wuge-card-title">人格 (主运/性格) <span class="fortune-badge" id="badge-ren">-</span></div>
                <div class="wuge-card-value" id="val-ren">- <span>画</span></div>
              </div>
              <div class="wuge-card" id="card-di">
                <div class="wuge-card-title">地格 (前运/家庭) <span class="fortune-badge" id="badge-di">-</span></div>
                <div class="wuge-card-value" id="val-di">- <span>画</span></div>
              </div>
              <div class="wuge-card" id="card-zong">
                <div class="wuge-card-title">总格 (后运/终身) <span class="fortune-badge" id="badge-zong">-</span></div>
                <div class="wuge-card-value" id="val-zong">- <span>画</span></div>
              </div>
              <div class="wuge-card" id="card-wai">
                <div class="wuge-card-title">外格 (人际/社交) <span class="fortune-badge" id="badge-wai">-</span></div>
                <div class="wuge-card-value" id="val-wai">- <span>画</span></div>
              </div>
              <div class="wuge-card" id="card-sancai">
                <div class="wuge-card-title">三才配置 (生克/健康) <span class="fortune-badge" id="badge-sancai">-</span></div>
                <div class="wuge-card-value" id="val-sancai">-</div>
              </div>
            </div>

            <!-- 书籍来源 -->
            <div class="wuge-resources" id="analysis-resources-section" style="display: none;">
              <h3>
                <svg style="width:20px;height:20px;stroke:currentColor;fill:none;vertical-align:middle;margin-right:4px;" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.782 18 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                古籍关联诗句
              </h3>
              <div id="analysis-resources-list"></div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer>
      <p>PiPiName 本地起名候选辅助工具 · 结果仅作为文化出处和姓名汉字笔画组合分析参考</p>
    </footer>
  </div>

  <script>
    const genForm = document.getElementById('generate-form');
    const checkForm = document.getElementById('check-form');
    const messageBanner = document.getElementById('message');
    const resultTbody = document.getElementById('result-tbody');
    const resultsEmpty = document.getElementById('results-empty');
    const resultsTableWrapper = document.getElementById('results-table-wrapper');
    const analysisEmpty = document.getElementById('analysis-empty');
    const analysisContent = document.getElementById('analysis-content');

    // Tab 切换逻辑
    function switchSidebarTab(tab) {
      document.getElementById('generate-sidebar').classList.toggle('active', tab === 'generate');
      document.getElementById('check-sidebar').classList.toggle('active', tab === 'check');
      const generateHealthCard = document.getElementById('generate-health-card');
      if (generateHealthCard) {
        generateHealthCard.style.display = tab === 'generate' ? 'block' : 'none';
      }
      const checkHealthCard = document.getElementById('check-health-card');
      if (checkHealthCard) {
        checkHealthCard.style.display = tab === 'check' ? 'block' : 'none';
      }
      
      const btns = document.querySelectorAll('.sidebar-tab-btn');
      btns[0].classList.toggle('active', tab === 'generate');
      btns[1].classList.toggle('active', tab === 'check');
    }

    // 修复 Content Tab 切换逻辑，避免 DOM 错误
    function switchContentTab(tab) {
      document.getElementById('tab-btn-results').classList.toggle('active', tab === 'results');
      document.getElementById('tab-btn-analysis').classList.toggle('active', tab === 'analysis');
      document.getElementById('tab-results').classList.toggle('active', tab === 'results');
      document.getElementById('tab-analysis').classList.toggle('active', tab === 'analysis');
    }

    function showMessage(text, type = 'info') {
      messageBanner.textContent = text;
      messageBanner.className = `message-banner ${type}`;
      messageBanner.style.display = 'block';
    }

    function hideMessage() {
      messageBanner.textContent = '';
      messageBanner.style.display = 'none';
    }

    function displayGender(gender) {
      return gender && !['未知', '双'].includes(gender) ? gender : '不限';
    }

    function formatSentence(sentence) {
      if (!sentence) return '';
      const escaped = sentence
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
      return escaped.replace(/「(.*?)」/g, '<span class="highlight-word">$1</span>');
    }

    function getFortuneClass(kind) {
      if (!kind) return 'fortune-xiong';
      if (kind.includes('大吉')) return 'fortune-daji';
      if (kind.includes('半吉')) return 'fortune-banji';
      if (kind.includes('中吉')) return 'fortune-zhongji';
      if (kind.includes('吉')) return 'fortune-ji';
      if (kind.includes('凶')) return 'fortune-xiong';
      return 'fortune-xiong';
    }

    async function readJson(response) {
      const json = await response.json();
      if (!response.ok) {
        throw new Error(json.detail || '请求失败');
      }
      return json;
    }

    // 加载系统状态
    async function loadHealth() {
      try {
        const response = await fetch('/api/health');
        if (response.ok) {
          const data = await response.json();
          document.querySelectorAll('.stat-sources').forEach((node) => {
            node.textContent = Number(data.sources).toLocaleString();
          });
          document.querySelectorAll('.stat-chars').forEach((node) => {
            node.textContent = Number(data.sentence_chars).toLocaleString();
          });
          document.querySelectorAll('.stat-names').forEach((node) => {
            node.textContent = Number(data.valid_names).toLocaleString();
          });
          document.querySelectorAll('.health-status-dot').forEach((dot) => {
            dot.style.background = '#22c55e';
            dot.title = '数据库已连接';
          });
        }
      } catch (e) {
        console.error('无法加载系统状态:', e);
      }
    }

    // 联动一键分析
    async function analyzeName(name, withResource = true) {
      showMessage(`正在为您测算姓名【${name}】的五格吉凶...`, 'info');
      analysisEmpty.style.display = 'none';
      analysisContent.style.display = 'none';
      
      // 同步侧栏表单的值并切换侧栏Tab
      const nameInput = checkForm.querySelector('input[name="name"]');
      if (nameInput) {
        nameInput.value = name;
      }
      switchSidebarTab('check');
      switchContentTab('analysis');

      try {
        const response = await fetch('/api/names/check', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            name: name,
            with_resource: withResource
          })
        });
        const json = await readJson(response);
        const report = json.report;
        
        // 头部
        document.getElementById('analysis-title-name').textContent = report.name;
        document.getElementById('analysis-title-complex').textContent = `繁体：${report.complex_name}（首/末笔画：${report.strokes.join(' / ')}）`;
        
        // 填充卡片
        updateWugeCard('tian', report.tian);
        updateWugeCard('ren', report.ren);
        updateWugeCard('di', report.di);
        updateWugeCard('zong', report.zong);
        updateWugeCard('wai', report.wai);
        
        // 三才
        const sancaiBadge = document.getElementById('badge-sancai');
        sancaiBadge.textContent = report.sancai_kind;
        sancaiBadge.className = `fortune-badge ${getFortuneClass(report.sancai_kind)}`;
        document.getElementById('val-sancai').innerHTML = `${report.sancai} <span>配置</span>`;
        document.getElementById('card-sancai').className = `wuge-card level-${getFortuneClass(report.sancai_kind).replace('fortune-', '')}`;
        
        // 关联古籍
        const resourcesSection = document.getElementById('analysis-resources-section');
        const resourcesList = document.getElementById('analysis-resources-list');
        resourcesList.innerHTML = '';
        
        if (json.resources && json.resources.length > 0) {
          for (const res of json.resources) {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'resource-item';
            
            const metaDiv = document.createElement('div');
            metaDiv.className = 'resource-meta';
            metaDiv.innerHTML = `<span>${res.source_title}</span> <span>${res.author || '未知'}</span>`;
            
            const sentDiv = document.createElement('div');
            sentDiv.className = 'resource-sentence';
            sentDiv.innerHTML = formatSentence(res.sentence);
            
            itemDiv.appendChild(metaDiv);
            itemDiv.appendChild(sentDiv);
            resourcesList.appendChild(itemDiv);
          }
          resourcesSection.style.display = 'block';
        } else {
          resourcesSection.style.display = 'none';
        }
        
        analysisContent.style.display = 'flex';
        hideMessage();
      } catch (error) {
        showMessage(error.message, 'error');
        analysisEmpty.style.display = 'block';
      }
    }

    function updateWugeCard(key, data) {
      const badge = document.getElementById(`badge-${key}`);
      const valEl = document.getElementById(`val-${key}`);
      const card = document.getElementById(`card-${key}`);
      
      badge.textContent = data.kind;
      badge.className = `fortune-badge ${getFortuneClass(data.kind)}`;
      valEl.innerHTML = `${data.value} <span>画</span>`;
      card.className = `wuge-card level-${getFortuneClass(data.kind).replace('fortune-', '')}`;
    }

    // 生成名字事件
    genForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData(genForm);
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
      
      showMessage('正在为您检索匹配的词库，筛选吉星笔画...', 'info');
      resultTbody.innerHTML = '';
      resultsEmpty.style.display = 'none';
      resultsTableWrapper.style.display = 'none';
      switchContentTab('results');

      try {
        const response = await fetch('/api/names/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        const json = await readJson(response);
        
        if (json.count === 0) {
          showMessage('未找到匹配该条件的候选姓名，可尝试调整笔画或更换词库出处。', 'info');
          resultsEmpty.style.display = 'block';
          return;
        }

        hideMessage();
        
        for (const item of json.items) {
          const tr = document.createElement('tr');
          
          // 姓名 (点击测算)
          const nameCell = document.createElement('td');
          const badge = document.createElement('span');
          badge.className = 'name-badge';
          badge.textContent = item.full_name;
          badge.onclick = () => analyzeName(item.full_name);
          nameCell.appendChild(badge);
          tr.appendChild(nameCell);
          
          // 性别
          const genderCell = document.createElement('td');
          genderCell.textContent = displayGender(item.gender);
          tr.appendChild(genderCell);
          
          // 笔画
          const strokeCell = document.createElement('td');
          const strokeTag = document.createElement('span');
          strokeTag.className = 'stroke-tag';
          strokeTag.textContent = `${item.stroke1} / ${item.stroke2}`;
          strokeCell.appendChild(strokeTag);
          tr.appendChild(strokeCell);
          
          // 古籍
          const sourceCell = document.createElement('td');
          sourceCell.textContent = `${item.source_title} ${item.author || ''}`;
          tr.appendChild(sourceCell);
          
          // 出处句子
          const sentenceCell = document.createElement('td');
          sentenceCell.className = 'resource-sentence';
          sentenceCell.innerHTML = formatSentence(item.sentence);
          tr.appendChild(sentenceCell);
          
          resultTbody.appendChild(tr);
        }
        
        resultsTableWrapper.style.display = 'flex';
      } catch (error) {
        showMessage(error.message, 'error');
        resultsEmpty.style.display = 'block';
      }
    });

    // 测算名字事件
    checkForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const data = new FormData(checkForm);
      const name = data.get('name');
      const withResource = data.get('with_resource') === 'on';
      await analyzeName(name, withResource);
    });

    // 初始化加载
    document.addEventListener('DOMContentLoaded', () => {
      loadHealth();
    });
  </script>
</body>
</html>
"""

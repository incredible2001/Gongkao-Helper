"""HTML生成模块 - 生成带左侧导航的文章总结HTML页面（支持PC和移动端）"""

import html as html_mod
import json
import logging
import math
import os
import re

from scripts import config

logger = logging.getLogger("html_generator")

# ============ 通用 CSS ============

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f6fa; color: #2d3436; line-height: 1.8;
}

/* 水印 */
#watermark{position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden}
#watermark .wm{position:absolute;color:rgba(0,0,0,0.028);font-size:20px;white-space:nowrap;transform:rotate(-30deg);font-weight:600;letter-spacing:2px;user-select:none}
.wm-corner{position:fixed;right:12px;bottom:12px;z-index:9998;font-size:11px;color:rgba(0,0,0,0.12);letter-spacing:1px;pointer-events:none;user-select:none}

/* 汉堡菜单按钮 */
.menu-toggle {
    display: none;
    position: fixed; top: 12px; left: 12px;
    width: 42px; height: 42px;
    background: #1e272e; color: #fff;
    border: none; border-radius: 8px;
    font-size: 20px; cursor: pointer;
    z-index: 200; line-height: 42px; text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* 侧边栏遮罩 */
.sidebar-overlay {
    display: none;
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.45); z-index: 99;
}

/* 左侧导航 */
.sidebar {
    position: fixed; left: 0; top: 0; bottom: 0;
    width: 320px; background: #1e272e; color: #dfe6e9;
    overflow-y: auto; z-index: 100;
    padding: 20px 0;
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}
.sidebar h1 {
    font-size: 18px; color: #fff; padding: 10px 20px 5px;
    border-bottom: 1px solid #636e72; margin-bottom: 10px;
}
.sidebar .filter-box { padding: 8px 15px; }
.sidebar .filter-box select {
    width: 100%; padding: 6px 10px; border-radius: 4px;
    border: 1px solid #636e72; background: #2d3436; color: #dfe6e9;
    font-size: 13px;
}
.sidebar .search-box { padding: 8px 15px; }
.sidebar .search-box input {
    width: 100%; padding: 6px 10px; border-radius: 4px;
    border: 1px solid #636e72; background: #2d3436; color: #dfe6e9;
    font-size: 13px;
}
.sidebar .nav-list { list-style: none; }
.sidebar .nav-list li { border-bottom: 1px solid rgba(255,255,255,0.05); }
.sidebar .nav-list li a {
    display: block; padding: 8px 20px; color: #b2bec3;
    text-decoration: none; font-size: 13px; line-height: 1.5;
    transition: all 0.2s;
}
.sidebar .nav-list li a:hover { background: rgba(255,255,255,0.08); color: #fff; }
.sidebar .nav-list li a.active { background: #0984e3; color: #fff; }
.sidebar .nav-list li .nav-date { font-size: 11px; color: #636e72; }
.sidebar .nav-list li .nav-cat { font-size: 11px; color: #0984e3; float: right; }
.sidebar .stats {
    padding: 10px 20px; font-size: 12px; color: #636e72;
    border-top: 1px solid #636e72; margin-top: 10px;
}

/* 右侧内容 */
.main-content {
    margin-left: 320px; padding: 30px 40px;
    width: calc((100% - 320px) * 0.8);
    margin-left: calc(320px + (100% - 320px) * 0.1);
}

/* 文章卡片 */
.article-card {
    background: #fff; border-radius: 8px;
    padding: 28px 32px; margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 4px solid #0984e3;
}
.article-card h2 { font-size: 20px; color: #2d3436; margin-bottom: 8px; line-height: 1.4; }
.article-card h2 a { color: #2d3436; text-decoration: none; }
.article-card h2 a:hover { color: #0984e3; }
.article-card .meta { font-size: 13px; color: #636e72; margin-bottom: 16px; }
.article-card .meta span { margin-right: 15px; }
.article-card .meta a { color: #0984e3; text-decoration: none; }
.article-card .meta a:hover { text-decoration: underline; }

.section { margin-bottom: 14px; }
.section .label {
    display: inline-block; background: #dfe6e9; color: #2d3436;
    font-size: 12px; font-weight: 600; padding: 2px 10px;
    border-radius: 3px; margin-bottom: 6px;
}
.section .label.essence { background: #ffeaa7; color: #2d3436; }
.section .label.brief { background: #dfe6e9; color: #2d3436; font-style: italic; }
.section .label.positive { background: #55efc4; color: #2d3436; }
.section .label.negative { background: #fab1a0; color: #2d3436; }
.section .label.cause { background: #74b9ff; color: #2d3436; }
.section .label.measure { background: #a29bfe; color: #fff; }
.section .label.quote { background: #fd79a8; color: #fff; }
.section p { font-size: 15px; color: #34495e; }

.quotes-list { list-style: none; padding: 0; }
.quotes-list li {
    position: relative; padding: 8px 16px; margin-bottom: 8px;
    background: #ffeaa7; border-radius: 4px; font-size: 14px;
    color: #2d3436; font-style: italic;
}
.quotes-list li::before {
    content: "\\201C"; font-size: 28px; color: #fdcb6e;
    position: absolute; left: 2px; top: -4px;
}

.summary-box {
    background: #f8f9fa; border: 1px solid #dfe6e9;
    border-radius: 4px; padding: 12px 16px;
    font-size: 14px; color: #636e72; margin-top: 10px;
}

/* 翻页（仅底部） */
.pagination { text-align: center; padding: 30px 0; }
.pagination a {
    display: inline-block; padding: 8px 16px; margin: 0 4px;
    background: #0984e3; color: #fff; text-decoration: none;
    border-radius: 4px; font-size: 14px;
}
.pagination a:hover { background: #0770c2; }
.pagination a.current { background: #2d3436; }
.pagination a.disabled { background: #b2bec3; pointer-events: none; }

/* 跳到末篇角标 */
.go-last {
    position: fixed; right: 20px; bottom: 80px;
    background: #1e272e; color: #fff;
    padding: 8px 14px; border-radius: 20px;
    font-size: 13px; cursor: pointer;
    z-index: 200; text-decoration: none;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    transition: all 0.2s;
    display: flex; align-items: center; gap: 4px;
}
.go-last:hover { background: #0984e3; transform: translateY(-2px); }

/* 返回顶部 */
.back-top {
    position: fixed; right: 20px; bottom: 30px;
    width: 40px; height: 40px; background: #0984e3;
    color: #fff; text-align: center; line-height: 40px;
    border-radius: 50%; cursor: pointer; font-size: 18px;
    display: none; z-index: 200;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* ======== 移动端适配 ======== */
@media (max-width: 768px) {
    .menu-toggle { display: block; }
    .sidebar-overlay.active { display: block; }

    .sidebar {
        transform: translateX(-100%);
        transition: transform 0.3s ease;
        width: 280px; z-index: 150;
    }
    .sidebar.open { transform: translateX(0); }

    .main-content {
        margin-left: 0 !important;
        padding: 60px 16px 20px 16px;
        width: 100% !important;
    }

    .article-card { padding: 18px 16px; }
    .article-card h2 { font-size: 17px; }
    .section p { font-size: 14px; }

    .go-last { right: 12px; bottom: 70px; padding: 6px 12px; font-size: 12px; }
    .back-top { right: 12px; bottom: 20px; width: 36px; height: 36px; line-height: 36px; }

    body::after { font-size: 32px; letter-spacing: 4px; }
}
"""

# ============ 通用 JS ============

JS = """
// 汉堡菜单
var menuBtn = document.getElementById('menuToggle');
var sidebar = document.querySelector('.sidebar');
var overlay = document.getElementById('sidebarOverlay');
if (menuBtn) {
    menuBtn.onclick = function() {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    };
}
if (overlay) {
    overlay.onclick = function() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    };
}

// 栏目筛选
function filterCategory(cat) {
    var items = document.querySelectorAll('.nav-list li[data-cat]');
    var cards = document.querySelectorAll('.article-card[data-cat]');
    items.forEach(function(li) {
        li.style.display = (cat === 'all' || li.dataset.cat === cat) ? '' : 'none';
    });
    cards.forEach(function(c) {
        c.style.display = (cat === 'all' || c.dataset.cat === cat) ? '' : 'none';
    });
}

// 搜索功能
function searchArticles(keyword) {
    keyword = keyword.toLowerCase();
    var items = document.querySelectorAll('.nav-list li');
    var cards = document.querySelectorAll('.article-card');
    items.forEach(function(li) {
        var title = li.querySelector('a').textContent.toLowerCase();
        li.style.display = title.indexOf(keyword) >= 0 || !keyword ? '' : 'none';
    });
    cards.forEach(function(c) {
        var title = c.querySelector('h2').textContent.toLowerCase();
        var content = c.textContent.toLowerCase();
        c.style.display = (title.indexOf(keyword) >= 0 || content.indexOf(keyword) >= 0 || !keyword) ? '' : 'none';
    });
}

// 高亮当前文章
function highlightNav() {
    var cards = document.querySelectorAll('.article-card');
    var navLinks = document.querySelectorAll('.nav-list li a');
    var scrollPos = window.scrollY + 100;
    cards.forEach(function(card, i) {
        if (card.offsetTop <= scrollPos && card.offsetTop + card.offsetHeight > scrollPos) {
            navLinks.forEach(function(a) { a.classList.remove('active'); });
            if (navLinks[i]) navLinks[i].classList.add('active');
        }
    });
}

// 返回顶部 + 滚动事件
var btn = document.getElementById('backTop');
window.onscroll = function() {
    if (btn) btn.style.display = window.scrollY > 300 ? 'block' : 'none';
    highlightNav();
};
if (btn) btn.onclick = function() { window.scrollTo({top:0,behavior:'smooth'}); };

// 跳到最后一篇
var goLast = document.getElementById('goLast');
if (goLast) {
    goLast.onclick = function(e) {
        e.preventDefault();
        var cards = document.querySelectorAll('.article-card');
        if (cards.length) {
            cards[cards.length - 1].scrollIntoView({behavior:'smooth'});
        }
    };
}
"""


def _escape(text):
    if not text:
        return ""
    return html_mod.escape(str(text))


def _format_sections(text):
    """将【xxx】分段内容渲染为带换行的HTML，便于阅读"""
    if not text or "【" not in text:
        return f"<p>{text}</p>"
    parts = re.split(r'(?=【[^】]+】)', text)
    html_parts = []
    for part in parts:
        part = part.strip()
        if part:
            html_parts.append(f"<p style='margin-bottom:6px'>{part}</p>")
    return "\n    ".join(html_parts)


def _render_article_card(article, index):
    title = _escape(article.get("title", ""))
    date = _escape(article.get("date", ""))
    category = _escape(article.get("category", ""))
    url = _escape(article.get("url", ""))
    source = _escape(article.get("source", ""))

    brief = _escape(article.get("brief", ""))
    essence = _escape(article.get("essence", ""))
    impact_pos = _escape(article.get("impact_positive", ""))
    impact_neg = _escape(article.get("impact_negative", ""))
    cause = _escape(article.get("cause_analysis", ""))
    measures = _escape(article.get("measures", ""))
    quotes = article.get("key_quotes", [])
    summary = _escape(article.get("summary", ""))

    failed = article.get("_failed", False)

    parts = [f'<div class="article-card" id="article-{index}" data-cat="{category}">']
    parts.append(f'  <h2><a href="{url}" target="_blank">{title}</a></h2>')
    parts.append(f'  <div class="meta"><span>{date}</span><span>{category}</span><a href="{url}" target="_blank">查看原文 &rarr;</a></div>')

    if failed:
        parts.append('  <div class="section"><p style="color:#e74c3c;">（AI分析失败，请检查API配置后重试）</p></div>')
        parts.append('</div>')
        return "\n".join(parts)

    if brief:
        parts.append(f'  <div class="section"><div class="label brief">简介</div><p>{brief}</p></div>')

    if essence:
        parts.append(f'  <div class="section"><div class="label essence">本质</div><p>{essence}</p></div>')

    if impact_pos:
        parts.append(f'  <div class="section"><div class="label positive">有利影响</div>{_format_sections(impact_pos)}</div>')

    if impact_neg:
        parts.append(f'  <div class="section"><div class="label negative">不利影响</div>{_format_sections(impact_neg)}</div>')

    if cause:
        parts.append(f'  <div class="section"><div class="label cause">原因分析</div>{_format_sections(cause)}</div>')

    if measures:
        parts.append(f'  <div class="section"><div class="label measure">措施/对策</div>{_format_sections(measures)}</div>')

    if quotes:
        parts.append(f'  <div class="section"><div class="label quote">金句</div>')
        parts.append('  <ul class="quotes-list">')
        for q in quotes:
            if q:
                parts.append(f'    <li>{_escape(q)}</li>')
        parts.append('  </ul></div>')

    if summary:
        parts.append(f'  <div class="summary-box">{summary}</div>')

    parts.append('</div>')
    return "\n".join(parts)


def _render_pagination(current, total):
    """生成底部翻页链接"""
    if total <= 1:
        return ""
    parts = []
    if current > 1:
        parts.append(f'<a href="page_{current-1}.html">&laquo; 上一页</a>')
    for i in range(1, total + 1):
        cls = ' class="current"' if i == current else ""
        parts.append(f'<a href="page_{i}.html"{cls}>{i}</a>')
    if current < total:
        parts.append(f'<a href="page_{current+1}.html">下一页 &raquo;</a>')
    return "\n    ".join(parts)


def generate_html(summaries, output_file=None, page_num=1, total_pages=1):
    """生成PC版多页HTML页面"""
    if output_file is None:
        output_file = os.path.join(config.OUTPUT_DIR, f"page_{page_num}.html")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    sorted_summaries = sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)
    categories = sorted(set(s.get("category", "") for s in sorted_summaries if s.get("category")))

    nav_items = []
    for i, s in enumerate(sorted_summaries):
        cat = _escape(s.get("category", ""))
        title_short = _escape(s.get("title", ""))[:35]
        date = _escape(s.get("date", ""))
        nav_items.append(f'    <li data-cat="{cat}"><a href="#article-{i}">{title_short}</a> <span class="nav-date">{date}</span> <span class="nav-cat">{cat}</span></li>')

    cards = [_render_article_card(s, i) for i, s in enumerate(sorted_summaries)]

    cat_options = '<option value="all">全部栏目</option>\n'
    for c in categories:
        cat_options += f'          <option value="{_escape(c)}">{_escape(c)}</option>\n'

    page_title = f"人民观点·公考素材积累 ({len(sorted_summaries)}篇)"

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_escape(page_title)}</title>
<style>{CSS}</style>
</head>
<body>

<button class="menu-toggle" id="menuToggle">☰</button>
<div class="sidebar-overlay" id="sidebarOverlay"></div>

<div class="sidebar">
  <h1>人民观点·公考素材积累</h1>
  <div class="filter-box">
    <select onchange="filterCategory(this.value)">
      {cat_options}
    </select>
  </div>
  <div class="search-box">
    <input type="text" placeholder="搜索文章..." oninput="searchArticles(this.value)">
  </div>
  <ul class="nav-list">
{chr(10).join(nav_items)}
  </ul>
  <div class="stats">共 {len(sorted_summaries)} 篇文章 | {config.DATE_START} ~ {config.DATE_END}</div>
</div>

<div class="main-content">
{chr(10).join(cards)}

  <div class="pagination">
    {_render_pagination(page_num, total_pages)}
  </div>
</div>

<a class="go-last" id="goLast" href="#">▼ 末篇</a>
<div class="back-top" id="backTop">&#9650;</div>
<div id="watermark"></div>
<div class="wm-corner">公考素材积累·小红书@星儿Yax</div>

<script>{JS}
(function(){{
    var c=document.getElementById('watermark'),txt='公考素材积累·小红书@星儿Yax';
    var W=window.innerWidth,H=window.innerHeight;
    for(var y=-100;y<H+200;y+=200){{
        for(var x=-200;x<W+200;x+=300){{
            var s=document.createElement('span');
            s.className='wm';s.textContent=txt;
            s.style.left=x+'px';s.style.top=y+'px';
            c.appendChild(s);
        }}
    }}
}})();
</script>
</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"HTML已生成: {output_file} ({len(sorted_summaries)}篇文章)")
    return output_file


def generate_mobile_html(summaries, output_file=None):
    """生成按周分页的移动端HTML（每周一个文件，便于阅读和分享）"""
    from datetime import datetime

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    sorted_summaries = sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)
    all_categories = sorted(set(s.get("category", "") for s in sorted_summaries if s.get("category")))

    # 按ISO周分组
    weeks = {}  # week_key -> {articles, start_date, end_date}
    for s in sorted_summaries:
        d = s.get("date", "")
        if not d:
            continue
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
            iso = dt.isocalendar()
            week_key = f"{iso[0]}-W{iso[1]:02d}"
        except ValueError:
            continue
        if week_key not in weeks:
            weeks[week_key] = {"articles": [], "dates": []}
        weeks[week_key]["articles"].append(s)
        weeks[week_key]["dates"].append(d)

    # 计算每周的日期范围
    for wk in weeks.values():
        wk["start"] = min(wk["dates"])
        wk["end"] = max(wk["dates"])

    sorted_week_keys = sorted(weeks.keys(), reverse=True)  # 最新周在前
    total_articles = len(sorted_summaries)

    # 生成每周页面
    pages = []
    for idx, week_key in enumerate(sorted_week_keys):
        wk = weeks[week_key]
        week_articles = sorted(wk["articles"], key=lambda x: x.get("date", ""), reverse=True)
        week_categories = sorted(set(a.get("category", "") for a in week_articles if a.get("category")))

        # 周导航信息
        prev_week = sorted_week_keys[idx + 1] if idx + 1 < len(sorted_week_keys) else None
        next_week = sorted_week_keys[idx - 1] if idx - 1 >= 0 else None

        # 周选择器选项
        week_options = ""
        for wk_key in sorted_week_keys:
            wk_info = weeks[wk_key]
            sel = ' selected' if wk_key == week_key else ''
            label = f"{wk_key} ({wk_info['start']}~{wk_info['end']}, {len(wk_info['articles'])}篇)"
            week_options += f'<option value="week_{wk_key}.html"{sel}>{label}</option>\n'

        # 栏目筛选选项
        cat_options = '<option value="all">全部栏目</option>'
        for c in week_categories:
            cat_options += f'<option value="{_escape(c)}">{_escape(c)}</option>'

        # 渲染文章卡片（服务端渲染，不依赖JS）
        cards_html = []
        for i, a in enumerate(week_articles):
            cards_html.append(_render_mobile_card(a, i))
        cards_str = "\n".join(cards_html)

        # 渲染侧边栏导航
        nav_html = []
        for i, a in enumerate(week_articles):
            cat = _escape(a.get("category", ""))
            title_short = _escape(a.get("title", ""))[:30]
            date = _escape(a.get("date", ""))
            nav_html.append(f'<li data-cat="{cat}"><a href="#article-{i}" onclick="closeSidebar()">{title_short}</a> <span class="nav-date">{date}</span> <span class="nav-cat">{cat}</span></li>')
        nav_str = "\n".join(nav_html)

        # 前后周导航HTML
        prev_link = f'<a href="week_{prev_week}.html" class="week-nav-btn">&laquo; 上一周</a>' if prev_week else '<span class="week-nav-btn disabled">&laquo; 上一周</span>'
        next_link = f'<a href="week_{next_week}.html" class="week-nav-btn">下一周 &raquo;</a>' if next_week else '<span class="week-nav-btn disabled">下一周 &raquo;</span>'

        week_title = f"{wk['start']} ~ {wk['end']}"
        page_title = f"{week_key} 人民观点·公考素材积累"

        html_content = _build_weekly_html(
            page_title=page_title,
            week_key=week_key,
            week_title=week_title,
            week_count=len(week_articles),
            total_count=total_articles,
            week_options=week_options,
            cat_options=cat_options,
            prev_link=prev_link,
            next_link=next_link,
            cards_html=cards_str,
            nav_html=nav_str,
            date_range=f"{config.DATE_START} ~ {config.DATE_END}",
        )

        output_path = os.path.join(config.OUTPUT_DIR, f"week_{week_key}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        pages.append(f"week_{week_key}.html")

    # 生成index.html重定向到最新周
    latest_week = sorted_week_keys[0] if sorted_week_keys else None
    if latest_week:
        index_file = os.path.join(config.OUTPUT_DIR, "index.html")
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(f'<!DOCTYPE html><html><head><meta charset="UTF-8"><title>人民观点·公考素材积累</title>'
                    f'<meta http-equiv="refresh" content="0;url=week_{latest_week}.html"></head>'
                    f'<body><p>正在跳转... <a href="week_{latest_week}.html">点击这里</a></p></body></html>')

    logger.info(f"按周分页HTML已生成: {len(pages)} 个周页面, 共 {total_articles} 篇文章")
    return pages


def _render_mobile_card(article, index):
    """渲染移动端文章卡片（服务端渲染）"""
    title = _escape(article.get("title", ""))
    date = _escape(article.get("date", ""))
    category = _escape(article.get("category", ""))
    url = _escape(article.get("url", ""))
    brief = _escape(article.get("brief", ""))
    essence = _escape(article.get("essence", ""))
    impact_pos = _escape(article.get("impact_positive", ""))
    impact_neg = _escape(article.get("impact_negative", ""))
    cause = _escape(article.get("cause_analysis", ""))
    measures = _escape(article.get("measures", ""))
    quotes = article.get("key_quotes", [])
    summary = _escape(article.get("summary", ""))
    failed = article.get("_failed", False)

    parts = [f'<div class="article-card" id="article-{index}" data-cat="{category}">']
    parts.append(f'<h2><a href="{url}" target="_blank">{title}</a></h2>')
    parts.append(f'<div class="meta"><span>{date}</span><span>{category}</span><a href="{url}" target="_blank">原文→</a></div>')

    if failed:
        parts.append('<div class="section"><p style="color:#e74c3c">（AI分析失败）</p></div></div>')
        return "\n".join(parts)

    if brief:
        parts.append(f'<div class="section"><div class="label brief">简介</div><p>{brief}</p></div>')
    if essence:
        parts.append(f'<div class="section"><div class="label essence">本质</div><p>{essence}</p></div>')
    if impact_pos:
        parts.append(f'<div class="section"><div class="label positive">有利影响</div>{_format_sections(impact_pos)}</div>')
    if impact_neg:
        parts.append(f'<div class="section"><div class="label negative">不利影响</div>{_format_sections(impact_neg)}</div>')
    if cause:
        parts.append(f'<div class="section"><div class="label cause">原因分析</div>{_format_sections(cause)}</div>')
    if measures:
        parts.append(f'<div class="section"><div class="label measure">措施/对策</div>{_format_sections(measures)}</div>')
    if quotes:
        parts.append('<div class="section"><div class="label quote">金句</div><ul class="quotes-list">')
        for q in quotes:
            if q:
                parts.append(f'<li>{_escape(q)}</li>')
        parts.append('</ul></div>')
    if summary:
        parts.append(f'<div class="summary-box">{summary}</div>')
    parts.append('</div>')
    return "\n".join(parts)


def _build_weekly_html(page_title, week_key, week_title, week_count, total_count,
                       week_options, cat_options, prev_link, next_link,
                       cards_html, nav_html, date_range):
    """构建按周分页的HTML页面"""

    weekly_css = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #f5f6fa; color: #2d3436; line-height: 1.8;
}
#watermark{position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden}
#watermark .wm{position:absolute;color:rgba(0,0,0,0.028);font-size:16px;white-space:nowrap;transform:rotate(-30deg);font-weight:600;letter-spacing:2px;user-select:none}
.wm-corner{position:fixed;right:8px;bottom:8px;z-index:9998;font-size:10px;color:rgba(0,0,0,0.12);letter-spacing:1px;pointer-events:none;user-select:none}

/* 顶部栏 */
.top-bar {
    position: fixed; top: 0; left: 0; right: 0;
    background: #1e272e; color: #fff;
    padding: 10px 16px; z-index: 200;
    display: flex; align-items: center; gap: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.top-bar .menu-btn {
    background: none; border: none; color: #fff;
    font-size: 22px; cursor: pointer; padding: 4px 8px;
    flex-shrink: 0;
}
.top-bar .title {
    font-size: 14px; font-weight: 600; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}
.top-bar .count {
    font-size: 12px; color: #b2bec3; margin-left: auto; flex-shrink: 0;
}

/* 周选择器 */
.week-selector {
    background: #fff; padding: 10px 16px; margin-top: 50px;
    border-bottom: 1px solid #dfe6e9;
}
.week-selector select {
    width: 100%; padding: 8px 10px; border-radius: 6px;
    border: 1px solid #dfe6e9; background: #fff;
    font-size: 13px; color: #2d3436;
}
.week-nav {
    display: flex; gap: 8px; margin-top: 8px;
}
.week-nav-btn {
    flex: 1; display: block; text-align: center;
    padding: 8px 12px; border-radius: 6px;
    background: #0984e3; color: #fff;
    text-decoration: none; font-size: 13px;
}
.week-nav-btn:hover { background: #0770c2; }
.week-nav-btn.disabled {
    background: #b2bec3; color: #fff; cursor: default;
    pointer-events: none;
}
.week-info {
    text-align: center; padding: 8px 0 4px;
    font-size: 15px; font-weight: 600; color: #2d3436;
}
.week-sub {
    text-align: center; font-size: 12px; color: #636e72;
    padding-bottom: 8px;
}

/* 侧边栏 */
.sidebar-overlay {
    display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.45); z-index: 299;
}
.sidebar-overlay.active { display: block; }
.sidebar {
    position: fixed; top: 0; left: 0; bottom: 0;
    width: 280px; background: #1e272e; color: #dfe6e9;
    overflow-y: auto; z-index: 300;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    padding: 16px 0;
}
.sidebar.open { transform: translateX(0); }
.sidebar .sb-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 16px 12px; border-bottom: 1px solid #636e72; margin-bottom: 8px;
}
.sidebar .sb-header span { font-size: 15px; font-weight: 600; }
.sidebar .sb-close {
    background: none; border: none; color: #b2bec3;
    font-size: 20px; cursor: pointer; padding: 4px;
}
.sidebar .filter-box { padding: 8px 12px; }
.sidebar .filter-box select {
    width: 100%; padding: 6px 10px; border-radius: 4px;
    border: 1px solid #636e72; background: #2d3436; color: #dfe6e9;
    font-size: 13px;
}
.sidebar .search-box { padding: 8px 12px; }
.sidebar .search-box input {
    width: 100%; padding: 8px 10px; border-radius: 4px;
    border: 1px solid #636e72; background: #2d3436; color: #dfe6e9;
    font-size: 14px;
}
.sidebar .nav-list { list-style: none; }
.sidebar .nav-list li { border-bottom: 1px solid rgba(255,255,255,0.05); }
.sidebar .nav-list li a {
    display: block; padding: 10px 16px; color: #b2bec3;
    text-decoration: none; font-size: 13px; line-height: 1.5;
}
.sidebar .nav-list li a:hover { background: rgba(255,255,255,0.08); color: #fff; }
.sidebar .nav-list li a.active { background: #0984e3; color: #fff; }
.sidebar .nav-list li .nav-date { font-size: 11px; color: #636e72; }
.sidebar .nav-list li .nav-cat { font-size: 11px; color: #0984e3; float: right; }
.sidebar .stats {
    padding: 10px 16px; font-size: 12px; color: #636e72;
    border-top: 1px solid #636e72; margin-top: 8px;
}

/* 内容区 */
.content {
    padding: 8px 14px 20px;
    max-width: 720px; margin: 0 auto;
}

/* 文章卡片 */
.article-card {
    background: #fff; border-radius: 8px;
    padding: 18px 16px; margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    border-left: 3px solid #0984e3;
}
.article-card h2 { font-size: 16px; color: #2d3436; margin-bottom: 6px; line-height: 1.45; }
.article-card h2 a { color: #2d3436; text-decoration: none; }
.article-card .meta { font-size: 12px; color: #636e72; margin-bottom: 12px; }
.article-card .meta span { margin-right: 10px; }
.article-card .meta a { color: #0984e3; text-decoration: none; }

.section { margin-bottom: 10px; }
.section .label {
    display: inline-block; background: #dfe6e9; color: #2d3436;
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 3px; margin-bottom: 4px;
}
.section .label.essence { background: #ffeaa7; }
.section .label.brief { background: #dfe6e9; font-style: italic; }
.section .label.positive { background: #55efc4; }
.section .label.negative { background: #fab1a0; }
.section .label.cause { background: #74b9ff; }
.section .label.measure { background: #a29bfe; color: #fff; }
.section .label.quote { background: #fd79a8; color: #fff; }
.section p { font-size: 14px; color: #34495e; line-height: 1.75; }

.quotes-list { list-style: none; padding: 0; }
.quotes-list li {
    position: relative; padding: 8px 12px 8px 20px; margin-bottom: 6px;
    background: #ffeaa7; border-radius: 4px; font-size: 13px;
    color: #2d3436; font-style: italic; line-height: 1.6;
}
.quotes-list li::before {
    content: "\\201C"; font-size: 22px; color: #fdcb6e;
    position: absolute; left: 4px; top: -2px;
}
.summary-box {
    background: #f8f9fa; border: 1px solid #dfe6e9;
    border-radius: 4px; padding: 10px 12px;
    font-size: 13px; color: #636e72; margin-top: 8px;
}

/* 底部周导航 */
.bottom-nav {
    padding: 16px 14px 24px;
    max-width: 720px; margin: 0 auto;
    display: flex; gap: 8px;
}

/* 返回顶部 */
.back-top {
    position: fixed; right: 14px; bottom: 18px;
    width: 36px; height: 36px; background: #0984e3;
    color: #fff; text-align: center; line-height: 36px;
    border-radius: 50%; cursor: pointer; font-size: 16px;
    display: none; z-index: 200;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

@media (min-width: 769px) {
    .content { padding: 8px 24px 30px; max-width: 860px; }
    .article-card { padding: 24px 28px; }
    .article-card h2 { font-size: 19px; }
    .section p { font-size: 15px; }
    .bottom-nav { max-width: 860px; }
}
"""

    weekly_js = """
// 侧边栏控制
function openSidebar() {
    document.querySelector('.sidebar').classList.add('open');
    document.getElementById('sidebarOverlay').classList.add('active');
}
function closeSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    document.getElementById('sidebarOverlay').classList.remove('active');
}

// 周跳转
function jumpWeek(sel) {
    if (sel.value) window.location.href = sel.value;
}

// 栏目筛选
function filterCategory(cat) {
    var items = document.querySelectorAll('.nav-list li[data-cat]');
    var cards = document.querySelectorAll('.article-card[data-cat]');
    items.forEach(function(li) {
        li.style.display = (cat === 'all' || li.dataset.cat === cat) ? '' : 'none';
    });
    cards.forEach(function(c) {
        c.style.display = (cat === 'all' || c.dataset.cat === cat) ? '' : 'none';
    });
}

// 搜索
function searchArticles(kw) {
    kw = kw.toLowerCase();
    var items = document.querySelectorAll('.nav-list li');
    var cards = document.querySelectorAll('.article-card');
    items.forEach(function(li) {
        var title = li.querySelector('a').textContent.toLowerCase();
        li.style.display = title.indexOf(kw) >= 0 || !kw ? '' : 'none';
    });
    cards.forEach(function(c) {
        var title = c.querySelector('h2').textContent.toLowerCase();
        var content = c.textContent.toLowerCase();
        c.style.display = (title.indexOf(kw) >= 0 || content.indexOf(kw) >= 0 || !kw) ? '' : 'none';
    });
}

// 返回顶部
var backBtn = document.getElementById('backTop');
window.onscroll = function() {
    if (backBtn) backBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
};
if (backBtn) backBtn.onclick = function() { window.scrollTo({top:0,behavior:'smooth'}); };
"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>{_escape(page_title)}</title>
<style>{weekly_css}</style>
</head>
<body>

<div class="top-bar">
  <button class="menu-btn" onclick="openSidebar()">☰</button>
  <div class="title">人民观点·公考素材积累</div>
  <div class="count">{week_count}篇 / 共{total_count}篇</div>
</div>

<div class="sidebar-overlay" id="sidebarOverlay" onclick="closeSidebar()"></div>

<div class="sidebar">
  <div class="sb-header">
    <span>本周目录</span>
    <button class="sb-close" onclick="closeSidebar()">✕</button>
  </div>
  <div class="filter-box">
    <select onchange="filterCategory(this.value)">
      {cat_options}
    </select>
  </div>
  <div class="search-box">
    <input type="text" placeholder="搜索本周文章..." oninput="searchArticles(this.value)">
  </div>
  <ul class="nav-list">
{nav_html}
  </ul>
  <div class="stats">{date_range}</div>
</div>

<div class="week-selector">
  <select onchange="jumpWeek(this)">
    {week_options}
  </select>
  <div class="week-nav">
    {prev_link}
    {next_link}
  </div>
</div>

<div class="week-info">{week_title}</div>
<div class="week-sub">{week_key} · {week_count}篇文章</div>

<div class="content">
{cards_html}
</div>

<div class="bottom-nav">
  {prev_link}
  {next_link}
</div>

<div class="back-top" id="backTop">&#9650;</div>
<div id="watermark"></div>
<div class="wm-corner">公考素材积累·小红书@星儿Yax</div>

<script>
{weekly_js}
(function(){{
    var c=document.getElementById('watermark'),txt='公考素材积累·小红书@星儿Yax';
    var W=window.innerWidth,H=window.innerHeight;
    for(var y=-100;y<H+200;y+=180){{
        for(var x=-200;x<W+200;x+=260){{
            var s=document.createElement('span');
            s.className='wm';s.textContent=txt;
            s.style.left=x+'px';s.style.top=y+'px';
            c.appendChild(s);
        }}
    }}
}})();
</script>
</body>
</html>"""


def generate_single_file_html(summaries, output_file=None, per_page=15):
    """生成单文件内部分页版（所有数据嵌入JS，客户端翻页，一个文件即可分享）"""
    sorted_summaries = sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)

    if output_file is None:
        # 文件名自动带上最新文章日期
        latest_date = sorted_summaries[0].get("date", "") if sorted_summaries else ""
        date_tag = latest_date.replace("-", "") if latest_date else ""
        suffix = f" {date_tag}" if date_tag else ""
        output_file = os.path.join(config.OUTPUT_DIR, f"人民观点_公考素材积累{suffix}.html")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    sorted_summaries = sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)
    categories = sorted(set(s.get("category", "") for s in sorted_summaries if s.get("category")))

    # 嵌入数据
    compact = []
    for s in sorted_summaries:
        compact.append({
            "title": s.get("title", ""),
            "date": s.get("date", ""),
            "category": s.get("category", ""),
            "url": s.get("url", ""),
            "brief": s.get("brief", ""),
            "essence": s.get("essence", ""),
            "impact_positive": s.get("impact_positive", ""),
            "impact_negative": s.get("impact_negative", ""),
            "cause_analysis": s.get("cause_analysis", ""),
            "measures": s.get("measures", ""),
            "key_quotes": s.get("key_quotes", []),
            "summary": s.get("summary", ""),
            "_failed": s.get("_failed", False),
        })

    data_json = json.dumps(compact, ensure_ascii=False)
    cat_options = '<option value="all">全部栏目</option>'
    for c in categories:
        cat_options += f'<option value="{_escape(c)}">{_escape(c)}</option>'

    total = len(sorted_summaries)
    date_range = f"{config.DATE_START} ~ {config.DATE_END}"

    css = """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:#f5f6fa;color:#2d3436;line-height:1.8}

/* 水印层 */
#watermark{position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden}
#watermark .wm{position:absolute;color:rgba(0,0,0,0.028);font-size:16px;white-space:nowrap;transform:rotate(-30deg);font-weight:600;letter-spacing:2px;user-select:none}
/* 右下角角标水印 */
.wm-corner{position:fixed;right:8px;bottom:8px;z-index:9998;font-size:10px;color:rgba(0,0,0,0.12);letter-spacing:1px;pointer-events:none;user-select:none;writing-mode:horizontal-tb}

.top-bar{position:fixed;top:0;left:0;right:0;background:#1e272e;color:#fff;padding:6px 10px;z-index:200;display:flex;align-items:center;gap:4px;box-shadow:0 2px 8px rgba(0,0,0,.15)}
.top-bar .menu-btn{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;padding:2px 6px;flex-shrink:0}
.top-bar .title{font-size:13px;font-weight:600;white-space:nowrap;flex-shrink:0;padding-right:4px;border-right:1px solid rgba(255,255,255,.15)}
.help-btn{background:rgba(255,255,255,.15);border:none;color:#fff;padding:2px 8px;border-radius:3px;font-size:11px;cursor:pointer;margin-left:6px;white-space:nowrap}
.help-btn:hover{background:rgba(255,255,255,.3)}

/* 帮助弹窗 */
.help-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:399}
.help-overlay.active{display:block}
.help-modal{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);width:min(92vw,520px);max-height:80vh;background:#fff;border-radius:10px;z-index:400;box-shadow:0 8px 30px rgba(0,0,0,.2);overflow:hidden}
.help-modal.active{display:block}
.help-header{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;background:#1e272e;color:#fff;font-size:15px;font-weight:600}
.help-close{background:none;border:none;color:#fff;font-size:18px;cursor:pointer;padding:2px 6px}
.help-body{padding:16px 20px;overflow-y:auto;max-height:calc(80vh - 50px);font-size:13px;line-height:1.8;color:#2d3436}
.help-body h3{font-size:14px;margin:14px 0 6px;color:#0984e3}
.help-body h3:first-child{margin-top:0}
.help-body ul{padding-left:18px;margin:4px 0}
.help-body li{margin-bottom:4px}
.help-body b{color:#2d3436}
.top-pager{flex:1;display:flex;align-items:center;justify-content:flex-end;gap:2px;overflow-x:auto;min-width:0;-webkit-overflow-scrolling:touch;scrollbar-width:none}
.top-pager::-webkit-scrollbar{display:none}
.top-pager .pg-btn{padding:2px 5px;background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:3px;font-size:12px;cursor:pointer;line-height:1.4;flex-shrink:0}
.top-pager .pg-btn:hover{background:rgba(255,255,255,.25)}
.top-pager .pg-btn.current{background:#0984e3}
.top-pager .pg-btn.disabled{opacity:.4;pointer-events:none}
.top-pager .pg-info{font-size:11px;color:#b2bec3;padding:0 2px;white-space:nowrap;flex-shrink:0}
.top-pager input{width:34px;padding:2px 3px;border:1px solid rgba(255,255,255,.2);border-radius:3px;background:rgba(255,255,255,.1);color:#fff;font-size:11px;text-align:center;flex-shrink:0}
.top-pager input::placeholder{color:rgba(255,255,255,.4)}
@media(max-width:480px){.top-pager .pg-info,.top-pager .pg-num{display:none}.top-pager input{width:30px}}

.sidebar-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:299}
.sidebar-overlay.active{display:block}
.sidebar{position:fixed;top:0;left:0;bottom:0;width:280px;background:#1e272e;color:#dfe6e9;overflow-y:auto;z-index:300;transform:translateX(-100%);transition:transform .3s;padding:16px 0}
.sidebar.open{transform:translateX(0)}
.sidebar .sb-header{display:flex;align-items:center;justify-content:space-between;padding:0 16px 12px;border-bottom:1px solid #636e72;margin-bottom:8px}
.sidebar .sb-header span{font-size:15px;font-weight:600}
.sidebar .sb-close{background:none;border:none;color:#b2bec3;font-size:20px;cursor:pointer;padding:4px}
.sidebar .filter-box,.sidebar .search-box{padding:8px 12px}
.sidebar select,.sidebar input{width:100%;padding:8px 10px;border-radius:4px;border:1px solid #636e72;background:#2d3436;color:#dfe6e9;font-size:13px}
.sidebar .nav-list{list-style:none}
.sidebar .nav-list li{border-bottom:1px solid rgba(255,255,255,.05)}
.sidebar .nav-list li a{display:block;padding:10px 16px;color:#b2bec3;text-decoration:none;font-size:13px;line-height:1.5}
.sidebar .nav-list li a:hover{background:rgba(255,255,255,.08);color:#fff}
.sidebar .nav-list li .nav-date{font-size:11px;color:#636e72}
.sidebar .nav-list li .nav-cat{font-size:11px;color:#0984e3;float:right}
.sidebar .stats{padding:10px 16px;font-size:12px;color:#636e72;border-top:1px solid #636e72;margin-top:8px}

/* 分页控制 */
.pager{background:#fff;padding:6px 14px;display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:wrap;border-bottom:1px solid #eee;font-size:12px}
.pager .pg-btn{display:inline-block;padding:3px 8px;background:#0984e3;color:#fff;text-decoration:none;border-radius:3px;font-size:12px;cursor:pointer;border:none;line-height:1.4}
.pager .pg-btn:hover{background:#0770c2}
.pager .pg-btn.current{background:#2d3436}
.pager .pg-btn.disabled{background:#b2bec3;pointer-events:none}
.pager .pg-info{font-size:11px;color:#999;padding:0 4px}

.content{padding:42px 14px 20px;max-width:720px;margin:0 auto}

.article-card{background:#fff;border-radius:8px;padding:18px 16px;margin-bottom:16px;box-shadow:0 1px 4px rgba(0,0,0,.06);border-left:3px solid #0984e3}
.article-card h2{font-size:16px;color:#2d3436;margin-bottom:6px;line-height:1.45}
.article-card h2 a{color:#2d3436;text-decoration:none}
.article-card .meta{font-size:12px;color:#636e72;margin-bottom:12px}
.article-card .meta span{margin-right:10px}
.article-card .meta a{color:#0984e3;text-decoration:none}

.section{margin-bottom:10px}
.section .label{display:inline-block;background:#dfe6e9;color:#2d3436;font-size:11px;font-weight:600;padding:2px 8px;border-radius:3px;margin-bottom:4px}
.section .label.essence{background:#ffeaa7}
.section .label.brief{background:#dfe6e9;font-style:italic}
.section .label.positive{background:#55efc4}
.section .label.negative{background:#fab1a0}
.section .label.cause{background:#74b9ff}
.section .label.measure{background:#a29bfe;color:#fff}
.section .label.quote{background:#fd79a8;color:#fff}
.section p{font-size:14px;color:#34495e;line-height:1.75}

.quotes-list{list-style:none;padding:0}
.quotes-list li{position:relative;padding:8px 12px 8px 20px;margin-bottom:6px;background:#ffeaa7;border-radius:4px;font-size:13px;color:#2d3436;font-style:italic;line-height:1.6}
.quotes-list li::before{content:"\\201C";font-size:22px;color:#fdcb6e;position:absolute;left:4px;top:-2px}
.summary-box{background:#f8f9fa;border:1px solid #dfe6e9;border-radius:4px;padding:10px 12px;font-size:13px;color:#636e72;margin-top:8px}

.nav-float{position:fixed;right:14px;bottom:18px;z-index:200;display:none;flex-direction:column;gap:6px}
.nav-float button{width:36px;height:36px;background:#0984e3;color:#fff;text-align:center;line-height:36px;border-radius:50%;cursor:pointer;font-size:15px;border:none;box-shadow:0 2px 8px rgba(0,0,0,.2)}
.nav-float button:hover{background:#0770c2}

@media(min-width:769px){.content{padding:42px 24px 30px;max-width:860px}.article-card{padding:24px 28px}.article-card h2{font-size:19px}.section p{font-size:15px}}
"""

    js = r"""
var DATA=DATA_JSON,PP=PER_PAGE,cur=1,filtered=DATA;

function esc(s){var d=document.createElement('div');d.appendChild(document.createTextNode(s||''));return d.innerHTML}
function fmtSec(t){if(!t||t.indexOf('【')<0)return'<p>'+esc(t)+'</p>';return t.split(/(?=【[^】]+】)/).map(function(p){return p.trim()?'<p style="margin-bottom:5px">'+esc(p.trim())+'</p>':''}).join('')}

function renderCard(a,i){
    var cat=esc(a.category||''),o='<div class="article-card" id="a-'+i+'" data-cat="'+cat+'">';
    o+='<h2><a href="'+esc(a.url||'')+'" target="_blank">'+esc(a.title||'')+'</a></h2>';
    o+='<div class="meta"><span>'+esc(a.date||'')+'</span><span>'+cat+'</span><a href="'+esc(a.url||'')+'" target="_blank">原文→</a></div>';
    if(a._failed){o+='<div class="section"><p style="color:#e74c3c">（AI分析失败）</p></div></div>';return o}
    if(a.brief)o+='<div class="section"><div class="label brief">简介</div><p>'+esc(a.brief)+'</p></div>';
    if(a.essence)o+='<div class="section"><div class="label essence">本质</div><p>'+esc(a.essence)+'</p></div>';
    if(a.impact_positive)o+='<div class="section"><div class="label positive">有利影响</div>'+fmtSec(a.impact_positive)+'</div>';
    if(a.impact_negative)o+='<div class="section"><div class="label negative">不利影响</div>'+fmtSec(a.impact_negative)+'</div>';
    if(a.cause_analysis)o+='<div class="section"><div class="label cause">原因分析</div>'+fmtSec(a.cause_analysis)+'</div>';
    if(a.measures)o+='<div class="section"><div class="label measure">措施/对策</div>'+fmtSec(a.measures)+'</div>';
    if(a.key_quotes&&a.key_quotes.length){o+='<div class="section"><div class="label quote">金句</div><ul class="quotes-list">';a.key_quotes.forEach(function(q){if(q)o+='<li>'+esc(q)+'</li>'});o+='</ul></div>'}
    if(a.summary)o+='<div class="summary-box">'+esc(a.summary)+'</div>';
    o+='</div>';return o;
}

function render(){
    var total=filtered.length,pages=Math.ceil(total/PP)||1;
    if(cur>pages)cur=pages;
    var s=(cur-1)*PP,e=Math.min(s+PP,total),html='';
    for(var i=s;i<e;i++)html+=renderCard(filtered[i],i);
    document.getElementById('cards').innerHTML=html||'<p style="text-align:center;color:#636e72;padding:40px">无匹配文章</p>';
    renderPager(pages,total);
    renderNav(s,e);
    window.scrollTo({top:0,behavior:'instant'});
}

function renderPager(pages,total){
    var mk=function(isTop){
        var h='<button class="pg-btn'+(cur<=1?' disabled':'')+'" onclick="go(1)">«</button>';
        h+='<button class="pg-btn'+(cur<=1?' disabled':'')+'" onclick="go('+(cur-1)+')">‹</button>';
        var s=Math.max(1,cur-2),e=Math.min(pages,cur+2);
        if(s>1)h+='<span class="pg-info">…</span>';
        for(var i=s;i<=e;i++)h+='<button class="pg-btn'+(i===cur?' current':'')+'" onclick="go('+i+')">'+i+'</button>';
        if(e<pages)h+='<span class="pg-info">…</span>';
        h+='<button class="pg-btn'+(cur>=pages?' disabled':'')+'" onclick="go('+(cur+1)+')">›</button>';
        h+='<button class="pg-btn'+(cur>=pages?' disabled':'')+'" onclick="go('+pages+')">»</button>';
        h+='<span class="pg-info">'+cur+'/'+pages+'页·'+total+'篇</span>';
        h+='<input id="pg'+(isTop?'T':'B')+'" type="number" min="1" max="'+pages+'" placeholder="页" onkeydown="if(event.key===\'Enter\')jumpTo(this.value,'+pages+')"><button class="pg-btn" style="padding:2px 5px" onclick="jumpTo(document.getElementById(\'pg'+(isTop?'T':'B')+'\').value,'+pages+')">跳</button>';
        return h;
    };
    document.getElementById('pagerTop').innerHTML=mk(true);
    document.getElementById('pagerBot').innerHTML=mk(false);
}

function jumpTo(v,maxP){var p=parseInt(v);if(p>=1&&p<=maxP){cur=p;render();document.getElementById('topBar').scrollIntoView()}}

function renderNav(s,e){
    var h='';for(var i=s;i<e;i++){
        var a=filtered[i],cat=esc(a.category||''),t=esc((a.title||'').substring(0,30));
        h+='<li data-cat="'+cat+'"><a href="#a-'+i+'" onclick="closeSB()">'+t+'</a> <span class="nav-date">'+esc(a.date||'')+'</span> <span class="nav-cat">'+cat+'</span></li>';
    }
    document.getElementById('navList').innerHTML=h;
}

function go(p){cur=p;render();document.getElementById('topBar').scrollIntoView()}

function filterCat(cat){
    filtered=cat==='all'?DATA:DATA.filter(function(a){return a.category===cat});
    cur=1;render();
}
function searchKW(kw){
    kw=kw.toLowerCase();
    filtered=!kw?DATA:DATA.filter(function(a){
        return((a.title||'')+(a.brief||'')+(a.essence||'')+(a.summary||'')).toLowerCase().indexOf(kw)>=0;
    });
    cur=1;render();
}
function openSB(){document.querySelector('.sidebar').classList.add('open');document.getElementById('overlay').classList.add('active')}
function closeSB(){document.querySelector('.sidebar').classList.remove('open');document.getElementById('overlay').classList.remove('active')}
function toggleHelp(){document.getElementById('helpModal').classList.toggle('active');document.getElementById('helpOverlay').classList.toggle('active')}

var nf=document.getElementById('navFloat');
window.onscroll=function(){if(nf)nf.style.display=window.scrollY>300?'flex':'none'};

// 键盘左右方向键翻页
document.onkeydown=function(e){
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
    var pages=Math.ceil(filtered.length/PP);
    if(e.key==='ArrowLeft'&&cur>1){cur--;render()}
    if(e.key==='ArrowRight'&&cur<pages){cur++;render()}
};

// 手机端左右滑动翻页
(function(){
    var sx=0,sy=0,tracking=false;
    document.addEventListener('touchstart',function(e){
        if(e.target.closest('.sidebar')||e.target.closest('.top-bar'))return;
        sx=e.touches[0].clientX;sy=e.touches[0].clientY;tracking=true;
    },{passive:true});
    document.addEventListener('touchend',function(e){
        if(!tracking)return;tracking=false;
        var dx=e.changedTouches[0].clientX-sx,dy=e.changedTouches[0].clientY-sy;
        if(Math.abs(dx)<60||Math.abs(dy)>Math.abs(dx))return;
        var pages=Math.ceil(filtered.length/PP);
        if(dx<0&&cur<pages){cur++;render()}
        if(dx>0&&cur>1){cur--;render()}
    },{passive:true});
})();

render();

// 生成水印阵列
(function(){
    var c=document.getElementById('watermark'),txt='公考素材积累·小红书@星儿Yax';
    var W=window.innerWidth,H=window.innerHeight;
    var stepX=260,stepY=180;
    for(var y=-100;y<H+200;y+=stepY){
        for(var x=-200;x<W+200;x+=stepX){
            var s=document.createElement('span');
            s.className='wm';s.textContent=txt;
            s.style.left=x+'px';s.style.top=y+'px';
            c.appendChild(s);
        }
    }
})();""".replace("DATA_JSON", data_json).replace("PER_PAGE", str(per_page))

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>人民观点·公考素材积累 ({total}篇)</title>
<style>{css}</style>
</head>
<body>

<div class="top-bar" id="topBar">
  <button class="menu-btn" onclick="openSB()">☰</button>
  <div class="title">人民观点·公考素材积累 <button class="help-btn" onclick="toggleHelp()">使用说明</button></div>
  <div class="top-pager" id="pagerTop"></div>
</div>

<!-- 使用说明弹窗 -->
<div class="help-overlay" id="helpOverlay" onclick="toggleHelp()"></div>
<div class="help-modal" id="helpModal">
  <div class="help-header">
    <span>📖 使用说明</span>
    <button class="help-close" onclick="toggleHelp()">✕</button>
  </div>
  <div class="help-body">
    <h3>📋 页面布局</h3>
    <p>本页面为<b>单文件内部分页版</b>，所有文章嵌入一个HTML文件中，无需联网即可阅读。</p>
    <ul>
      <li><b>顶部栏</b>：左侧☰菜单按钮和标题，右侧翻页控件（支持输入页码跳转）</li>
      <li><b>内容区</b>：每页显示15篇文章卡片，包含简介、本质、影响分析、原因、对策、金句等结构化内容</li>
      <li><b>底部翻页</b>：完整页码导航，支持首页/末页跳转和页码输入</li>
      <li><b>右下角按钮</b>：滚动页面后出现▲（回顶部）和▼（到底部）两个快捷按钮</li>
    </ul>

    <h3>🔍 目录导航</h3>
    <ul>
      <li>点击左上角 <b>☰</b> 按钮展开侧边栏目录</li>
      <li>目录仅显示<b>当前页</b>的文章列表，点击标题可快速定位到对应文章</li>
      <li>侧边栏支持<b>栏目筛选</b>（下拉菜单）和<b>关键词搜索</b>（输入即过滤）</li>
      <li>筛选和搜索后，翻页会自动更新为筛选结果的页数</li>
      <li>点击侧边栏外的灰色区域可关闭目录</li>
    </ul>

    <h3>📄 翻页方式</h3>
    <ul>
      <li><b>顶部翻页</b>：固定在页面顶部，随时可用，显示当前页码和总页数</li>
      <li><b>底部翻页</b>：显示完整页码列表，点击数字直接跳转</li>
      <li><b>页码输入</b>：在输入框中输入页码后按回车或点击「跳」按钮，可快速跳转到指定页</li>
      <li><b>键盘翻页</b>：按 ← 左方向键上一页，→ 右方向键下一页</li>
      <li><b>手势翻页</b>（手机端）：在内容区左滑切换下一页，右滑切换上一页</li>
    </ul>

    <h3>💡 温馨提示</h3>
    <ul>
      <li>点击文章标题可跳转到<b>人民网原文</b>阅读全文</li>
      <li>页面适配<b>手机端</b>，可直接在手机浏览器中打开阅读</li>
    </ul>
  </div>
</div>

<div class="sidebar-overlay" id="overlay" onclick="closeSB()"></div>
<div class="sidebar">
  <div class="sb-header"><span>目录导航</span><button class="sb-close" onclick="closeSB()">✕</button></div>
  <div class="filter-box"><select onchange="filterCat(this.value)">{cat_options}</select></div>
  <div class="search-box"><input type="text" placeholder="搜索文章..." oninput="searchKW(this.value)"></div>
  <ul class="nav-list" id="navList"></ul>
  <div class="stats">{date_range}</div>
</div>

<div class="content" id="cards"></div>
<div class="pager" id="pagerBot"></div>

<div class="nav-float" id="navFloat">
  <button onclick="window.scrollTo({{top:0,behavior:'smooth'}})" title="回到顶部">▲</button>
  <button onclick="window.scrollTo({{top:document.body.scrollHeight,behavior:'smooth'}})" title="跳到底部">▼</button>
</div>
<div id="watermark"></div>
<div class="wm-corner">公考素材积累·小红书@星儿Yax</div>

<script>{js}</script>
</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"单文件内部分页版已生成: {output_file} ({total}篇文章, 每页{per_page}篇)")
    return output_file


def generate_all(summaries, batch_size=None):
    """分批生成所有HTML页面和索引（PC多页版 + 单文件版）"""
    if batch_size is None:
        batch_size = config.HTML_BATCH_SIZE

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    total_pages = math.ceil(len(summaries) / batch_size)

    sorted_summaries = sorted(summaries, key=lambda x: x.get("date", ""), reverse=True)

    # PC多页版
    pages = []
    for page_num in range(1, total_pages + 1):
        start = (page_num - 1) * batch_size
        end = min(start + batch_size, len(sorted_summaries))
        batch = sorted_summaries[start:end]
        output_file = os.path.join(config.OUTPUT_DIR, f"page_{page_num}.html")
        generate_html(batch, output_file, page_num, total_pages)
        pages.append(f"page_{page_num}.html")

    # 索引页
    index_file = os.path.join(config.OUTPUT_DIR, "index.html")
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>人民观点·公考素材积累</title>
<meta http-equiv="refresh" content="0;url=page_1.html"></head>
<body><p>正在跳转... <a href="page_1.html">点击这里</a></p></body></html>""")

    # 按周分页版
    weekly_pages = generate_mobile_html(sorted_summaries)
    pages.extend(weekly_pages)

    # 单文件内部分页版
    generate_single_file_html(sorted_summaries)

    logger.info(f"共生成 {total_pages} 个多页HTML + {len(weekly_pages)} 个周页面 + 1个单文件版 + index.html")
    return pages

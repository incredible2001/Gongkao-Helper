"""爬虫模块 - 采集人民网观点频道文章列表和正文"""

import json
import logging
import os
import re
import time
from datetime import datetime

import requests
from lxml import html as lxml_html

from scripts import config

logger = logging.getLogger("scraper")


def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def _get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    })
    return session


def _fetch_page(session, url, retries=None):
    if retries is None:
        retries = config.MAX_RETRIES
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=config.REQUEST_TIMEOUT)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return resp.text
            logger.warning(f"HTTP {resp.status_code} for {url}")
        except requests.RequestException as e:
            logger.warning(f"Request error (attempt {attempt+1}/{retries}) for {url}: {e}")
        if attempt < retries - 1:
            time.sleep(config.REQUEST_DELAY * (attempt + 1))
    return None


def _build_page_url(base_url, page_num):
    if page_num == 1:
        return base_url
    return base_url.replace("index.html", f"index{page_num}.html")


def _extract_article_links_from_list(page_html):
    """从列表页HTML中提取文章链接、标题、日期"""
    tree = lxml_html.fromstring(page_html)
    results = []

    # 方式1: 列表页格式 <ul class="list_16"><li><a>title</a> <em>date</em></li>
    for li in tree.xpath('//ul[contains(@class,"list_16")]/li'):
        a_els = li.xpath('.//a/@href')
        titles = li.xpath('.//a/text()')
        dates = li.xpath('.//em/text()')
        if a_els and titles:
            href = a_els[0]
            title = titles[0].strip()
            date = dates[0].strip() if dates else ""
            if re.search(r'/n1/\d{4}/\d{4}/', href):
                full_url = href if href.startswith("http") else f"http://opinion.people.com.cn{href}"
                results.append({"url": full_url, "title": title, "date": date})

    # 方式2: hdNews格式 <div class="hdNews"><p><strong><a>title</a></strong>
    if not results:
        for div in tree.xpath('//div[contains(@class,"hdNews")]'):
            a_els = div.xpath('.//strong/a/@href')
            titles = div.xpath('.//strong/a/text()')
            if a_els and titles:
                href = a_els[0]
                title = titles[0].strip()
                if re.search(r'/n1/\d{4}/\d{4}/', href):
                    full_url = href if href.startswith("http") else f"http://opinion.people.com.cn{href}"
                    date_match = re.search(r'/n1/(\d{4})/(\d{4})/', href)
                    date = ""
                    if date_match:
                        y, md = date_match.group(1), date_match.group(2)
                        date = f"{y}-{md[:2]}-{md[2:]}"
                    results.append({"url": full_url, "title": title, "date": date})

    # 方式3: 通用匹配所有含日期的链接
    if not results:
        all_links = tree.xpath('//a/@href')
        all_texts = tree.xpath('//a/text()')
        seen = set()
        for href, text in zip(all_links, all_texts):
            m = re.search(r'/n1/(\d{4})/(\d{4})/', href)
            if m and href not in seen:
                seen.add(href)
                y, md = m.group(1), m.group(2)
                date = f"{y}-{md[:2]}-{md[2:]}"
                full_url = href if href.startswith("http") else f"http://opinion.people.com.cn{href}"
                title = text.strip()
                if title:
                    results.append({"url": full_url, "title": title, "date": date})

    return results


def collect_article_list(categories=None):
    """从所有栏目列表页采集文章链接列表"""
    if categories is None:
        categories = config.CATEGORIES

    session = _get_session()
    all_articles = {}  # url -> article_info

    for cat in categories:
        cat_name = cat["name"]
        base_url = cat["url"]
        max_pages = cat["max_pages"]
        logger.info(f"采集栏目: {cat_name} (max_pages={max_pages})")

        for page_num in range(1, max_pages + 1):
            page_url = _build_page_url(base_url, page_num)
            page_html = _fetch_page(session, page_url)
            if page_html is None:
                logger.info(f"  {cat_name} 第{page_num}页无法访问，停止翻页")
                break

            articles = _extract_article_links_from_list(page_html)
            if not articles:
                logger.info(f"  {cat_name} 第{page_num}页无文章，停止翻页")
                break

            new_count = 0
            for art in articles:
                if art["url"] not in all_articles:
                    art["category"] = cat_name
                    all_articles[art["url"]] = art
                    new_count += 1

            logger.info(f"  {cat_name} 第{page_num}页: {len(articles)}篇, 新增{new_count}篇")

            # 检查日期是否超出范围
            oldest_date = articles[-1]["date"] if articles else ""
            if oldest_date and oldest_date < config.DATE_START:
                logger.info(f"  {cat_name} 第{page_num}页最早日期{oldest_date}超出范围，停止翻页")
                break

            time.sleep(config.REQUEST_DELAY)

    # 过滤日期范围
    filtered = []
    for art in all_articles.values():
        if art["date"] and art["date"] >= config.DATE_START:
            filtered.append(art)
        elif not art["date"]:
            filtered.append(art)  # 无日期的保留

    filtered.sort(key=lambda x: x["date"], reverse=True)
    logger.info(f"共采集 {len(filtered)} 篇文章（去重后），日期范围: {config.DATE_START} ~ {config.DATE_END}")
    return filtered


def fetch_article_content(url, session=None):
    """获取单篇文章的正文内容"""
    if session is None:
        session = _get_session()

    page_html = _fetch_page(session, url)
    if page_html is None:
        return None

    tree = lxml_html.fromstring(page_html)

    # 标题
    title_els = tree.xpath('//h1/text()')
    title = title_els[0].strip() if title_els else ""
    title = title.replace("\xa0", " ").strip()

    # 日期
    date_els = tree.xpath('//meta[@name="publishdate"]/@content')
    date = date_els[0].strip() if date_els else ""

    # 来源
    source_els = tree.xpath('//meta[@name="source"]/@content')
    source = source_els[0].strip() if source_els else ""

    # 正文 - 多种选择器兼容
    content_parts = []
    for selector in [
        '//div[@class="rm_txt_con cf"]//p',
        '//div[@id="rwb_zw"]//p',
        '//div[contains(@class,"text_con")]//p',
        '//div[contains(@class,"article")]//p',
    ]:
        paragraphs = tree.xpath(selector)
        if paragraphs:
            for p in paragraphs:
                text = p.text_content().strip()
                text = text.replace("\xa0", " ").replace("‌", "")
                if text and len(text) > 5:
                    content_parts.append(text)
            break

    if not content_parts:
        # 最后手段：获取所有 <p> 标签
        for p in tree.xpath('//p'):
            text = p.text_content().strip()
            text = text.replace("\xa0", " ").replace("‌", "")
            if text and len(text) > 20:
                content_parts.append(text)

    content = "\n\n".join(content_parts)

    return {
        "title": title,
        "date": date,
        "source": source,
        "content": content,
        "url": url,
    }


def fetch_all_articles(articles_list, batch_size=None, progress_file=None):
    """批量抓取文章正文，支持断点续传"""
    if batch_size is None:
        batch_size = config.SCRAPER_BATCH_SIZE

    # 加载进度
    done_urls = set()
    results = []
    if progress_file and os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            progress = json.load(f)
            done_urls = set(progress.get("done_urls", []))
            logger.info(f"从断点恢复: 已完成 {len(done_urls)} 篇")

    # 加载已有结果
    existing = {}
    if os.path.exists(config.ARTICLES_JSON):
        with open(config.ARTICLES_JSON, "r", encoding="utf-8") as f:
            for art in json.load(f):
                existing[art["url"]] = art

    session = _get_session()
    total = len(articles_list)

    for i, art_info in enumerate(articles_list):
        url = art_info["url"]

        if url in done_urls and url in existing and existing[url].get("content"):
            results.append(existing[url])
            continue

        logger.info(f"抓取正文 [{i+1}/{total}]: {art_info['title'][:40]}")

        content_data = fetch_article_content(url, session)
        if content_data and content_data["content"]:
            article = {
                **art_info,
                "content": content_data["content"],
                "source": content_data.get("source", ""),
            }
            # 用实际页面标题和日期覆盖
            if content_data["title"]:
                article["title"] = content_data["title"]
            if content_data["date"]:
                article["date"] = content_data["date"]
        else:
            article = {**art_info, "content": ""}
            logger.warning(f"  无法获取正文: {url}")

        results.append(article)
        done_urls.add(url)

        # 定期保存进度
        if (i + 1) % 10 == 0:
            _save_progress(progress_file, done_urls, results)
            logger.info(f"  进度保存: {i+1}/{total}")

        time.sleep(config.REQUEST_DELAY)

    # 最终保存
    _save_progress(progress_file, done_urls, results)
    return results


def _save_progress(progress_file, done_urls, results):
    if progress_file:
        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump({"done_urls": list(done_urls), "count": len(done_urls)}, f, ensure_ascii=False)
    # 同时保存文章数据
    with open(config.ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_articles():
    if os.path.exists(config.ARTICLES_JSON):
        with open(config.ARTICLES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


if __name__ == "__main__":
    setup_logging()
    articles = collect_article_list()
    logger.info(f"列表采集完成，共 {len(articles)} 篇")
    # 保存列表
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    logger.info(f"列表已保存到 {config.ARTICLES_JSON}")

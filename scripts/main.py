"""主流程编排 - 人民网观点频道文章自动总结

用法（在项目根目录下执行）:
  python scripts/main.py collect          # 仅采集文章列表
  python scripts/main.py fetch            # 仅抓取文章正文（需先collect）
  python scripts/main.py analyze          # 仅AI分析（需先fetch）
  python scripts/main.py html             # 仅生成HTML（需先analyze）
  python scripts/main.py run              # 执行全流程（collect -> fetch -> analyze -> html）
  python scripts/main.py update           # 增量更新：采集新文章 + 抓取 + 分析 + 生成HTML
  python scripts/main.py mobile           # 仅生成按周分页HTML
  python scripts/main.py test [N]         # 测试模式：采集后取前N篇(默认10)运行全流程
  python scripts/main.py status           # 查看当前进度
"""

import json
import logging
import os
import sys

# 确保 scripts 包可被正确导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts import config
from scripts.scraper import setup_logging, collect_article_list, fetch_all_articles, load_articles
from scripts.analyzer import analyze_batch, load_summaries
from scripts.html_generator import generate_all, generate_mobile_html, generate_single_file_html

logger = logging.getLogger("main")


def cmd_collect():
    """采集文章列表"""
    logger.info("=" * 50)
    logger.info("步骤1: 采集文章列表")
    logger.info("=" * 50)

    articles = collect_article_list()

    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    logger.info(f"列表保存完成: {len(articles)} 篇 -> {config.ARTICLES_JSON}")
    return articles


def cmd_fetch(articles=None):
    """抓取文章正文"""
    logger.info("=" * 50)
    logger.info("步骤2: 抓取文章正文")
    logger.info("=" * 50)

    if articles is None:
        articles = load_articles()
    if not articles:
        logger.error("无文章数据，请先运行 collect")
        return []

    results = fetch_all_articles(articles, progress_file=config.PROGRESS_JSON)

    has_content = sum(1 for r in results if r.get("content"))
    logger.info(f"正文抓取完成: {has_content}/{len(results)} 篇有正文")

    return results


def cmd_analyze(articles=None):
    """AI分析文章"""
    logger.info("=" * 50)
    logger.info("步骤3: AI分析文章")
    logger.info("=" * 50)

    if not config.AI_API_KEY:
        logger.error("AI_API_KEY 未配置！请编辑 config.py 填入你的 Mimo API Key")
        logger.error("或设置环境变量: MIMO_API_KEY=your_key_here")
        return []

    if articles is None:
        articles = load_articles()
    if not articles:
        logger.error("无文章数据，请先运行 fetch")
        return []

    articles_with_content = [a for a in articles if a.get("content")]
    logger.info(f"待分析: {len(articles_with_content)} 篇（跳过 {len(articles)-len(articles_with_content)} 篇无正文）")

    summaries = analyze_batch(articles_with_content)

    failed = sum(1 for s in summaries if s.get("_failed"))
    logger.info(f"分析完成: {len(summaries)} 篇, 成功 {len(summaries)-failed} 篇, 失败 {failed} 篇")

    return summaries


def cmd_html(summaries=None):
    """生成HTML"""
    logger.info("=" * 50)
    logger.info("步骤4: 生成HTML页面")
    logger.info("=" * 50)

    if summaries is None:
        summaries = load_summaries()
    if not summaries:
        logger.error("无分析数据，请先运行 analyze")
        return []

    pages = generate_all(summaries)
    logger.info(f"HTML生成完成: {len(pages)} 个页面 -> {config.OUTPUT_DIR}")
    return pages


def cmd_run():
    """全流程执行"""
    articles = cmd_collect()
    articles = cmd_fetch(articles)
    summaries = cmd_analyze(articles)
    pages = cmd_html(summaries)
    return pages


def cmd_update():
    """增量更新：采集新文章 + 抓取 + 分析 + 生成HTML（断点续传，自动跳过已完成的）"""
    logger.info("=" * 50)
    logger.info("增量更新模式")
    logger.info("=" * 50)

    articles = cmd_collect()
    articles = cmd_fetch(articles)
    summaries = cmd_analyze(articles)
    pages = cmd_html(summaries)

    logger.info(f"增量更新完成! 共 {len(pages)} 个页面 -> {config.OUTPUT_DIR}")
    return pages


def cmd_mobile():
    """仅生成单文件移动端HTML"""
    logger.info("=" * 50)
    logger.info("生成单文件移动端HTML")
    logger.info("=" * 50)

    summaries = load_summaries()
    if not summaries:
        logger.error("无分析数据，请先运行 analyze")
        return None

    output_file = generate_mobile_html(summaries)
    logger.info(f"单文件版生成完成: {output_file}")
    return output_file


def cmd_test(n=10):
    """测试模式：取前N篇运行全流程"""
    logger.info("=" * 50)
    logger.info(f"测试模式: 采集列表 -> 取前{n}篇 -> 全流程")
    logger.info("=" * 50)

    all_articles = cmd_collect()
    if not all_articles:
        logger.error("采集失败")
        return

    test_articles = all_articles[:n]
    logger.info(f"测试选取前 {len(test_articles)} 篇:")
    for i, a in enumerate(test_articles):
        logger.info(f"  {i+1}. [{a.get('category','')}] {a.get('title','')[:50]} ({a.get('date','')})")

    articles = cmd_fetch(test_articles)

    if config.AI_API_KEY:
        summaries = cmd_analyze(articles)
        pages = cmd_html(summaries)
        logger.info(f"测试完成! 请打开 {config.OUTPUT_DIR}/page_1.html 查看结果")
    else:
        logger.warning("AI_API_KEY 未配置，跳过AI分析和HTML生成")
        logger.info(f"正文已抓取保存到 {config.ARTICLES_JSON}")
        logger.info("请在 config.py 中配置 API Key 后运行: python main.py analyze && python main.py html")


def cmd_status():
    """查看当前进度"""
    print(f"配置信息:")
    print(f"  日期范围: {config.DATE_START} ~ {config.DATE_END}")
    print(f"  AI API Key: {'已配置' if config.AI_API_KEY else '未配置'}")
    print(f"  AI Base URL: {config.AI_BASE_URL}")
    print(f"  AI Model: {config.AI_MODEL}")
    print()

    articles = load_articles()
    if articles:
        dates = [a.get("date", "") for a in articles if a.get("date")]
        cats = {}
        for a in articles:
            c = a.get("category", "未知")
            cats[c] = cats.get(c, 0) + 1
        has_content = sum(1 for a in articles if a.get("content"))
        print(f"文章列表: {len(articles)} 篇")
        print(f"  有正文: {has_content} 篇")
        if dates:
            print(f"  日期范围: {min(dates)} ~ {max(dates)}")
        print(f"  栏目分布:")
        for c, cnt in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"    {c}: {cnt} 篇")
    else:
        print("文章列表: 无数据")

    print()
    summaries = load_summaries()
    if summaries:
        failed = sum(1 for s in summaries if s.get("_failed"))
        print(f"AI分析: {len(summaries)} 篇 (成功 {len(summaries)-failed}, 失败 {failed})")
    else:
        print("AI分析: 无数据")

    print()
    if os.path.exists(config.OUTPUT_DIR):
        html_files = [f for f in os.listdir(config.OUTPUT_DIR) if f.endswith(".html")]
        print(f"HTML输出: {len(html_files)} 个文件")
    else:
        print("HTML输出: 无")


def main():
    setup_logging()

    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == "collect":
        cmd_collect()
    elif cmd == "fetch":
        cmd_fetch()
    elif cmd == "analyze":
        cmd_analyze()
    elif cmd == "html":
        cmd_html()
    elif cmd == "run":
        cmd_run()
    elif cmd == "update":
        cmd_update()
    elif cmd == "mobile":
        cmd_mobile()
    elif cmd == "test":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        cmd_test(n)
    elif cmd == "status":
        cmd_status()
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()

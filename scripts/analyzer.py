"""AI分析模块 - 调用Mimo API(Anthropic协议)提取文章结构化总结"""

import json
import logging
import os
import re
import time

from scripts import config

logger = logging.getLogger("analyzer")

SYSTEM_PROMPT = """你是一位专业的公考面试备考助手。你需要分析人民网评论文章，提取结构化内容帮助考生备考面试。

请严格按照JSON格式输出，不要包含任何其他文字：

{
  "brief": "文章简介：用2-3句话概述文章讲了什么事/什么现象，交代背景和事件（如有）",
  "essence": "本质：透过现象看本质，这篇文章讨论的核心社会问题或深层矛盾是什么（一句话概括）",
  "impact_positive": "有利影响：如有积极影响，必须分主体阐述（如：【政府层面】...；【社会层面】...；【群众层面】...）。每个主体下的影响必须具体，有解释或举例。如果没有积极影响则留空字符串",
  "impact_negative": "不利影响：必须分主体阐述（如：【政府公信力】...；【生态环境】...；【群众利益】...）。每个主体下的影响必须具体，避免空泛概括，要有具体说明。如果没有不利影响则留空字符串",
  "cause_analysis": "原因分析：必须分主体或分层次阐述（如：【制度层面】...；【思想层面】...；【执行层面】...）。每条原因要有具体解释，不能只是几个词的堆砌",
  "measures": "措施/对策：必须分主体阐述（如：【政府/监管部门】...；【社会/媒体】...；【个人/企业】...）。每条措施必须具体可操作，附带简短解释，禁止出现"完善机制""加强监管"等空泛表述，要说清楚完善什么机制、怎么监管",
  "key_quotes": ["金句1：文中最有力量或最精炼的原话，适合面试直接引用", "金句2", "金句3"],
  "summary": "一段话总结（100字以内，适合面试答题时直接引用）"
}

重要要求：
1. brief 字段是必须的，用来简要介绍文章背景和事件
2. 影响、原因、措施都要分主体/层面，用【】标注
3. 每条内容必须具体，有解释或举例，不能是几个词的堆砌
4. key_quotes 提取2-4句文章原话，保持原文表述
5. 所有内容用中文输出"""


def _get_client():
    try:
        import anthropic
        return anthropic.Anthropic(
            api_key=config.AI_API_KEY,
            base_url=config.AI_BASE_URL,
        )
    except ImportError:
        logger.error("anthropic SDK 未安装，请运行: pip install anthropic")
        raise


def analyze_article(article):
    """分析单篇文章，返回结构化总结"""
    client = _get_client()

    title = article.get("title", "")
    content = article.get("content", "")
    if not content:
        logger.warning(f"文章无正文内容，跳过: {title}")
        return None

    # 限制正文长度，避免token过多
    max_content_len = 6000
    if len(content) > max_content_len:
        content = content[:max_content_len] + "...(截断)"

    user_msg = f"标题：{title}\n\n正文：\n{content}"

    try:
        response = client.messages.create(
            model=config.AI_MODEL,
            max_tokens=config.AI_MAX_TOKENS,
            temperature=config.AI_TEMPERATURE,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        result_text = response.content[0].text.strip()

        # 提取JSON（可能被包裹在 ```json ``` 中）
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            logger.error(f"AI返回非JSON格式: {result_text[:200]}")
            return None

        # 合并原始文章信息
        return {
            "title": title,
            "date": article.get("date", ""),
            "category": article.get("category", ""),
            "url": article.get("url", ""),
            "source": article.get("source", ""),
            **result,
        }

    except Exception as e:
        logger.error(f"AI分析失败 [{title[:30]}]: {e}")
        return None


def analyze_batch(articles, batch_size=None):
    """批量分析文章"""
    if batch_size is None:
        batch_size = config.ANALYZER_BATCH_SIZE

    # 加载已有结果（断点续传）
    existing_summaries = {}
    if os.path.exists(config.SUMMARIES_JSON):
        with open(config.SUMMARIES_JSON, "r", encoding="utf-8") as f:
            for s in json.load(f):
                existing_summaries[s["url"]] = s

    results = list(existing_summaries.values())
    pending = [a for a in articles if a["url"] not in existing_summaries]
    total = len(pending)

    if not pending:
        logger.info("所有文章均已分析，无需重复处理")
        return results

    logger.info(f"待分析: {total} 篇, 已完成: {len(existing_summaries)} 篇")

    for i, article in enumerate(pending):
        title = article.get("title", "")
        logger.info(f"分析 [{i+1}/{total}]: {title[:40]}")

        summary = analyze_article(article)
        if summary:
            results.append(summary)
            logger.info(f"  分析完成: essence={summary.get('essence', '')[:50]}")
        else:
            # 保存基本信息，分析失败的留占位
            results.append({
                "title": title,
                "date": article.get("date", ""),
                "category": article.get("category", ""),
                "url": article.get("url", ""),
                "brief": "",
                "essence": "（分析失败，请重试）",
                "impact_positive": "",
                "impact_negative": "",
                "cause_analysis": "",
                "measures": "",
                "key_quotes": [],
                "summary": "",
                "_failed": True,
            })

        # 定期保存
        if (i + 1) % batch_size == 0:
            _save_summaries(results)
            logger.info(f"  进度保存: {i+1}/{total}")

        time.sleep(0.5)  # API请求间隔

    _save_summaries(results)
    return results


def _save_summaries(results):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(config.SUMMARIES_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def load_summaries():
    if os.path.exists(config.SUMMARIES_JSON):
        with open(config.SUMMARIES_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

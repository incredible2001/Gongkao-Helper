"""配置文件 - 人民网观点频道文章自动总结

所有敏感配置通过环境变量读取，支持 .env 文件：
  1. 复制 .env.example 为 .env
  2. 在 .env 中填入真实的 API Key
"""

import os

# 自动加载 .env 文件（无需额外依赖）
_env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_file):
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import os

# ============ AI API 配置 ============
AI_API_KEY = os.environ.get("MIMO_API_KEY", "")  # 必填，通过环境变量或 .env 文件设置
AI_BASE_URL = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/anthropic")
AI_MODEL = os.environ.get("MIMO_MODEL", "mimo-v2.5-pro")
AI_MAX_TOKENS = 4096
AI_TEMPERATURE = 0.3

# ============ 爬虫配置 ============
REQUEST_TIMEOUT = 15  # 请求超时秒数
REQUEST_DELAY = 1.0  # 请求间隔秒数，避免过快
MAX_RETRIES = 3  # 最大重试次数
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# ============ 采集栏目配置 ============
# name: 栏目名称, url: 列表页首页地址, max_pages: 最大翻页数
CATEGORIES = [
    {"name": "人民锐评", "url": "http://opinion.people.com.cn/GB/436867/index.html", "max_pages": 15},
    {"name": "壹时评", "url": "http://opinion.people.com.cn/GB/223228/index.html", "max_pages": 20},
    {"name": "人民时评", "url": "http://opinion.people.com.cn/GB/8213/49160/49219/index.html", "max_pages": 15},
    {"name": "今日谈", "url": "http://opinion.people.com.cn/GB/8213/49160/49221/index.html", "max_pages": 15},
    {"name": "金台随笔", "url": "http://opinion.people.com.cn/GB/8213/49160/461967/index.html", "max_pages": 10},
    {"name": "暖闻热评", "url": "http://opinion.people.com.cn/GB/8213/49160/461973/index.html", "max_pages": 10},
    {"name": "人民论坛", "url": "http://opinion.people.com.cn/GB/8213/49160/49220/index.html", "max_pages": 15},
]

# ============ 路径配置 ============
# 项目根目录（scripts/ 的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_DIR = os.path.join(BASE_DIR, "logs")

ARTICLES_JSON = os.path.join(DATA_DIR, "articles.json")
SUMMARIES_JSON = os.path.join(DATA_DIR, "summaries.json")
PROGRESS_JSON = os.path.join(DATA_DIR, "progress.json")
LOG_FILE = os.path.join(LOG_DIR, "scraper.log")

# ============ 批处理配置 ============
SCRAPER_BATCH_SIZE = 50  # 爬虫每批抓取文章数
ANALYZER_BATCH_SIZE = 10  # AI分析每批文章数
HTML_BATCH_SIZE = 50  # 每个HTML文件包含文章数

# ============ 日期范围 ============
# 近一年的起始日期（运行时动态计算，也可手动指定）
from datetime import datetime, timedelta
DATE_START = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
DATE_END = datetime.now().strftime("%Y-%m-%d")

"""人民网观点频道文章自动总结 - 入口脚本

用法:
  python main.py collect          # 仅采集文章列表
  python main.py fetch            # 仅抓取文章正文
  python main.py analyze          # 仅AI分析
  python main.py html             # 仅生成HTML
  python main.py run              # 执行全流程
  python main.py update           # 增量更新
  python main.py mobile           # 生成按周分页HTML
  python main.py test [N]         # 测试模式
  python main.py status           # 查看当前进度
"""
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.main import main

if __name__ == "__main__":
    main()

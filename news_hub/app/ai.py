"""AI 摘要模块：调用 DeepSeek 把当天新闻总结成日报"""
import os
from openai import OpenAI

# 创建与 ai 大模型交互的客户端对象（只创建一次，反复使用）
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

# 新闻编辑角色 + 输出要求 + 防编造约束
SYSTEM_PROMPT = (
    "你是新闻编辑，根据提供的新闻写一份今日简报，"
    "按主题分组、每条一两句话，只依据提供的内容，不要编造。"
)


def summarize_today(news_items: list) -> str:
    """把新闻列表总结成日报，返回文本。

    news_items: 字典列表，每项至少含 title、content 两个键
    """
    if not news_items:
        return "今天还没有新闻。"

    # 拼装新闻数据：标题全保留，正文截断控制 token
    lines = []
    for i, item in enumerate(news_items, 1):
        content = (item.get('content') or '')[:500]   # 每条正文只取前 500 字
        lines.append(f"{i}. {item['title']}\n{content}")
    news_text = "\n\n".join(lines)

    response = client.chat.completions.create(
        model="deepseek-v4-flash",      # 模型名以你账号实际开通的为准
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"以下是今天的新闻：\n\n{news_text}\n\n请根据以上内容生成今日新闻简报。"},
        ],
        stream=False,
    )
    return response.choices[0].message.content


# 直接运行本文件时用假数据测试（python ai.py）
if __name__ == "__main__":
    fake_news = [
        {"title": "测试新闻一：苹果发布新系统", "content": "苹果今日正式推送了新一代操作系统，修复了多个问题。"},
        {"title": "测试新闻二：某公司发布新品", "content": "该公司今日召开发布会，展示了多款硬件产品。"},
    ]
    print(summarize_today(fake_news))
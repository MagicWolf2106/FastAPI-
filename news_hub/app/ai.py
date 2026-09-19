"""AI 摘要模块：调用 DeepSeek 把当天新闻总结成日报"""
import os
from openai import OpenAI

# 创建与 ai 大模型交互的客户端对象（只创建一次，反复使用）
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

SYSTEM_PROMPT = (
    "你是新闻编辑，根据提供的新闻写一份今日简报，"
    "按主题分组、每条一两句话，只依据提供的内容，不要编造。"
)


def summarize_today(news_items: list) -> str:
    """把新闻列表总结成日报，返回str文本。
    news_items: 字典列表，每项至少含 title、content 两个键
    """
    # print(news_items)
    # 将db返回的列表转换为字符串喂给ai
    news = '\n'.join(f"标题：{item['title']}，内容：{item['content']}" for item in news_items[:10])
    response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
          {"role": "system", "content": SYSTEM_PROMPT},
          {"role": "user", "content": news}   # db里单独一个函数截取内容后返回
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
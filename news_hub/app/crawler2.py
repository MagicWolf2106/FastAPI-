import time
import requests
from lxml import html
from datetime import datetime

# ===== 配置 =====
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}
LIST_URL = "https://it.ithome.com/"
API_URL = "https://it.ithome.com/category/domainpage?domain=it&subdomain=&ot={ot}"
MAX_COUNT = 10              # 默认最多抓多少条新闻


def ot_to_ms(data_ot: str) -> int:
    """把 data-ot 时间字符串转成毫秒时间戳，等价于 JS 的 new Date(...).getTime()"""
    return int(datetime.fromisoformat(data_ot).timestamp() * 1000)


def parse_li(li):
    """从单个 <li> 节点提取：标题、链接、data-ot（发布时间）"""
    title = li.xpath('.//h2/a/text()')[0].strip()
    href = li.xpath('.//h2/a/@href')[0]
    ot = li.xpath('./div/@data-ot')[0]
    return title, href, ot


def run(max_count: int = MAX_COUNT):
    """运行爬虫，返回 (标题列表, 发布时间列表, 正文列表)，三个列表一一对应。"""

    # ── 第一步：抓列表页，拿初始条目 + 游标 ──
    resp = requests.get(LIST_URL, headers=HEADERS)
    doc = html.fromstring(resp.text)
    li_list = doc.xpath('//*[@id="list"]//ul[@class="bl"]/li')

    news_titles = []
    news_hrefs = []
    news_ots = []
    seen_hrefs = set()      # 用于去重（初始列表里的旧文章可能在接口批次里再次出现）

    for li in li_list:
        title, href, ot = parse_li(li)
        news_titles.append(title)
        news_hrefs.append(href)
        news_ots.append(ot)
        seen_hrefs.add(href)

    # JS: $('#list .bl .c').last().data('ot') → 列表最后一条的发布时间作为翻页游标
    last_ot = li_list[-1].xpath('./div/@data-ot')[0]
    print(f"初始条目：{len(news_titles)} 条")

    # ── 第二步：循环"加载更多"（复刻 JS 的游标翻页）──
    while True:
        resp = requests.post(API_URL.format(ot=ot_to_ms(last_ot)), headers=HEADERS)
        data = resp.json()

        # JS: count === 0 时隐藏按钮 → 这里直接结束
        if not data["success"] or data["content"]["count"] == 0:
            print("没有更多了")
            break

        frag = html.fromstring(data["content"]["html"])
        batch = frag.xpath('//li')
        for li in batch:
            title, href, ot = parse_li(li)
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            news_titles.append(title)
            news_hrefs.append(href)
            news_ots.append(ot)

        # JS 追加后最后一条变了 → 游标推进到新批次的最后一条
        last_ot = batch[-1].xpath('./div/@data-ot')[0]
        print(f"已累计 {len(news_titles)} 条")
        if len(news_titles) >= max_count:      # 够数了就不再翻页
            break
        time.sleep(1)

    # 只保留前 max_count 条
    news_titles = news_titles[:max_count]
    news_hrefs = news_hrefs[:max_count]
    news_ots = news_ots[:max_count]

    # ── 第三步：进详情页抓正文 ──
    news_content = []

    for href in news_hrefs:
        news = requests.get(href, headers=HEADERS)
        content = html.fromstring(news.text)

        containers = content.xpath('//*[@id="paragraph"]')
        if not containers:                      # 个别页面结构不同，跳过防崩
            print(f"未找到正文容器：{href}")
            news_content.append("")
            continue

        container = containers[0]
        # 过滤掉居中的段落（图片），取所有 p 的纯文本（含嵌套标签文字）
        p_list = container.xpath('.//p[not(contains(@style, "text-align: center"))]')
        p_content = [p.text_content().strip() for p in p_list]
        news_content.append("\n".join(t for t in p_content if t))

        time.sleep(1)   # 详情页逐个请求，限速避免被封

    # 发布时间：直接用列表页的 data-ot（ISO 格式）转成 datetime
    news_times = [datetime.fromisoformat(ot) for ot in news_ots]

    return news_titles, news_times, news_content


# 直接运行本文件时，预览抓取结果（python "crawler2.py"）
if __name__ == "__main__":
    titles, times, contents = run()
    for t, tm, c in zip(titles, times, contents):
        print(t, "|", tm)
        print(c)
        print("=" * 100)
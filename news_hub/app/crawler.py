import requests
from lxml import html

url = "https://maomu.com/news"
result = requests.get(url)
document = html.fromstring(result.text)

# print(result.text)  # 源码

news_titles = []; news_hrefs = []; news_contents = []

for i in range (1,11):
    news_title = document.xpath(f'//*[@id="__nuxt"]/section/main/div/div[2]/div/div/div[1]/div/ul[1]/li[{i}]/div[3]/div/div[1]/a/h3/text()')
    news_href = document.xpath(f'//*[@id="__nuxt"]/section/main/div/div[2]/div/div/div[1]/div/ul[1]/li[{i}]/div[3]/div/div[1]/a/@href')
    news_titles.append(news_title[0])
    news_hrefs.append(news_href[0])
    # news_content = requests.get(news_href[i])   # 访问每一条新闻

    # print(i, news_title, news_href)
# print(news_titles)
# print(news_hrefs)

for i in news_hrefs:
    news = requests.get(i)
    content = html.fromstring(news.text)
    container = content.xpath("//div[contains(@class, 'articleContent')]")
    print(container)
    # p_list = container.xpath('.//p')   # 有 . → 只在容器内部找所有 p
    # print(p_list[i])



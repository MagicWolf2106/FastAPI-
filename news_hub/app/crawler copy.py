import requests
from lxml import html


url = "https://it.ithome.com/"
result = requests.get(url)
document = html.fromstring(result.text)
# document = html.fromstring(html_fragment)

# print(result.text)  # 源码

news_titles = []; news_hrefs = []; 

for i in range (1,11):
    news_title = document.xpath(f'//*[@id="list"]/div[1]/ul/li[{i}]/div/h2/a/text()')
    print(news_title)
    news_href = document.xpath(f'//*[@id="list"]/div[1]/ul/li[{i}]/div/h2/a/@href')
    news_titles.append(news_title[0])
    news_hrefs.append(news_href[0])

news_content = [];     # 列表里的每一项就是一篇文章
# time_content = []

for i in news_hrefs:
    p_content = []  # 其中每一项就是文章的一个段落
    news = requests.get(i)
    content = html.fromstring(news.text)
    container = content.xpath('//*[@id="paragraph"]')[0]   # 获取p标签外的容器
    p_list = container.xpath('.//p[not(contains(@style, "text-align: center"))]')   # 过滤不含有。。。的
    news_time = container.xpath('//*[@id="pubtime_baidu"]/text()')
    # time_content.append(news_time)
    for p in p_list:
        p_content.append(p.text_content())  # 获取p标签里的文字，包括嵌套的标签文字
    str_content = "\n".join(p_content)  # 将段落拼接
    news_content.append(str_content)

for i in news_content:
    print(i, end='\n')
    print('='*100)
# for i in time_content:
#     print(i, end='\n')
#     print('='*100)

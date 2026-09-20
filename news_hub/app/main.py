from contextlib import asynccontextmanager
import re
from datetime import datetime
from fastapi import FastAPI, Query, Depends, HTTPException
from pydantic import BaseModel, Field

from init_db import init_db
import crawler2
import db
import ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时最开始运行：建库建表
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "hello"}


# 手动添加新闻（测试）
class News(BaseModel):
    title: str = Field(default='标题', min_length=1)
    content: str = Field(default='文章', min_length=1)


@app.post("/add_news", description="手动添加新闻（测试）")
def add_news(news: News, conn=Depends(db.get_db)):
    new_id = db.add_news(conn, news.title, news.content)
    return {"id": new_id, "message": "添加成功"}


# 获取新闻（分页展示，?page= 参数）
@app.get("/get_news", description="获取新闻（分页展示）")
def get_news(page: int = Query(1, ge=1, description='第几页'),
             conn=Depends(db.get_db)):
    return {"page": page, "items": db.get_news(conn, page)}

# 收藏新闻
@app.post("/add_favor_news", description='收藏新闻')
def add_favor_news(id: int, conn=Depends(db.get_db)):
    db.add_favor_news(conn, id)
    return {"message": "收藏成功"}

# 获取收藏的新闻
@app.get("/get_favor_news", description="获取收藏的新闻")
def get_favor_news(page: int=1,
                   conn=Depends(db.get_db)):
    return {"page:": page, "item": db.get_favor_news(conn, page)}

# 删除新闻
@app.delete('/del_news', description='删除新闻')
def del_news(id: int, conn=Depends(db.get_db)):
    db.del_news(conn, id)
    return {"message": "删除成功"}

# 搜索新闻，按照标题匹配
@app.get("/search_news", description="搜索新闻，按照标题匹配")
def search_news(name='标题', page:int=1,
                conn=Depends(db.get_db)):
    return {"page:": page, "item": db.search_news(conn, name, page)}


# 通过爬虫自动添加：调用接口时才运行爬虫，抓完直接入库（标题重复的跳过）
@app.post("/auto_add_news", description="运行爬虫，把抓到的新闻入库")
def auto_add_news(conn=Depends(db.get_db)):
    news_titles, news_times, news_content = crawler2.run()
    for title, time, content in zip(news_titles, news_times, news_content):
        count = 0; rep = 0
        if db.title_exists(conn, title):
            rep += 1
            continue
        db.add_news(conn, title, content, time)
        count += 1
    return {"title": f"添加成功！已添加{count}条，扫描到重复{rep}条未添加"}


# 生成今日新闻日报：查库取当天新闻 → AI 总结 → 返回
@app.post("/daily_report", description="AI 总结今天的新闻，生成日报")
def daily_report(conn=Depends(db.get_db)):
    news_items = db.get_today_news(conn)
    summary = ai.summarize_today(news_items)
    db.ai_report(conn, summary)   # 提交到数据库另一个表
    return {"summary": summary}


# ===== ai_report 摘要表：增删查（复用通用 API）=====
c = db.ai_report_crud   # 简短别名


@app.post("/report_add", description="手动新增一条 AI 摘要（测试用）")
def report_add(content: str = Query(..., description='摘要正文'), conn=Depends(db.get_db)):
    new_id = c['insert'](conn, content=content, time=datetime.now())
    return {"id": new_id, "message": "添加成功"}


@app.get("/report_list", description="分页查询 AI 摘要")
def report_list(page: int = Query(1, ge=1), conn=Depends(db.get_db)):
    return {"page": page, "items": c['page'](conn, page)}


@app.get("/report_search", description="按内容模糊搜索 AI 摘要")
def report_search(name: str = Query(..., description='关键词'), page: int = 1,
                  conn=Depends(db.get_db)):
    return {"page": page, "items": db.ai_report_crud['search'](conn, "content", name, page)}


@app.delete("/report_del", description="按 id 删除 AI 摘要")
def report_del(id: int, conn=Depends(db.get_db)):
    if not db.ai_report_crud['exists'](conn, id):
        raise HTTPException(status_code=404, detail="该摘要不存在")
    db.ai_report_crud['delete'](conn, id)
    return {"message": "删除成功"}

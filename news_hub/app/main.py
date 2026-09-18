from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Depends
from pydantic import BaseModel, Field

from init_db import init_db
import crawler2
import db


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

# 通过爬虫自动添加：调用接口时才运行爬虫，抓完直接入库
@app.post("/auto_add_news", description="运行爬虫，把抓到的新闻入库")
def auto_add_news(conn=Depends(db.get_db)):
    titles, times, contents = crawler2.run()      # 爬虫在这里才真正运行
    count = 0
    for t, tm, c in zip(titles, times, contents):
        db.add_news(conn, t, c, tm)               # 逐条入库
        count += 1
    return {"count": count, "message": "爬取并入库完成"}


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

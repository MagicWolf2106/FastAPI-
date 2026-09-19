import pymysql
from datetime import datetime

# ===== 数据库连接配置（init_db.py 也复用这里）=====
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'hjj060302'
DB_NAME = 'fastAPI_News'
 

def get_db():
    """通过 yield 依赖注入，把连接交给接口用，用完自动关。"""
    conn = pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASSWORD,
                           database=DB_NAME,
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        yield conn
    finally:
        conn.close()


def add_news(conn, title: str, content: str, news_time=None):
    """添加一条新闻，返回新记录 id。news_time 是文章发布时间，不传则用当前时间。"""
    if news_time is None:
        news_time = datetime.now()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO news (title, content, news_time) VALUES (%s, %s, %s)",
        (title, content, news_time),
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    return new_id


def get_news(conn, page: int = 1, size: int = 10):
    """分页查询新闻，返回当前页数据。"""
    offset = (page - 1) * size
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content, news_time FROM news ORDER BY id DESC LIMIT %s OFFSET %s",
        (size, offset),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows

def get_today_news(conn):
    """获取今天的新闻（按文章发布时间过滤）"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content, news_time FROM news "
        "WHERE DATE(news_time) = CURDATE() ORDER BY id DESC",
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def del_news(conn, id: int):
    '''删除新闻，根据id'''
    cursor = conn.cursor()
    # news_name = cursor.execute("SELECT TITLE FROM {DB_NAME} WHERE id = %s", (id))
    cursor.execute(f"delete from news WHERE id = %s", (id))
    conn.commit()
    cursor.close()
    return 

    # 需要添加没有找到的逻辑

def add_favor_news(conn, id: int):
    '''收藏新闻'''
    cursor = conn.cursor()
    cursor.execute("UPDATE news SET is_favorite = 1 WHERE id = %s",
                   (id))
    conn.commit()
    cursor.close()
    return 

def get_favor_news(conn, page: int=1, size:int=10):
    '''获取收藏的新闻，分页查询'''
    offset = (page - 1) * size # 查询的起始索引
    cursor = conn.cursor()
    # 先只按照时间降序，后续完善
    cursor.execute("select id, title, content from news where is_favorite = 1 order by id desc limit %s, %s", 
                   (offset, size))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def search_news(conn, name:str, page: int=1, size: int=10):
    '''根据关键字搜索新闻'''
    offset = (page - 1) * size # 查询的起始索引
    cursor = conn.cursor()
    like = f"%{name}%"
    # 先只按照时间降序，后续完善
    cursor.execute("select id, title, content from news where title like %s order by id desc limit %s,%s  ",
                   (like, offset, size))
    rows = cursor.fetchall()
    cursor.close()
    return rows
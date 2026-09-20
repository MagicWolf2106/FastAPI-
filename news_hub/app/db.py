import pymysql
from datetime import date, datetime

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
        "SELECT id, title, content, news_time FROM news ORDER BY news_time DESC LIMIT %s OFFSET %s",
        (size, offset),
    )   # 按照时间倒序，最新的在最前面
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


def title_exists(conn, title: str) -> bool:
    """检查标题是否已入库（用于爬虫入库前去重）"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM news WHERE title = %s LIMIT 1", (title,))
    row = cursor.fetchone()
    cursor.close()
    return row is not None  # 空返回true（没有重复），非空false（有重复的）


def get_today_news(conn):
    """让ai获取今天的新闻（按文章发布时间过滤）"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, LEFT(content, 300) AS content, news_time FROM news "
        "WHERE DATE(news_time) = CURDATE() ORDER BY id DESC",
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows

def ai_report(conn, summary):
    '''将ai生成的报告提交到数据库'''
    cursor = conn.cursor()
    cur_time = datetime.now()
    cursor.execute("insert into ai_report(time, content) values (%s, %s)",
                   (cur_time, summary))
    conn.commit()
    cursor.close()



# ===== 通用 CRUD 工厂：给定表名即可生成增删查（news / ai_report 都可用）=====
def table_crud(table: str, default_cols: str = "*"):
    """生成一套针对某张表的通用操作函数，返回 dict。
    table: 表名
    default_cols: 查询时默认取的列，如 "id, content, time"
    """
    def insert(conn, **values):
        """插入一条记录，返回新 id。如 insert(conn, content='xxx', time=now)"""
        cols = ", ".join(values.keys())
        ph = ", ".join(["%s"] * len(values))
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO {table} ({cols}) VALUES ({ph})",
            tuple(values.values()),
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id

    def page(conn, page: int = 1, size: int = 10, where=None, params=()):
        """分页查询。where 传入拼接条件（可选），如 'content like %s'"""
        offset = (page - 1) * size
        cond = f" WHERE {where}" if where else ""
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {default_cols} FROM {table}{cond} "
            f"ORDER BY id DESC LIMIT %s OFFSET %s",
            (*params, size, offset),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def search(conn, col, keyword: str, page: int = 1, size: int = 10):
        """按某列模糊搜索（sql 里的列名是可信配置，不拼用户输入）"""
        like = f"%{keyword}%"
        offset = (page - 1) * size
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {default_cols} FROM {table} WHERE {col} LIKE %s "
            f"ORDER BY id DESC LIMIT %s OFFSET %s",
            (like, size, offset),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def delete(conn, id: int):
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", (id,))
        conn.commit()
        cursor.close()

    def exists(conn, id: int) -> bool:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {table} WHERE id = %s LIMIT 1", (id,))
        row = cursor.fetchone()
        cursor.close()
        return row is not None

    return {"insert": insert, "page": page, "search": search,
            "delete": delete, "exists": exists}


# 为 ai_report 表直接生成一套通用操作，后续 main 里 import 用
ai_report_crud = table_crud("ai_report", "id, content, time")
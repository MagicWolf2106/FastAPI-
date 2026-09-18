"""数据库初始化文件（main.py 启动时最先生成）。

负责：
1. 若库不存在则创建（连到 MySQL 服务器，先不指定库）
2. 若 news 表不存在则建表

全部用 IF NOT EXISTS，多次运行安全。
"""
import pymysql

# 从 db.py 复用连接配置，避免两处重复写密码
from db import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# ===== 建表（仅标题/正文/日期 + 主键）=====
CREATE_NEWS_SQL = """
CREATE TABLE IF NOT EXISTS news (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    title      VARCHAR(255) NOT NULL,
    content    LONGTEXT,
    news_time  DATETIME,
    is_favorite int(1) not null default 0 comment '是否收藏'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def init_db():
    """建库建表。"""
    conn = pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASSWORD)
    # try:
    #     cursor = conn.cursor()
    #     cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4")
    #     cursor.execute(f"USE `{DB_NAME}`")
    #     cursor.execute(CREATE_NEWS_SQL)
    #     conn.commit()
    #     cursor.close()
    # finally:
    #     conn.close()

    try:
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` ")   # 尝试自己写一遍
        cursor.execute(f"USE `{DB_NAME}`")
        cursor.execute(CREATE_NEWS_SQL)
        conn.commit()
        cursor.close()

    finally:
        conn.close()
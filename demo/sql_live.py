from biliLive import BiliApi, CommandList
import sqlite3

"""
自定义 Command 实现弹幕于数据库通信
"""

# 继承创建指令对像
class MyCommandList(CommandList):

    def __init__(self):
        super().__init__()
        # 绑定方法 read
        self.command = {
            "read": self.read,
            # 绑定方法 write
            "write": self.write
        }

        # 定时发送
        self.timeLoopList = {
            12: "12s sendMsg"
        }

        self.sql = None
    

    def connect(self):
        if self.sql is None:
            # 连接db文件
            self.sql = sqlite3.connect("command.db")
            try:
                # 检测save_connect表是否存在 不存在创建
                sql_command = """CREATE TABLE save_connect (
                        cot      INT       PRIMARY KEY,
                        userName TEXT (20) NOT NULL,
                        userId   INT       NOT NULL,
                        msg      TEXT      NOT NULL
                );"""
                self.sql.execute(sql_command)
                self.sql.commit()
            except sqlite3.OperationalError:
                pass
    
    def read(self, commKey, msg):
        self.connect()
        sql_command = "select * FROM save_connect"
        # 执行sql语句
        data = self.sql.execute(sql_command)
        print(data.fetchall())

    def write(self, commKey, msg):
        self.connect()
        # 向数据库写入当前使用 /write 指令用户的数据
        name, id, msg = msg["userName"], str(msg["userId"]), msg["msg"]
        sql_command = f"INSERT INTO save_connect (userName,userId,msg) VALUES ('{name}',{id},'{msg}');"
        # 执行sql语句
        self.sql.execute(sql_command)
        self.sql.commit()

    def commandError(self):
        return super().commandError()
    
    def commandNameError(self):
        return super().commandNameError()

    def purviewError(self):
        return super().purviewError()


# 实列化
headers = BiliApi.bilibili_headers
headers["cookie"] += open("cookie.txt", "r").read()
api = BiliApi(headers)

live = api.live("5545364")
live.bind(MyCommandList())

# 开启弹幕轮查
live.msg_loop()
# 开启定时发送
live.send_msg_loop()
# 堵塞主线程
input("")
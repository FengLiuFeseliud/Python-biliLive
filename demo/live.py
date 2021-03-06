import sys
from biliLive import BiliApi, commandList, liveLog

"""
设置弹幕机
"""

# 一行设置输出统一格式 并将输出内容保存进文件
liveLog()

headers = BiliApi.bilibili_headers
headers["cookie"] += open("cookie.txt", "r").read()
api = BiliApi(headers)

MyCommandList = commandList()

# 指令方法 /text
def text(commKey, msg):
    print(f"打印字符串 -> {commKey[0]}")

# 绑定方法 /text
MyCommandList.command = {
    "text": text
}

# 定时发送
MyCommandList.timeLoopList = {
    12: "12s sendMsg"
}

live = api.live("5545364")
live.bind(MyCommandList)

# 开启弹幕轮查
live.msg_loop()
# 开启定时发送
live.time_loop()
# 堵塞主线程
input("")
from biliLive import BiliApi, CommandList

"""
设置弹幕机
"""

headers = BiliApi.bilibili_headers
headers["cookie"] += open("cookie.txt", "r").read()
api = BiliApi(headers)

live = api.live("5545364")
commandList = CommandList(live)

# 指令方法 /text
def text(commKey, msg):
    print(f"打印字符串 -> {commKey[0]}")

# 绑定方法 /text
commandList.command = {
    "text": text
}

# 定时发送
sendMsgList = {
    12: "12s sendMsg"
}

# 开启弹幕轮查
live.msg_loop(commandList)
# 开启定时发送
live.send_msg_loop(sendMsgList)
# 堵塞主线程
input("")
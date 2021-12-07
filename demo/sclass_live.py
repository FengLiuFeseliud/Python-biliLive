import time
from biliLive import BiliApi, Command, Live

"""
继承设置弹幕机
"""

# 继承创建Live
class MyLive(Live):

    def __init__(self, headers, liveData):
        super().__init__(headers, liveData)
        self.sleep = 3

    def set_command_list(self, msg):
        """
        实现 set_command_list 并使用#号分割
        """
        print(super().set_command_list(msg))
        return super().set_command_list(msg)
        
    def msg_log(self, msg):
        """
        实现 msg_log
        """
        print("要调用父类Live打印新弹幕了!!!")
        return super().msg_log(msg)
    
    def command_log(self, code, msg, comm):
        return super().command_log(code, msg, comm)
    
    def set_time(self, msg_time):
        """
        实现 set_time 并统一时间格式 "%H:%M:%S"
        """
        if type(msg_time) == float:
            msg_time = time.strftime("%H:%M:%S", time.localtime(msg_time)) 
            return msg_time

        time_float = time.mktime(time.strptime(msg_time ,"%Y-%m-%d %H:%M:%S"))
        return time.strftime("%H:%M:%S", time.localtime(time_float)) 
    
    def send_msg_loop(self, sendMsgList):
        """
        实现 send_msg_loop
        """
        print("要调用父类Live开启定时发送了!!!")
        # 开启定时发送
        return super().send_msg_loop(sendMsgList)
    
    def msg_loop(self, commandList):
        """
        实现 msg_loop
        """
        print("要调用父类Live开启弹幕轮查了!!!")
        # 开启弹幕轮查
        return super().msg_loop(commandList)
    
    def send_msg(self, msg):
        """
        实现 send_msg 并实现3s延迟发送
        """
        code =  super().send_msg(msg)
        if code != 0:
            print(f"send_msg 失败code:{code}")
        # 3s
        time.sleep(self.sleep)
        return code


# 继承创建指令对像
class MyCommandList(Command):

    def __init__(self, BiliLive):
        super().__init__(BiliLive)
        # 绑定方法 /text
        self.command = {
            "text": self.text
        }

        # 设置指令标识符为 #
        self.commandSign = ""

    # 指令方法 text
    def text(self, commKey, msg):
        print(f"打印字符串 -> {commKey[0]}")

    def commandNameError(self):
        """
        实现 commandNameError
        """
        print("发生了commandNameError错误 要调用父类command 发送弹幕提醒了")
        # 发送自定义弹幕
        return self.api.send_msg("这是一个自定义NameError错误")
    
    def commandError(self):
        """
        实现 commandError
        """
        print("发生了commandError错误 要调用父类command 发送弹幕提醒了")
        # 发送弹幕
        return super().commandError()
    
    def purviewError(self):
        """
        实现 purviewError
        """
        print("发生了purviewError错误 要调用父类command 发送弹幕提醒了")
        # 发送弹幕
        return super().purviewError()


# 实列化
headers = BiliApi.bilibili_headers
headers["cookie"] += open("cookie.txt", "r").read()
api = BiliApi(headers)

live = MyLive(api.headers, api.getLiveRoom("5545364"))
commandList = MyCommandList(live)

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
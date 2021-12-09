import time
from biliLive import BiliApi, CommandList, Event

"""
继承设置弹幕机
"""

# 继承创建Event
class MyEvent(Event):

    def set_command_list(self, msg, commandSign):
        """
        实现 set_command_list 并使用#号分割
        """
        command_list = msg.strip(" ").split("#")[1:]
        commandSign = msg.strip(" ")[0]
        if len(command_list) != 0:
            comm = command_list[0].strip(commandSign)
        else:
            comm = ""
        commKey = command_list[1:]
        return commandSign, comm, commKey
        
    def msg_log(self, msg):
        """
        实现 msg_log
        """
        print("要调用父类Live打印新弹幕了!!!")
        return super().msg_log(msg)
    
    def set_time(self, msg_time):
        """
        实现 set_time 并统一时间格式 "%H:%M:%S"
        """
        if type(msg_time) == float:
            msg_time = time.strftime("%H:%M:%S", time.localtime(msg_time)) 
            return msg_time

        time_float = time.mktime(time.strptime(msg_time ,"%Y-%m-%d %H:%M:%S"))
        return time.strftime("%H:%M:%S", time.localtime(time_float)) 
    
    def send_msg_loop(self):
        """
        实现 send_msg_loop
        """
        print("要调用父类Live开启定时发送了!!!")
        # 开启定时发送
        return super().send_msg_loop()
    
    def msg_loop(self):
        """
        实现 msg_loop
        """
        print("要调用父类Live开启弹幕轮查了!!!")
        # 开启弹幕轮查
        return super().msg_loop()
    
    def send_msg(self, msg):
        """
        实现 send_msg 并实现3s延迟发送
        """
        code =  super().send_msg(msg)
        if code != 0:
            print(f"send_msg 失败code:{code}")
        # 3s
        time.sleep(3)
        return code
    
    def command_log(self, code, msg, comm):
        """
        事件 command_log 指令执行成功
        """
        return super().command_log(code, msg, comm)
    
    def command_err_log(self, code, msg, comm):
        """
        事件 command_err_log 指令执行失败
        """
        return super().command_err_log(code, msg, comm)


# 继承创建指令对像
class MyCommandList(CommandList):

    def __init__(self):
        super().__init__()
        # 绑定方法 /text
        self.command = {
            "text": self.text
        }

        # 定时发送
        self.timeLoopList = {
             12: "12s sendMsg"
        }

        # 设置指令标识符为 #
        self.commandSign = "#"

    # 指令方法 text
    def text(self, commKey, msg):
        print(f"打印字符串 -> {commKey[0]}")

    def commandNameError(self):
        """
        实现 commandNameError
        """
        print("发生了commandNameError错误 要调用父类command 发送弹幕提醒了")
        # 发送自定义弹幕
        return self.event.send_msg("这是一个自定义NameError错误")
    
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

live = api.live("5545364")
# 将 MyCommandList 绑定到live
live.bind(MyCommandList(), MyEvent())

# 开启弹幕轮查
live.msg_loop()
# 开启定时发送
live.send_msg_loop()
# 堵塞主线程
input("")
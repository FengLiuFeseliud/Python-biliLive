from abc import ABCMeta, abstractmethod
from biliLive.http_api import Link
import biliLive.bilibiliApi as bapi
from threading import Thread
import time


class User(Link, metaclass=ABCMeta):

    def __init__(self, headers, userData):
        super().__init__(headers)
        self.api = bapi.BiliApi(headers)
        # 用户id
        self.id = userData["mid"]
        # 用户
        self.name = userData["uname"]
        # 用户头像
        self.cover = userData["face"]
        # 用户等级
        self.level = userData["level"]["current_level"]
        # 用户经验
        self.exp = userData["level"]["current_exp"]
        # 用户下一级经验
        self.upExp = userData["level"]["next_exp"]

# 抽象直播间
class Live(Link, metaclass=ABCMeta):

    def __init__(self, headers, liveData):
        super().__init__(headers)
        self.api = bapi.BiliApi(headers)
        # 房间号
        self.id = liveData["room_id"]
        # 标题
        self.name = liveData["title"]
        # 标签
        self.tags = liveData["tags"].split(",")
        # 主播uid
        self.userId = liveData["uid"]
        # 主播
        self.userName = liveData["uname"]
        # 主播粉丝数
        self.attention = liveData["attention"]
        # 房间介绍
        self.description = liveData["description"]
        # 人气
        self.online = liveData["online"]
        # 房间地址
        self.liveUrl = liveData["live_url"]
        # 房间封面
        self.cover = liveData["cover"]
        # 房间背景
        self.background = liveData["background"]
        # 房间分区
        self.area = {
            "parent_area":[liveData["parent_area_id"], liveData["parent_area_name"]],
            "area": [liveData["area_id"], liveData["area_name"]]
        }
        # 房间分区转字符串
        self.area_str = "%s · %s" % (self.area["parent_area"][1], self.area["area"][1])
        # 房间开播时间
        self.live_time = liveData["live_time"]
        # 房间直播id
        self.live_id = liveData["live_id"]
        self._getLiveRoomStyle()

        msgList = MsgList(self.api.getLiveMsg(self.id))
        self.msg_loop_not_time_list = msgList.getMsgTimeList()
        self.old_msg_loop_time_list = self.msg_loop_not_time_list.copy()
        # 弹幕轮查间隙时间 (秒)
        self.msg_loop_sleep = 2

        self.__code = None

    def _getLiveRoomStyle(self):
        roomUserData = self.api.getLiveRoomUserData(self.id)
        self.style = {
            "msgColor": roomUserData["property"]["danmu"]["color"]
        }

    def _getMsgStyle(self, msg):
        msg = {
            "color": self.style["msgColor"],
            "send_time": int(time.time()),
            "msg": msg
        }
        return msg
    
    def _msg_loop(self, commandList):
        def loop(commandList):
            while True:
                msgList = MsgList(self.api.getLiveMsg(self.id))
                self.msg_loop_time_list = msgList.getMsgTimeList()
                for msg in msgList:
                    commandSign, comm, commKey  = self.set_command_list(msg["msg"], commandList.commandSign)

                    if not msg["time"] in self.old_msg_loop_time_list:
                        # 新弹幕回调
                        self.msg_log(msg)
                    
                    # 查询指令列表
                    if commandSign == commandList.commandSign:
                        if msg["time"] in self.msg_loop_not_time_list:
                            continue

                        # 将该弹幕加入已执行列表
                        self.msg_loop_not_time_list.append(msg["time"])
                        
                        if not comm in commandList.command:
                            self.__code = commandList.commandNameError()
                            self.command_log(self.__code, msg, "commandNameError")
                            continue
                        
                        # 执行指令对应方法
                        try:
                            # 检查指令权限
                            if comm in commandList.purviewCommand:
                                if msg["userId"] in commandList.purview:
                                    self.__code = commandList.command[comm](commKey, msg)
                                    self.command_log(self.__code, msg, comm)
                                else:
                                    self.__code = commandList.purviewError()
                                    self.command_log(self.__code, msg, "purviewError")
                                
                                continue

                            self.__code = commandList.command[comm](commKey, msg)
                            self.command_log(self.__code, msg, comm)
                        except IndexError:
                            # 执行指令错误回调
                            self.__code = commandList.commandError()
                            self.command_log(self.__code, msg, "commandError")
                    
                    #定时重置已执行列表 初始化时将历史弹幕加入
                    time_list_len = len(self.msg_loop_time_list) * 2
                    if len(self.msg_loop_not_time_list) == time_list_len:
                        # 将已执行列表后半变前半 后半用于后续加入
                        self.msg_loop_not_time_list = self.msg_loop_not_time_list[time_list_len - 1:]
                
                time.sleep(self.msg_loop_sleep)
                self.old_msg_loop_time_list = self.msg_loop_time_list
                        
        thread = Thread(target=loop, args=(commandList,))
        thread.setDaemon(True)
        thread.start()
        self.msg_loop_thread = thread
    
    def _send_msg_loop(self, sendMsgList):
        send_msg_thread_list = []
        def loop(sendTime, sendMsg):
            while True:
                time.sleep(sendTime)
                self.command_log(self.send_msg(sendMsg), None, None)
        
        for sendTime in sendMsgList:
            thread = Thread(target=loop, args=(sendTime, sendMsgList[sendTime]))
            thread.setDaemon(True)
            send_msg_thread_list.append(thread)
        
        for thread in send_msg_thread_list:
            thread.start()

        self.send_msg_loop_thread = send_msg_thread_list
    
    @abstractmethod
    def set_command_list(self, msg, commandSign):
        """
        设置指令格式, 默认使用 任意指令标识符, 参数空格隔开
        """
        command_list = msg.strip(" ").split(" ")
        commandSign = list(command_list[0])[0]
        comm = command_list[0].strip(commandSign)
        commKey = command_list[1:]
        return commandSign, comm, commKey

    @abstractmethod
    def send_msg(self, msg):
        """
        调用父类send_msg 发送弹幕\n
        父类参数: self.id , self._getMsgStyle(msg)
        """
        return self.api.sendLiveMsg(self.id, self._getMsgStyle(msg))
    
    @abstractmethod
    def send_msg_loop(self, sendMsgList):
        """
        调用父类send_msg_loop 开启定时发送
        """
        self._send_msg_loop(sendMsgList)
    
    @abstractmethod
    def msg_loop(self, commandList):
        """
        调用父类msg_loop 开启弹幕轮查
        """
        self._msg_loop(commandList)
    
    @abstractmethod
    def set_time(self, msg_time):
        """
        统一格式化时间\n
        定时发送调用时 msg_time为时间戳\n
        其他情况 msg_time为时间字符串 "%Y-%m-%d %H:%M:%S"
        """
        if type(msg_time) == float:
            msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg_time)) 

        return msg_time

    @abstractmethod
    def msg_log(self, msg):
        """
        新弹幕回调
        """
        print("[%s] %s: %s" % (self.set_time(msg["time"]), msg["userName"], msg["msg"]))

    @abstractmethod
    def command_log(self, code, msg, comm):
        """
        指令回调
        """
        # 定时发送调用时的默认数据格式 code, None, None
        if msg is None and comm is None:
            if code == 0:
                print('[%s] 定时发送成功!' % self.set_time(time.time()))
            else:
                print('[%s] 定时发送失败... code:%s' % (self.set_time(time.time()), code))
            
            return

        print('[%s] "%s: %s" 执行成功 -> %s' % (self.set_time(msg["time"]), msg["userName"], msg["msg"], comm))
        

class MsgList:

    def __init__(self, msgList):
        self.index = 0
        self.msgList = msgList
        self.data_len = len(msgList)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == self.data_len:
            raise StopIteration

        msg = self.msgList[self.index]
        data = {
            "time": msg["timeline"],
            "msg": msg["text"],
            "userName": msg["nickname"],
            "userId": msg["uid"]
        }
        self.index += 1
        return data
    
    def getMsgTimeList(self):
        return [msg["timeline"] for msg in self.msgList]


# 抽象指令对像
class Command(metaclass=ABCMeta):

    def __init__(self, BiliLive):
        self.api = BiliLive
        self.purview = []
        self.purviewCommand = []
        self.command = {}
        self.commandSign = "/"
    
    @abstractmethod
    def commandError(self):
        """
        commandError 指令参数错误
        """
        return self.api.send_msg("您的指令参数填错啦!")

    @abstractmethod
    def commandNameError(self):
        """
        commandNameError 指令名字错误
        """
        return self.api.send_msg("您的指令名字填错啦!")
    
    @abstractmethod
    def purviewError(self):
        """
        purviewError 指令权限错误
        """
        return self.api.send_msg("您的指令权限不足...")
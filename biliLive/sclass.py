from abc import ABCMeta, abstractmethod
import os
from biliLive.http_api import Link
import biliLive.bilibiliApi as bapi
from threading import Thread
import time, sys


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
        self.commandList = None
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
    
    def bind(self, commandList=None, event=None):
        if event is None:
            self.__event = bapi.event()
            self.__event.live = self
        else:
            self.__event = event
            self.__event.live = self
        
        if commandList is None:
            self.__commandList = bapi.commandList()
            self.__commandList.event = self.__event
        else:
            self.__commandList = commandList
            self.__commandList.event = self.__event

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
    
    def __msg_look(self, msg):
        commandSign, comm, commKey  = self.__event.set_command_list(msg["msg"], self.__commandList.commandSign)
        
        if not msg["time"] in self.old_msg_loop_time_list:
            # 新弹幕回调
            self.__event.msg_log(msg)
        
        # 查询指令列表
        if commandSign == self.__commandList.commandSign:
            if msg["time"] in self.msg_loop_not_time_list:
                return

            # 将该弹幕加入已执行列表
            self.msg_loop_not_time_list.append(msg["time"])
            
            if not comm in self.__commandList.command:
                self.__code = self.__commandList.commandNameError()
                self.__event.command_err_log(self.__code, msg, "commandNameError")
                return
            
            # 执行指令对应方法
            try:
                # 检查指令权限
                if comm in self.__commandList.purviewCommand:
                    if msg["userId"] in self.__commandList.purview:
                        self.__code = self.__commandList.command[comm](commKey, msg)
                        self.__event.command_log(self.__code, msg, comm)
                    else:
                        self.__code = self.__commandList.purviewError()
                        self.__event.command_err_log(self.__code, msg, "purviewError")
                    
                    return

                self.__code = self.__commandList.command[comm](commKey, msg)
                self.__event.command_log(self.__code, msg, comm)
            except IndexError:
                # 执行指令错误回调
                self.__code = self.__commandList.commandError()
                self.__event.command_err_log(self.__code, msg, "commandError")
    
    def _msg_loop(self):
        def loop():
            while True:
                msgList = MsgList(self.api.getLiveMsg(self.id))
                self.msg_loop_time_list = msgList.getMsgTimeList()
                for msg in msgList:
                    self.__msg_look(msg)
                    
                    #定时重置已执行列表 初始化时将历史弹幕加入
                    time_list_len = len(self.msg_loop_time_list) * 2
                    if len(self.msg_loop_not_time_list) == time_list_len:
                        # 将已执行列表后半变前半 后半用于后续加入
                        self.msg_loop_not_time_list = self.msg_loop_not_time_list[time_list_len - 1:]
                
                time.sleep(self.msg_loop_sleep)
                self.old_msg_loop_time_list = self.msg_loop_time_list
                        
        thread = Thread(target=loop)
        thread.setDaemon(True)
        thread.start()
        self.msg_loop_thread = thread
    
    def time_loop_job(self, jobTime, job):
        while True:
            time.sleep(jobTime)
            self.__event.command_log(job(), None, None)
    
    def _time_loop(self):
        send_msg_thread_list = []
        
        for jobTime in self.__commandList.timeLoopList:
            if type(self.__commandList.timeLoopList[jobTime]) == str:
                def job():
                    return self.__event.send_msg(self.__commandList.timeLoopList[jobTime])
            else:
                job = self.__commandList.timeLoopList[jobTime]
            thread = Thread(target=self.time_loop_job, args=(jobTime, job))
            thread.setDaemon(True)
            send_msg_thread_list.append(thread)
        
        for thread in send_msg_thread_list:
            thread.start()

        self.send_msg_loop_thread = send_msg_thread_list
    
    def msg_loop(self):
        self.__event.msg_loop()
    
    def time_loop(self):
        self.__event.time_loop()


class Event(metaclass=ABCMeta):

    def __init__(self):
        self.live = None
    
    @abstractmethod
    def set_command_list(self, msg, commandSign):
        """
        设置指令格式, 默认使用 任意指令标识符, 参数空格隔开
        叁数:
        msg: 弹幕数据列表
        commandSign: 当前绑定的指令标识符
        需返回: 指令标识符, 无标识符的指令字段, 指令参数
        """
        command_list = msg.strip(" ").split(" ")
        commandSign = list(command_list[0])[0]
        comm = command_list[0].strip(commandSign)
        commKey = command_list[1:]
        return commandSign, comm, commKey
    
    @abstractmethod
    def send_msg(self, msg):
        """
        send_msg 发送弹幕\n
        父类参数: self.id , self._getMsgStyle(msg)
        self._getMsgStyle: 用户当前弹幕样式
        self.id: 房间号
        """
        return self.live.api.sendLiveMsg(self.live.id, self.live._getMsgStyle(msg))
    
    @abstractmethod
    def time_loop(self):
        """
        事件 time_loop 启动定时发送
        """
        self.live._time_loop()
    
    @abstractmethod
    def msg_loop(self):
        """
        事件 msg_loop 启动弹幕轮查
        """
        self.live._msg_loop()

    @abstractmethod
    def msg_log(self, msg):
        """
        事件 msg_log 新弹幕会经过这里
        """
        print("%s: %s" % (msg["userName"], msg["msg"]))

    @abstractmethod
    def command_log(self, code, msg, comm):
        """
        事件 command_log 指令执行成功
        """
        # 定时发送调用时的默认数据格式 code, None, None
        if msg is None and comm is None:
            if code == 0:
                print('定时发送成功')
            else:
                print('定时发送失败... code:%s' % code)
            
            return

        print('"%s: %s" 执行成功 -> %s' % (msg["userName"], msg["msg"], comm))
    
    @abstractmethod
    def command_err_log(self, code, msg, comm):
        """
        事件 command_err_log 指令执行错误
        """
        print('"%s: %s" 指令执行错误 -> %s' % (msg["userName"], msg["msg"], comm))

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
class CommandList(metaclass=ABCMeta):

    def __init__(self):
        self.event = None
        self.purview = []
        self.purviewCommand = []
        self.command = {}
        self.commandSign = "/"
        self.timeLoopList = {}
    
    @abstractmethod
    def commandError(self):
        """
        commandError 指令参数错误
        """
        return self.event.send_msg("您的指令参数填错啦!")

    @abstractmethod
    def commandNameError(self):
        """
        commandNameError 指令名字错误
        """
        return self.event.send_msg("您的指令名字填错啦!")
    
    @abstractmethod
    def purviewError(self):
        """
        purviewError 指令权限错误
        """
        return self.event.send_msg("您的指令权限不足...")


class LiveLog(metaclass=ABCMeta):

    def __init__(self, save_in="./log"):
        self.__terminal = sys.stdout
        self.save_in = save_in
        self.__save_in_obj = None
        self.save_in_load = False

        self.__set_log_path = self.set_log_path()
        sys.stdout = self

    def __save_in_open(self):
        if not os.path.isdir(self.save_in):
            os.makedirs(self.save_in)

        if not self.save_in_load:
            self.__save_in_obj = open(self.__set_log_path, "a", encoding="utf-8")
            self.save_in_load = True
    
    def __save_in_close(self):
        if self.save_in_load:
            self.__save_in_obj.close()
            self.save_in_load = False
    
    @abstractmethod
    def set_log_path(self):
        return time.strftime(f"{self.save_in}/log_%Y_%m_%d_%H_%M_%S.txt", time.localtime())
    
    @abstractmethod
    def set_log_style(self, log):
        log_time = time.strftime("%H:%M:%S", time.localtime())
        log_msg = "[%s] %s" % (log_time, log)
        return log_msg
    
    def write(self, log):
        self.__save_in_open()

        if log != "\n":
            log = self.set_log_style(log)

        if self.save_in_load:
            self.__save_in_obj.write(log)
        self.__terminal.write(log)

        self.__save_in_close()
    
    def flush(self):
        self.__terminal.flush()
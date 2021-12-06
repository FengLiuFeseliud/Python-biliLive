from abc import ABCMeta, abstractclassmethod, abstractstaticmethod
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
                    smsg = msg["msg"].strip(" ").split(" ")
                    comm = smsg[0].strip(commandList.commandSign)
                    commandSign = list(smsg[0])[0]
                    commKey = smsg[1:]
                    
                    # 查询指令列表
                    if commandSign == commandList.commandSign:
                        if msg["time"] in self.msg_loop_not_time_list:
                            continue

                        # 将该弹幕加入已执行列表
                        self.msg_loop_not_time_list.append(msg["time"])
                        
                        if not comm in commandList.command:
                            commandList.commandNameError()
                            continue
                        
                        # 执行指令对应方法
                        try:
                            # 检查指令权限
                            if comm in commandList.purviewCommand:
                                if msg["userId"] in commandList.purview:
                                    commandList.comman[comm](commKey)
                                else:
                                    commandList.purviewError()

                            commandList.command[comm](commKey)
                        except IndexError:
                            # 执行指令错误回调
                            commandList.commandError()
                    
                    #定时重置已执行列表 初始化时将历史弹幕加入
                    time_list_len = len(self.msg_loop_time_list) * 2
                    if len(self.msg_loop_not_time_list) == time_list_len:
                        # 将已执行列表后半变前半 后半用于后续加入
                        self.msg_loop_not_time_list = self.msg_loop_not_time_list[time_list_len - 1:]
                
                time.sleep(2)
                        
        thread = Thread(target=loop, args=(commandList,))
        thread.setDaemon(True)
        thread.start()
        self.msg_loop_thread = thread
    
    def _send_msg_loop(self, sendMsgList):
        send_msg_thread_list = []
        def loop(sendTime, sendMsg):
            while True:
                time.sleep(sendTime)
                self.send_msg(sendMsg)
        
        for sendTime in sendMsgList:
            thread = Thread(target=loop, args=(sendTime, sendMsgList[sendTime]))
            thread.setDaemon(True)
            send_msg_thread_list.append(thread)
        
        for thread in send_msg_thread_list:
            thread.start()

        self.send_msg_loop_thread = send_msg_thread_list

    @abstractclassmethod
    def send_msg(self, msg):
        pass
    
    @abstractstaticmethod
    def send_msg_loop(self):
        pass
    
    @abstractclassmethod
    def msg_loop(self):
        pass


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


class command(metaclass=ABCMeta):

    def __init__(self, BiliLive):
        self.api = BiliLive
        self.purview = []
        self.purviewCommand = []
        self.command = {}
    
    @abstractstaticmethod
    def commandError(self):
        pass

    @abstractstaticmethod
    def commandNameError(self):
        pass
    
    @abstractstaticmethod
    def purviewError(self):
        pass
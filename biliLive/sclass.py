from abc import ABCMeta, abstractmethod
from zlib import decompress
from collections import namedtuple
from biliLive.http_api import Link
from threading import Thread, Lock
import biliLive.bilibiliApi as bapi
import requests
import sys
import os
import time
import websocket
import json
import struct

HeaderTuple = namedtuple('HeaderTuple', ('pack_len', 'raw_header_size', 'ver', 'operation', 'seq_id'))
HEADER_STRUCT = struct.Struct('>I2H2I')
WS_OP_HEARTBEAT = 2, #心跳
WS_OP_HEARTBEAT_REPLY = 3 # 心跳回应 
WS_OP_MESSAGE = 5 # 弹幕,消息等
WS_OP_USER_AUTHENTICATION = 7 # 用户进入房间
WS_OP_CONNECT_SUCCESS = 8 # 进房回应

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

        # 弹幕轮查间隙时间 (秒)
        self.msg_loop_sleep = 2
        self.__code = None
        self.bind()

        def get_live(room_id):
            api = f"https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo?id={room_id}&type=0"
            with requests.get(api) as req:
                data = req.json()["data"]
                host, port = data["host_list"][0]["host"], data["host_list"][0]["wss_port"]
            return host, port, data["token"]
        # 信息流服务器列表
        host, port, token = get_live(self.id)
        self.host_list = ["wss://%s:%s/sub" % (host, port)]
        # 认证包正文
        self.certificationPack = {
            "roomid": self.id,
            "uid": 0,
            "protover": 1,
            "platform": "web",
            "clientver": "1.4.0",
            "key": token,
            "type": 2
        }

        self.wsAppEvent = {
            WS_OP_HEARTBEAT_REPLY: self.heart_beat_reply,
            WS_OP_MESSAGE: self.new_message,
            WS_OP_CONNECT_SUCCESS: self.connect_success
        }

        # 直播间cmd
        self.liveEvent = {
            # 弹幕
            "DANMU_MSG": self._message,
            # 普通用户进入房间
            "INTERACT_WORD": self.__event.welcome,
            # 老爷(直播会员)进入房间
            "WELCOME_GUARD": self.__event.welcome_guard,
            # 舰长进入房间
            "ENTRY_EFFECT": self.__event.entry_effect,
            # SC留言
            "SUPER_CHAT_MESSAGE": self.__event.super_msg,
            # SC留言
            "SUPER_CHAT_MESSAGE_JPN": self.__event.super_msg,
            # 投喂礼物
            "SEND_GIFT": self.__event.send_gift,
            # 连击礼物
            "COMBO_SEND": self.__event.combo_send_gift,
            # 直播游戏 也是送礼物(不知道有什么用) 
            "LIVE_INTERACTIVE_GAME": self.__event.send_gift_game,
            # 天选之人开始
            "ANCHOR_LOT_START": self.__event.anchor_lot_start,
            # 天选之人结束
            "ANCHOR_LOT_END": self.__event.anchor_lot_end,
            # 天选之人结果
            "ANCHOR_LOT_AWARD": self.__event.anchor_lot_award,
            # 上舰长
            "GUARD_BUY": self.__event.guard_buy,
            # 续费了舰长
            "USER_TOAST_MSG": self.__event.guard_renew,
            # 大公告
            "NOTICE_MSG": self.__event.notice_msg,
            # 小时榜变动
            "ACTIVITY_BANNER_UPDATE_V2": self.__event.activity_banner_update,
            # 关注数变动
            "ROOM_REAL_TIME_MESSAGE_UPDATE": self.__event.room_data_update,
            # 高能榜变动
            "ONLINE_RANK_V2": self.__event.online_rank,
            # 主播榜变动
            "ONLINE_RANK_COUNT": self.__event.live_rank,
            # 热门榜变动
            "HOT_RANK_CHANGED_V2": self.__event.hot_rank,
            # 热门榜计数? (不清楚能干嘛)
            "HOT_RANK_CHANGED": self.__event.hot_rank_changed,
            # 直播活动变动 (我估计这里一直会变直接留空了 需要的写)
            "WIDGET_BANNER": self.__event.activity,
            # 热门榜限时上榜
            "HOT_RANK_SETTLEMENT_V2": self.__event.hot_rank_settlement,
            # 同上 这个数据少
            "HOT_RANK_SETTLEMENT": self.__event.hot_rank_settlement,
            # 停止直播室名单 (下播名单?)
            "STOP_LIVE_ROOM_LIST": self.__event.stop_live_room_list,
            # pk数据
            "PK_BATTLE_PROCESS": self.__event.pk_battle_process,
            # pk数据新
            "PK_BATTLE_PROCESS_NEW": self.__event.pk_battle_process_new,
            # pk决赛
            "PK_BATTLE_FINAL_PROCESS": self.__event.pk_battle_process_final,
            # pk结束
            "PK_BATTLE_END": self.__event.pk_battle_end,
            # pk结算
            "PK_BATTLE_SETTLE_USER": self.__event.pk_battle_settle_user,
            # pk结算
            "PK_BATTLE_SETTLE_V2": self.__event.pk_battle_settle,
            # pk连胜
            "COMMON_NOTICE_DANMAKU": self.__event.common_notice_danmaku,
            "ENTRY_EFFECT_MUST_RECEIVE": self.__event.miscellaneous,
        }
    
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
    
    def make_packet(self, data, operation):
        body = json.dumps(data).encode('utf-8')
        header = HEADER_STRUCT.pack(
            HEADER_STRUCT.size + len(body),
            HEADER_STRUCT.size,
            1,
            operation,
            1
        )
        return header + body
    
    def set_body(self, message):
        header = HeaderTuple(*HEADER_STRUCT.unpack_from(message, 0))
        body = message[HEADER_STRUCT.size: header.pack_len]
        if header.ver == 2:
            return self.set_body(decompress(body))
        else:
            try:
                return header, json.loads(body.decode())
            except:
                # 心跳包回应
                popularity =int.from_bytes(message[HEADER_STRUCT.size: HEADER_STRUCT.size + 4],'big')
                return header, popularity
    
    def _msg_loop(self, debug=False):
        def loop():
            if debug:
                websocket.enableTrace(True)
            # 设置连接
            wsapp = websocket.WebSocketApp(self.host_list[0],
                on_message=self.on_message, on_ping=self.on_ping, on_pong=self.on_pong, on_close=self.on_close, 
                    on_error=self.on_error)

            wsapp.on_open = self.on_open
            # 打开连接
            wsapp.run_forever(ping_interval=40, ping_timeout=30)
            
        thread = Thread(target=loop)
        thread.setDaemon(True)
        thread.start()
        self.msg_loop_thread = thread
    
    def on_message(self, wsapp, message):
        """
        事件 on_message 接收服务器数据
        """

        # 数据解析
        header, message = self.set_body(message)
        # 事件执行
        if header.operation in self.wsAppEvent:
            self.wsAppEvent[header.operation](message)
        else:
            print("未知数据协议:%s" % message)
        
    
    def on_ping(self, wsapp, message):
        pass

    def on_pong(self, wsapp, message):
        """
        事件 on_pong 接收到服务器心跳包
        """

        # 向服务器发送心跳包
        print("发送心跳包...")
        wsapp.send(self.make_packet({}, 2))

    def on_open(self, wsapp):
        """
        事件 on_open 连接启动
        """

        # 发送认证包
        print("正在连接 %s (id: %s)直播间, 发送认证包..." % (self.name, self.id))
        wsapp.send(self.make_packet(self.certificationPack, 7))
    
    def on_close(self, wsapp, close_status_code, close_msg):
        print(wsapp, close_status_code, close_msg, "on_close........")
    
    def on_error(wsapp, err):
        print("Got a an error: ", err)
    
    def heart_beat_reply(self, popularity):
        """
        事件 heart_beat_reply 心跳回应
        """
        self.__event.popularity_update(popularity)
    
    def connect_success(self, message):
        """
        事件 connect_success 进房回应
        """
        print("连接成功! 接收到了服务器的进房回应")
    
    def new_message(self, message):
        """
        事件 new_message 直播间信息
        """
        if message["cmd"] in self.liveEvent:
            self.liveEvent[message["cmd"]](message)
        else:
            self.__event.miscellaneous(message)

    def _message(self, message):
        msg = format.msg(message)
        commandSign, comm, commKey  = self.__event.set_command_list(msg["msg"], self.__commandList.commandSign)
        
        # 新弹幕回调
        self.__event.msg_log(msg)
        
        # 检查是否为指令
        if commandSign != self.__commandList.commandSign:
            return
        
        # 查询指令列表
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
    
    def msg_loop(self, debug=False):
        self.__event.msg_loop(debug)
    
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
    def msg_loop(self, debug):
        """
        事件 msg_loop 启动弹幕轮查
        """
        self.live._msg_loop(debug)

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
    
    def welcome(self, msg):
        """
        事件 welcome 普通用户进入房间
        """
        msg = format.welcome(msg)
        print("%s 进入了房间!" % msg["userName"])
    
    def welcome_guard(self, msg):
        """
        事件 welcome_guard 老爷用户进入房间
        """
        print(msg)

    def entry_effect(self, msg):
        """
        事件 entry_effect 舰长进入房间(不确定)
        """
        msg = format.entry_effect(msg)
        print(msg["copy_writing"])

    def super_msg(self, msg):
        """
        事件 super_msg SC留言
        """
        msg = format.super_msg(msg)
        print("%s发送了价值%s的SE! 时长%s: %s" % (msg["userName"], msg["price"], 
                                    msg["endTime"], msg["msg"]))

    def send_gift(self, msg):
        """
        事件 send_gift 投喂礼物
        """
        msg = format.send_gift(msg)
        print("%s%s了%s个%s!" % (msg["userName"], msg["action"], msg["num"], msg["giftName"]))

    def combo_send_gift(self, msg):
        """
        事件 combo_send_gift 连击投喂礼物
        """
        msg = format.send_gift(msg)
        print("%s连击%s了%s个%s!" % (msg["userName"], msg["action"], msg["num"], msg["giftName"]))
    
    def send_gift_game(self, msg):
        """
        事件 send_gift_game 直播游戏
        """
        msg = format.send_gift(msg)
        print("%s送了%s个%s!" % (msg["userName"], msg["num"], msg["giftName"]))

    def anchor_lot_start(self, msg):
        """
        事件 anchor_lot_start 天选之人开始
        """
        print(msg)

    def anchor_lot_end(self, msg):
        """
        事件 anchor_lot_end 天选之人结束
        """
        print(msg)

    def anchor_lot_award(self, msg):
        """
        事件 anchor_lot_award 天选之人结果
        """
        msg, list_str = format.anchor_lot_award(msg), ""
        for uesr in msg["userList"]:
            list_str += uesr["uname"]
        print("天选之人 %s 结果: %s" % (msg["name"], list_str))

    def guard_buy(self, msg):
        """
        事件 guard_buy 上舰长
        """
        msg = format.guard_buy(msg)
        print("%s开通了%s月%s" % (msg["userName"], msg["num"], msg["giftName"]))

    def guard_renew(self, msg):
        """
        事件 guard_renew 续费了舰长
        """
        print(msg)
    
    def notice_msg(self, msg):
        """
        事件 notice_msg 大公告
        """
        print(msg)

    def activity_banner_update(self, msg):
        """
        事件 activity_banner_update 小时榜变动
        """
        print(msg)

    def room_data_update(self, msg):
        """
        事件 room_data_update 粉丝关注变动
        """
        msg = format.room_data(msg)
        print("关注变动! 关注数:%s 粉丝团人数:%s" % (msg["fans"], msg["fansClub"]))
    
    def online_rank(self, msg):
        """
        事件 online_rank 高能榜变更
        """
        msg, data = msg['data']['list'], ""
        for user in msg:
            data += " %s-%s " % (user["uname"], user["score"])
        print("高能榜变更! %s" % data)
    
    def live_rank(self, msg):
        """
        事件 live_rank 主播榜变更
        """
        print("主播现在排在%s!" % msg["data"]["count"])
    
    def hot_rank(self, msg):
        """
        事件 hot_rank 热门榜变更
        """
        msg = format.hot_rank(msg)
        print("主播现在%s排在%s!" % (msg["rankDesc"], msg["rank"]))
    
    def activity(self, msg):
        """
        事件 activity 活动内容变更
        我估计这里一直会变直接留空了 需要的写
        """
        pass
    
    def hot_rank_changed(self, msg):
        """
        事件 hot_rank_changed 热门榜计数? (不清楚能干嘛)
        """
        pass

    def hot_rank_settlement(self, msg):
        if msg["cmd"] == "HOT_RANK_SETTLEMENT":
            return
        
        msg = format.hot_rank_settlement(msg)
        print(msg["rankDesc"])

    def stop_live_room_list(self, msg):
        """
        事件 stop_live_room_list 停止直播室名单 (下播名单?)
        """
        pass
    
    def popularity_update(self, popularity):
        """
        事件 popularity_update 心跳回应更新人气值
        """
        print("当前人气值: %s" % popularity)
    
    def pk_battle_process(self, msg):
        """
        事件 pk_battle_process pk数据
        """
        print(msg)

    def pk_battle_process_new(self, msg):
        """
        事件 pk_battle_process_new pk数据新
        """
        print(msg)

    def pk_battle_process_final(self, msg):
        """
        事件 pk_battle_process_final pk决赛
        """
        print(msg)

    def pk_battle_end(self, msg):
        """
        事件 pk_battle_end pk结束
        """
        print(msg)

    def pk_battle_settle_user(self, msg):
        """
        事件 pk_battle_settle_user pk结算
        """
        print(msg)

    def pk_battle_settle(self, msg):
        """
        事件 pk_battle_settle pk结算
        """
        print(msg)

    def common_notice_danmaku(self, msg):
        """
        事件 common_notice_danmaku pk连胜
        """
        print(msg)
    
    def miscellaneous(self, msg):
        """
        事件 miscellaneous 未知事件全部会调用
        """
        print("未知信息...")
        

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


class format:
    """
    数据格式化
    """

    @staticmethod
    def msg(data):
        """
        弹幕数据
        msg: 内容
        userId: 用户id
        userName: 用户名
        badge: 用户粉丝牌子
        level: 用户直播用户等级
        time: 时间
        color: 弹幕颜色
        """
        data = data["info"]
        return {
            "msg": data[1],
            "userId": data[2][0],
            "userName": data[2][1],
            "badge": data[3],
            "level": data[4][1],
            "time": data[9]["ts"],
            "color": data[9]["ct"],
        }
    
    @staticmethod
    def send_gift(data):
        """
        送礼物数据
        action: 动作
        giftId: 礼物id
        giftName: 礼物名称
        num: 送礼物数量
        userName: 用户名
        userId: 用户id
        medal_info: 用户粉丝牌子
        """
        data, cmd = data["data"], data["cmd"]
        if cmd == "LIVE_INTERACTIVE_GAME":
            data["medal_info"] = ""
            data["action"] = ""
        if cmd == "COMBO_SEND":
            data["gift_num"] = data["total_num"]
        if cmd == "SEND_GIFT":
            return {
                "action": "",
                "giftId": data["giftId"],
                "giftName": data["giftName"],
                "num": data["num"],
                "userName": data["uname"],
                "userId": data["uid"],
                "medal_info": data["medal_info"]
            }
        return {
            "action": data["action"],
            "giftId": data["gift_id"],
            "giftName": data["gift_name"],
            "num": data["gift_num"],
            "userName": data["uname"],
            "userId": data["uid"],
            "medal_info": data["medal_info"]
        }
    
    @staticmethod
    def welcome(data):
        """
        普通用户进入房间数据
        userName: 用户名
        userId: 用户id
        medal: 用户粉丝牌子
        roomId: 直播间id
        time: 时间
        """
        data = data["data"]
        return {
            "userName": data["uname"],
            "userId": data["uid"],
            "medal": data["fans_medal"],
            "roomId": data["roomid"],
            "time": data["timestamp"]
        }

    @staticmethod
    def entry_effect(data):
        """
        舰长进入房间数据
        copy_writing: 进入房间消息
        userId: 用户id
        basemap: 进入房间消息背景
        face: 用户头像
        privilegeType: 舰长类型
        time: 时间
        """
        data = data["data"]
        return {
            "copy_writing": data["copy_writing"],
            "userId": data["uid"],
            "basemap": data["basemap_url"],
            "face": data["face"],
            "privilegeType": data["privilege_type"],
            "time": data["trigger_time"]
        }
    
    @staticmethod
    def room_data(data):
        """
        房间关注更新数据
        roomId: 房间号
        fans: 关注数
        fansClub: 粉丝团人数
        """
        data = data["data"]
        return {
            "roomId": data["roomid"],
            "fans": data["fans"],
            "fansClub": data["fans_club"]
        }
    
    @staticmethod
    def hot_rank(data):
        """
        热门榜更新数据
        rank: 排名
        name: 榜单名
        rankDesc: 榜单简介
        icon: 图标
        time: 时间
        """
        data = data["data"]
        return {
            "rank": data["rank"],
            "name": data["area_name"],
            "rankDesc": data["rank_desc"],
            "icon": data["icon"],
            "time": data["timestamp"]
        }
    @staticmethod
    def hot_rank_settlement(data):
        """
        进入限时热门榜总榜数据
        rank: 排名
        name: 榜单名
        rankDesc: 榜单简介
        icon: 图标
        time: 时间
        """
        return {
            "rank": data["rank"],
            "name": data["area_name"],
            "rankDesc": data["rank_desc"],
            "icon": data["icon"],
            "time": data["timestamp"]
        }

    @staticmethod
    def super_msg(data):
        """
        SC留言数据
        background: SC背景样式
        userName: 用户名
        level: 用户直播用户等级
        userId: 用户id
        giftId: 礼物id
        giftName: 礼物名称
        num: 送礼物数量
        medal: 用户粉丝牌子
        msg: 内容
        price: 价格
        time: SC开始显示时间
        endTime: SC时长
        """
        data, cmd = data["data"], data["cmd"]
        return {
            "background": {
                'background_bottom_color': data["background_bottom_color"],
                'background_color': data["background_color"],
                'background_color_end': data["background_color_end"],
                'background_color_start': data["background_color_start"],
                'background_icon': data["background_icon"],
                'background_image': data["background_image"],
                'background_price_color': data["background_price_color"],
            } if cmd != "SUPER_CHAT_MESSAGE_JPN" else {
                "background_bottom_color": data["background_bottom_color"],
                "background_color": data["background_color"],
                'background_color_end': "",
                'background_color_start': "",
                "background_icon": data["background_icon"],
                "background_image": data["background_image"],
                "background_price_color": data["background_price_color"]

            },
            "userName": data["user_info"]["uname"],
            "userId": data["uid"],
            "level": data["user_info"]["user_level"],
            "giftId": data["gift"]["gift_id"],
            "giftName": data["gift"]["gift_name"],
            "num": data["gift"]["num"],
            "medal": data["medal_info"],
            "msg": data["message"],
            "price": data["price"],
            "time": data["start_time"],
            "endTime": data["time"]
        }

    @staticmethod
    def my_room_guard_renew(data):
        """
        自动续费舰长 
        userName: 用户名
        icon: 图标
        msgSelf: 自动续费舰长消息
        roomid: 房间号
        type: 舰长类型
        """
        return {
            "userName": data["name"],
            "icon": data["side"]["head_icon"],
            "msgSelf": data["msg_self"],
            "roomid": data["roomid"],
            "type": data["msg_type"]
        }
    
    @staticmethod
    def guard_buy(data):
        """
        开通舰长数据
        userName: 用户名
        userId: 用户id
        giftName: 舰长类型
        giftId: 礼物id
        num: 开通月数?
        time: 开始时间
        endTime: 结束时间
        """
        data = data["data"]
        return {
            "userName": data["username"],
            "userId": data["uid"],
            "giftName": data["gift_name"],
            "giftId": data["gift_id"],
            "num": data["num"],
            "time": data["start_time"],
            "endTime": data["end_time"]
        }
    
    @staticmethod
    def anchor_lot_award(data):
        """
        天选之人结果数据
        name: 天选之人标题
        num: 数量
        image: 图片?
        userList: 中奖用户名单
        """
        data = data["data"]
        return {
            "name": data["award_name"],
            "num": data["award_num"],
            "image": data["award_image"],
            "userList": data["award_users"],
        }


class LiveLog(metaclass=ABCMeta):

    def __init__(self, save_in="./log"):
        self.__terminal = sys.stdout
        self.save_in = save_in
        self.__save_in_obj = None
        self.save_in_load = False
        self.lock = Lock()

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
        
        if log == "":
            return

        self.lock.acquire()
        if log != "\n":
            log = self.set_log_style(log)
        

        if self.save_in_load:
            self.__save_in_obj.write(log)
        self.__terminal.write(log)

        self.__save_in_close()
        self.lock.release()
    def flush(self):
        self.__terminal.flush()
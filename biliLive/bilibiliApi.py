from biliLive.http_api import Link
import biliLive.sclass as sc

BILIBILI_API = "https://api.bilibili.com"
BILIBILI_LIVE_API = "https://api.live.bilibili.com"

class BiliApi(Link):

    def __init__(self, headers=None):
        super().__init__(headers)
    
    def getUserData(self):
        """
        -101 未登录
        """
        api = BILIBILI_API + "/x/web-interface/nav"
        data = self._link(api)
        return data["data"] if data["code"] == 0 else data["code"]
    
    def getLiveRoom(self, room_id):
        api = BILIBILI_LIVE_API + "/xlive/web-room/v1/index/getRoomBaseInfo"
        data = self._link(f"{api}?room_ids={room_id}&req_biz=link-center")
        return data["data"]["by_room_ids"][room_id] if data["code"] == 0 else data["code"]

    def getLiveRoomUserData(self, room_id):
        api = BILIBILI_LIVE_API + "/xlive/web-room/v1/index/getInfoByUser"
        data = self._link(f"{api}?room_id={room_id}")
        return data["data"] if data["code"] == 0 else data["code"]
    
    def getLiveMsg(self, room_id):
        api = BILIBILI_LIVE_API + "/xlive/web-room/v1/dM/gethistory"
        data = self._link(f'{api}?roomid={room_id}')
        return data["data"]["room"] if data["code"] == 0 else data["code"]
    
    def sendLiveMsg(self, room_id, msg):
        api = BILIBILI_LIVE_API + "/msg/send"
        csrf_token = self._cookie_key("bili_jct")["bili_jct"]
        post_data = {
            "bubble": 0,
            "msg": msg["msg"],
            "color": msg["color"],
            "mode": 1,
            "fontsize": 25,
            "rnd": msg["send_time"],
            "roomid": room_id,
            "csrf": csrf_token,
            "csrf_token": csrf_token
        }
        data = self._link(api, data=post_data, mode="POST")
        return data["code"]
    
    def user(self):
        userData = self.getUserData()
        if type(userData) == int:
            return userData

        return BiliUser(self.headers, userData)
    
    def live(self, room_id):
        liveData = self.getLiveRoom(room_id)
        if type(liveData) == int:
            return liveData

        return BiliLive(self.headers, liveData)
        


class BiliUser(sc.User):

    def __init__(self, headers, userData):
        super().__init__(headers, userData)


class BiliLive(sc.Live):

    def set_command_list(self, msg, commandSign):
        return super().set_command_list(msg, commandSign)

    def send_msg(self, msg):
        return super().send_msg(msg)
    
    def msg_loop(self, commandList):
        return super().msg_loop(commandList)
    
    def send_msg_loop(self, sendMsgList):
        return super().send_msg_loop(sendMsgList)
    
    def set_time(self, msg_time):
        return super().set_time(msg_time)
    
    def msg_log(self, msg):
        return super().msg_log(msg)
    
    def command_log(self, code, msg, comm):
        return super().command_log(code, msg, comm)


class CommandList(sc.Command):
    
    def commandError(self):
        return super().commandError()
    
    def commandNameError(self):
        return super().commandNameError()
    
    def purviewError(self):
        return super().purviewError()
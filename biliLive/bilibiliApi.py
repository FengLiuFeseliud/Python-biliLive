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
        if data["code"] != 0:
            return

        for roomId in data["data"]["by_room_ids"]:
            return data["data"]["by_room_ids"][roomId]

    def getLiveRoomUserData(self, room_id):
        api = BILIBILI_LIVE_API + "/xlive/web-room/v1/index/getInfoByUser"
        data = self._link(f"{api}?room_id={room_id}")
        return data["data"] if data["code"] == 0 else data["code"]
    
    def getLiveMsg(self, room_id):
        api = BILIBILI_LIVE_API + "/xlive/web-room/v1/dM/gethistory"
        data = self._link(f'{api}?roomid={room_id}')
        return data["data"]["room"] if data["code"] == 0 else data["code"]
    
    def getLiveServer(self, room_id):
        api =  BILIBILI_LIVE_API + "/xlive/web-room/v1/index/getDanmuInfo"
        data = self._link(f"{api}?id={room_id}&type=0")
        return data["data"] if data["code"] == 0 else data["code"]
    
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
        
        liveServer = self.getLiveServer(liveData["room_id"])
        if type(liveServer) == int:
            return liveServer

        liveData.update(liveServer)
        return sc.Live(self.headers, liveData)

class BiliUser(sc.User):

    def __init__(self, headers, userData):
        super().__init__(headers, userData)


class event(sc.Event):

    def set_command_list(self, msg, commandSign):
        return super().set_command_list(msg, commandSign)

    def send_msg(self, msg):
        return super().send_msg(msg)
    
    def msg_loop(sel, debug):
        return super().msg_loop(debug)
    
    def time_loop(self):
        return super().time_loop()
    
    def msg_log(self, msg):
        return super().msg_log(msg)
    
    def command_log(self, code, msg, comm):
        return super().command_log(code, msg, comm)
    
    def command_err_log(self, code, msg, comm):
        return super().command_err_log(code, msg, comm)


class commandList(sc.CommandList):
    
    def commandError(self):
        return super().commandError()
    
    def commandNameError(self):
        return super().commandNameError()
    
    def purviewError(self):
        return super().purviewError()


class liveLog(sc.LiveLog):

    def set_log_path(self):
        return super().set_log_path()
    
    def set_log_style(self, log):
        return super().set_log_style(log)
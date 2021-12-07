# biliLive

bilibili Python 弹幕机

### **简单使用**

```python
from biliLive import BiliApi, CommandList

"""
设置一个打印字符串到终端的指令 名为 /text
指令格式: /text 要打印的字符串
并每12秒发送弹幕 弹幕内容: "12s sendMsg"
"""

# 默认请求头
headers = BiliApi.bilibili_headers
headers["cookie"] += "用户cookie"
api = BiliApi(headers)

# 连接房间
live = api.live("房间号")

# 指令方法 /text
def text(commKey,):
    # commKey是后面空格的参数
    # 如/text xxx xxx xxx 后面的[xxx, xxx, xxx]
    print(f"打印字符串 -> {commKey[0]}")

# 实列化弹幕指令对像 CommandList
commandList = CommandList(live)
commandList.command = {
    # 指令 /text
    "text": text,
}

# 定时发送
sendMsgList = {
    12: "12s sendMsg"
}

# 弹幕轮查间隙时间为3秒
live.msg_loop_sleep = 3

# 开启弹幕轮查
live.msg_loop(commandList)
# 开启定时发送
live.send_msg_loop(sendMsgList)
# 堵塞主线程
live.send_msg_loop_thread[-1].join()
```



### **设置弹幕指令**

```python
from biliLive import BiliApi, CommandList

api = BiliApi()
live = api.live("房间号")

# 实列化弹幕指令对像 CommandList
commandList = CommandList(live)

# 指令标志符号
commandList.commandSign

# 设置指令
commandList.command = {
    "弹幕指令": 绑定方法,
    "弹幕指令": 绑定方法,
    ...
}

# 将指令设置权限指令
commandList.purviewCommand = [
    "已经设置的弹幕指令",
    "已经设置的弹幕指令",
    ...
]

# 指定权限用户
commandList.purview = [
    用户uid, # int
    用户uid,
    ...
]

"""
错误 (默认发送弹幕提醒)
返回code，如果需要发送弹幕，可以将发送弹幕返回的状态码返回，来判断弹幕是否发送成功
"""

def commandError():
    print("commandError了啊 不会看指令文档???")
    return 0


# 指令参数错误执行
commandList.commandError = commandError
# 指令错误执行
commandList.commandNameError = 绑定方法
# 权限不足执行
commandList.purviewError = 绑定方法

# 定时发送
sendMsgList = {
    时间 : 信息,
    12: "12s sendMsg",
    ...
}

# 开启弹幕轮查
live.msg_loop(commandList)
# 开启定时发送
live.send_msg_loop(sendMsgList)
# 找一种东西堵塞主线程 如: gui, input()
live.send_msg_loop_thread[-1].join()

```



## 使用文档

> ### biliApi 对象
>
> ` biliApi = BiliApi(headers=headers)` 实例化 BiliApi 对象
>
> **参数说明：**
>
> headers：请求头
>
>  
>
> `biliApi.getUserData() ` 获取登录用户数据， cookie 无效返回-101
>
> `biliApi.getLiveRoom(room_id)` 获取直播间数据
>
> **参数说明：**
>
> room_id：房间号
>
>  
>
> `biliApi.getLiveRoomUserData(room_id)` 获取登录用户在指定直播间的设置
>
> **参数说明：**
>
> room_id：房间号
>
>  
>
> `biliApi.getLiveMsg(room_id)`  获取指定直播间的弹幕
>
> **参数说明：**
>
> room_id：房间号
>
>  
>
> `biliApi.sendLiveMsg(room_id, msg)` 使用登录用户向指定直播间发送弹幕
>
> **参数说明：**
>
> room_id：房间号
>
> msg：弹幕内容
>
>  
>
> `biliApi.user()`  实例化 user 对象
>
> `biliApi.live()` 实例化 live 对象
>
>  
>
> # 以下重点！！！
>
> **以下重点！！！ 以下重点！！！ 以下重点！！！ 以下重点！！！**
>
> ## **弹幕机 live 对象**
>
> 该对象支持继承 Live 类自定义实现，也可以使用`biliApi.live()` 快速实例化
>
> `biliApi.live()` 实例化的对象使用内部默认设置
>
> ```python
> from biliLive import BiliApi, CommandList
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> live = api.live("房间号")
> 
> # live 对象属性
> 
> # BiliApi
> live.api
> # 房间号
> live.id
> # 标题
> live.name
> # 标签
> live.tags
> # 主播uid
> live.userId
> # 主播
> live.userName
> # 主播粉丝数
> live.attention
> # 房间介绍
> live.description
> # 人气
> live.online
> # 房间地址
> live.liveUrl
> # 房间封面
> live.cover
> # 房间背景
> live.background
> # 房间分区
> live.area
> # 房间分区转字符串
> live.area_str
> # 房间开播时间
> live.live_time
> # 房间直播id
> live.live_id
> # 弹幕轮查间隙时间 (秒) 默认两秒
> self.msg_loop_sleep
> ```
>
>  
>
> 使用`biliApi.live()` 快速实例化的只用以下两方法
>
> 需要细节操作请继承 Live 类自定义实现
>
> `live.msg_loop(commandList)` 开启弹幕轮查
>
> **参数说明：**
>
> commandList：指令对象 
>
>  
>
> `live.send_msg_loop(sendMsgList)` 开启定时发送
>
> **参数说明：**
>
> sendMsgList：定时发送字典
>
>  
>
> ## **继承 Live 类自定义实现弹幕机**
>
> ```python
> from biliLive import BiliApi, Command, Live
> 
> # 继承创建弹幕机
> class MyLive(Live):
> 
>     def __init__(self, headers, liveData):
>         super().__init__(headers, liveData)
>         
>     def set_command_list(self, msg, commandSign):
>         """
>         设置指令格式, 默认使用 任意指令标识符, 参数空格隔开
>         
>         回调参数:
>         msg: 当前弹幕内容
>         commandSign: 当前指令标识符
>         """
>         return super().set_command_list(msg)
>         
> 	def send_msg(self, msg):
>         """
>         调用父类send_msg 发送弹幕\n
>         父类参数: self.id , self._getMsgStyle(msg)
>         
>         参数:
>         msg: 弹幕内容
>         """
>         return super().send_msg(msg)
>     
>     def send_msg_loop(self, sendMsgList):
>         """
>         调用父类send_msg_loop 开启定时发送
>         
>         参数:
>         sendMsgList: 定时发送字典
>         """
>         return super().send_msg_loop(sendMsgList)
>     
>     def msg_loop(self, commandList):
>         """
>         调用父类msg_loop 开启弹幕轮查
>         
>         参数:
>         commandList: 指令对象
>         """
>         return super().msg_loop(commandList)
>     
>     def set_time(self, msg_time):
>         """
>         统一格式化时间\n
>         定时发送调用时 msg_time为时间戳\n
>         其他情况 msg_time为时间字符串 "%Y-%m-%d %H:%M:%S"
>         
>         父类默认统一格式化时间为 "%Y-%m-%d %H:%M:%S" 格式
>         if type(msg_time) == float:
>             msg_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(msg_time)) 
> 
>         return msg_time
>         
>         回调参数:
>         msg_time: 浮点时间戳/时间字符串
>         """
>         
>         return super().set_time(msg_time)
> 
>     def msg_log(self, msg):
>         """
>         新弹幕回调
>         
>         回调参数:
>         msg: 当前弹幕数据字典
>         """
>         return super().msg_log(msg)
> 
>     def command_log(self, code, msg, comm):
>         """
>         指令回调
>         
>         
>         父类默认实现
>         # 定时发送调用时的默认数据格式 code, None, None
>         if msg is None and comm is None:
>             if code == 0:
>                 print('[%s] 定时发送成功!' % self.set_time(time.time()))
>             else:
>                 print('[%s] 定时发送失败... code:%s' % (self.set_time(time.time()), code))
>             
>             return
> 
>         print('[%s] "%s: %s" 执行成功 -> %s' % (self.set_time(msg["time"]), msg["userName"], msg["msg"], comm))
>         
>         回调参数:
>         code: 指令返回的值
>         msg: 当前弹幕数据字典
>         comm: 当前指令
>         """
>         return super().command_log(code, msg, comm)
>     
>     
> # 实例化
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> # 连接直播间
> live = MyLive(api.headers, api.getLiveRoom("房间号"))
> commandList = CommandList(live)
> 
> # 指令方法 /text
> def text(commKey, msg):
>     print(f"打印字符串 -> {commKey[0]}")
> 
> # 绑定方法 /text
> commandList.command = {
>     "text": text
> }
> 
> # 定时发送
> sendMsgList = {
>     12: "12s sendMsg"
> }
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop(commandList)
> # 开启定时发送
> live.send_msg_loop(sendMsgList)
> # 堵塞主线程
> input("")
> ```
>
> 
>
> ## **项目地址有演示文件可以查看** !!!!
>
> 
>
> ## **指令对象 commandList 对象 **
>
> 该对象支持继承 commandList 类自定义实现，也可以导入`commandList ` 快速实例化
>
> `commandList ` 实例化的对象使用内部默认设置
>
> 
>
> 绑定的方法在被调用时会被转入两个参数  **commKey，msg**
>
> commKey：指令参数列表 （在默认指令格式下 "/text xxx xxx xxx" 的三个xxx就是指令参数）
>
> msg：当前调用指令的 msg 数据
>
> ```python
> from biliLive import BiliApi, CommandList
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> live = api.live("房间号")
> # 直接实例化 指令对象
> commandList = CommandList(live)
> # 设置指令标记符 (默认为 / )
> commandList.commandSign = "#"
> 
> # 方法 text
> def text(commKey, msg):
>     print(f"打印字符串 -> {commKey[0]}")
>     
> # 方法 ptext
> def ptext(commKey, msg):
>     print(f"权限指令 打印字符串 -> {commKey[0]}")
> 
> # 绑定方法 text 为指令 #text
> commandList.command = {
>     "text": text,
>     # 绑定方法 ptext 为指令 #ptext
>     "ptext": ptext
> }
> 
> # 设置权限用户
> commandList.purview = [
>     34394509 # 用户uid
> ]
> 
> # 设置将指令设置为权限指令
> commandList.purviewCommand = [
>     # 将指令 #ptext 设置为权限指令
>     "ptext"
> ]
>         
> # 定时发送
> sendMsgList = {
>     12: "12s sendMsg"
> }
> 
> # 指令参数方法
> def commandError():
>     print("commandError了啊 不会看指令文档???")
>     return 0
> 
> # 不绑定 默认发送弹幕提醒
> 
> # 指令参数错误执行
> commandList.commandError = commandError
> # 指令错误执行
> commandList.commandNameError = 绑定方法
> # 权限不足执行
> commandList.purviewError = 绑定方法
> 
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop(commandList)
> # 开启定时发送
> live.send_msg_loop(sendMsgList)
> # 堵塞主线程
> live.send_msg_loop_thread[-1].join()
> ```
>
> 
>
> ## **继承 command 类自定义实现指令对象**
>
> ```python
> from biliLive import BiliApi, Command
> 
> # 继承创建指令对象
> class MyCommandList(Command):
>     
>     def __init__(self, BiliLive):
>         super().__init__(BiliLive)
> 		# 可以在内部设置指令 也可以外部
>         self.commandSign = "#"
>         self.purview = [
>             ...
>         ]
>         self.purviewCommand = [
>             "print"
>         ]
>         self.command = {
>             "text": self.text,
>             "print": self.print
>         }
>     
>     def text(self, commKey, msg):
>         print(f"打印字符串 -> {commKey[0]}")
>        	
>     def ptext(self, commKey, msg):
>         print(f"purviewCommand 打印字符串 -> {commKey[0]}")
>     
>     def commandError(self):
>         """
>         commandError 指令参数错误
>         调用父类 commandError()
>         """
>         return super().commandError()
>     
>     def commandNameError(self):
>         """
>         commandNameError 指令名字错误
>         调用父类 commandNameError()
>         """
>         return super().commandNameError()
>     
>     def purviewError(self):
>         """
>         purviewError 指令权限错误
>         调用父类 purviewError()
>         """
>         return super().purviewError()
> 
> 
> # 实例化
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> # 连接直播间
> live = api.live("房间号")
> commandList = MyCommandList(live)
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop(commandList)
> # 开启定时发送
> live.send_msg_loop(sendMsgList)
> # 堵塞主线程
> input("")
> ```
>
>  
>
> ## **项目地址有演示文件可以查看** !!!!
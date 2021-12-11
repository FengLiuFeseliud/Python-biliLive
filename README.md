# biliLive

bilibili Python 弹幕机框架，使用代码快速塔建b站弹幕机，实现完全自定义

## **更新**

### v0.3.0

1，引入 [websocket-client](https://github.com/websocket-client/websocket-client) 库实现长连接，获取更多数据

2，事件 Event 添加更多事件，收到礼物，上舰，获取人气，粉丝数更新，热门榜等等...

### v0.2.0

1，点歌模块 PlayCloudMusic， 点歌模块事件 MusicEvent

2， 将直播间事件分离出 Live 类 加入直播间事件 Event

3， 加入 LiveLog  一行设置输出统一格式 并将输出内容保存进文件 （同样支持自定义）

4，send_msg_loop 更名为 time_loop，sendMsgList 更名为 timeLoopList

## **安装**

```python
pip install biliLive
```

点歌模块播放使用 pydub 使用请安装依赖 ffmpeg，pyaudio

注意 pyaudio 必须去下面下载 然后使用 `pip install pyaudio的下载路径` 安装

https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

ffmpeg 这个估计都有 没有的话下载解压将 ffmpeg 目录下的 bin 文件夹加入环境变量

https://ffmpeg.org/download.html

## **简单使用**

```python
from biliLive import BiliApi, commandList, liveLog

"""
设置一个打印字符串到终端的指令 名为 /text
指令格式: /text 要打印的字符串
并每12秒发送弹幕 弹幕内容: "12s sendMsg"
保存日志到 ./log
"""

# 一行设置输出统一格式 并将输出内容保存进文件
liveLog()

# 默认请求头
headers = BiliApi.bilibili_headers
headers["cookie"] += "用户cookie"
api = BiliApi(headers)

# 指令方法 /text
def text(commKey, msg):
    # commKey 是后面空格的参数
    # 如/text xxx xxx xxx 后面的[xxx, xxx, xxx]
    # msg 当前执行该指令的弹幕
    print(f"打印字符串 -> {commKey[0]}")

# 实列化弹幕指令对像 commandList
MyCommandList = commandList()

# 绑定方法 /text
MyCommandList.command = {
    # 指令 /text
    "text": text
}

# 定时发送
MyCommandList.timeLoopList = {
    # 秒数: 要执行的
    # 为字符串时视为发送弹幕
    12: "12s sendMsg"
}

# 连接房间
live = api.live("房间号")
# 绑定指令对像到房间
live.bind(MyCommandList)

# 开启弹幕轮查
live.msg_loop()
# 开启定时发送
live.time_loop()
# 堵塞主线程
input("")
```



## **设置弹幕指令**

```python
from biliLive import BiliApi, commandList

api = BiliApi()
live = api.live("房间号")

# 实列化弹幕指令对像 CommandList
commandList = commandList()

# 指令标志符号
commandList.commandSign
# Live 对象绑定的直播间事件
commandList.event

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

# 定时执行
commandList.timeLoopList = {
    秒数: 绑定方法
}

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

# 连接房间
live = api.live("房间号")
# 绑定指令对像到房间
live.bind(commandList)

# 开启弹幕轮查
live.msg_loop()
# 开启定时发送
live.time_loop()
# 堵塞主线程
input("")
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
> ## **日志操作 LiveLog 对象**
>
> 实现所有输出统一格式  如： [时间] 输出内容
>
> 并根据设置 保存日志到不同txt文件
>
> 如何使用？ 很简单全部使用默认设置只用在入口文件上面 实列化 liveLog 对象
>
> ```python
> from biliLive import liveLog
> import time
> 
> # 日志输出
> liveLog()
> # 实列化完成后所有 print 输出都会被统一格式后打印到控制台
> # 并且所有 print 输出都会被保存进txt文件
> 
> print("我要出门了!!!")
> # 休息3秒
> time.sleep(3)
> print("我出门回来了!!!")
> print("什么? 你说我3秒就回来了?")
> print("因为我是超能力者啊 xD")
> ```
>
> `liveLog(save_in="./log")` 
>
> **参数说明：**
>
> save_in：日志文件保存目录
>
> 
>
> 不满足默认设置？ 可以自行设置，内部方法已经封装好了 只用管设置
>
> ## **继承 LiveLog 类自定义实现直播间事件**
>
> ```python
> from biliLive import LiveLog
> import time
> 
> class MyLiveLog(LiveLog):
> 
>  def set_log_style(self, log):
>      """
>      设置日志格式
>      默认: "[%H:%M:%S] 内容"
>      """
>      # 将日志格式修改为 "{%Y-%m-%d %H:%M:%S} 内容"
>      log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
>      log_msg = "{%s} %s" % (log_time, log)
>      return log_msg
> 
>  def set_log_path(self):
>      """
>      设置日志文件名格式
>      self.save_in 为设置的日志保存路径
>      默认: "{self.save_in}/log_%Y_%m_%d_%H_%M_%S.txt"
>      """
>      # 将日志文件名格式修改为 "{self.save_in}/logfile_%H_%M_%S_%Y_%m_%d_.txt"
>      return time.strftime(f"{self.save_in}/logfile_%H_%M_%S_%Y_%m_%d_.txt", time.localtime())
> 
> # 日志输出
> MyLiveLog()
> # 实列化完成后所有 print 输出都会被统一格式后打印到控制台
> # 并且所有 print 输出都会被保存进txt文件
> 
> print("我要出门了!!!")
> time.sleep(0.5)
> print("我出门回来了!!!")
> print("什么? 你说我0.5就回来了?")
> print("因为我是超能力者啊 xD")
> ```
>
> 
>
> # 以下重点！！！
>
> **以下重点！！！ 以下重点！！！ 以下重点！！！ 以下重点！！！**
>
> ## **弹幕机 live 对象**
>
> 使用`biliApi.live()` 实例化
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
> `live.bind(commandList=None, event=None)`  绑定事件到直播间
>
> ### 参数:
>
> commandList：自定义指令对象
>
> event：自定义直播间事件对象
>
> 
>
> 使用`biliApi.live()` 快速实例化的只用以下两方法
>
> 需要细节操作请继承 Live 类自定义实现
>
> `live.msg_loop()` 开启弹幕轮查
>
> `live.send_msg_loop()` 开启定时发送
>
> ## **Event 对象**
>
> 直播间事件对象，可以导入 event 快速实例化，然后对其重新设置
>
> 也可以继承 Event 一次性设置多个事件
>
> 别忘了最后调用` live.bind()`绑定事件到直播间！！！
>
> ## **继承 Event 类自定义实现直播间事件**
>
> ```python
> from biliLive import BiliApi, commandList, Event, liveLog
> 
> # 日志输出
> liveLog()
> 
> # 继承创建直播间事件
> class MyEvent(Event):
> 
>      def set_command_list(self, msg, commandSign):
>          """
>          设置指令格式, 默认使用 任意指令标识符, 参数空格隔开
>          叁数:
>          msg: 弹幕数据列表
>          commandSign: 当前绑定的指令标识符
>          需返回: 指令标识符, 无标识符的指令字段, 指令参数
>          """
>          return super().set_command_list(msg, commandSign)
> 
>      def send_msg(self, msg):
>          """
>          send_msg 发送弹幕\n
>          父类参数: self.id , self._getMsgStyle(msg)
>          self._getMsgStyle: 用户当前弹幕样式
>          self.id: 房间号
>          """
>          print("我要向直播间发送弹幕了!!!")
>          return super().send_msg(msg)
> 
>      def msg_loop(self):
>          """
>          事件 msg_loop 启动弹幕轮查
>          """
>          print("msg_loop 弹幕轮查准备启动!!!")
>          return super().msg_loop()
> 
>      def time_loop(self):
>          """
>          事件 time_loop 启动定时发送
>          """
>          print("time_loop 定时发送准备启动!!!")
>          return super().time_loop()
> 
>      def msg_log(self, msg):
>          """
>          事件 msg_log 新弹幕会经过这里
>          """
>          print("有新弹幕出现辣!")
>          return super().msg_log()
> 
>      def command_err_log(self, code, msg, comm):
>          """
>          事件 command_err_log 指令执行错误
>          叁数:
>          code: 状态码
>          msg: 弹幕
>          comm: 执行的指令
>          """
>          print("事件 command_err_log 指令执行错误")
>          return super().command_err_log(code, msg, comm)
> 
>  	def command_log(self, code, msg, comm):
>          """
>          事件 command_log 指令执行成功
>          叁数:
>          code: 状态码
>          msg: 弹幕
>          comm: 执行的指令
>          """
>          print("事件 command_log 指令执行成功")
>          return super().command_log(code, msg, comm)
>         
>     """
>     以下为0.3.0新增事件 (太长了以下复制的源码 
>     实际不改输出直接用 super() 就行)
>     """
> 
> 	def welcome(self, msg):
>         """
>         事件 welcome 普通用户进入房间
>         """
>         msg = format.welcome(msg)
>         print("%s 进入了房间!" % msg["userName"])
>     
>     def welcome_guard(self, msg):
>         """
>         事件 welcome_guard 老爷用户进入房间
>         """
>         print(msg)
> 
>     def entry_effect(self, msg):
>         """
>         事件 entry_effect 舰长进入房间(不确定)
>         """
>         msg = format.entry_effect(msg)
>         print(msg["copy_writing"])
> 
>     def super_msg(self, msg):
>         """
>         事件 super_msg SC留言
>         """
>         msg = format.super_msg(msg)
>         print("%s发送了价值%s的SE! 时长%s: %s" % (msg["userName"], msg["price"], 
>                                     msg["endTime"], msg["msg"]))
> 
>     def send_gift(self, msg):
>         """
>         事件 send_gift 投喂礼物
>         """
>         msg = format.send_gift(msg)
>         print("%s%s了%s个%s!" % (msg["userName"], msg["action"], msg["num"], msg["giftName"]))
> 
>     def combo_send_gift(self, msg):
>         """
>         事件 combo_send_gift 连击投喂礼物
>         """
>         msg = format.send_gift(msg)
>         print("%s连击%s了%s个%s!" % (msg["userName"], msg["action"], msg["num"], msg["giftName"]))
>     
>     def send_gift_game(self, msg):
>         """
>         事件 send_gift_game 直播游戏
>         """
>         msg = format.send_gift(msg)
>         print("%s送了%s个%s!" % (msg["userName"], msg["num"], msg["giftName"]))
> 
>     def anchor_lot_start(self, msg):
>         """
>         事件 anchor_lot_start 天选之人开始
>         """
>         print(msg)
> 
>     def anchor_lot_end(self, msg):
>         """
>         事件 anchor_lot_end 天选之人结束
>         """
>         print(msg)
> 
>     def anchor_lot_award(self, msg):
>         """
>         事件 anchor_lot_award 天选之人结果
>         """
>         msg, list_str = format.anchor_lot_award(msg), ""
>         for uesr in msg["userList"]:
>             list_str += uesr["uname"]
>         print("天选之人 %s 结果: %s" % (msg["name"], list_str))
> 
>     def guard_buy(self, msg):
>         """
>         事件 guard_buy 上舰长
>         """
>         msg = format.guard_buy(msg)
>         print("%s开通了%s月%s" % (msg["userName"], msg["num"], msg["giftName"]))
> 
>     def guard_renew(self, msg):
>         """
>         事件 guard_renew 续费了舰长
>         """
>         print(msg)
>     
>     def notice_msg(self, msg):
>         """
>         事件 notice_msg 大公告
>         """
>         print(msg)
> 
>     def activity_banner_update(self, msg):
>         """
>         事件 activity_banner_update 小时榜变动
>         """
>         print(msg)
> 
>     def room_data_update(self, msg):
>         """
>         事件 room_data_update 粉丝关注变动
>         """
>         msg = format.room_data(msg)
>         print("关注变动! 关注数:%s 粉丝团人数:%s" % (msg["fans"], msg["fansClub"]))
>     
>     def online_rank(self, msg):
>         """
>         事件 online_rank 高能榜变更
>         """
>         msg, data = msg['data']['list'], ""
>         for user in msg:
>             data += " %s-%s " % (user["uname"], user["score"])
>         print("高能榜变更! %s" % data)
>     
>     def live_rank(self, msg):
>         """
>         事件 live_rank 主播榜变更
>         """
>         print("主播现在排在%s!" % msg["data"]["count"])
>     
>     def hot_rank(self, msg):
>         """
>         事件 hot_rank 热门榜变更
>         """
>         msg = format.hot_rank(msg)
>         print("主播现在%s排在%s!" % (msg["rankDesc"], msg["rank"]))
>     
>     def activity(self, msg):
>         """
>         事件 activity 活动内容变更
>         我估计这里一直会变直接留空了 需要的写
>         """
>         pass
>     
>     def hot_rank_changed(self, msg):
>         """
>         事件 hot_rank_changed 热门榜计数? (不清楚能干嘛)
>         """
>         pass
> 
>     def hot_rank_settlement(self, msg):
>         if msg["cmd"] == "HOT_RANK_SETTLEMENT":
>             return
>         
>         msg = format.hot_rank_settlement(msg)
>         print(msg["rankDesc"])
> 
>     def stop_live_room_list(self, msg):
>         """
>         事件 stop_live_room_list 停止直播室名单 (下播名单?)
>         """
>         pass
>     
>     def popularity_update(self, popularity):
>         """
>         事件 popularity_update 心跳回应更新人气值
>         """
>         print("当前人气值: %s" % popularity)
>     
>     def pk_battle_process(self, msg):
>         """
>         事件 pk_battle_process pk数据
>         """
>         print(msg)
> 
>     def pk_battle_process_new(self, msg):
>         """
>         事件 pk_battle_process_new pk数据新
>         """
>         print(msg)
> 
>     def pk_battle_process_final(self, msg):
>         """
>         事件 pk_battle_process_final pk决赛
>         """
>         print(msg)
> 
>     def pk_battle_end(self, msg):
>         """
>         事件 pk_battle_end pk结束
>         """
>         print(msg)
> 
>     def pk_battle_settle_user(self, msg):
>         """
>         事件 pk_battle_settle_user pk结算
>         """
>         print(msg)
> 
>     def pk_battle_settle(self, msg):
>         """
>         事件 pk_battle_settle pk结算
>         """
>         print(msg)
> 
>     def common_notice_danmaku(self, msg):
>         """
>         事件 common_notice_danmaku pk连胜
>         """
>         print(msg)
>     
>     def miscellaneous(self, msg):
>         """
>         事件 miscellaneous 未知事件全部会调用
>         """
>         print("未知信息...")
> 
> 
> # 实例化
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> MyCommandList = commandList()
> 
> # 指令方法 /text
> def text(commKey, msg):
> 	print(f"打印字符串 -> {commKey[0]}")
> 
> # 绑定方法 /text
> MyCommandList.command = {
> 	"text": text
> }
> 
> # 定时发送
> MyCommandList.timeLoopList = {
> 	12: "12s sendMsg"
> }
> 
> # 连接直播间
> live = api.live("房间号")
> # 绑定 MyCommandList MyEvent 到直播间
> live.bind(MyCommandList, MyEvent())
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop()
> # 开启定时发送
> live.time_loop()
> # 堵塞主线程
> input("")
> ```
>
> 
>
> ## **项目地址有演示文件可以查看** !!!!
>
> ## **格式化数据 format 类**
>
> format 方法全部为静态用于各种数据格式化方便调用
>
> ```python
> from biliLive import format
> 
> 
> class format:
>     """
>     数据格式化
>     """
> 
>     @staticmethod
>     def msg(data):
>         """
>         弹幕数据
>         msg: 内容
>         userId: 用户id
>         userName: 用户名
>         badge: 用户粉丝牌子
>         level: 用户直播用户等级
>         time: 时间
>         color: 弹幕颜色
>         """
>         ...
>     
>     @staticmethod
>     def send_gift(data):
>         """
>         送礼物数据
>         action: 动作
>         giftId: 礼物id
>         giftName: 礼物名称
>         num: 送礼物数量
>         userName: 用户名
>         userId: 用户id
>         medal_info: 用户粉丝牌子
>         """
>         ...
>     
>     @staticmethod
>     def welcome(data):
>         """
>         普通用户进入房间数据
>         userName: 用户名
>         userId: 用户id
>         medal: 用户粉丝牌子
>         roomId: 直播间id
>         time: 时间
>         """
>         ...
> 
>     @staticmethod
>     def entry_effect(data):
>         """
>         舰长进入房间数据
>         copy_writing: 进入房间消息
>         userId: 用户id
>         basemap: 进入房间消息背景
>         face: 用户头像
>         privilegeType: 舰长类型
>         time: 时间
>         """
>         ...
>     
>     @staticmethod
>     def room_data(data):
>         """
>         房间关注更新数据
>         roomId: 房间号
>         fans: 关注数
>         fansClub: 粉丝团人数
>         """
>         ...
>     
>     @staticmethod
>     def hot_rank(data):
>         """
>         热门榜更新数据
>         rank: 排名
>         name: 榜单名
>         rankDesc: 榜单简介
>         icon: 图标
>         time: 时间
>         """
>         ...
>         
>     @staticmethod
>     def hot_rank_settlement(data):
>         """
>         进入限时热门榜总榜数据
>         rank: 排名
>         name: 榜单名
>         rankDesc: 榜单简介
>         icon: 图标
>         time: 时间
>         """
>         ...
> 
>     @staticmethod
>     def super_msg(data):
>         """
>         SC留言数据
>         background: SC背景样式
>         userName: 用户名
>         level: 用户直播用户等级
>         userId: 用户id
>         giftId: 礼物id
>         giftName: 礼物名称
>         num: 送礼物数量
>         medal: 用户粉丝牌子
>         msg: 内容
>         price: 价格
>         time: SC开始显示时间
>         endTime: SC时长
>         """
>         ...
> 
>     @staticmethod
>     def my_room_guard_renew(data):
>         """
>         自动续费舰长
>         userName: 用户名
>         icon: 图标
>         msgSelf: 自动续费舰长消息
>         roomid: 房间号
>         type: 舰长类型
>         """
>         ...
>     
>     @staticmethod
>     def guard_buy(data):
>         """
>         开通舰长数据
>         userName: 用户名
>         userId: 用户id
>         giftName: 舰长类型
>         giftId: 礼物id
>         num: 开通月数?
>         time: 开始时间
>         endTime: 结束时间
>         """
>         ...
>     
>     @staticmethod
>     def anchor_lot_award(data):
>         """
>         天选之人结果数据
>         name: 天选之人标题
>         num: 数量
>         image: 图片?
>         userList: 中奖用户名单
>         """
>         ...
> ```
>
> 
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
> 
>
> 别忘了最后调用` live.bind()`绑定事件到直播间！！！
>
> ```python
> from biliLive import BiliApi, commandList
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += "用户cookie"
> api = BiliApi(headers)
> 
> # 直接实例化 指令对象
> MyCommandList = commandList()
> # 设置指令标记符 (默认为 / )
> MyCommandList.commandSign = "#"
> 
> # 方法 text
> def text(commKey, msg):
> print(f"打印字符串 -> {commKey[0]}")
> 
> # 方法 ptext
> def ptext(commKey, msg):
> print(f"权限指令 打印字符串 -> {commKey[0]}")
> 
> # 绑定方法 text 为指令 #text
> MyCommandList.command = {
> "text": text,
> # 绑定方法 ptext 为指令 #ptext
> "ptext": ptext
> }
> 
> # 设置权限用户
> MyCommandList.purview = [
> 34394509 # 用户uid
> ]
> 
> # 设置将指令设置为权限指令
> MyCommandList.purviewCommand = [
> # 将指令 #ptext 设置为权限指令
> "ptext"
> ]
> 
> # 定时发送
> MyCommandList.timeLoopList = {
> 12: "12s sendMsg"
> }
> 
> # 指令参数方法
> def commandError():
> print("commandError了啊 不会看指令文档???")
> return 0
> 
> # 不绑定 默认发送弹幕提醒
> 
> # 指令参数错误执行
> MyCommandList.commandError = commandError
> # 指令错误执行
> MyCommandList.commandNameError = 绑定方法
> # 权限不足执行
> MyCommandList.purviewError = 绑定方法
> 
> # 连接直播间
> live = api.live("房间号")
> # 绑定 MyCommandList 到直播间
> live.bind(MyCommandList)
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop()
> # 开启定时发送
> live.time_loop()
> # 堵塞主线程
> input("")
> ```
>
> 
>
> ## **继承 CommandList 类自定义实现指令对象**
>
> ```python
> from biliLive import BiliApi, CommandList
> 
> # 继承创建指令对象
> class MyCommandList(CommandList):
> 
> 	def __init__(self, BiliLive):
>   	 super().__init__(BiliLive)
> 		 # 可以在内部设置指令 也可以外部
>       self.commandSign = "#"
>       self.purview = [
>           ...
>       ]
>       self.purviewCommand = [
>           "print"
>       ]
>       self.command = {
>           "text": self.text,
>           "print": self.print
>       }
> 
>   def text(self, commKey, msg):
>       print(f"打印字符串 -> {commKey[0]}")
> 
>   def ptext(self, commKey, msg):
>       print(f"purviewCommand 打印字符串 -> {commKey[0]}")
> 
>   def commandError(self):
>       """
>       commandError 指令参数错误
>       调用父类 commandError()
>       """
>       return super().commandError()
> 
>   def commandNameError(self):
>       """
>       commandNameError 指令名字错误
>       调用父类 commandNameError()
>       """
>       return super().commandNameError()
> 
>   def purviewError(self):
>       """
>       purviewError 指令权限错误
>       调用父类 purviewError()
>       """
>       return super().purviewError()
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
> # 绑定 MyCommandList 到直播间
> live.bind(MyCommandList)
> 
> # 运行...
> 
> # 开启弹幕轮查
> live.msg_loop()
> # 开启定时发送
> live.time_loop()
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
> ## 以下是一些功能性模块 用来方便实现功能 也可以自己做
>
> ## **点歌 PlayCloudMusic 对象**
>
> 该类使用了 pycloudmusic163 库 实现了基于网易云音乐的歌曲下载与查询 播放 
>
> pycloudmusic163 库也是我做的 有兴趣可以去看看其他使用方法
>
> pycloudmusic163：https://github.com/FengLiuFeseliud/pycloudmusic163
>
> PlayCloudMusic 继承了 pycloudmusic163 库的 Music163 
>
> 因此可以在其内部直接使用 `self` 调用 Music163 的方法
>
> 
>
> ` PlayCloudMusic(play_path, not_play_music_in_playlist=None, cookie="")` 点歌模块
>
> play_path：下载歌曲的目录 (用于播放)
>
> not_play_music_in_playlist：空闲歌单 没人点歌随机播放该歌单
>
> cookie：网易云用户cookie
>
> ```python
> import time
> from biliLive import *
> 
> # 以下就都可以点歌了 当然肯定是绑定指令后使用...
> 
> # 实例化点歌模块
> # https://music.163.com/#/playlist?id=738561159
> play_list = PlayCloudMusic("./music_play", "6787578252", "网易云用户cookie")
> 
> # 闲置状态下缓存多少歌曲 默认两首 两首正好一首播一首下
> play_list.play_list_cache_len = 2
> 
> # 下载线程每隔多久检查有新任务 默认5秒 太快会bug 播放线程抢不过下载线程 一直卡播放
> # 没必要太快 3 2分钟都行 因为下一次是整个列表全部下载 播放线程播放已经下载好的
> play_list.download_music_loop_sleep = 5
> 
> 
> # 创建点歌线程
> play_list.download_music_loop()
> # 创建下载线程
> play_list.play_music_loop()
> 
> # 模拟ID点歌
> # https://music.163.com/#/song?id=1436950545
> 
> # 先休息5秒等前面两个线程执行
> time.sleep(5)
> play_list.send_music(1436950545, None)
> 
> # 堵塞主线程
> input("")
> ```
>
> 
>
> `PlayCloudMusic.get_all_play_music()` 返回下载队列和播放队列
>
> `PlayCloudMusic.play_music_loop_stop()`  关闭播放队列
>
> `PlayCloudMusic.download_music_loop_in()` 关闭下载队列
>
> `PlayCloudMusic.play_music_loop()`  开启播放队列
>
> `PlayCloudMusic.download_music_loop()` 开启下载队列
>
> `PlayCloudMusic.bind(musicEvent_)`  绑定事件到当前类
>
> 
>
> ## **如何用弹幕指令调用这个模块呢？ 很简单**
>
> ```python
> from pycloudmusic163.music163 import LoginMusic163, Music163
> from biliLive import *
> 
> # 一行设置输出统一格式 并将输出内容保存进文件
> liveLog()
> 
> # 在指令用点歌 肯定要设置指令 这里使用继承创建
> 
> # 继承创建指令对象
> class MyCommandList(CommandList):
> 
>  def __init__(self):
>      super().__init__()
> 
>      # 默认指令标识符
>      self.commandSign = "/"
> 
>      # 绑定指令
>      self.command = {
>          # 现在点歌指令为 /点歌
>          "点歌": self.add_music_func,
>          # 现在取消点歌指令为 /取消点歌
>          "取消点歌": self.del_play_music
>      }
> 
>      # 实例化点歌模块
>      self.play_list = PlayCloudMusic("./music_play", "6787578252", r"用户cookie")
> 
>      # 使用默认点歌模块事件绑定给 PlayCloudMusic 对象
>      self.play_list.bind(musicEvent())
>      self.play_list.play_list_cache_len = 2
> 
>      # 创建点歌线程
>      self.play_list.download_music_loop()
>      # 创建下载线程
>      self.play_list.play_music_loop()
> 
>  # 指令默认参数commKey, msg
>  # commKey: 指令参数
>  # msg: 弹幕数据
> 
>  # 指令 /点歌
>  def add_music_func(self, commKey, msg):
>      # 直接调用 PlayCloudMusic.send_music(music,msg) 来发送任务
>      # PlayCloudMusic.send_music(music,msg) 会转去调用点歌事件的 send_music
>      self.play_list.send_music(commKey[0], msg)
> 
>  # 指令 /取消点歌
>  def del_play_music(self, commKey, msg):
>      # 直接调用 PlayCloudMusic.del_play_music(msg) 来删除任务
>      # 和 PlayCloudMusic.send_music(music,msg) 一样也会转去调用点歌事件的方法
>      # PlayCloudMusic.del_play_music(msg) 会去调用点歌事件的 del_play_music(msg)
>      # 调用点歌事件的 del_play_music(msg) 可以格式化数据
> 
>      # 返回值 True 有任务被删除了 False 没有任务被删除
>      del_in = self.play_list.del_user_music(msg)
>      if not del_in:
>          # 调用直播间事件发送弹幕
>          self.event.send_msg("大哥! 您还没点歌啊 怎么取消？")
> 
>  def commandError(self):
>      return super().commandError()
> 
>  def commandNameError(self):
>      return super().commandNameError()
> 
>  def purviewError(self):
>      return super().purviewError()
> 
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += open("cookie.txt", "r").read()
> api = BiliApi(headers)
> 
> # 设置直播间
> live = api.live("5545364")
> live.bind(MyCommandList())
> 
> # 运行...
> 
> live.msg_loop()
> live.time_loop()
> 
> # 堵塞主线程
> input("")
> ```
>
> 以上！ 你就有了一个带日志保存的只点歌的弹幕机纯代码只需46行！
>
> ```python
> from pycloudmusic163.music163 import LoginMusic163, Music163
> from biliLive import *
> 
> 
> liveLog()
> class MyCommandList(CommandList):
> 
>  def __init__(self):
>      super().__init__()
>      self.commandSign = "/"
>      self.command = {
>          "点歌": self.add_music_func,
>          "取消点歌": self.del_play_music
>      }
> 
>      self.play_list = PlayCloudMusic("./music_play", "6787578252", r"用户cookie")
>      self.play_list.bind(musicEvent())
>      self.play_list.play_list_cache_len = 2
>      self.play_list.download_music_loop()
>      self.play_list.play_music_loop()
> 
>  def add_music_func(self, commKey, msg):
>      self.play_list.send_music(commKey[0], msg)
> 
>  def del_play_music(self, commKey, msg):
>      del_in = self.play_list.del_user_music(msg)
>      if not del_in:
>          self.event.send_msg("大哥! 您还没点歌啊 怎么取消？")
> 
>  def commandError(self):
>      return super().commandError()
> 
>  def commandNameError(self):
>      return super().commandNameError()
> 
>  def purviewError(self):
>      return super().purviewError()
> 
> headers = BiliApi.bilibili_headers
> headers["cookie"] += open("cookie.txt", "r").read()
> api = BiliApi(headers)
> live = api.live("5545364")
> live.bind(MyCommandList())
> live.msg_loop()
> live.time_loop()
> input("")
> ```
>
> 
>
> ## **点歌事件 musicEvent 对象**
>
> 这个类一样有很多点歌事件 可以自定义 如下
>
> 别忘了  musicEvent 对象要用 `PlayCloudMusic.bind()`  绑定事件到点歌模块！！！
>
> ```python
> from biliLive import *
> 
> class MyMusicEvent(MusicEvent):
> 
>  # 只有一个属性  self.api = None 绑定后为 点歌模块实例
>  # 内部使用 self.api 就可以调用
> 
>  def cookie_invalidation(self, code):
>      """
>      事件 cookie_invalidation cookie无效时被调用
>      """
>      return super().cookie_invalidation(code)
> 
>  def set_msuic_file_name(self, music_object):
>      """
>      设置缓存音乐文件名
>      事件参数:
>      music_object: music 对像
>      """
>      return super().set_msuic_file_name(music_object)
> 
>  def send_music(self, msuic, msg):
>      """
>      事件 send_music 向下载队列发送任务
>      """
>      return super().send_music(msuic, msg)
> 
>  def set_music_name(self, music_object):
>      """
>      设置打印音乐字符串
>      事件参数:
>      music_object: music 对像
>      """
>      return super().set_music_name(music_object)
> 
>  def add_music(self, music_object, play_list, download_music_list):
>      """
>      事件 add_music 下载队列被添加任务
>      事件参数:
>      music_object: music 对像
>      play_list: 播放队列
>      download_music_list: 下载队列
>      """
>      return super().add_music(music_object, play_list, download_music_list)
> 
>  def play_music(self, music_object, play_list, download_music_list):
>      """
>      事件 play_music 播放队列准备播放
>      事件参数:
>      music_object: music 对像
>      play_list: 播放队列
>      download_music_list: 下载队列
>      """
>      return super().play_music(music_object, play_list, download_music_list)
> 
>  def download_music(self, music_object, play_list, download_music_list):
>      """
>      事件 download_music 下载队列成功下载完成一条任务
>      事件参数:
>      music_object: music 对像
>      play_list: 播放队列
>      download_music_list: 下载队列
>      """
>      return super().download_music(music_object, play_list, download_music_list)
> 
>  def download_music_err(self, code, music_object, play_list, download_music_list):
>      """
>      事件 download_music_err 下载队列下载失败
>      事件参数:
>      code: 状态码
>      music_object: music 对像
>      play_list: 播放队列
>      download_music_list: 下载队列
>      """
>      return super().download_music_err(code, music_object, play_list, download_music_list)
> 
>  def del_play_music(self, msg):
>      """
>      默认取消点歌, 不能取消正在IO的任务
>      需返回: music 对象, 从哪个队列删除数据
>      之后只用调用 PlayCloudMusic.del_play_music() 删除
>      """
>      return super().del_play_music(msg)
> ```
>
> 
>
> ## **项目地址有演示文件可以查看** !!!!
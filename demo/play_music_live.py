import time
from pycloudmusic163.music163 import LoginMusic163, Music163
from biliLive import BiliApi
from biliLive import CommandList, MusicEvent
from biliLive.bilibiliApi import event
from biliLive.music import PlayCloudMusic


"""
快速创建自定义支持点歌弹幕机的 demo

使用网易云音乐API, 这个库也是我的
网易云音乐API 项目地址:
https://github.com/FengLiuFeseliud/pycloudmusic163
"""

# 继承创建点歌事件
class MyMusicEvent(MusicEvent):
    
    def cookie_invalidation(self, code):
        """
        事件 cookie_invalidation cookie 无效时被调用

        内容其实是用 pycloudmusic163 尝试获取登录用的信息
        如果 cookie 无效时自然没有数据
        """

        """
        cookie 无效时需要新 cookie 的话
        可以在这里写自动登录操作
        pycloudmusic163 库支持以下登录:

        邮箱密码登录
        手机密码登录
        手机验证码登录
        二维码登录
        """

        pass

    def add_music(self, music_object, play_list, download_music_list):
        """
        事件 add_music 下载队列被添加任务
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        return super().add_music(music_object, play_list, download_music_list)

    def del_play_music(self, msg):
        """
        默认取消点歌, 不能取消正在IO的任务
        需返回: music 对象, 从哪个队列删除数据
        之后只用调用 PlayCloudMusic.del_play_music() 删除
        """
        return super().del_play_music(msg)
    
    def set_music_name(self, music_object):
        """
        设置打印音乐字符串
        事件参数:
        music_object: music 对像
        """
        return super().set_music_name(music_object)
    
    def send_music(self, msuic, msg):
        """
        事件 send_music 向下载队列发送任务
        """
        return super().send_music(msuic, msg)
    
    def set_msuic_file_name(self, music_object):
        """
        设置缓存音乐文件名
        事件参数:
        music_object: music 对像
        """

        # 修改原 set_msuic_file_namec 的文件名
        # 不要这样设置文件名 几率报错
        # 报错原因是 music_object.name_str 不处理会有特殊符号被加入文件名报错
        # 这里只是为了演示文件名设置
        return "%s_%s.mp3" % (music_object.id, music_object.name_str)
    
    def play_music(self, music_object, play_list, download_music_list):
        """
        事件 play_music 播放队列准备播放
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """

        # 修改原 play_music 的打印
        print("play_music: 我负责播放 下载不是我的事... 呜")
    
    def download_music(self, music_object, play_list, download_music_list):
        """
        事件 download_music 下载队列成功下载完成一条任务
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """

        # 修改原 download_music 的打印
        print("别急 下载队列在播放队列播放时又偷偷下载了一条数据了!!!")
    
    def download_music_err(self, code, music_object, play_list, download_music_list):
        """
        事件 download_music_err 下载队列下载失败
        事件参数:
        code: 状态码
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        return super().download_music_err(code, music_object, play_list, download_music_list)


# 继承创建指令对象
class MyCommandList(CommandList):

    def __init__(self):
        super().__init__()

        # 默认指令标识符
        self.commandSign = "/"

        # 绑定指令
        self.command = {
            "点歌": self.add_music_func,
            "取消点歌": self.del_play_music
        }
        
        # 实例化点歌模块
        # https://music.163.com/#/playlist?id=738561159

        self.play_list = PlayCloudMusic("./music_play", "6787578252", login_music163())
        self.play_list.playlist(self.play_list)

        # 将自定义点歌模块事件绑定给 PlayCloudMusic 对象
        self.play_list.bind(MyMusicEvent())
        self.play_list.play_list_cache_len = 2

        # 创建点歌线程
        self.play_list.download_music_loop()
        # 创建下载线程
        self.play_list.play_music_loop()
    
    # 指令默认参数commKey, msg
    # commKey: 指令参数
    # msg: 弹幕数据

    # 指令 /点歌
    def add_music_func(self, commKey, msg):
        # 直接调用 PlayCloudMusic.send_music(music,msg) 来发送任务
        # PlayCloudMusic.send_music(music,msg) 会转去调用点歌事件的 send_music
        self.play_list.send_music(commKey[0], msg)

    # 指令 /取消点歌
    def del_play_music(self, commKey, msg):
        # 直接调用 PlayCloudMusic.del_play_music(msg) 来删除任务
        # 和 PlayCloudMusic.send_music(music,msg) 一样也会转去调用点歌事件的方法
        # PlayCloudMusic.del_play_music(msg) 会去调用点歌事件的 del_play_music(msg)
        # 调用点歌事件的 del_play_music(msg) 可以格式化数据
        
        # 返回值 True 有任务被删除了 False 没有任务被删除
        del_in = self.play_list.del_user_music(msg)
        if not del_in:
            # 调用直播间事件发送弹幕
            self.event.send_msg("大哥! 您还没点歌啊 怎么取消？")

    def commandError(self):
        return super().commandError()
    
    def commandNameError(self):
        return super().commandNameError()
    
    def purviewError(self):
        return super().purviewError()


def login_music163():
    with open("music163_cookie.txt", "r") as file:
        cookie = file.read()
        headers = Music163.music163_headers
        headers["cookie"] += cookie
        music163 = Music163(headers)
    
    my = music163.my()
    # 如果 cookie 无效, 进行二维码登录
    if type(my) == int:
        login = LoginMusic163()
        key = login.login_qr_key()
        print(key[1])
        while True:
            code, music163, cookie = login.login_qr(key)
            if code == 803:
                my = music163.my()
                print(my.name, my.signature, my.id)
                break
                
            time.sleep(2)
    else:
        return cookie

    with open("music163_cookie.txt", "w") as file:
        file.write(cookie)

    return cookie


# 实际化弹幕机

headers = BiliApi.bilibili_headers
headers["cookie"] += open("cookie.txt", "r").read()
api = BiliApi(headers)

live = api.live("5545364")

# 绑定自定义 MyCommandList
live.bind(MyCommandList(), event())

# 运行...

live.msg_loop()
live.send_msg_loop()
input()
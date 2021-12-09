from abc import ABCMeta, abstractmethod
from pycloudmusic163 import Music163
import pycloudmusic163.object as object
from threading import Thread
from pydub import AudioSegment
from pydub.playback import play
import random, time

class PlayCloudMusic(Music163):

    def __init__(self, play_path, not_play_music_in_playlist=None, cookie=""):
        super().__init__(headers=None)
        headers = Music163.music163_headers
        headers["cookie"] += cookie
        self.headers = headers
        self.__not_play_music_in_playlist = self.playlist(not_play_music_in_playlist)
        self.__play_music_loop_in = False
        self.__play_path = play_path
        self.__play_list = []
        self.__download_music_loop_in = False
        self.__download_music_list = []
        # 闲置状态下缓存多少歌曲
        self.play_list_cache_len = 1
        # 下载线程每隔多久检查有新任务
        self.download_music_loop_sleep = 5
        # 点歌事件类
        self.__musicEvent = None
        self.bind()
    
    def bind(self, musicEvent_=None):
        """
        绑定事件到当前类
        """
        if musicEvent_ is None:
            self.__musicEvent = musicEvent()
            self.__musicEvent.api = self
        else:
            self.__musicEvent = musicEvent_
            self.__musicEvent.api = self
        
        # 事件 cookie_invalidation 检查cookie
        code = self.my()
        if type(code) != object.my:
            self.__musicEvent.cookie_invalidation(code)

    def _add_music(self, music_object, msg):
        if type(music_object) != object.music:
            music_object = object.music(self.headers, music_object)
        self.__download_music_list.append((music_object, msg))
        # 调用 add_music 事件
        self.__musicEvent.add_music(music_object, self.__play_list,
                                                                    self.__download_music_list)
        return 0

    
    def send_music(self, msuic, msg):
        """
        向下载队列发送任务 使用 musicEvent 对象 send_music
        """
        return self.__musicEvent.send_music(msuic, msg)
    
    def get_all_play_music(self):
        """
        返回下载队列和播放队列
        """
        return self.__play_list, self.__download_music_list

    def del_user_music(self, msg):
        """
        从下载队列和播放队列删除任务
        """
        data = self.__musicEvent.del_play_music(msg)
        if data is None:
            return False

        music, in_play_list = data
        if in_play_list == "play_list":
            self.__play_list.remove(music)
            return True
        
        if in_play_list == "download_music_list":
            self.__download_music_list.remove(music)
            return True
        
        return False
    
    def play_music_loop_in(self):
        return self.__play_music_loop_in
    
    def download_music_loop_in(self):
        return self.__download_music_loop_in
    
    def play_music_loop_stop(self):
        """
        关闭播放队列
        """
        self.__play_music_loop_in = False
    
    def download_music_loop_in(self):
        """
        关闭下载队列
        """
        self.__download_music_loop_in = False
    
    def __add_thread(self, target):
        thread = Thread(target=target)
        thread.setDaemon(True)
        thread.start()
        return thread
    
    def play_music_loop(self):
        """
        开启播放队列
        """
        self.__play_music_loop_in = True
        def loop():
            while self.__play_music_loop_in:
                if self.__play_list != []:
                    for music_object in self.__play_list:
                        # 调用 play_music 事件
                        self.__musicEvent.play_music(music_object[0], self.__play_list,
                                                                    self.__download_music_list)
                        musicFileName = self.__musicEvent.set_msuic_file_name(music_object[0])
                        play(AudioSegment.from_mp3("%s/%s" % (self.__play_path, musicFileName)))
                        self.__play_list.remove(music_object)
                else:
                    if self.__download_music_list == []:
                        # 如果播放队列小于设置的最小值并且下载队列为空 向下载队列添加歌曲
                        while len(self.__play_list) < self.play_list_cache_len and len(self.__download_music_list) < self.play_list_cache_len:
                            music = random.choice(self.__not_play_music_in_playlist.music_list)
                            self._add_music(music, None)

        self.play_music_thread = self.__add_thread(loop)

    def download_music_loop(self):
        """
        开启下载队列
        """
        self.__download_music_loop_in = True
        def loop():
            while self.__download_music_loop_in:
                if self.__download_music_list != []:
                    for music_object in self.__download_music_list:
                        musicFileName = self.__musicEvent.set_msuic_file_name(music_object[0])
                        def download_callback(req, path):
                            return musicFileName, ""
                        
                        code = music_object[0].play(self.__play_path, download_callback=download_callback)
                        if code != 0:
                            # 调用 download_music_err 事件
                            self.__musicEvent.download_music_err(code, music_object[0], self.__play_list, 
                                                                            self.__download_music_list)

                            self.__download_music_list.remove(music_object)
                            continue
                        
                        # 调用 download_music 事件
                        self.__musicEvent.download_music(music_object[0], self.__play_list,
                                                                    self.__download_music_list)
                        self.__play_list.append(music_object)
                        self.__download_music_list.remove(music_object)

                # 下载线程休息
                time.sleep(self.download_music_loop_sleep)

        self.download_music_thread = self.__add_thread(loop)


# 抽象点歌模块事件
class MusicEvent(metaclass=ABCMeta):

    def __init__(self):
        # 被绑定后为点歌模块实例
        self.api = None

    @abstractmethod
    def cookie_invalidation(self, code):
        """
        事件 cookie_invalidation cookie无效时被调用
        """
        pass

    @abstractmethod
    def send_music(self, music, msg):
        """
        事件 send_music 向下载队列发送任务
        """
        music_list = self.api.search(music)
        if type(music_list) == int:
            music = self.music(music)
            if type(music) == int:
                return music

            return self.api._add_music(music[0], msg)
        
        music = object.music(self.api.headers, music_list["songs"][0])
        return self.api._add_music(music, msg)
    
    @abstractmethod
    def set_msuic_file_name(self, music_object):
        """
        设置缓存音乐文件名
        事件参数:
        music_object: music 对像
        """
        return "%s.mp3" % music_object.id

    @abstractmethod
    def set_music_name(self, music_object):
        """
        设置打印音乐字符串
        事件参数:
        music_object: music 对像
        """
        return "%s - %s (id: %s)" % (music_object.name_str, music_object.artist_str, music_object.id)

    @abstractmethod
    def add_music(self, music_object, play_list, download_music_list):
        """
        事件 add_music 下载队列被添加任务
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        print("成功点歌 %s ! 播放队列里还有%s首" % (self.set_music_name(music_object), len(play_list)))
    
    @abstractmethod
    def play_music(self, music_object, play_list, download_music_list):
        """
        事件 play_music 播放队列准备播放
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        print("开始播放 %s ..." % self.set_music_name(music_object))
    
    @abstractmethod
    def download_music(self, music_object, play_list, download_music_list):
        """
        事件 download_music 下载队列成功下载完成一条任务
        事件参数:
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        print("缓存完成 %s ... 下载队列里还有%s首" % (self.set_music_name(music_object), len(download_music_list)))

    @abstractmethod
    def download_music_err(self, code, music_object, play_list, download_music_list):
        """
        事件 download_music_err 下载队列下载失败
        事件参数:
        code: 状态码
        music_object: music 对像
        play_list: 播放队列
        download_music_list: 下载队列
        """
        print("%s 下载发生错误... code:%s 下载队列里还有%s首，播放队列里还有%s首" % ((self.set_music_name(music_object), code, 
                                                        len(download_music_list), len(play_list))))

    @abstractmethod
    def del_play_music(self, msg):
        """
        默认取消点歌, 不能取消正在IO的任务
        需返回: music 对象, 从哪个队列删除数据
        之后只用调用 PlayCloudMusic.del_play_music() 删除
        """
        play_lisy, download_music_list = self.api.get_all_play_music()
        for music in play_lisy:
            if music[1] is None:
                continue

            if music[1]["userId"] == msg["userId"]:
                return music[0], "play_lisy"
        
        for music in download_music_list:
            if music[1] is None:
                continue
            
            if music[1]["userId"] == msg["userId"]:
                return music, "download_music_list"


class musicEvent(MusicEvent):
    
    def cookie_invalidation(self, code):
        return super().cookie_invalidation(code)
    
    def set_msuic_file_name(self, music_object):
        return super().set_msuic_file_name(music_object)
    
    def send_music(self, msuic, msg):
        return super().send_music(msuic, msg)

    def set_music_name(self, music_object):
        return super().set_music_name(music_object)

    def add_music(self, music_object, play_list, download_music_list):
        return super().add_music(music_object, play_list, download_music_list)
    
    def play_music(self, music_object, play_list, download_music_list):
        return super().play_music(music_object, play_list, download_music_list)
    
    def download_music(self, music_object, play_list, download_music_list):
        return super().download_music(music_object, play_list, download_music_list)
    
    def download_music_err(self, code, music_object, play_list, download_music_list):
        return super().download_music_err(code, music_object, play_list, download_music_list)
    
    def del_play_music(self, msg):
        return super().del_play_music(msg)

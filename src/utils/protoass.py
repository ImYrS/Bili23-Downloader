# from . import bilidanmu_pb2 as Danmaku
import google.protobuf.text_format as text_format
import bilidanmu_pb2 as Danmaku
import datetime

class BiliProtoAss:
    def __init__(self,title:str="",author:str="Bili23 Downloader",created:str=datetime.datetime.now(),
                 language:str="简体中文",Timer:str="100.0000",duration:int=15000,
                 ResX:int=None,ResY:int=None,WarpStyle:int=2):
        """
        将Proto转化为Ass文件
        title: 标题
        author: 作者
        created: 创建时间
        duration: 单个弹幕的持续时间，单位ms
        language: 原始语言
        Timer: 定时器(默认100.0000,200.0000则播放速度为2倍,保留4位小数)
        ResX: 原始宽度
        ResY: 原始高度
        """
        self.header={
            'Title':title,
            'ScriptType':"v4.00+",
            'Collisions':"Normal",
            'Author':author,
            'Created':created,
            'Original Script':language,
            'WrapStyle':WarpStyle,
            'Timer':Timer
        }
        if ResX:
            self.header['PlayerResX']=ResX
        if ResY:
            self.header['PlayerResY']=ResY

        self.duration=duration

    def __toList(self, content):
        """
        将content解码并返回
        """
        danmakuSeg = Danmaku.DmSegMobileReply()
        danmakuSeg.ParseFromString(content)
        danmakuList=[]
        for i in range(len(danmakuSeg.elems)):
            danmu={} #此条弹幕的所有属性
            thisContent=text_format.MessageToString(danmakuSeg.elems[i], as_utf8=True)
            thisContent=thisContent.split('\n')
            for j in thisContent:
                # 处理单个弹幕属性
                if j=='' or j=='\n':
                    continue
                split=j.find(':') # 找到冒号的位置
                key=j[:split]
                value=j[split+1:]
                # 去除空格
                key=key.strip()
                value=value.strip()
                danmu[key]=value
            if danmu:
                danmakuList.append(danmu)
        return danmakuList

    def getDanmu(self, content):
        """
        通过content获取弹幕，只返回ass格式的Event文本，不包含Format文本
        """
        danmakuList=self.__toList(content)
        Events=""
        for i in danmakuList:
            # print(i)
            # 处理单个弹幕
            if 'progress' not in i or 'content' not in i: # 如果没有progress或content则跳过
                continue
            Event="Dialogue: 0,"
            Event+=self.formatMS(int(i['progress']))+","
            Event+=self.formatMS(int(i['progress'])+self.duration)+","
            Event+="DanMu,,0,0,0,Banner;0,"
            Event+=i['content']

            Events+=Event+"\n"
        return Events

    def getInfo(self):
        """
        返回Ass文件头部
        """
        header="""[Script Info]
        ; Script generated by Bili23 Downloader\n
        ; Download from www.bilibili.com
        """
        for i in self.header.keys():
            header+=i+": "+str(self.header[i])+"\n"
        header+="""
        [v4+ Styles]
        Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, TertiaryColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, AlphaLevel, Encoding
        Style: DanMu,微软雅黑,25,&H7fFFFFFF,&H7fFFFFFF,&H7f000000,&H7f000000,0,0,0,0,100,100,0,0,1,1,0,2,20,20,2,0

        [Events]
        Format: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
        """
        return header

    def toAss(self,content):
        All=""
        All+=self.getInfo()
        All+=self.getDanmu(content)
        return All
        
    def formatMS(self,milliseconds:int):
        seconds, ms = divmod(milliseconds, 1000) # 使用 timedelta 进行转换 
        td = datetime.timedelta(seconds=seconds) # 获取时、分、秒 
        hours, remainder = divmod(td.seconds, 3600) 
        minutes, seconds = divmod(remainder, 60)

        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, ms)
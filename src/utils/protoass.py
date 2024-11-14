# from . import bilidanmu_pb2 as Danmaku
from google.protobuf.json_format import MessageToDict
import bilidanmu_pb2 as Danmaku
import datetime

class BiliProtoAss:
    def __init__(self,title:str="",author:str="Bili23 Downloader",created:str=datetime.datetime.now(),
                 language:str="简体中文",Timer:str="100.0000",duration:int=15000,
                 ResX:int=None,ResY:int=None,WarpStyle:int=2,alpha:float=0.8):
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
        WarpStyle: 字幕换行方式
        alpha: 透明度，0-1之间，0为完全透明，1为完全不透明
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


        self.alpha=str(hex(int(alpha*255))[2:]) # 透明度
        self.StyleFormat=[
            "Name", "Fontname", "Fontsize", "PrimaryColour", 
            "SecondaryColour", "TertiaryColour", "BackColour",
            "Bold", "Italic", "Underline", "StrikeOut", "ScaleX", 
            "ScaleY", "Spacing", "Angle", "BorderStyle", "Outline",
            "Shadow","Alignment", "MarginL", "MarginR", "MarginV",
            "AlphaLevel","Encoding"
        ]
        self.StyleSheet = [
            {
                "Name": "Normal",
                "Fontname": "黑体",
                "Fontsize": 25,
                "PrimaryColour": f"&H{self.alpha}FFFFFF", ## 注意颜色表示为16进制ABGR
                "SecondaryColour": f"&H{self.alpha}000000",
                "TertiaryColour": f"&H{self.alpha}000000",
                "BackColour": "&H00000000",
                "Bold": 0,
                "Italic": 0,
                "Underline": 0,
                "StrikeOut": 0,
                "ScaleX": 100,
                "ScaleY": 100,
                "Spacing": 0,
                "Angle": 0,
                "BorderStyle": 1,
                "Outline": 1,
                "Shadow": 0,
                "Alignment": 8,# 注意！此处遵循ASS格式标准，SSA标准与此不同
                "MarginL": 10,
                "MarginR": 10,
                "MarginV": 2,
                "AlphaLevel": 0,
                "Encoding": 134 # 简体中文
            }
        ]
        ## 基于Normal进行新样式创造
        BTM=self.StyleSheet[0].copy()
        BTM.update({
            "Name":"BTM",
            "Alignment":2, # 注意！此处遵循ASS格式标准，SSA标准与此不同
        })
        self.StyleSheet.append(BTM)
        
        TOP=self.StyleSheet[0].copy()
        TOP.update({
            "Name":"TOP",
            "Alignment":8, 
        })
        self.StyleSheet.append(TOP)


        self.EventFormat=[
            "Marked", "Start", "End", "Style", "Name", "MarginL", 
            "MarginR", "MarginV", "Effect", "Text"
        ]
        self.EvnetTemplate={
            "Marked":0,
            "Start":None,
            "End":None,
            "Style":"Normal",
            "Name":None,
            "MarginL":0,
            "MarginR":0,
            "MarginV":0,
            "Effect":"Banner",
            "Text":None
        }

        self.duration=duration

    def __decode(self, content):
        """
        将content解码并返回
        """
        danmakuSeg = Danmaku.DmSegMobileReply()
        danmakuSeg.ParseFromString(content)
        danmakuList=MessageToDict(danmakuSeg)["elems"]
        return danmakuList

    def getDanmu(self, content):
        """
        通过content获取弹幕，只返回ass格式的Event文本，不包含Format文本
        """
        danmakuList=self.__decode(content)
        Events=""
        for i in danmakuList:
            # print(i)
            # 处理单个弹幕
            danmu=self.danmuFormater(i)
            if danmu is None:
                continue
            for key in danmu.keys():
                if danmu[key] is None:
                    danmu[key]=""
            Event="Dialogue: "
            Event+=",".join(str(danmu[key]) for key in self.EventFormat)
            Events+=Event+"\n"
        return Events

    def getInfo(self):
        """
        Ass文件头部
        """
        header="[Script Info]\n;Script generated by Bili23 Downloader\n;Download from www.bilibili.com\n"
        for i in self.header.keys():
            header+=i+": "+str(self.header[i])+"\n"
        return header

    def getStyle(self):
        """
        Ass文件Style部分
        """
        header = "[v4+ Styles]\n"       
        header+="Format: "+", ".join(self.StyleFormat)+'\n'
        for style in self.StyleSheet:
            header += "Style: " + ",".join(str(style[key]) for key in self.StyleFormat) + "\n"
        return header

    def getEventHeader(self):
        header="[Events]"
        header+="Format: "+", ".join(self.EventFormat)+'\n'
        return header

    def toAss(self,content):
        All=""
        All+=self.getInfo()+"\n"
        All+=self.getStyle()+"\n"
        All+=self.getEventHeader()
        All+=self.getDanmu(content)
        return All
        
    def danmuFormater(self,danmu:dict):
        """
        格式化弹幕
        None为无效弹幕
        """
        if 'progress' not in danmu.keys() or 'content' not in danmu.keys():
            # 处理无效弹幕
            return None
        danmuInfo=self.EvnetTemplate.copy()
        danmu['color']=danmu.get('color',16777215)
        danmu['fontsize']=danmu.get('fontsize',25)
        if danmu['mode'] in [1,2,3]:
            # 普通弹幕
            danmuInfo.update({
                "Start":self.formatMS(danmu['progress']),
                "End":self.formatMS(danmu['progress']+self.duration),
                "Text":self.textHandler(danmu['content'],danmu['color'],danmu['fontsize'])
            })
        elif danmu['mode']==4:
            # 底部弹幕
            danmuInfo.update({
                "Start":self.formatMS(danmu['progress']),
                "End":self.formatMS(danmu['progress']+self.duration),
                "Style":"BTM",
                "Text":self.textHandler(danmu['content'],danmu['color'],danmu['fontsize'])
            })
        elif danmu['mode']==5:
            # 顶部弹幕
            danmuInfo.update({
                "Start":self.formatMS(danmu['progress']),
                "End":self.formatMS(danmu['progress']+self.duration),
                "Style":"TOP",
                "Text":self.textHandler(danmu['content'],danmu['color'],danmu['fontsize'])
            })
        elif danmu['mode']==6:
            # 逆向弹幕
            danmuInfo.update({
                "Start":self.formatMS(danmu['progress']),
                "End":self.formatMS(danmu['progress']+self.duration),
                "Style":"Normal",
                "Text":self.textHandler(danmu['content'],danmu['color'],danmu['fontsize']),
                "Effect":"Banner;0;1"
            })
        else:
            return None
        return danmuInfo

    def formatMS(self,milliseconds:int):
        seconds, ms = divmod(milliseconds, 1000) # 使用 timedelta 进行转换 
        td = datetime.timedelta(seconds=seconds) # 获取时、分、秒 
        hours, remainder = divmod(td.seconds, 3600) 
        minutes, seconds = divmod(remainder, 60)

        return "{:02}:{:02}:{:02}:{:02}".format(hours, minutes, seconds, ms)
    
    def textHandler(self,text:str,color:int=16777215,size:int=25):
        """
        给文本加上颜色、透明度、字体大小
        """
        color=str(hex(color)[2:])# 转化为十六进制RGB
        ## 将RGB转化为BGR
        realcolor="&H"+color[4:]+color[2:4]+color[:2]
        text="{\\1a&H"+self.alpha+"}{\\c"+realcolor+"}{\\fs"+str(size)+"}"+text
        return text
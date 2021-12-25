import tkinter as tk
from tkinter.filedialog import *
from ttkbootstrap import Style
from tkinter import ttk
import predict
import cv2
from PIL import Image, ImageTk
import time
import ctypes


class Surface(ttk.Frame):
    #初始化各页面参数
    pic_path = ""
    viewhigh = 600
    viewwide = 600
    update_time = 0
    thread = None
    thread_run = False
    camera = None
    color_transform = {"green": ("绿牌", "#55FF55"), "yello": ("黄牌", "#FFFF00"), "blue": ("蓝牌", "#6666FF")}

    def __init__(self, win):
        #创建布局参数
        ttk.Frame.__init__(self, win)
        frame_left = ttk.Frame(self)#左边
        frame_right1 = ttk.Frame(self)#右一
        frame_right2 = ttk.Frame(self)#右二
        win.title("车牌自动识别")#窗口名
        win.iconbitmap('tk.ico')# 设置窗口图标
        # 设置窗口的大小宽x高+偏移量
        win.geometry('950x700')

        #调用pack进行布局
        self.pack(fill=tk.BOTH, expand=tk.YES, padx="5", pady="5")
        frame_left.pack(side=LEFT, expand=1, fill=BOTH)
        frame_right1.pack(side=TOP, expand=1, fill=tk.Y)
        frame_right2.pack(side=RIGHT, expand=0)
        ttk.Label(frame_left, text='原图：').pack(anchor="nw")
        ttk.Label(frame_right1, text='车牌截图：').grid(column=0, row=0, sticky=tk.W)

        from_pic_ctl = ttk.Button(frame_right2, text="打开图片", width=20, command=self.from_pic)#点击打开图片按钮时调用from_pic
        self.image_ctl = ttk.Label(frame_left)#于左侧显示图片
        self.image_ctl.pack(anchor="nw")

        #进行结果显示的布局
        self.roi_ctl = ttk.Label(frame_right1)
        self.roi_ctl.grid(column=0, row=1, sticky=tk.W)
        ttk.Label(frame_right1, text='识别结果：').grid(column=0, row=2, sticky=tk.W)
        self.r_ctl = ttk.Label(frame_right1, text="")
        self.r_ctl.grid(column=0, row=3, sticky=tk.W)
        self.color_ctl = ttk.Label(frame_right1, text="", width="20")
        self.color_ctl.grid(column=0, row=4, sticky=tk.W)
        from_pic_ctl.pack(anchor="se", pady="5")

        #此处调用后端predict代码
        self.predictor = predict.CardPredictor()
        self.predictor.train_svm()

    #读取并判断图片大小，开头设置了展示大小为600*600，若小于则直接返回图片数据，若大于则先缩放
    def get_imgtk(self, img_bgr):
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im)
        wide = imgtk.width()
        high = imgtk.height()
        if wide > self.viewwide or high > self.viewhigh:
            wide_factor = self.viewwide / wide
            high_factor = self.viewhigh / high
            factor = min(wide_factor, high_factor)

            wide = int(wide * factor)
            if wide <= 0: wide = 1
            high = int(high * factor)
            if high <= 0: high = 1
            im = im.resize((wide, high), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=im)
        return imgtk

    #车牌区域的图片处理，有些车牌是斜的，这个函数会将截取区域便形成标准的长方形
    def show_roi(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi = ImageTk.PhotoImage(image=roi)
            self.roi_ctl.configure(image=self.imgtk_roi, state='enable')
            self.r_ctl.configure(text=str(r))
            self.update_time = time.time()
            try:
                c = self.color_transform[color]
                self.color_ctl.configure(text=c[0], background=c[1], state='enable')
            except:
                self.color_ctl.configure(state='disabled')
        elif self.update_time + 8 < time.time():
            self.roi_ctl.configure(state='disabled')
            self.r_ctl.configure(text="")
            self.color_ctl.configure(state='disabled')

    #打开图片
    def from_pic(self):
        self.thread_run = False
        self.pic_path = askopenfilename(title="选择识别图片", filetypes=[("jpg图片", "*.jpg")])
        if self.pic_path:
            img_bgr = predict.imreadex(self.pic_path)#img_bgr存储文件路径
            self.imgtk = self.get_imgtk(img_bgr)#调用get_imgtk读取图片
            self.image_ctl.configure(image=self.imgtk)#
            resize_rates = (1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4)
            for resize_rate in resize_rates:
                print("resize_rate:", resize_rate)
                r, roi, color = self.predictor.predict(img_bgr, resize_rate)
                if r:
                    break
            self.show_roi(r, roi, color)


#关闭窗口并输出关闭提示
def close_window():
    print("destroy")
    if surface.thread_run:
        surface.thread_run = False
        surface.thread.join(2.0)
    win.destroy()


if __name__ == '__main__':
    win = tk.Tk()#创建窗口
    # 告诉操作系统使用程序自身的dpi适配
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    # 获取屏幕的缩放因子
    ScaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0)
    # 设置程序缩放
    win.tk.call('tk', 'scaling', ScaleFactor / 75)
    # 设置窗口主题为深色
    style = Style(theme='darkly')
    win = style.master
    surface = Surface(win)#像窗口填充信息
    win.protocol('WM_DELETE_WINDOW', close_window)#关闭窗口
    win.mainloop()#此语句类似循环while true，不加的话重新打开一张图片后页面不会刷新。

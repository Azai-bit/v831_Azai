from maix import image, display, camera
import time
import serial
import struct
from maix import event
from select import select
queue = mjpg.Queue(maxsize=8)
mjpg.MjpgServerThread(
    "0.0.0.0", 18811, mjpg.BytesImageHandlerFactory(q=queue)).start()

ser = serial.Serial("/dev/ttyS1", 115200)    # 连接串口


def check_key():
    import os
    tmp = "/dev/input/by-path/"
    if os.path.exists(tmp):
        for i in os.listdir(tmp):
            if i.find("kbd") != -1:
                return tmp + i
    return "/dev/input/event0"


dev = event.InputDevice(check_key())
left_flag = False
right_flag = False
polar_flag = False
line_count = 0
mode = 1
def check_black(color):
    if sum(color) < 10:
        return True
    else:
        return False
while True:
    img = camera.capture()
    if mode == 1:#数线，3根后跳转到模式2
        left_colors = img.get_blob_color((0, 20, 40, 200), 0, 0)
        right_colors = img.get_blob_color((200, 20, 40, 200), 0, 0)
        left_flag = check_black(left_colors)
        right_flag = check_black(right_colors)
        if left_flag==True and polar_flag == False:
            polar_flag = True
        elif right_flag==True and polar_flag ==True:
            polar_flag = False
            line_count+=1
        if line_count == 3:#经历3条线后，发送倒车指令，切换到摆正指示
            mode = 2
            data = struct.pack(">BBBB", 0xFD, 0xFD, 0xFD, 0xFE)
            ser.write(data)
        if left_flag==True:
            img.draw_rectangle(0, 20, 40, 220, 
                                       color=(255, 0, 0), thickness=1) #将找到的颜色区域画出来
        else:
            img.draw_rectangle(0, 20, 40, 220, 
                                       color=(255, 255, 255), thickness=1) #将找到的颜色区域画出来
        if right_flag==True:
            img.draw_rectangle(200, 20, 240, 220, 
                                       color=(255, 0, 0), thickness=1) #将找到的颜色区域画出来
        else:
            img.draw_rectangle(200, 20, 240, 220, 
                                       color=(255, 255, 255), thickness=1) #将找到的颜色区域画出来
    elif mode == 2:
        line = img.find_line()
        if line:
            ang = int(line["rotation"]/1.5*128+128)
            if ang>250:
              ang=250
            elif ang<0:
              ang=0
            offset = line["cy"]
            if ang > 240:
                mode = 3
                data = struct.pack(">BBBB", 0xFD, 0xFD, 0xFD, 0xFE)
                ser.write(data)
    img.draw_string(0,10, "mode:"+str(mode), scale = 2, color = (255, 0,20), thickness = 2)
    img.draw_string(0,30, "line:"+str(line_count), scale = 2, color = (0, 180, 20), thickness = 2)

#   img.draw_rectangle(9, 9, 21, 21, 
#                                color=(255, 255, 255), thickness=1) #将找到的颜色区域画出来
#   img.draw_rectangle(10, 10, 20, 20, 
#                                color=(int(left_colors[0]), int(left_colors[1]), int(left_colors[2])), thickness=-1) #将找到的颜色区域画出来
    jpg = utils.rgb2jpg(img.convert("RGB").tobytes(), img.width, img.height)
    queue.put(mjpg.BytesImage(jpg))
    display.show(img)
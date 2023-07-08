from maix import camera, mjpg, utils, display, image
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
ang = 128
offset = 200
line_count = 0
while True:
    img = camera.capture()
    line = img.find_line()
    if line:
        ang = int(line["rotation"]/1.5*128+128)
        if ang>250:
          ang=250
        elif ang<0:
          ang=0
        offset = line["cy"]
        
        
        
        
        
        img.draw_line(line["rect"][0], line["rect"][1], line["rect"][2],
                      line["rect"][3], color=(255, 255, 255), thickness=1)
        img.draw_line(line["rect"][2], line["rect"][3], line["rect"][4],
                      line["rect"][5], color=(255, 255, 255), thickness=1)
        img.draw_line(line["rect"][4], line["rect"][5], line["rect"][6],
                      line["rect"][7], color=(255, 255, 255), thickness=1)
        img.draw_line(line["rect"][6], line["rect"][7], line["rect"][0],
                      line["rect"][1], color=(255, 255, 255), thickness=1)
        img.draw_circle(line["cx"], line["cy"], 4,
                        color=(255, 255, 255), thickness=1)
        img.draw_string(line["rect"][2], line["rect"][3], "offset:"+str(offset)+"angle:"+str(ang), scale = 0.8, color = (0, 0, 255), thickness = 1)
        #print(line)
        data = struct.pack(">BBBB", 0xFD, int(offset), int(ang), 0xFE)
        ser.write(data)
    jpg = utils.rgb2jpg(img.convert("RGB").tobytes(), img.width, img.height)
    queue.put(mjpg.BytesImage(jpg))
    display.show(img)

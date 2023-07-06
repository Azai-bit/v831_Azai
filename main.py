#-----------------------------------------------IMPORT-----------------------------------------------
from maix import camera, mjpg, utils, display,image
import serial,struct
import thred
from maix import event
from select import select

#-----------------------------------------------INITIAL-----------------------------------------------
#key
def check_key():
	import os
	tmp = "/dev/input/by-path/"
	if os.path.exists(tmp):
		for i in os.listdir(tmp):
			if i.find("kbd") != -1:
				return tmp + i
	return "/dev/input/event0"
dev = event.InputDevice(check_key())

#mjpg
# queue = mjpg.Queue(maxsize=8)
# mjpg.MjpgServerThread(
#     "0.0.0.0", 18811, mjpg.BytesImageHandlerFactory(q=queue)).start()

#serial
ser = serial.Serial("/dev/ttyS1",115200,timeout = 0)    # 连接串口

#Threshold
#red =[31, 71, 36, 127, 21, 127]
red = thred.read_thred('thred.txt')
black = [(0, 28, -128, 127, -128, 127)]
#-----------------------------------------------GLOBAL-----------------------------------------------
sys_mode = 0
mode = 0
max_pixel=0
count = 0
x_sum = 0
pix_sum = 0
x_ave = 0
pix_ave = 0
#-----------------------------------------------FUNCTION-----------------------------------------------
def find_maxblob(blobs):
    max_pixel = 0
    for b in blobs:
        pix = b["w"]*b["h"]
        if pix > max_pixel:
            max_pixel = pix
            max_blob = b
    return max_blob

def mode_task():
    global mode,max_pixel,count,x_sum,x_ave,pix_ave,pix_sum
    img = camera.capture()
    if mode==0:
        mks = img.find_qrcodes()
        if mks:
            for mk in mks:
                string = mk['payload']
                #print(sting)
                img.draw_string(0, 20 , string , scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
                mode = eval(string)
                if mode==1 or mode ==2:
                    data = struct.pack(">BBBB", 0xAA, int(mode), 1, 0xBB)
                    ser.write(data)

    elif mode==1 or mode==2:#要求1 或 要求2
        blobs = img.find_blobs(black, merge=True)    #在图片中查找lab阈值内的颜色色块 merge 合并小框。
        if blobs:
            max_blob = find_maxblob(blobs)
            img.draw_rectangle(max_blob["x"], max_blob["y"], max_blob["x"] + max_blob["w"], max_blob["y"] + max_blob["h"], 
                            color=(0, 0, 255), thickness=1) #将找到的颜色区域画出
            img.draw_string(0, 20 , str(max_blob["pixels"]) , scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
            if max_blob["pixels"]>20000:
                data = struct.pack(">BBBB", 0xAA, 0xFE, 0xFE, 0xBB)
                ser.write(data)
                mode = 0

    elif mode==3:#发挥1
        
        if count<100:#前100帧数，锁定位置
            blobs = img.find_blobs(red, merge=True)    #在图片中查找lab阈值内的颜色色块 merge 合并小框。
            if blobs:
                max_blob = find_maxblob(blobs)
                img.draw_rectangle(max_blob["x"], max_blob["y"], max_blob["x"] + max_blob["w"], max_blob["y"] + max_blob["h"], 
                                color=(0, 0, 255), thickness=1) #将找到的颜色区域画出来
                x_sum+=max_blob["x"]
                pix_sum+=max_blob["pixels"]
                count+=1
        elif count==100:
            #img.draw_string(0, 20 , str(x_sum/count) , scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
            x_ave=x_sum/count
            pix_ave=pix_sum/count
            if pix_ave < 100:
                if x_ave>100:
                    if x_ave>200:#远最右
                        route = 2
                    else:#远右
                        route = 3
                else:
                    if x_ave<50:#远最左
                        route = 1
                    else:#远左
                        route = 4
            elif pix_ave <1000:
                if x_ave>100:#中右
                    route = 8
                else:#中左
                    route = 7
            else:
                if x_ave>100:#近右
                    route = 6
                else:#近左
                    route = 5
            data = struct.pack(">BBBB", 0xAA, int(mode), int(route), 0xBB)
            ser.write(data)
            count+=1
        else:
            blobs = img.find_blobs(red, merge=True)    #在图片中查找lab阈值内的颜色色块 merge 合并小框。
            if blobs:
                max_blob = find_maxblob(blobs)
                img.draw_rectangle(max_blob["x"], max_blob["y"], max_blob["x"] + max_blob["w"], max_blob["y"] + max_blob["h"], 
                                color=(0, 0, 255), thickness=1) #将找到的颜色区域画出
                #img.draw_string(0, 20 , str(max_blob["pixels"]) , scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
                if max_blob["pixels"]>14000:#找到火源
                    data = struct.pack(">BBBB", 0xAA, 0xFE, 0xFE, 0xBB)
                    ser.write(data)
                    mode = 0
    elif mode==4:#发挥2
        if direct==0:
            mks = img.find_qrcodes()
            if mks:
                for mk in mks:
                    string = mk['payload']
                    #print(sting)
                    #img.draw_string(0, 20 , string , scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
                    direct = eval(string)-4
                    data = struct.pack(">BBBB", 0xAA,int(mode),int(direct), 0xBB)#根据识别到的二维码
                    ser.write(data)
        mode = 0
    img.draw_string(0, 0 , "mode:"+str(mode), scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
    img.draw_string(0, 20 , "pix:"+str(pix_ave), scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
    img.draw_string(0, 40 , "x:"+str(x_ave), scale = 2.0, color = (255, 0, 0), thickness = 2)  #内框ID
    # jpg = utils.rgb2jpg(img.convert("RGB").tobytes(), img.width, img.height)
    # queue.put(mjpg.BytesImage(jpg))
    display.show(img)
def HMI_init():
    for i in range(6):
        if i <2:
            data = b"h%d.val=%d\xff\xff\xff"%(i,red[i])
        else:
            data = b"h%d.val=%d\xff\xff\xff"%(i,red[i]+128)
        ser.write(data)

def mode_debug():
    global red
    img = camera.capture()
    data = ser.readline()
    if data:
        if data[0]==0xAA:
            if data[1]<2:
                red[data[1]]=data[2]
            elif data[1]<6:
                red[data[1]]=data[2]-128
            elif data[1]==6:
                thred.save_thred(red,'thred.txt')
            elif data[1]==7:
                HMI_init()
    img = img.binary([(red)], invert=False, zero=False) # invert 取反阈值，zero 是否不填充阈值区域。
    display.show(img)

#-----------------------------------------------MAIN-----------------------------------------------
def main():
    global sys_mode,dev
    while True:
        r, w, x = select([dev], [], [], 0) # if r == 0 or set 0 will read() raise BlockingIOError 
        if r:
            for data in dev.read():
                if data.code == 0x02:
                    sys_mode = 0
                if data.code == 0x03:
                    sys_mode = 1
        if sys_mode==0:
            mode_task()
        elif sys_mode==1:
            mode_debug()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback, time
        msg = traceback.format_exc()
        print(msg)
        img = image.new(size = (240, 240), color = (255, 0, 0), mode = "RGB")
        img.draw_string(0, 0, msg, scale = 0.8, color = (255, 255, 255), thickness = 1)
        display.show(img)
        time.sleep(20)
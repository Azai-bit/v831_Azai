# generated by maixhub, tested on maixpy3 v0.4.8
from maix import nn, camera, display, image
from collections import deque
input_size = (224, 224)
model = "model-59503.awnn.mud"
labels = ['finger']
anchors = [1.25, 1.16, 2.38, 2.12, 1.53, 1.5, 1.69, 1.38, 1.78, 1.67]
boxlist = deque(maxlen=80)
def interpolate_points(p1, p2):
    global boxlist
    x1, y1 = p1
    x2, y2 = p2
    
    dx = (x2 - x1) / 11
    dy = (y2 - y1) / 11
    
    points = []
    for i in range(1, 11):
        x = x1 + i * dx
        y = y1 + i * dy
        boxlist.append([x, y])
    
    #return points

class YOLOv2:
    def __init__(self, model_path, labels, anchors, net_in_size, net_out_size):
        self.labels = labels
        self.anchors = anchors
        self.net_in_size = net_in_size
        self.net_out_size = net_out_size
        print("-- load model:", model)
        self.model = nn.load(model_path)
        print("-- load ok")
        print("-- init yolo2 decoder")
        self._decoder = nn.decoder.Yolo2(len(labels), anchors, net_in_size=net_in_size, net_out_size=net_out_size)
        print("-- init complete")

    def run(self, img, nms=0.3, threshold=0.5):
        out = self.model.forward(img, layout="hwc")
        boxes, probs = self._decoder.run(out, nms=nms, threshold=threshold, img_size=input_size)
        return boxes, probs

    def draw(self, img, boxes, probs):
        for i, box in enumerate(boxes):
            class_id = probs[i][0]
            prob = probs[i][1][class_id]
            msg = "{}:{:.2f}%".format(self.labels[class_id], prob*100)
            img.draw_rectangle(box[0], box[1], box[0] + box[2], box[1] + box[3], color=(255, 255, 255), thickness=2)
            #img.draw_string(box[0] + 2, box[1] + 2, msg, scale = 1.2, color = (255, 255, 255), thickness = 2)

def main():
    global boxlist
    line_poins=[]
    p1=[0,0]
    p2=[0,0]
    camera.config(size=input_size)
    yolov2 = YOLOv2(model, labels, anchors, input_size, (input_size[0] // 32, input_size[1] // 32))
    while True:
        img = camera.capture()
        boxes, probs = yolov2.run(img, nms=0.3, threshold=0.5)
        if boxes:
            for b in boxes:
                p1 = p2
                p2 = [int(b[0]+b[2]/2-5), int(b[1]+b[3]/2-5)]
                interpolate_points(p1,p2)
        if boxlist:
            for b in boxlist:
                img.draw_circle(int(b[0]), int(b[1]), 8, color=(204, 84, 100), 
                            thickness=-1)  #画一个中心点在（150,150），半径为20的实心红圆
            #yolov2.draw(img, boxes, probs)
        display.show(img)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback, time
        msg = traceback.format_exc()
        print(msg)
        img = image.new(size = (240, 240), color = (255, 0, 0), mode = "RGB")
        img.draw_string(0, 0, msg[-30:], scale = 0.8, color = (255, 255, 255), thickness = 1)
        img.draw_string(0, 20, msg[-60:-30], scale = 0.8, color = (255, 255, 255), thickness = 1)
        display.show(img)
        time.sleep(20)
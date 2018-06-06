import sys
import time
import cv2
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QLabel
from PyQt5.uic import loadUi
import psutil
import datetime
import threading

class Warning(QDialog):
    def __init__(self):
        super(Warning,self).__init__()
        loadUi('warning.ui',self)

class PyQt(QDialog):

    totalTime = datetime.timedelta(0)

    def __init__(self,intervalRam=1):
        super(PyQt,self).__init__()
        loadUi('design.ui',self)
        self.intervalRam = intervalRam
        threadRam = threading.Thread(target=self.runRam, args=())
        threadRam.daemon=True
        threadRam.start()
        threadCpu = threading.Thread(target=self.runCpu, args=())
        threadCpu.daemon=True
        threadCpu.start()
        threadTimeCalculator = threading.Thread(target=self.runTime, args=())
        threadTimeCalculator.start()
        self.reset()
        self.image=None
        self.image2 = None
        self.startButton.clicked.connect(self.start_webcam)
        self.stopButton.clicked.connect(self.stop_webcam)
        self.detectButton.setCheckable(True)
        self.detectButton.toggled.connect(self.detect_webcam_face)
        self.face_Enabled=False
        self.face_Cascade=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


    def start_webcam(self):
        self.capture=cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH,640)

        self.timer=QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)

    def update_frame(self):
        ret,self.image=self.capture.read()
        self.image=cv2.flip(self.image,1)

        if(self.face_Enabled):
            detected_image = self.detect_face(self.image)
            self.displayImage(detected_image,1)
        else:
            self.displayImage(self.image,1)

    def detect_face(self,img):
        color = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        faces = self.face_Cascade.detectMultiScale(color,1.1,5,minSize=(30,30))

        if faces is ():
            self.calculateTime()
            self.reset()

        for(x,y,w,h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            self.start_stop()
            print(self.printTime())

        return img

    def displayImage(self,img,window=1):
        qformat=QImage.Format_Indexed8

        if len(self.image.shape)==3: #rows[0],columns[1],channels[2]
            if self.image.shape[2]==4:
                qformat=QImage.Format_RGBA8888
            else:
                qformat=QImage.Format_RGB888

        outImage=QImage(img,img.shape[1],img.shape[0],img.strides[0],qformat)
        outImage = outImage.rgbSwapped()

        if window==1:
            self.imgLabel.setPixmap(QPixmap.fromImage(outImage))
            self.imgLabel.setScaledContents(True)

    def stop_webcam(self):
        self.timer.stop()

    def detect_webcam_face(self, status):
        if status:
            self.detectButton.setText('Stop Detection')
            self.face_Enabled = True

        else:
            self.detectButton.setText('Detect Face')
            self.face_Enabled = False

    def reset(self):
        self.timeAdvisor = 0.0
        self.accumulator = datetime.timedelta(0)
        self.started = None

    def start_stop(self):
        if self.started:
            self.accumulator += 2*(
                datetime.datetime.utcnow() - self.started
            )
            self.started = None
        else:
            self.started = datetime.datetime.utcnow()

    @property
    def elapsed(self):
        if self.started:
            return self.accumulator + 2*(
                datetime.datetime.utcnow() - self.started
            )
        return self.accumulator
    #
    #
    #   self.totalTime uyarı zamanı için kullanılacak.
    #
    #
    def printTime(self):
        return "<Local Time: {}  Total Time: {}  Ram Usage: ½{}  CPU Usage: %{}  Status: {}>".format(
            self.elapsed, self.totalTime, self.ram_usage, self.cpu_usage, self.status
        )

    def calculateTime(self):
        self.elapsed
        global totalTime
        self.totalTime += self.elapsed
        #
        # 5 saniye sonra tavsiye açılıyor.
        #
        if (self.totalTime.seconds > self.timeAdvisor):
            self.dialog = Warning()
            self.dialog.setWindowTitle('Warning')
            self.dialog.show()
            self.setImage()
            self.totalTime=datetime.timedelta(0)
            self.face_Enabled = False

    def setImage(self):
        self.image2=cv2.imread('advice.jpg')
        qformat2 = QImage.Format_Indexed8
        if len(self.image2.shape)==3:
            if (self.image2.shape[2])==4:
                qformat2=QImage.Format_RGBA8888
            else:
                qformat2=QImage.Format_RGB888
        img2 = QImage(self.image2, self.image2.shape[1], self.image2.shape[0], self.image2.strides[0], qformat2)
        img2 = img2.rgbSwapped()
        self.dialog.imgLabel2.setPixmap(QPixmap.fromImage(img2))
        self.dialog.imgLabel2.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.dialog.exerciseButton.clicked.connect(self.backToWebCam)

    def backToWebCam(self):
        self.face_Enabled = True
        self.dialog.hide()

    def runRam(self):
        while True:
            self.ram_usage = psutil.virtual_memory().percent
            time.sleep(self.intervalRam)

    def runCpu(self):
        while True:
            self.cpu_usage = psutil.cpu_percent(interval=3)

    def runTime(self):
        self.cpu_usage = 0.0
        while True:
            if self.ram_usage > 50.0:
                if self.cpu_usage > 20.0:
                    self.timeAdvisor = 60*60
                    self.status = "Hard"
            elif self.ram_usage > 30.0:
                if  self.cpu_usage > 5.0:
                    self.timeAdvisor = 30*60
                    self.status = "Normal"
            elif self.ram_usage < 30.0:
                self.timeAdvisor = 15*60
                self.status = "Easy"


if __name__=='__main__':
    app=QApplication(sys.argv)
    window=PyQt()
    window.setWindowTitle('Face Detection')
    window.show()
    sys.exit(app.exec_())


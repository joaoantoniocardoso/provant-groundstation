import sys
from PyQt4 import QtGui, uic
import PyQt4.Qwt5 as Qwt
from ui.items import CustomTreeItem
from ui.data import DataSet
import random
from helpers.serialHelpers import list_serial_ports
from PyQt4.Qwt5.anynumpy import *
from provant_serial import ProvantSerial
from ui.artificalHorizon import AttitudeIndicator
from ui.speedometer import SpeedoMeter
XRANGE = 500

#just tricking my auto-complete
arange = arange

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('vant3.ui', self)
        self.setupTreeWidget()
        self.show()
        self.setupPlot()
        self.dataSets = {}
        self.provantSerial = None
        legend = Qwt.QwtLegend()
        self.qwtPlot.insertLegend(legend, Qwt.QwtPlot.TopLegend)
        self.setupSerial()
        self.timerCounter =0
        self.horizon = AttitudeIndicator(self.frame_2)
        self.lay3.addWidget(self.horizon)
        #self.Dial = SpeedoMeter(self.frameh_2)
        #print dir(self.frame_2)

    def setupSerial(self):
        self.serialList.clear()
        for serial in list_serial_ports():
            self.serialList.addItem(serial)
        self.serialConnect.clicked.connect(self.connectToSerial)

    def connectToSerial(self):
        try:
            self.setSerial(ProvantSerial(serial_name=str(self.serialList.currentText())))
            self.serialStatus.setText('OK!')
        except Exception, e:
            self.serialStatus.setText("ERROR!")
            print e


    def setSerial(self, ser):
        self.provantSerial = ser

    def addPoint(self, datasetName, y):
        if datasetName not in self.dataSets:
            self.dataSets[datasetName] = DataSet(self, datasetName)
            self.dataSets[datasetName].curve.attach(self.qwtPlot)
            self.addSingleData(datasetName)
            self.dataSets[datasetName].setColor(self.getColor(datasetName))
        self.dataSets[datasetName].addPoint(y)

    def addArray(self, datasetName, points):
        datasetName_ = datasetName + str(0)
        if datasetName_ not in self.dataSets:
            self.addDataTree(datasetName, len(points))
            for i in range(len(points)):
                datasetName_ = datasetName+str(i)
                self.dataSets[datasetName_] = DataSet(self, datasetName_)
                self.dataSets[datasetName_].curve.attach(self.qwtPlot)
                self.dataSets[datasetName_].setColor(self.getColor(datasetName_))
        for i in range(len(points)):
                self.dataSets[datasetName+str(i)].addPoint(points[i])

    def setupPlot(self):
        self.startTimer(50)

    def getDataFromSerial(self):
        self.provantSerial.update()
        self.addArray('Attitude', (self.provantSerial.attitude.x, self.provantSerial.attitude.y, self.provantSerial.attitude.z))
        self.addArray('Gyro', self.provantSerial.imu.gyro)
        self.addArray('MotorSetpoint', (self.provantSerial.motor.motor[0], self.provantSerial.motor.motor[1]))
        self.addArray('ServoAngle', (self.provantSerial.servo.servo[4], self.provantSerial.servo.servo[5]))

    def updateData(self):
        self.getDataFromSerial()
        for namea, dataset in self.dataSets.items():
            dataset.update()
        self.qwtPlot.replot()
        self.lMotorSetpoint.setValue(self.provantSerial.motor.motor[0])
        self.rMotorSetpoint.setValue(self.provantSerial.motor.motor[1])
        self.lServo.setValue(self.provantSerial.servo.servo[4])
        self.rServo.setValue(self.provantSerial.servo.servo[5])

    def timerEvent(self, e):
        self.timerCounter += 1
        if self.provantSerial:
            self.updateData()
        elif (self.timerCounter % 1000) == 1:
            self.setupSerial()


    def setupTreeWidget(self):
        #self.treeWidget.header().setResizeMode(3)
        self.treeWidget.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.treeWidget.header().setResizeMode(1, QtGui.QHeaderView.Fixed)
        self.treeWidget.header().setResizeMode(2, QtGui.QHeaderView.Fixed)
        self.treeWidget.header().setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        self.treeWidget.setColumnWidth(1, 40)

    def addDataTree(self, data, children_number):
        parent = CustomTreeItem(self, self.treeWidget, data, self.treeWidget, color=False)
        for i in range(children_number):
            CustomTreeItem(self, parent, data+str(i))
        self.treeWidget.resizeColumnToContents(2)

    def addSingleData(self, name):
        CustomTreeItem(self, self.treeWidget, name, self.treeWidget)

    def disablePlot(self, name):
        self.dataSets[name].curve.detach()

    def enablePlot(self, name):
        self.dataSets[name].curve.attach(self.qwtPlot)

    def setPlotColor(self, name, color):
        #print color
        self.dataSets[name].setColor(color)

    def getColor(self, name):
        return self.findNode(name).colorChooser.color()

    def findNode(self, name, node=None):
        if not node:
            root = self.treeWidget.invisibleRootItem()
            node = root
        else:
            #print node.text(0)
            if node.text(0) == name:
                return node
        for i in range(node.childCount()):
            if self.findNode(name, node.child(i)):
                return self.findNode(name, node.child(i))


if __name__ == '__main__':
    #ser = ProvantSerial()
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    #window.setSerial(ser)
    #window.addDataTree('acc',3)
    sys.exit(app.exec_())

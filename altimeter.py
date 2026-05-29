import requests
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from PyQt5 import QtGui
import math
import csv
import random
from datetime import datetime

app = QtWidgets.QApplication([])

# ===== CSV =====
file = open("rocket_data.csv", "w", newline="")
writer = csv.writer(file)
writer.writerow(["Time","Alt","Temp","Speed","Pressure","Ax","Ay","Az"])

# ===== WINDOW =====
win = QtWidgets.QWidget()
win.setWindowTitle("🚀 Rocket Mission Control")
win.setStyleSheet("background-color:#0b0f1a; color:white;")
layout = QtWidgets.QGridLayout()
win.setLayout(layout)

# ===== LABELS =====
alt_label = QtWidgets.QLabel("ALT: 0 m")
spd_label = QtWidgets.QLabel("SPD: 0 m/s")
temp_label = QtWidgets.QLabel("TEMP: 0 °C")
prs_label = QtWidgets.QLabel("PRS: 0 bar")

for i, lbl in enumerate([alt_label, spd_label, temp_label, prs_label]):
    lbl.setStyleSheet("font-size:18px; padding:6px; border:1px solid #333;")
    layout.addWidget(lbl, 0, i)

# ===== GRAPHS =====
alt_plot = pg.PlotWidget(title="Altitude")
spd_plot = pg.PlotWidget(title="Speed")
acc_plot = pg.PlotWidget(title="Acceleration")

for p in [alt_plot, spd_plot, acc_plot]:
    p.setBackground('#0b0f1a')

layout.addWidget(alt_plot,1,0,1,2)
layout.addWidget(spd_plot,1,2,1,2)
layout.addWidget(acc_plot,2,0,1,3)

# ===== ROCKET PANEL =====
rocket_plot = pg.PlotWidget()
rocket_plot.setBackground('#0b0f1a')
rocket_plot.setXRange(-3,3)
rocket_plot.setYRange(-3,3)
rocket_plot.hideAxis('bottom')
rocket_plot.hideAxis('left')
rocket_plot.setFixedWidth(260)
rocket_plot.setFixedHeight(300)

layout.addWidget(rocket_plot,2,3)

# ===== BODY (FIXED HEIGHT) =====
body = QtWidgets.QGraphicsRectItem(-0.25, -1.2, 0.5, 2.2)
body.setBrush(QtGui.QColor(0,220,255))
body.setPen(QtGui.QPen(QtGui.QColor(0,220,255)))

# ===== NOSE (VISIBLE NOW) =====
# ===== TRIANGULAR HEAD =====
nose = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(0, 2.2),     # sharp top tip
        QtCore.QPointF(0.4, 1.2),   # right base
        QtCore.QPointF(-0.4, 1.2)   # left base
    ])
)

nose.setBrush(QtGui.QColor(0, 200, 255))   # blue fill
nose.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))  # black border (visible on white)
nose.setBrush(QtGui.QColor(255, 0, 0))   # red fill
nose.setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 2))  # darker red border

# ===== FINS =====
fin_left = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(-0.25, -0.2),
        QtCore.QPointF(-0.7, -1.2),
        QtCore.QPointF(-0.25, -1.2)
    ])
)

fin_right = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(0.25, -0.2),
        QtCore.QPointF(0.7, -1.2),
        QtCore.QPointF(0.25, -1.2)
    ])
)

for fin in [fin_left, fin_right]:
    fin.setBrush(QtGui.QColor(0,220,255))
    fin.setPen(QtGui.QPen(QtGui.QColor(0,220,255)))

# ===== NOZZLE =====
nozzle = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(-0.2, -1.2),
        QtCore.QPointF(0.2, -1.2),
        QtCore.QPointF(0, -1.6)
    ])
)
nozzle.setBrush(QtGui.QColor(180,180,180))

# ===== FLAME =====
flame = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(-0.15, -1.6),
        QtCore.QPointF(0.15, -1.6),
        QtCore.QPointF(0, -2.4)
    ])
)
flame.setBrush(QtGui.QColor(255,200,0))

# ===== GROUP =====
rocket_group = QtWidgets.QGraphicsItemGroup()
rocket_group.addToGroup(body)
rocket_group.addToGroup(nose)
rocket_group.addToGroup(fin_left)
rocket_group.addToGroup(fin_right)
rocket_group.addToGroup(nozzle)
rocket_group.addToGroup(flame)
rocket_group.setPos(0.8, 0)
rocket_plot.addItem(rocket_group)

# ===== ALTITUDE SCALE =====
scale_x = -1.8

line = pg.InfiniteLine(pos=scale_x, angle=90, pen=pg.mkPen('cyan', width=2))
rocket_plot.addItem(line)

for i in range(5):
    y = -2 + i
    tick = pg.PlotDataItem(x=[scale_x-0.1, scale_x+0.1], y=[y, y], pen='cyan')
    rocket_plot.addItem(tick)

# ===== ARROW =====
arrow = pg.ArrowItem(pos=(scale_x, -2), angle=0, brush='orange')
rocket_plot.addItem(arrow)

# ===== CURVES =====
alt_curve = alt_plot.plot(pen='y')
spd_curve = spd_plot.plot(pen='c')

acc_plot.addLegend()
accX_curve = acc_plot.plot(pen='r', name="X")
accY_curve = acc_plot.plot(pen='g', name="Y")
accZ_curve = acc_plot.plot(pen='b', name="Z")

# ===== DATA =====
alt_data, spd_data = [], []
accX_data, accY_data, accZ_data = [], [], []

# ===== UPDATE =====
def update():
    try:
        res = requests.get("http://192.168.4.1/data", timeout=1).text
        v = res.split(',')

        alt = float(v[0])
        temp = float(v[1])
        spd = float(v[2])
        prs = float(v[3])
        ax = float(v[4])
        ay = float(v[5])
        az = float(v[6])

        alt_label.setText(f"ALT: {alt:.2f} m")
        spd_label.setText(f"SPD: {spd:.2f} m/s")
        temp_label.setText(f"TEMP: {temp:.2f} °C")
        prs_hpa = float(v[3])
        prs = prs_hpa / 1000.0   # convert to bar

        writer.writerow([datetime.now().strftime("%H:%M:%S"),alt,temp,spd,prs,ax,ay,az])
        file.flush()

        alt_data.append(alt)
        spd_data.append(spd)
        accX_data.append(ax)
        accY_data.append(ay)
        accZ_data.append(az)

        if len(alt_data)>100:
            alt_data.pop(0)
            spd_data.pop(0)
            accX_data.pop(0)
            accY_data.pop(0)
            accZ_data.pop(0)

        alt_curve.setData(alt_data)
        spd_curve.setData(spd_data)
        accX_curve.setData(accX_data)
        accY_curve.setData(accY_data)
        accZ_curve.setData(accZ_data)

        # rotation
        angle = math.atan2(ay, az) * 180 / math.pi
        rocket_group.setRotation(angle)

        # altitude arrow
        scaled = (alt / 100) * 4
        scaled = max(min(scaled, 4), 0)
        arrow.setPos(scale_x, -2 + scaled)

        # flame animation
        flame.setScale(1 + random.uniform(-0.3, 0.4))
        r = random.randint(200, 255)
        g = random.randint(100, 200)
        flame.setBrush(QtGui.QColor(r, g, 0))
        flame.setPen(QtGui.QPen(QtGui.QColor(255, 80, 0)))


    except:
        pass  

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(200)

win.resize(1100,600)
win.show()
app.exec()
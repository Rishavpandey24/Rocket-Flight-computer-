import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from PyQt5 import QtGui
import math
import csv
import random
from datetime import datetime
import serial
    
app = QtWidgets.QApplication([])

# ===== SERIAL =====
nano = serial.Serial('COM10', 9600, timeout=1)
uno  = serial.Serial('COM9', 9600, timeout=1)

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

# ===== ROCKET =====
body = QtWidgets.QGraphicsRectItem(-0.25, -1.2, 0.5, 2.2)
body.setBrush(QtGui.QColor(0,220,255))
body.setPen(QtGui.QPen(QtGui.QColor(0,220,255)))

nose = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(0, 2.2),
        QtCore.QPointF(0.4, 1.2),
        QtCore.QPointF(-0.4, 1.2)
    ])
)
nose.setBrush(QtGui.QColor(255, 0, 0))
nose.setPen(QtGui.QPen(QtGui.QColor(150, 0, 0), 2))

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

nozzle = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(-0.2, -1.2),
        QtCore.QPointF(0.2, -1.2),
        QtCore.QPointF(0, -1.6)
    ])
)
nozzle.setBrush(QtGui.QColor(180,180,180))

flame = QtWidgets.QGraphicsPolygonItem(
    QtGui.QPolygonF([
        QtCore.QPointF(-0.15, -1.6),
        QtCore.QPointF(0.15, -1.6),
        QtCore.QPointF(0, -2.4)
    ])
)
flame.setBrush(QtGui.QColor(255,200,0))

rocket_group = QtWidgets.QGraphicsItemGroup()
rocket_group.addToGroup(body)
rocket_group.addToGroup(nose)
rocket_group.addToGroup(fin_left)
rocket_group.addToGroup(fin_right)
rocket_group.addToGroup(nozzle)
rocket_group.addToGroup(flame)
rocket_group.setPos(0.8, 0)
rocket_plot.addItem(rocket_group)

# ===== SCALE =====
scale_x = -1.8
line = pg.InfiniteLine(pos=scale_x, angle=90, pen=pg.mkPen('cyan', width=2))
rocket_plot.addItem(line)

for i in range(5):
    y = -2 + i
    tick = pg.PlotDataItem(x=[scale_x-0.1, scale_x+0.1], y=[y, y], pen='cyan')
    rocket_plot.addItem(tick)

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

# ===== STATE =====
last_alt = 0
smooth_alt = 0
smooth_spd = 0
last_time = datetime.now()

# ===== UPDATE =====
def update():
    global last_alt, smooth_alt, smooth_spd, last_time

    try:
        # UNO
        ax = ay = az = 0
        if uno.in_waiting:
            line = uno.readline().decode(errors='ignore').strip()
            parts = line.split()
            if len(parts) >= 3:
                ax = float(parts[0])
                ay = float(parts[1])
                az = float(parts[2])

        # NANO
        alt = last_alt
        if nano.in_waiting:
            alt_line = nano.readline().decode(errors='ignore').strip()
            try:
                alt = float(alt_line)
            except:
                pass

        # SMOOTH ALT
        smooth_alt = 0.8 * smooth_alt + 0.2 * alt

        # SPEED FIX
        current_time = datetime.now()
        dt = (current_time - last_time).total_seconds()
        last_time = current_time

        if dt > 0:
            raw_spd = (smooth_alt - last_alt) / dt
        else:
            raw_spd = 0

        smooth_spd = 0.7 * smooth_spd + 0.3 * raw_spd
        last_alt = smooth_alt

        # PITCH ROLL
        pitch = math.atan2(ax, math.sqrt(ay*ay + az*az)) * 180 / math.pi
        roll  = math.atan2(ay, math.sqrt(ax*ax + az*az)) * 180 / math.pi

        # UI
        alt_label.setText(f"ALT: {smooth_alt:.2f} m")
        spd_label.setText(f"SPD: {smooth_spd:.2f} m/s")
        temp_label.setText(f"TEMP: 30.00 °C")
        prs_label.setText(f"PRS: 1.00 bar")

        writer.writerow([datetime.now().strftime("%H:%M:%S"),
                         smooth_alt,30,smooth_spd,1,ax,ay,az])
        file.flush()

        alt_data.append(smooth_alt)
        spd_data.append(smooth_spd)

        accX_data.append(pitch)
        accY_data.append(roll)
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

        rocket_group.setRotation(roll)

        scaled = (smooth_alt / 100) * 4
        scaled = max(min(scaled, 4), 0)
        arrow.setPos(scale_x, -2 + scaled)

        flame.setScale(1 + random.uniform(-0.3, 0.4))
        r = random.randint(200, 255)
        g = random.randint(100, 200)
        flame.setBrush(QtGui.QColor(r, g, 0))
        flame.setPen(QtGui.QPen(QtGui.QColor(255, 80, 0)))

    except Exception as e:
        print("Error:", e)

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(200)

win.resize(1100,600)
win.show()
app.exec()
from PyQt5.QtWidgets import QDial
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QRadialGradient
import math


class AviaKnob(QDial):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._start_angle = 135
        self._span_angle = 270

        self._light_on = False
        self._light_color = QColor("#8b7cff")

        self.setRange(0, 255)
        self.setValue(0)

        self.setNotchesVisible(False)
        self.setWrapping(False)
        self.setFixedSize(78, 78)

    def setRange(self, minimum: int, maximum: int):
        super().setRange(minimum, maximum)

        if self.value() < minimum:
            self.setValue(minimum)

        if self.value() > maximum:
            self.setValue(maximum)

        self.update()

    def setStartValue(self):
        self.setValue(self.minimum())
        self.update()

    def setAngleRange(self, start_angle: float, span_angle: float):
        self._start_angle = start_angle
        self._span_angle = span_angle
        self.update()

    def valueRatio(self):
        minimum = self.minimum()
        maximum = self.maximum()
        value = self.value()

        if maximum == minimum:
            return 0.0

        value = max(minimum, min(value, maximum))
        return (value - minimum) / (maximum - minimum)

    def on(self, color=None):
        self._light_on = True
        if color:
            self._light_color = QColor(color)
        self.update()

    def off(self):
        self._light_on = False
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h)
        cx = w / 2
        cy = h / 2

        value_ratio = self.valueRatio()
        angle = self._start_angle + self._span_angle * value_ratio

        tick_radius_outer = size * 0.48
        tick_radius_inner = size * 0.41

        p.setPen(QPen(QColor("#9aa6ad"), 1))

        for i in range(23):
            a = self._start_angle + self._span_angle * i / 22
            rad = math.radians(a)

            x1 = cx + tick_radius_inner * math.cos(rad)
            y1 = cy + tick_radius_inner * math.sin(rad)
            x2 = cx + tick_radius_outer * math.cos(rad)
            y2 = cy + tick_radius_outer * math.sin(rad)

            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        outer = QRectF(cx - size * 0.39, cy - size * 0.39, size * 0.78, size * 0.78)
        p.setPen(QPen(QColor("#050607"), 4))
        p.setBrush(QBrush(QColor("#070809")))
        p.drawEllipse(outer)

        bevel = QRectF(cx - size * 0.34, cy - size * 0.34, size * 0.68, size * 0.68)
        p.setPen(QPen(QColor("#22272b"), 3))
        p.setBrush(QBrush(QColor("#111417")))
        p.drawEllipse(bevel)

        body = QRectF(cx - size * 0.29, cy - size * 0.29, size * 0.58, size * 0.58)

        grad = QRadialGradient(QPointF(cx - size * 0.10, cy - size * 0.13), size * 0.38)
        grad.setColorAt(0.0, QColor("#3a3f43"))
        grad.setColorAt(0.55, QColor("#15191c"))
        grad.setColorAt(1.0, QColor("#050607"))

        p.setPen(QPen(QColor("#030405"), 2))
        p.setBrush(QBrush(grad))
        p.drawEllipse(body)

        if self._light_on:
            light = QRectF(
                cx - size * 0.27,
                cy - size * 0.27,
                size * 0.54,
                size * 0.54
            )

            light_grad = QRadialGradient(QPointF(cx, cy), size * 0.30)

            light_grad.setColorAt(0.0, QColor(
                self._light_color.red(),
                self._light_color.green(),
                self._light_color.blue(),
                230
            ))

            light_grad.setColorAt(0.45, QColor(
                self._light_color.red(),
                self._light_color.green(),
                self._light_color.blue(),
                150
            ))

            light_grad.setColorAt(0.8, QColor(
                self._light_color.red(),
                self._light_color.green(),
                self._light_color.blue(),
                70
            ))

            light_grad.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(light_grad))
            p.drawEllipse(light)

        rad = math.radians(angle)

        r1 = size * 0.08
        r2 = size * 0.24

        x1 = cx + r1 * math.cos(rad)
        y1 = cy + r1 * math.sin(rad)
        x2 = cx + r2 * math.cos(rad)
        y2 = cy + r2 * math.sin(rad)

        p.setPen(QPen(QColor("#f4f0e8"), 7, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush


class AviaVerticalToggle(QWidget):
    positionChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(50, 90)

        self._position = 0  # 0=верх, 1=центр, 2=низ
        self._circle_pos = 4

        self._positions = {
            0: 4,
            1: 27,
            2: 50,
        }

        self.animation = QPropertyAnimation(self, b"circle_pos")
        self.animation.setDuration(150)

        self.setCursor(Qt.PointingHandCursor)

    def get_circle_pos(self):
        return self._circle_pos

    def set_circle_pos(self, pos):
        self._circle_pos = pos
        self.update()

    circle_pos = pyqtProperty(int, get_circle_pos, set_circle_pos)

    def mousePressEvent(self, event):
        self.setPosition((self._position + 1) % 3)
        super().mousePressEvent(event)

    def position(self):
        return self._position

    def setPosition(self, position: int):
        position = max(0, min(2, position))

        if position == self._position:
            return

        self._position = position

        self.animation.stop()
        self.animation.setStartValue(self._circle_pos)
        self.animation.setEndValue(self._positions[position])
        self.animation.start()

        self.positionChanged.emit(position)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        bg_color = QColor("#151719")
        border_color = QColor("#050607")
        accent = QColor("#d8c89f")

        painter.setPen(QPen(border_color, 3))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(2, 2, 46, 86, 20, 20)

        # подсветка только НЕ в нижнем положении
        if self._position != 2:
            painter.setPen(QPen(accent, 2))
            painter.drawRoundedRect(5, 5, 40, 80, 18, 18)

        painter.setPen(QPen(QColor("#050607"), 2))
        painter.setBrush(QBrush(QColor("#e8dcc0")))
        painter.drawEllipse(QRect(7, int(self._circle_pos), 36, 36))

        painter.setPen(QPen(QColor("#ffffff"), 3, Qt.SolidLine, Qt.RoundCap))
        y = int(self._circle_pos) + 18
        painter.drawLine(18, y, 32, y)
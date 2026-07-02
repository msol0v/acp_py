from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient


class AviaLamp(QWidget):
    clicked = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(50, 50)

        self._on = False
        self._color = "green"  # "green" или "red"

    # --- управление ---
    def setOn(self, state: bool):
        self._on = state
        self.update()

    def isOn(self):
        return self._on

    def setColor(self, color: str):
        """
        color: "green" или "red"
        """
        self._color = color
        self.update()

    def mousePressEvent(self, event):
        self.clicked.emit()
        #self.setOn(not self._on)

    # --- палитры ---
    def _get_colors(self):
        if self._color == "red":
            if self._on:
                return (
                    QColor("#ff5a4f"),  # центр
                    QColor("#a8241c"),
                    QColor("#2a0a08"),
                    QColor(255, 80, 60, 60)  # glow
                )
            else:
                return (
                    QColor("#3a1a18"),
                    QColor("#1a0a09"),
                    QColor("#070303"),
                    None
                )
        else:  # green
            if self._on:
                return (
                    QColor("#6cff8f"),
                    QColor("#1f8f4a"),
                    QColor("#0a2a16"),
                    QColor(80, 255, 140, 60)
                )
            else:
                return (
                    QColor("#2a332d"),
                    QColor("#121615"),
                    QColor("#070909"),
                    None
                )

    # --- отрисовка ---
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        size = min(w, h)
        cx = w / 2
        cy = h / 2

        # корпус
        outer = QRectF(cx - size * 0.48, cy - size * 0.48, size * 0.96, size * 0.96)
        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(QColor("#0a0c0e")))
        p.drawEllipse(outer)

        # фаска
        bevel = QRectF(cx - size * 0.40, cy - size * 0.40, size * 0.80, size * 0.80)
        p.setPen(QPen(QColor("#22272b"), 2))
        p.setBrush(QBrush(QColor("#14181c")))
        p.drawEllipse(bevel)

        # цвета
        c1, c2, c3, glow_color = self._get_colors()

        # лампа
        lamp_rect = QRectF(cx - size * 0.32, cy - size * 0.32, size * 0.64, size * 0.64)

        grad = QRadialGradient(cx, cy, size * 0.35)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(0.5, c2)
        grad.setColorAt(1.0, c3)

        p.setPen(QPen(QColor("#020303"), 2))
        p.setBrush(QBrush(grad))
        p.drawEllipse(lamp_rect)

        # glow
        if self._on and glow_color:
            glow = QRadialGradient(cx, cy, size * 0.55)
            glow.setColorAt(0.0, glow_color)
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(QRectF(cx - size * 0.55, cy - size * 0.55,
                                size * 1.10, size * 1.10))



class AviaRectLamp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(59, 30)

        self._on = False

        # цвета
        self._color_on = QColor("#ff3b2f")
        self._color_off = QColor("#3a0d0d")

    # --- управление ---
    def on(self):
        self._on = True
        self.update()

    def off(self):
        self._on = False
        self.update()

    def setState(self, state: bool):
        self._on = state
        self.update()

    def isOn(self):
        return self._on

    # --- отрисовка ---
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # --- внешний корпус ---
        outer = QRectF(0, 0, w, h)
        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(QColor("#0c0f12")))
        p.drawRoundedRect(outer, 10, 10)

        # --- внутренняя рамка ---
        inner_frame = QRectF(4, 4, w - 8, h - 8)
        p.setPen(QPen(QColor("#1a1f24"), 2))
        p.setBrush(QBrush(QColor("#111417")))
        p.drawRoundedRect(inner_frame, 8, 8)

        # --- сама лампа ---
        lamp_rect = QRectF(8, 8, w - 16, h - 16)

        if self._on:
            base_color = self._color_on
            center_alpha = 240
            mid_alpha = 170
            edge_alpha = 60
        else:
            base_color = self._color_off
            center_alpha = 80
            mid_alpha = 40
            edge_alpha = 10

        grad = QRadialGradient(
            lamp_rect.center(),
            max(lamp_rect.width(), lamp_rect.height()) * 0.7
        )

        grad.setColorAt(0.0, QColor(base_color.red(), base_color.green(), base_color.blue(), center_alpha))
        grad.setColorAt(0.5, QColor(base_color.red(), base_color.green(), base_color.blue(), mid_alpha))
        grad.setColorAt(1.0, QColor(base_color.red(), base_color.green(), base_color.blue(), edge_alpha))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(lamp_rect, 6, 6)

        # --- лёгкий внешний glow (только в активе) ---
        if self._on:
            glow = QRadialGradient(
                lamp_rect.center(),
                max(w, h)
            )

            glow.setColorAt(0.0, QColor(255, 60, 40, 60))
            glow.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setBrush(QBrush(glow))
            p.drawRoundedRect(outer, 10, 10)

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient


class AviaLampToggleButton(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(80, 50)

        self._checked = False     # состояние кнопки
        self._lamp_on = False     # состояние лампы

        self._lamp_color = QColor("#6cff8f")  # только зелёный

        self.setCursor(Qt.PointingHandCursor)

    # ------------------ КНОПКА ------------------
    def isChecked(self):
        return self._checked

    def setChecked(self, state: bool):
        if self._checked == state:
            return

        self._checked = state
        self.toggled.emit(state)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)

    # ------------------ ЛАМПА ------------------
    def lampOn(self):
        self._lamp_on = True
        self.update()

    def lampOff(self):
        self._lamp_on = False
        self.update()

    def setLamp(self, state: bool):
        self._lamp_on = state
        self.update()

    # ------------------ РЕНДЕР ------------------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # ===== КОРПУС =====
        if self._checked:
            bg = QColor("#1e252b")   # нажата
        else:
            bg = QColor("#3a4650")   # отпущена

        outer = QRectF(1, 1, w - 2, h - 2)

        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(outer, 12, 12)

        # внутренняя фаска
        inner = QRectF(5, 5, w - 10, h - 10)
        p.setPen(QPen(QColor("#4a5862"), 1))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner, 9, 9)

        shadow = QRectF(4, 4, w - 8, h - 8)

        grad = QRadialGradient(shadow.center(), max(w, h))
        grad.setColorAt(0.0, QColor(0, 0, 0, 120))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(shadow, 10, 10)

        # ===== ЛАМПА =====
        lamp_size = 18
        lx = w - 28
        ly = (h - lamp_size) / 2

        cx = lx + lamp_size / 2
        cy = ly + lamp_size / 2

        # кольцо
        p.setPen(QPen(QColor("#050607"), 1))
        p.setBrush(QBrush(QColor("#0a0c0e")))
        p.drawEllipse(QRectF(lx - 3, ly - 3, lamp_size + 6, lamp_size + 6))

        # сама лампа
        if self._lamp_on:
            grad = QRadialGradient(cx, cy, lamp_size * 0.9)
            grad.setColorAt(0.0, QColor(108, 255, 143, 255))
            grad.setColorAt(0.5, QColor(40, 180, 90, 160))
            grad.setColorAt(1.0, QColor(10, 40, 20, 20))
        else:
            grad = QRadialGradient(cx, cy, lamp_size * 0.9)
            grad.setColorAt(0.0, QColor("#2a332d"))
            grad.setColorAt(0.6, QColor("#121615"))
            grad.setColorAt(1.0, QColor("#070909"))

        p.setPen(QPen(QColor("#020303"), 1))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(lx, ly, lamp_size, lamp_size))
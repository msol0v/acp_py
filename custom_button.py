from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QFont

GREEN_ON = QColor("#20ff4f")

ORANGE_ON = QColor("#ffb000")
ORANGE_DIM = QColor("#4a2b08")

TEXT_DIM = QColor("#4b5358")
TEXT_DIM_CHECKED = QColor("#6a737a")

TEXT_WHITE = QColor("#f2f2f2")

class AviaCallButton(QWidget):
    toggled = pyqtSignal(bool)
    clicked = pyqtSignal()

    def __init__(self, text="",parent=None):
        super().__init__(parent)

        self.setFixedSize(105, 72)

        self._text = str(text)
        self._checked = False

        # Три полоски: только постоянный зелёный свет
        self._bars_on = False
        self._bars_color = GREEN_ON

        # Мигание только текста оранжевым
        self._text_blink_enabled = False
        self._text_blink_visible = True
        self._blink_color = ORANGE_ON

        self.setCursor(Qt.PointingHandCursor)

    # ---------- состояние кнопки ----------
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
            self.clicked.emit()

    # ---------- текст ----------
    def setText(self, text: str):
        self._text = text
        self.update()

    def text(self):
        return self._text

    # ---------- мигание текста ----------
    def startTextBlink(self):
        self._text_blink_enabled = True
        self.update()

    def stopTextBlink(self):
        self._text_blink_enabled = False
        self._text_blink_visible = True
        self.update()

    def setBlinkVisible(self, visible: bool):
        if not self._text_blink_enabled:
            return

        self._text_blink_visible = visible
        self.update()

    # ---------- полоски ----------
    def barsOn(self):
        self._bars_on = True
        self.update()

    def barsOff(self):
        self._bars_on = False
        self.update()

    def setBars(self, state: bool):
        self._bars_on = state
        self.update()

    # ---------- отрисовка ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        outer = QRectF(1, 1, w - 2, h - 2)

        body_grad = QLinearGradient(0, 0, 0, h)

        if self._checked:
            body_grad.setColorAt(0.0, QColor("#14191d"))
            body_grad.setColorAt(0.5, QColor("#101417"))
            body_grad.setColorAt(1.0, QColor("#090b0d"))
        else:
            body_grad.setColorAt(0.0, QColor("#2a3136"))
            body_grad.setColorAt(0.45, QColor("#1c2226"))
            body_grad.setColorAt(1.0, QColor("#111518"))

        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(body_grad))
        p.drawRoundedRect(outer, 9, 9)

        inner = QRectF(5, 5, w - 10, h - 10)

        if self._checked:
            p.setPen(QPen(QColor("#080a0c"), 2))
        else:
            p.setPen(QPen(QColor("#3a444b"), 1))

        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner, 7, 7)

        if not self._checked:
            p.setPen(QPen(QColor(255, 255, 255, 28), 1))
            p.drawLine(12, 7, w - 12, 7)

        # ---------- три полоски ----------
        bar_w = w * 0.42
        bar_h = 4
        bar_x = (w - bar_w) / 2
        bar_y0 = 13
        bar_gap = 7

        if self._bars_on:
            color = self._bars_color
            glow = QColor(color.red(), color.green(), color.blue(), 90)

            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(glow))

            for i in range(3):
                y = bar_y0 + i * bar_gap
                p.drawRoundedRect(QRectF(bar_x - 2, y - 1, bar_w + 4, bar_h + 2), 2, 2)

            p.setBrush(QBrush(color))
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor("#4b5358")))

        for i in range(3):
            y = bar_y0 + i * bar_gap
            p.drawRoundedRect(QRectF(bar_x, y, bar_w, bar_h), 2, 2)

        # ---------- текст ----------
        if self._text.strip():

            font = QFont("Arial")
            font.setBold(True)
            font.setPointSize(15)
            p.setFont(font)

            if self._text_blink_enabled:
                if self._text_blink_visible:
                    text_color = self._blink_color
                else:
                    text_color = QColor("#3a2a18")
            else:
                text_color = QColor("#4b5358") if not self._checked else QColor("#6a737a")

            p.setPen(text_color)

            text_rect = QRectF(4, 34, w - 8, h - 36)
            p.drawText(text_rect, Qt.AlignCenter, self._text)

# =========================================================
# БАЗОВАЯ ОТРИСОВКА КОРПУСА
# =========================================================

class _AviaButtonBase(QWidget):

    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(105, 72)

        self._checked = False

        self.setCursor(Qt.PointingHandCursor)

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

    # ---------- общий корпус ----------
    def drawBase(self, p: QPainter):

        w = self.width()
        h = self.height()

        outer = QRectF(1, 1, w - 2, h - 2)

        body_grad = QLinearGradient(0, 0, 0, h)

        if self._checked:
            body_grad.setColorAt(0.0, QColor("#14191d"))
            body_grad.setColorAt(0.5, QColor("#101417"))
            body_grad.setColorAt(1.0, QColor("#090b0d"))
        else:
            body_grad.setColorAt(0.0, QColor("#2a3136"))
            body_grad.setColorAt(0.45, QColor("#1c2226"))
            body_grad.setColorAt(1.0, QColor("#111518"))

        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(body_grad))
        p.drawRoundedRect(outer, 9, 9)

        inner = QRectF(5, 5, w - 10, h - 10)

        if self._checked:
            p.setPen(QPen(QColor("#080a0c"), 2))
        else:
            p.setPen(QPen(QColor("#3a444b"), 1))

        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(inner, 7, 7)

        if not self._checked:
            p.setPen(QPen(QColor(255, 255, 255, 28), 1))
            p.drawLine(12, 7, w - 12, 7)


# =========================================================
# ВАРИАНТ 1
# Только нижняя надпись
# =========================================================

class AviaTextButton(_AviaButtonBase):

    def __init__(self, text="CALL", parent=None):
        super().__init__(parent)

        self._text = str(text)

    def setText(self, text):
        self._text = str(text)
        self.update()

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        self.drawBase(p)

        # нижний текст
        font = QFont("Arial")
        font.setBold(True)
        font.setPointSize(15)

        p.setFont(font)
        p.setPen(QColor("#f2f2f2"))

        text_rect = QRectF(4, 34, self.width() - 8, self.height() - 36)

        p.drawText(text_rect, Qt.AlignCenter, self._text)


# =========================================================
# ВАРИАНТ 2
# Верхняя светящаяся надпись + нижняя статичная
# =========================================================

class AviaDualTextButton(_AviaButtonBase):

    def __init__(self,
                 top_text="None",
                 bottom_text="None",
                 parent=None):

        super().__init__(parent)

        self._top_text = str(top_text)
        self._bottom_text = str(bottom_text)

        self._top_light = False

    # ---------- верхний текст ----------
    def topOn(self):
        self._top_light = True
        self.update()

    def topOff(self):
        self._top_light = False
        self.update()

    def setTopText(self, text):
        self._top_text = str(text)
        self.update()

    def setBottomText(self, text):
        self._bottom_text = str(text)
        self.update()

    # ---------- render ----------
    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        self.drawBase(p)

        w = self.width()

        # ===== верхняя надпись =====
        top_font = QFont("Arial")
        top_font.setBold(True)
        top_font.setPointSize(15)

        p.setFont(top_font)

        if self._top_light:
            p.setPen(GREEN_ON)
        else:
            p.setPen(QColor("#4b5358"))

        top_rect = QRectF(4, 10, w - 8, 18)

        p.drawText(top_rect, Qt.AlignCenter, self._top_text)

        # ===== нижняя надпись =====
        bottom_font = QFont("Arial")
        bottom_font.setBold(True)
        bottom_font.setPointSize(15)

        p.setFont(bottom_font)
        p.setPen(QColor("#f2f2f2"))

        bottom_rect = QRectF(4, 34, w - 8, self.height() - 36)

        p.drawText(bottom_rect, Qt.AlignCenter, self._bottom_text)
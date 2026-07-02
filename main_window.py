import faulthandler


faulthandler.enable()

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QDial, QPlainTextEdit, QLabel
from _ui_main_window import Ui_AvionicsPanelWindow
import os
import json
from arinc_handler import ArincWorker
from custom_toggle import AviaVerticalToggle
from custom_dial import AviaKnob
from custom_lamp import AviaLamp, AviaRectLamp, AviaLampToggleButton
from custom_button import AviaCallButton, AviaTextButton, AviaDualTextButton

import FaultsLists

base_dir = os.path.dirname(os.path.abspath(__file__))

ChannelsCodes = {
    'NO_CHAN': 0,
    'VHF1' : 1,
    'VHF2' : 2,
    'VHF3' : 3,
    'HF1' : 4,
    'HF2' : 5,
    'INT' : 6,
    'CAB' : 7,
    'PA' : 8,
    'INVALID' : 9,
}

# Lamps_Chan_Codes = {
#     7:1,
#     8:2,
#     9:3,
#     10:4,
#     11:5,
#     12:0,
#     13:0,
# }

class MainWindow(QtWidgets.QMainWindow):

    sig_run_arinc_handler = pyqtSignal()

    # AMU state signals
    sig_change_amu_channel = pyqtSignal(int)
    sig_change_amu_mech_state = pyqtSignal(int)
    sig_change_amu_att_state = pyqtSignal(int)
    sig_change_amu_pin_prog = pyqtSignal(int, bool)
    sig_change_amu_selcal_state = pyqtSignal(int, bool)
    sig_change_amu_voice_state = pyqtSignal(int)
    sig_blink = pyqtSignal(bool)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_AvionicsPanelWindow()
        self.ui.setupUi(self)

        def find_layout_containing_widget(layout, widget):
            if layout is None:
                return None

            for i in range(layout.count()):
                item = layout.itemAt(i)

                if item.widget() is widget:
                    return layout, i

                child_layout = item.layout()
                if child_layout is not None:
                    result = find_layout_containing_widget(child_layout, widget)
                    if result is not None:
                        return result

            return None

        def replace_dial(old_dial):
            result = find_layout_containing_widget(self.ui.panelFrame.layout(), old_dial)

            if result is None:
                print(f"Не найден layout для: {old_dial.objectName()}")
                return old_dial

            layout, index = result

            parent = old_dial.parentWidget()

            knob = AviaKnob(parent)
            knob.setObjectName(old_dial.objectName())
            knob.setMinimum(old_dial.minimum())
            knob.setMaximum(old_dial.maximum())
            knob.setValue(old_dial.value())
            knob.setFixedSize(old_dial.size())

            layout.removeWidget(old_dial)
            old_dial.setParent(None)
            old_dial.deleteLater()

            layout.insertWidget(index, knob, alignment=Qt.AlignCenter)

            return knob

        dial_names = [
            "dialVHF1", "dialVHF2", "dialVHF3",
            "dialHF1", "dialHF2",
            "dialINT", "dialCAB",
            "dialPA",
            "dialVOR1", "dialVOR2", "dialMKR", "dialLS",
            "dialADF1", "dialADF2", "dialMLS",
        ]

        for name in dial_names:
            old = getattr(self.ui, name, None)

            if old is not None:
                new_knob = replace_dial(old)
                setattr(self.ui, name, new_knob)

        self.ui.int_rad_toggle = AviaVerticalToggle()

        layout = QHBoxLayout(self.ui.intRadTogglePlaceholder)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.ui.int_rad_toggle)

        self.ui.lamps_buttons = []
        for i in range(1,15):
            lamp = AviaLampToggleButton()
            self.ui.lamps_buttons.append(lamp)
            lamp_placeholder = getattr(self.ui, f"lampPlaceholder_{i}")
            layout = QHBoxLayout(lamp_placeholder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.ui.lamps_buttons[i-1])

        self.ui.lamps = []
        for i in range(15, 19):
            lamp = AviaLamp()
            lamp.setColor('red')
            self.ui.lamps.append(lamp)
            lamp_placeholder = getattr(self.ui, f"lampPlaceholder_{i}")
            layout = QHBoxLayout(lamp_placeholder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.ui.lamps[i - 15])


        self.ui.lamps_rect = []
        for i in range(19,35):
            lamp = AviaRectLamp()
            self.ui.lamps_rect.append(lamp)
            lamp_placeholder = getattr(self.ui, f"lampPlaceholder_{i}")
            layout = QHBoxLayout(lamp_placeholder)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.ui.lamps_rect[i-19])

        def replace_buttons(old_button, i):
            result = find_layout_containing_widget(self.ui.panelFrame.layout(), old_button)

            if result is None:
                print(f"Не найден layout для: {old_button.objectName()}")
                return old_button

            layout, index = result

            parent = old_button.parentWidget()

            btn_text = ''
            if i in range(5):
                btn_text = 'CALL'
            elif i == 5:
                btn_text = 'MECH'
            elif i == 6:
                btn_text = 'ATT'
            elif i == 7:
                btn_text = ''

            if i in range(8):
                btn = AviaCallButton(text=btn_text, parent=parent)
            elif i == 8:
                btn = AviaDualTextButton('ON', 'VOICE', parent=parent)
            elif i == 9:
                btn = AviaTextButton('RESET', parent=parent)

            # btn.setObjectName(old_button.objectName())
            # # btn.setMinimum(old_button.minimum())
            # # btn.setMaximum(old_button.maximum())
            # btn.setValue(old_button.value())
            # btn.setFixedSize(old_button.size())

            layout.removeWidget(old_button)
            old_button.setParent(None)
            old_button.deleteLater()

            layout.insertWidget(index, btn, alignment=Qt.AlignCenter)

            return btn

        self.ui.call_buttons = []

        button_names = [
            "btnCall1", "btnCall2", "btnCall3",
            "btnCall4", "btnCall5", "btnMech", "btnAtt", "btnPA", "btnVoice", "btnReset"
        ]

        for i, name in enumerate(button_names):
            old = getattr(self.ui, name, None)

            if old is not None:
                new_btn = replace_buttons(old, i)
                self.ui.call_buttons.append(new_btn)
                setattr(self.ui, name, new_btn)

        self._blink_state = False
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(250)  # 2 Hz
        self._blink_timer.timeout.connect(self._update_blink_state)
        self._blink_timer.start()

        for i in range(7):
            self.sig_blink.connect(self.ui.call_buttons[i].setBlinkVisible)

        # Get com-ports names
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Treads
        self.arinc_thread = QThread()
        self.arinc_handler = ArincWorker(config['arinc-port'])
        self.arinc_handler.moveToThread(self.arinc_thread)

        self.arinc_handler.sig_error.connect(self.slot_arinc_handler_error)
        self.arinc_handler.sig_connected.connect(self.slot_arinc_handler_connected)
        self.sig_run_arinc_handler.connect(self.arinc_handler.slot_connect)


        #Signals show
        self.arinc_handler.sig_show_state.connect(self.slot_show_state)
        self.arinc_handler.sig_show_pn.connect(self.ui.labelPN.setText)
        self.arinc_handler.sig_show_pn.connect(self.check_pn)
        self.arinc_handler.sig_show_errors.connect(self.slot_show_errors)
        self.arinc_handler.sig_show_rvir.connect(self.slot_show_rvir)
        self.arinc_handler.sig_show_tx_code.connect(self.slot_show_tx_code)

        #lamp-buttons reactions
        for lamp_idx in range(14):
            self.ui.lamps_buttons[lamp_idx].toggled.connect(
                lambda state, idx=lamp_idx: self.slot_lamp_button_toggled(idx, state)
            )

        self.sig_change_amu_channel.connect(self.arinc_handler.change_amu_channel)
        self.sig_change_amu_mech_state.connect(self.arinc_handler.change_amu_mech_state)
        self.sig_change_amu_att_state.connect(self.arinc_handler.change_amu_att_state)
        self.sig_change_amu_pin_prog.connect(self.arinc_handler.change_amu_pin_prog)
        self.sig_change_amu_selcal_state.connect(self.arinc_handler.change_amu_selcal_state)
        self.sig_change_amu_voice_state.connect(self.arinc_handler.change_amu_voice_state)

        self.arinc_thread.start()
        self.sig_run_arinc_handler.emit()

        self.active_lamp = None
        self.pn_id_code = None
        self.last_tx_code = 0

        #TEST
        #self.ui.btnPA.toggled.connect(self.test_chan_show)

    def lamp_off(self):
        if self.active_lamp:
            self.active_lamp.lampOff()
            self.active_lamp = None

    def _update_blink_state(self):
        self._blink_state = not self._blink_state
        self.sig_blink.emit(self._blink_state)

    @pyqtSlot(str)
    def check_pn(self, pn_code: str):
        if self.pn_id_code is None or self.pn_id_code != pn_code:
            self.pn_id_code = pn_code
            if 'AB' in pn_code or 'AC' in pn_code or 'AA' in pn_code:
                for i in range(16):
                    lbl_name = f'lbl_faults_{i}'
                    fault_lbl: QLabel = getattr(self.ui, lbl_name, None)
                    fault_lbl.setText(FaultsLists.Faults_AA_AB_AC[i])
            else:
                for i in range(16):
                    lbl_name = f'lbl_faults_{i}'
                    fault_lbl: QLabel = getattr(self.ui, lbl_name, None)
                    fault_lbl.setText(FaultsLists.Faults_AD_AE[i])


    @pyqtSlot(int)
    def slot_lamp_button_toggled(self, lamp_button_idx, state):
        channel = 0
        if state:
            self.ui.lamps_buttons[lamp_button_idx].lampOn()
        else:
            self.ui.lamps_buttons[lamp_button_idx].lampOff()

        if lamp_button_idx in range(7, 12):
            self.ui.call_buttons[lamp_button_idx - 7].startTextBlink() if state else self.ui.call_buttons[lamp_button_idx - 7].stopTextBlink()
            if lamp_button_idx > 8:
                pin_prog_state = self.ui.lamps_buttons[lamp_button_idx-9].isChecked()
                if pin_prog_state:
                    self.sig_change_amu_selcal_state.emit(lamp_button_idx - 7, state)
                else:
                    self.sig_change_amu_selcal_state.emit(lamp_button_idx - 7, state)
                    self.ui.lamps_buttons[lamp_button_idx].setChecked(False)
                    self.ui.lamps_buttons[lamp_button_idx].lampOff()
                    return
            else:
                self.sig_change_amu_selcal_state.emit(lamp_button_idx - 7, state)

        if lamp_button_idx == 12:
            self.ui.call_buttons[lamp_button_idx - 7].startTextBlink() if state else self.ui.call_buttons[lamp_button_idx - 7].stopTextBlink()
            self.sig_change_amu_mech_state.emit(1 if state else 0)

        if lamp_button_idx == 13:
            self.ui.call_buttons[lamp_button_idx - 7].startTextBlink() if state else self.ui.call_buttons[lamp_button_idx - 7].stopTextBlink()
            self.sig_change_amu_att_state.emit(1 if state else 0)

        if lamp_button_idx in range(8):
            self.sig_change_amu_pin_prog.emit(lamp_button_idx, state)
            if lamp_button_idx < 3 and self.ui.lamps_buttons[lamp_button_idx+9].isChecked():
                self.slot_lamp_button_toggled(lamp_button_idx+9, False)





    @pyqtSlot(str, int, int, int)
    def slot_show_state(self, name, state, volume, start_range):
        dial: AviaKnob = getattr(self.ui, f'dial{name}')
        label: QLabel = getattr(self.ui, f'vol{name}')
        dial.setValue(volume)
        dial.setRange(start_range, 255)
        label.setText(f"{volume}")
        if state == 1:
            dial.on()
        else:
            dial.off()

    @pyqtSlot(list)
    def slot_show_errors(self, errors: list):
        for i, error in enumerate(errors, 0):
            if i in range(16):
                if error:
                    self.ui.lamps_rect[i].on()
                else:
                    self.ui.lamps_rect[i].off()
            else:
                if error:
                    self.ui.lamps[i-18].setOn(True)
                else:
                    self.ui.lamps[i-18].setOn(False)

    @pyqtSlot(int, int, int, int)
    def slot_show_rvir(self, reset: int, voice: int, alt_int: int, alt_rad: int):
        if reset == 1:
            self.ui.btnReset.setChecked(True)
            for i in range(7, 14):
                self.slot_lamp_button_toggled(i, False)
        else:
            self.ui.btnReset.setChecked(False)

        if voice == 1:
            self.ui.btnVoice.topOn()
        else:
            self.ui.btnVoice.topOff()

        if alt_int == 0 and alt_rad == 0:
            self.ui.int_rad_toggle.setPosition(1)
            return

        if alt_int == 1:
            self.ui.int_rad_toggle.setPosition(0)

        if alt_rad == 1:
            self.ui.int_rad_toggle.setPosition(2)

    @pyqtSlot(int)
    def slot_show_tx_code(self, code: int):
        #print(f'{code:04b}')
        if code == 0x0F:
            print('Invalid channel')
            return

        if self.last_tx_code == 0 and code == 0:
                        return
        if self.last_tx_code > 0:
            self.ui.call_buttons[self.last_tx_code - 1].barsOff()
        if code > 0:
            self.ui.call_buttons[code - 1].barsOn()
        self.sig_change_amu_channel.emit(code)
        self.last_tx_code = code
        self.ui.comboBox.setCurrentIndex(code)

    # def test_chan_show(self, state: bool):
    #     for i in range(50):
    #         if state:
    #             self.slot_show_tx_code(7)
    #         else:
    #             self.slot_show_tx_code(0)


    @pyqtSlot()
    def slot_arinc_handler_connected(self):
        print('arinc handler connected')

    @pyqtSlot(str)
    def slot_arinc_handler_error(self, error:str):
        QMessageBox.critical(self, "ARINC Handler Error", error)



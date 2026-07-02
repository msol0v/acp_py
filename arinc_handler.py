import time
from sys import exception
from time import sleep
from typing import Optional, Dict, List, Any, Callable
from functools import lru_cache, wraps
import json

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    QTimer,
    QThread,
    pyqtSlot,
    QIODevice,
    QByteArray
)
from PyQt5.QtSerialPort import QSerialPort

def reverse_number(n: int) -> int:
    '''Переворачивает число побитово'''
    reversed_value = 0
    for i in range(8):
        if n & (1 << i):
            reversed_value |= (1 << (7 - i))
    return reversed_value

def base8_to_int(label_octet: str) -> int:
    """
    Преобразует строку лейбла восьмиричной сс в int

    Args:
        label_octet: строка с восьмеричным числом (например, '352')

    Returns:
        int: значение метки (инвертированное)
    """
    decimal_value = int(label_octet, 8)
    return reverse_number(decimal_value)

def int_to_base8(label: int) -> str:
    r = reverse_number(label)
    return oct(r)

class HandlerRegistry:
    """
    Регистратор обработчиков слов Arinc

    Example:
        registry = HandlerRegistry()

        @registry.label_handler('352')
        def label_352(self, word):
            # обработка метки 352
            pass
    """

    def __init__(self):
        self.label_handlers: Dict[int, Callable] = {}  # Обработчики по меткам (ключ - int)
        self.rx_labels_int: Dict[int, str] = {}  # [int hex] = str base 8

    def label_handler(self, label: str):
        """
        Декоратор для регистрации обработчика метки

        Args:
            label: строка с восьмеричной меткой (например, '352')
        """

        def decorator(func):
            label_int = base8_to_int(label)
            self.label_handlers[label_int] = func
            self.rx_labels_int[label_int] = label
            return func

        return decorator

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

ID_PN = {
    0   : 'ACP 2788 AA 02',
    2   : 'ACP 2788 AB 04',
    4   : 'ACP 2788 AB 05',
    6   : 'ACP 2788 AB 06',
    8   : 'ACP 2788 AD 01',
    10  : 'ACP 2788 AD 02',
    12  : 'ACP 2788 AD 03',
    14  : 'ACP 2788 AD 04',
    1   : 'ACP 2788 AC 01',
    3   : 'ACP 2788 AC 02',
    5   : 'ACP 2788 AC 03',
    7   : 'ACP 2788 AC 04',
    9   : 'ACP 2788 AE 01',
    11  : 'ACP 2788 AE 02',
    13  : 'ACP 2788 AE 03',
    15  : 'ACP 2788 AE 04',
}



class ArincWorker(QObject):
    """
    Воркер для работы с ARINC в отдельном потоке.
    Читает порт, парсит слова и отправляет сигналы в главный поток.
    """

    # Сигналы для передачи данных в главный поток
    sig_error = pyqtSignal(str)
    sig_connected = pyqtSignal()
    sig_bus_activity = pyqtSignal(dict)
    sig_start_activity_timer = pyqtSignal()
    sig_timer_connecting_start = pyqtSignal()
    sig_timer_connecting_stop = pyqtSignal()

    sig_show_state = pyqtSignal(str, int, int, int)
    sig_show_pn = pyqtSignal(str)
    sig_show_errors = pyqtSignal(list)
    sig_show_rvir = pyqtSignal(int, int, int, int)
    sig_show_tx_code = pyqtSignal(int)

    # Общий сигнал для неизвестных меток (опционально)
    sig_unknown_label = pyqtSignal(int, int)  # label_int, word_int


    # Таймер отправки 301 слова
    sig_start_amu_tx  = pyqtSignal()
    sig_stop_amu_tx = pyqtSignal()

    def __init__(self, port_name: str):
        super().__init__()

        # Параметры порта
        self._port_name = port_name
        self._baud_rate = 115200
        self.port = None

        # Состояние
        self._connected = False
        self._waiting_for_version = True
        self.sdac_activity = {'sdac_0':False, 'sdac_1':False}

        # Буфер для накопления данных
        self._rx_buffer = b''

        # Регистр обработчиков (нужен только для маппинга, но сами обработчики не вызываются)
        self.registry = HandlerRegistry()
        self._register_handlers()  # Регистрируем метки для маппинга
        self.handlers = self.registry.label_handlers
        self.rx_labels_int = self.registry.rx_labels_int
        del self.registry #Освобождаем память. Регистрация уже прошла

        # Таймеры для периодической отправки (работают в этом же потоке)
        self._setup_timers()

        # Счетчик активности шины
        self._last_activity_time = time.time()

        self.errors = [0 for _ in range(20)]

        #### AMU STATUS ###
        self.amu_channel = 0
        self.amu_channels = [0, 0, 0, 0, 0]
        self.amu_mech_state = 0
        self.amu_att_state = 0
        self.amu_pin_prog = 0
        self.amu_selcal_state = 0
        self.amu_voice_state = 0
        ###################


    @pyqtSlot(int)
    def change_amu_channel(self, chan_idx: int):
        self.amu_channel = chan_idx

    @pyqtSlot(int)
    def change_amu_mech_state(self, amu_mech_state: int):
        self.amu_mech_state = amu_mech_state

    @pyqtSlot(int)
    def change_amu_att_state(self, amu_att_state: int):
        self.amu_att_state = amu_att_state

    @pyqtSlot(int, bool)
    def change_amu_pin_prog(self, pin_prog_bit: int, state: bool):
        if state:
            self.amu_pin_prog |= 1 << pin_prog_bit
        else:
            self.amu_pin_prog &= ~(1 << pin_prog_bit)

    @pyqtSlot(int, bool)
    def change_amu_selcal_state(self, chan_idx: int, state: bool):
        if state:
            self.amu_selcal_state |= 1 << chan_idx
        else:
            self.amu_selcal_state &= ~(1 << chan_idx)

    @pyqtSlot(int)
    def change_amu_voice_state(self, amu_voice_state: int):
        self.amu_voice_state = amu_voice_state

    @pyqtSlot()
    def slot_connect(self):
        """
        Слот для подключения к порту.
        Вызывается из главного потока через сигнал.
        """
        print(f"Connecting to {self._port_name}...")

        # Создаем и открываем порт
        self.port = QSerialPort()
        self.port.setPortName(self._port_name)
        self.port.setBaudRate(self._baud_rate)

        # Подключаем сигналы
        self.port.readyRead.connect(self.handle_ready_read)
        # Подключаем сигнал errorOccurred к слоту, который принимает параметр
        self.port.errorOccurred.connect(self.handle_error)

        # Открываем порт
        mode = QIODevice.OpenMode(QIODevice.ReadWrite)
        if not self.port.open(mode):
            self.stop()
            return False

        print(f"ARINC port {self._port_name} opened successfully")

        # Отправляем команду version
        self._waiting_for_version = True
        self.port.write('version\n'.encode('utf-8'))

        # Запускаем таймер активности
        self.sig_timer_connecting_start.emit()

        return True

    @pyqtSlot()
    def stop(self):
        """Остановка работы"""
        self.activity_timer.stop()

        if self.port and self.port.isOpen():
            self.port.close()
            self._connected = False

    @pyqtSlot(QSerialPort.SerialPortError)
    def handle_error(self, error):
        """Обработка ошибок порта"""
        if error != QSerialPort.NoError:  # Игнорируем "нет ошибки"
            error_string = f'Port {self._port_name} error\n\r{self.port.errorString()}' if self.port else "Unknown error"
            self.sig_error.emit(error_string)

    def _setup_timers(self):
        """Настройка таймеров"""

        # Таймеры отправки слов


        # Таймер проверки активности шины
        self.activity_timer = QTimer()
        self.activity_timer.setInterval(700)
        self.activity_timer.timeout.connect(self._check_activity)

        self.timer_connecting = QTimer()
        self.timer_connecting.setInterval(1000)
        self.timer_connecting.setSingleShot(True)
        self.sig_timer_connecting_start.connect(self.timer_connecting.start)
        self.sig_timer_connecting_stop.connect(self.timer_connecting.stop)
        self.timer_connecting.timeout.connect(self.slot_connecting_timeout)

        self.sig_start_activity_timer.connect(self.activity_timer.start)

        self.timer_amu_tx = QTimer()
        self.timer_amu_tx.setInterval(9)
        self.timer_amu_tx.timeout.connect(self.send_301)
        self.sig_start_amu_tx.connect(self.timer_amu_tx.start)
        self.sig_stop_amu_tx.connect(self.timer_amu_tx.stop)

    @pyqtSlot()
    def _check_activity(self):
        """Проверка активности шины"""
        if time.time() - self._last_activity_time > 1.0:
            # Нет активности более 1 секунды
            self.sdac_activity = {'sdac_0':False, 'sdac_1':False}
            self.sig_bus_activity.emit(self.sdac_activity)
            self.stop()
            self.sig_error.emit('Error: SDAC Bus empty more than 1 sec\n\rARINC Handler Stopped')
        else:
            self.sig_bus_activity.emit(self.sdac_activity)

    @pyqtSlot()
    def slot_connecting_timeout(self):
        self.stop()
        self.sig_error.emit('Timeout connecting to Fizika Pribor')


    @pyqtSlot()
    def handle_ready_read(self):
        """Обработка входящих данных (в потоке порта)"""
        # Читаем все доступные данные
        data = self.port.readAll()
        if data.isEmpty():
            return

        # Конвертируем в bytes и добавляем в буфер
        self._rx_buffer += bytes(data)

        # Обновляем время активности
        self._last_activity_time = time.time()

        # Обрабатываем все полные строки
        while True:
            line_end = self._rx_buffer.find(b'\n')
            if line_end == -1:
                break

            line = self._rx_buffer[:line_end + 1]
            self._rx_buffer = self._rx_buffer[line_end + 1:]

            # Обрабатываем строку
            self._process_line(line)

    def _process_line(self, line: bytes):
        """Обработка одной строки данных"""
        if not line:
            return

        # Обработка ответа на команду version
        if self._waiting_for_version:
            line_str = line.decode('utf-8', errors='ignore').strip()
            if line_str == 'ver.USB-BSCk0':
                self.sig_timer_connecting_stop.emit()
                self._connected = True
                self._waiting_for_version = False
                self.sig_connected.emit()
                self._configure_fizz()  # Настраиваем преобразователь
                QThread.msleep(300) #Ожидание, пока порты включатся
                self.sig_start_activity_timer.emit()
                self.sig_start_amu_tx.emit()
            return

        # Обработка ARINC слов
        if line.startswith(b'dat'):
            try:
                # datNxxxxYYYY\n

                chan = int(line[3:4])
                word_b: bytes = line[4 : -5]
                label_b = word_b[-1:]
                # Конвертируем hex в int
                word_int = int.from_bytes(word_b, 'big')
                label_int = int.from_bytes(label_b, 'big')

                # Обновляем активность
                self.sdac_activity[f'sdac_{chan}'] = True

                # Вызываем нужный сигнал в зависимости от метки
                self.call_word_handler(label_int, word_int)

            except ValueError as e:
                print(f"Error converting hex: {e}")
            except Exception as e:
                print(f"Error parsing ARINC word: {e}")

    def call_word_handler(self, label_int: int, word_int: int):
        _handler = self.handlers.get(label_int)
        if _handler is None:
            #print(f"No handler for label {oct(reverse_number(label_int))}")
            return

        _handler(self, word_int)

    def _configure_fizz(self):
        """Настройка преобразователя"""
        self.port.write('start 1\n'.encode('utf-8'))
        self.port.write('start 2\n'.encode('utf-8'))
        #QThread.msleep(50)
        #self.port.clear()


    # Методы для отправки данных
    def send_word_list(self, word_list: list):
        """Отправка списка слов ARINC"""
        if not self._connected:
            return
        for word in word_list:
            fizz_command = f'send 1 {word}'
            self.port.write((fizz_command + '\n').encode('utf-8'))
            self.port.flush()

    @pyqtSlot(bool)
    def slot_fizz_speed(self, is_high: bool):
        """Изменение скорости передачи"""
        if not self._connected:
            return
        cmd = 'transmitter_freq 1\n' if is_high else 'transmitter_freq 3\n'
        self.port.write(cmd.encode('utf-8'))


    @pyqtSlot()
    def send_301(self):
        label = reverse_number(0o301)
        label_2 = reverse_number(0o303)
        # for chan_idx, chan_state in enumerate(self.amu_channels, 1):
        #   print(f'idx: {chan_idx}, state: {chan_state}')
        word = (self.amu_voice_state << 29 | self.amu_selcal_state << 24 |
                self.amu_pin_prog << 16 | self.amu_att_state << 15 | self.amu_mech_state << 14 |
                (self.amu_channel << 10) | label)

        word = f'{word:08X}'
        word_2 = f'{label_2:08X}'

        self.send_word_list([word])

    def _words_1_16_decode(self,word: int) -> dict[str, int]:
        params = {
            'sdi' : (word >> 8) & 0x03,
            'tx_code' :(word >> 10) & 0x0F,
            'alt_radio' : (word >> 14) & 0x01,
            'alt_int' : (word >> 15) & 0x01,
            'volume' : (word >> 16) & 0xFF,
            'chan_state':(word >> 24) & 0x01,
            'voice' : (word >> 25) & 0x01,
            'reset' : (word >> 26) & 0x01,
            'errors' : (word >> 27) & 0x0F,
        }

        if params['reset'] == 1: params['tx_code'] = 0

        self.amu_voice_state = params['voice']

        self._errors_decode(params['errors'], False)
        self.sig_show_rvir.emit(params['reset'],params['voice'],params['alt_int'],params['alt_radio'])
        self.sig_show_tx_code.emit(params['tx_code'])
        return params

    def _errors_decode(self, errors: int, first_16: bool):
        if first_16:
            #print(f'{errors:016b}')
            for i in range(16):
                self.errors[i] = (errors >> i) & 0x01
        else:
            for i in range(16, 20):
                self.errors[i] = (errors >> (i - 16)) & 0x01

        self.sig_show_errors.emit(self.errors)

    def _register_handlers(self):
        """Регистрация меток (нужно только для маппинга)"""

        @self.registry.label_handler('300')
        def label_300(self, word: int):
            label = 0o300
            self_test = (word >> 10) & 0x01
            errors_16 = (word >> 11) & 0xFFFF
            #print(f'{errors_16:016b}')
            acp_id = ID_PN.get((word >> 27) & 0x0F)
            self.sig_show_pn.emit('Unknown ID' if acp_id is None else acp_id)
            self._errors_decode(errors_16, True)

        @self.registry.label_handler('210')
        def label_210(self, word: int):
            label = 0o210
            decoded_word = self._words_1_16_decode(word)
            match decoded_word['sdi']:
                case 1: self.sig_show_state.emit('VHF1', decoded_word['chan_state'], decoded_word['volume'], 8)
                case 2: self.sig_show_state.emit('VHF2', decoded_word['chan_state'], decoded_word['volume'], 8)
                case 3: self.sig_show_state.emit('VHF3', decoded_word['chan_state'], decoded_word['volume'], 8)

        @self.registry.label_handler('211')
        def label_211(self, word: int):
            label = 0o211
            decoded_word = self._words_1_16_decode(word)
            match decoded_word['sdi']:
                case 1:
                    self.sig_show_state.emit('HF1', decoded_word['chan_state'], decoded_word['volume'], 8)
                case 2:
                    self.sig_show_state.emit('HF2', decoded_word['chan_state'], decoded_word['volume'], 8)

        @self.registry.label_handler('215')
        def label_215(self, word: int):
            label = 0o215
            decoded_word = self._words_1_16_decode(word)
            match decoded_word['sdi']:
                case 1:
                    self.sig_show_state.emit('INT', decoded_word['chan_state'], decoded_word['volume'], 0)
                case 2:
                    self.sig_show_state.emit('CAB', decoded_word['chan_state'], decoded_word['volume'], 0)

        @self.registry.label_handler('212')
        def label_212(self, word: int):
            label = 0o212
            decoded_word = self._words_1_16_decode(word)
            match decoded_word['sdi']:
                case 1:
                    self.sig_show_state.emit('ADF1', decoded_word['chan_state'], decoded_word['volume'], 0)
                case 2:
                    self.sig_show_state.emit('ADF2', decoded_word['chan_state'], decoded_word['volume'], 0)
                case 3:
                    self.sig_show_state.emit('PA', decoded_word['chan_state'], decoded_word['volume'], 0)

        @self.registry.label_handler('213')
        def label_213(self, word: int):
            label = 0o213
            decoded_word = self._words_1_16_decode(word)
            match decoded_word['sdi']:
                case 1:
                    self.sig_show_state.emit('VOR1', decoded_word['chan_state'], decoded_word['volume'], 0)
                case 2:
                    self.sig_show_state.emit('VOR2', decoded_word['chan_state'], decoded_word['volume'], 0)
                case 3:
                    self.sig_show_state.emit('MKR', decoded_word['chan_state'], decoded_word['volume'], 0)

        @self.registry.label_handler('217')
        def label_217(self, word: int):
            label = 0o217
            decoded_word = self._words_1_16_decode(word)
            self.sig_show_state.emit('LS', decoded_word['chan_state'], decoded_word['volume'], 0)

        @self.registry.label_handler('220')
        def label_220(self, word: int):
            label = 0o220
            pass
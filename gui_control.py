"""
Dobot Nova 5 - PyQt5 GUI + PS5 Joystick Kontrol
joystick_control.py üzerine görsel arayüz.
"""

import sys
import os
import re
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "TCP-IP-Python-V4"))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout,
    QSlider, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QPalette

import pygame
from dobot_api import DobotApiDashboard

from joystick_control import (
    JoystickRobotController, ROBOT_IP, DASHBOARD_PORT,
    HOME_JOINTS, SURGERY_JOINTS, MOVJ_SPEED,
    MODE_JOINT, MODE_TOOL, SPEED_MIN, SPEED_MAX, SPEED_STEP,
    DEADZONE, LOOP_HZ,
    AXIS_LX, AXIS_LY, AXIS_L2, AXIS_RX, AXIS_RY, AXIS_R2,
    BTN_CROSS, BTN_CIRCLE, BTN_TRIANGLE, BTN_SQUARE,
    BTN_L1, BTN_R1, BTN_SHARE, BTN_OPTIONS, BTN_PS, BTN_L3,
)


class SignalBridge(QObject):
    """Thread-safe sinyal köprüsü: worker thread → GUI"""
    log = pyqtSignal(str)
    status_update = pyqtSignal(dict)


class RobotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.controller = JoystickRobotController(ROBOT_IP)
        self.signals = SignalBridge()
        self.signals.log.connect(self._append_log)

        self.joystick = None
        self.worker_running = False

        self._init_ui()
        self._redirect_print()

        # Durum güncelleme timer'ı
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._poll_status)
        self.status_timer.start(500)

    def _init_ui(self):
        self.setWindowTitle("Dobot Nova 5 - Diş Sağlığı Robot Kontrol")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; }
            QGroupBox {
                color: #89b4fa;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 12px;
                font-weight: bold;
            }
            QGroupBox::title { subcontrol-position: top left; padding: 2px 8px; }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: 1px solid #585b70;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:pressed { background-color: #6c7086; }
            QTextEdit {
                background-color: #11111b;
                color: #a6adc8;
                border: 1px solid #45475a;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)

        # === ÜST SATIR: Durum + Mod ===
        top_row = QHBoxLayout()

        # Robot durumu
        status_group = QGroupBox("Robot Durumu")
        status_grid = QGridLayout(status_group)

        self.lbl_connection = self._status_label("Bağlantı Yok", "#f38ba8")
        self.lbl_robot_mode = self._status_label("---")
        self.lbl_errors = self._status_label("---")

        status_grid.addWidget(QLabel("Bağlantı:"), 0, 0)
        status_grid.addWidget(self.lbl_connection, 0, 1)
        status_grid.addWidget(QLabel("Robot Mode:"), 1, 0)
        status_grid.addWidget(self.lbl_robot_mode, 1, 1)
        status_grid.addWidget(QLabel("Hatalar:"), 2, 0)
        status_grid.addWidget(self.lbl_errors, 2, 1)

        top_row.addWidget(status_group)

        # Kontrol modu
        mode_group = QGroupBox("Kontrol Modu")
        mode_layout = QVBoxLayout(mode_group)

        self.lbl_mode = QLabel("EKLEM")
        self.lbl_mode.setFont(QFont("Arial", 28, QFont.Bold))
        self.lbl_mode.setAlignment(Qt.AlignCenter)
        self.lbl_mode.setStyleSheet("color: #a6e3a1;")
        mode_layout.addWidget(self.lbl_mode)

        self.lbl_active_jog = QLabel("---")
        self.lbl_active_jog.setFont(QFont("Arial", 14))
        self.lbl_active_jog.setAlignment(Qt.AlignCenter)
        self.lbl_active_jog.setStyleSheet("color: #f9e2af;")
        mode_layout.addWidget(self.lbl_active_jog)

        top_row.addWidget(mode_group)

        # Hız
        speed_group = QGroupBox("Hız")
        speed_layout = QVBoxLayout(speed_group)

        self.lbl_speed = QLabel(f"%{self.controller.speed}")
        self.lbl_speed.setFont(QFont("Arial", 28, QFont.Bold))
        self.lbl_speed.setAlignment(Qt.AlignCenter)
        self.lbl_speed.setStyleSheet("color: #89b4fa;")
        speed_layout.addWidget(self.lbl_speed)

        self.speed_bar = QProgressBar()
        self.speed_bar.setRange(SPEED_MIN, SPEED_MAX)
        self.speed_bar.setValue(self.controller.speed)
        self.speed_bar.setTextVisible(False)
        self.speed_bar.setFixedHeight(12)
        self.speed_bar.setStyleSheet("""
            QProgressBar { background-color: #313244; border-radius: 6px; }
            QProgressBar::chunk { background-color: #89b4fa; border-radius: 6px; }
        """)
        speed_layout.addWidget(self.speed_bar)

        top_row.addWidget(speed_group)

        # Tool mesafesi
        tool_group = QGroupBox("Tool Mesafesi")
        tool_layout = QVBoxLayout(tool_group)

        self.lbl_tool_dist = QLabel(f"{self.controller.tool_distance}mm")
        self.lbl_tool_dist.setFont(QFont("Arial", 18, QFont.Bold))
        self.lbl_tool_dist.setAlignment(Qt.AlignCenter)
        self.lbl_tool_dist.setStyleSheet("color: #cba6f7;")
        tool_layout.addWidget(self.lbl_tool_dist)

        self.slider_tool = QSlider(Qt.Horizontal)
        self.slider_tool.setRange(10, 500)  # 1cm - 50cm
        self.slider_tool.setValue(self.controller.tool_distance)
        self.slider_tool.setTickInterval(50)
        self.slider_tool.setStyleSheet("""
            QSlider::groove:horizontal { background: #313244; height: 8px; border-radius: 4px; }
            QSlider::handle:horizontal { background: #cba6f7; width: 18px; margin: -5px 0; border-radius: 9px; }
            QSlider::sub-page:horizontal { background: #cba6f7; border-radius: 4px; }
        """)
        self.slider_tool.valueChanged.connect(self._on_tool_slider_changed)
        self.slider_tool.sliderReleased.connect(self._on_tool_slider_released)
        tool_layout.addWidget(self.slider_tool)

        self.lbl_tool_cm = QLabel(f"{self.controller.tool_distance/10:.0f} cm")
        self.lbl_tool_cm.setAlignment(Qt.AlignCenter)
        self.lbl_tool_cm.setStyleSheet("color: #6c7086;")
        tool_layout.addWidget(self.lbl_tool_cm)

        top_row.addWidget(tool_group)
        main_layout.addLayout(top_row)

        # === ORTA SATIR: Pozisyon Butonları ===
        pos_group = QGroupBox("Pozisyon Kontrol")
        pos_layout = QHBoxLayout(pos_group)

        self.btn_home = QPushButton("◄ HOME GİT")
        self.btn_home.setStyleSheet("""
            QPushButton { background-color: #1e66f5; color: white; font-size: 14px; padding: 10px; }
            QPushButton:hover { background-color: #2a7bff; }
        """)
        self.btn_home.clicked.connect(lambda: self._run_async(
            lambda: self.controller.go_to_position(self.controller.home_joints, "HOME")
        ))

        self.btn_save_home = QPushButton("HOME\nKAYDET")
        self.btn_save_home.setStyleSheet("""
            QPushButton { background-color: #04a5e5; color: white; font-size: 11px; padding: 8px; }
            QPushButton:hover { background-color: #22bbff; }
        """)
        self.btn_save_home.clicked.connect(lambda: self._run_async(self.controller.save_home))

        self.btn_surgery = QPushButton("AMELİYAT GİT ►")
        self.btn_surgery.setStyleSheet("""
            QPushButton { background-color: #e64553; color: white; font-size: 14px; padding: 10px; }
            QPushButton:hover { background-color: #ff5566; }
        """)
        self.btn_surgery.clicked.connect(lambda: self._run_async(
            lambda: self.controller.go_to_position(self.controller.surgery_joints, "AMELİYAT")
        ))

        self.btn_save_surgery = QPushButton("AMELİYAT\nKAYDET")
        self.btn_save_surgery.setStyleSheet("""
            QPushButton { background-color: #df8e1d; color: white; font-size: 11px; padding: 8px; }
            QPushButton:hover { background-color: #ffaa22; }
        """)
        self.btn_save_surgery.clicked.connect(lambda: self._run_async(self.controller.save_surgery))

        self.btn_enable = QPushButton("ENABLE")
        self.btn_enable.setStyleSheet("""
            QPushButton { background-color: #40a02b; color: white; font-size: 14px; padding: 12px; }
            QPushButton:hover { background-color: #50c030; }
        """)
        self.btn_enable.clicked.connect(lambda: self._run_async(self.controller.enable_robot))

        self.btn_stop = QPushButton("DURDUR")
        self.btn_stop.setStyleSheet("""
            QPushButton { background-color: #fe640b; color: white; font-size: 14px; padding: 12px; }
            QPushButton:hover { background-color: #ff7722; }
        """)
        self.btn_stop.clicked.connect(self.controller._force_stop)

        self.btn_emergency = QPushButton("ACİL STOP")
        self.btn_emergency.setStyleSheet("""
            QPushButton { background-color: #d20f39; color: white; font-size: 14px;
                          padding: 12px; border: 2px solid #ff0000; }
            QPushButton:hover { background-color: #ff1144; }
        """)
        self.btn_emergency.clicked.connect(lambda: self._run_async(self.controller.disable_robot))

        pos_layout.addWidget(self.btn_save_home)
        pos_layout.addWidget(self.btn_home)
        pos_layout.addWidget(self.btn_surgery)
        pos_layout.addWidget(self.btn_save_surgery)
        pos_layout.addWidget(self.btn_enable)
        pos_layout.addWidget(self.btn_stop)
        pos_layout.addWidget(self.btn_emergency)

        main_layout.addWidget(pos_group)

        # === JOYSTICK HARİTASI ===
        map_group = QGroupBox("Joystick Haritası")
        map_layout = QHBoxLayout(map_group)

        eklem_text = (
            "EKLEM MODU\n"
            "Sol Analog Y → J1 taban\n"
            "Sol Analog X → J2 omuz\n"
            "Sağ Analog Y → J3 dirsek\n"
            "Sağ Analog X → J4 bilek\n"
            "L2/R2 → J5 | D-Pad Y → J6"
        )
        tool_text = (
            "TOOL MODU\n"
            "Sol Analog Y → X ileri/geri\n"
            "Sol Analog X → Y sol/sağ\n"
            "Sağ Analog Y → Z yukarı/aşağı\n"
            "Sağ Analog X → Rz dönüş\n"
            "L2/R2 → Rx | D-Pad Y → Ry"
        )

        lbl_eklem = QLabel(eklem_text)
        lbl_eklem.setFont(QFont("monospace", 10))
        lbl_eklem.setStyleSheet("color: #a6e3a1; padding: 8px;")

        lbl_tool = QLabel(tool_text)
        lbl_tool.setFont(QFont("monospace", 10))
        lbl_tool.setStyleSheet("color: #f9e2af; padding: 8px;")

        lbl_btns = QLabel(
            "BUTONLAR\n"
            "SHARE → Mod değiştir\n"
            "△/X → Hız +/-\n"
            "□ → Durdur\n"
            "R1 → Enable | L1 → Disable\n"
            "D-Pad ◄/► → Home/Ameliyat"
        )
        lbl_btns.setFont(QFont("monospace", 10))
        lbl_btns.setStyleSheet("color: #89b4fa; padding: 8px;")

        map_layout.addWidget(lbl_eklem)
        map_layout.addWidget(self._vsep())
        map_layout.addWidget(lbl_tool)
        map_layout.addWidget(self._vsep())
        map_layout.addWidget(lbl_btns)

        main_layout.addWidget(map_group)

        # === LOG ===
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # === ALT BAR: Başlat/Durdur ===
        bottom = QHBoxLayout()
        self.btn_start = QPushButton("JOYSTICK BAŞLAT")
        self.btn_start.setStyleSheet("""
            QPushButton { background-color: #40a02b; color: white; font-size: 15px; padding: 10px; }
            QPushButton:hover { background-color: #50c030; }
        """)
        self.btn_start.clicked.connect(self._start_worker)

        self.btn_quit = QPushButton("KAPAT")
        self.btn_quit.setStyleSheet("""
            QPushButton { background-color: #6c7086; color: white; font-size: 15px; padding: 10px; }
        """)
        self.btn_quit.clicked.connect(self.close)

        bottom.addWidget(self.btn_start, stretch=3)
        bottom.addWidget(self.btn_quit, stretch=1)
        main_layout.addLayout(bottom)

    def _status_label(self, text, color="#cdd6f4"):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 12, QFont.Bold))
        lbl.setStyleSheet(f"color: {color};")
        return lbl

    def _vsep(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #45475a;")
        return sep

    def _redirect_print(self):
        """print() çıktılarını GUI log'a yönlendir"""
        import builtins
        original_print = builtins.print
        def gui_print(*args, **kwargs):
            text = " ".join(str(a) for a in args)
            self.signals.log.emit(text)
            original_print(*args, **kwargs)
        builtins.print = gui_print

    def _append_log(self, text):
        # Durum sinyali kontrolü
        if text.startswith("__STATE__:"):
            state = text.split(":")[1]
            self._set_start_btn_state(state)
            return
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def _on_tool_slider_changed(self, value):
        """Slider sürüklenirken sadece etiketi güncelle"""
        self.lbl_tool_dist.setText(f"{value}mm")
        self.lbl_tool_cm.setText(f"{value/10:.0f} cm")

    def _on_tool_slider_released(self):
        """Slider bırakıldığında robota gönder ve kaydet"""
        value = self.slider_tool.value()
        self._run_async(lambda: self.controller.set_tool_distance(value))

    def _run_async(self, func):
        threading.Thread(target=func, daemon=True).start()

    def _poll_status(self):
        """GUI durum güncellemesi (ana thread'de çalışır)"""
        c = self.controller

        # Bağlantı
        if c.dashboard:
            self.lbl_connection.setText(ROBOT_IP)
            self.lbl_connection.setStyleSheet("color: #a6e3a1; font-weight: bold;")
        else:
            self.lbl_connection.setText("Bağlantı Yok")
            self.lbl_connection.setStyleSheet("color: #f38ba8; font-weight: bold;")

        # Mod
        self.lbl_mode.setText(c.mode)
        if c.mode == MODE_TOOL:
            self.lbl_mode.setStyleSheet("color: #f9e2af; font-size: 28px; font-weight: bold;")
        else:
            self.lbl_mode.setStyleSheet("color: #a6e3a1; font-size: 28px; font-weight: bold;")

        # Aktif jog
        if c.active_jog:
            self.lbl_active_jog.setText(f"Hareket: {c.active_jog}")
            self.lbl_active_jog.setStyleSheet("color: #f9e2af; font-size: 14px;")
        else:
            self.lbl_active_jog.setText("Beklemede")
            self.lbl_active_jog.setStyleSheet("color: #6c7086; font-size: 14px;")

        # Hız
        self.lbl_speed.setText(f"%{c.speed}")
        self.speed_bar.setValue(c.speed)

        # Tool mesafesi (slider hareket etmiyorken güncelle)
        if not self.slider_tool.isSliderDown():
            self.lbl_tool_dist.setText(f"{c.tool_distance}mm")
            self.lbl_tool_cm.setText(f"{c.tool_distance/10:.0f} cm")

        # Hata
        if c.error_state:
            self.lbl_errors.setText("HATA!")
            self.lbl_errors.setStyleSheet("color: #f38ba8; font-weight: bold;")
        else:
            self.lbl_errors.setText("Yok")
            self.lbl_errors.setStyleSheet("color: #a6e3a1; font-weight: bold;")

    def _set_start_btn_state(self, state):
        """Başlat butonunun durumunu ayarla: 'ready', 'running', 'no_joystick', 'no_robot'"""
        styles = {
            "ready": ("JOYSTICK BAŞLAT", True,
                "QPushButton { background-color: #40a02b; color: white; font-size: 15px; padding: 10px; }"
                "QPushButton:hover { background-color: #50c030; }"),
            "running": ("ÇALIŞIYOR", False,
                "QPushButton { background-color: #1e66f5; color: white; font-size: 15px; padding: 10px; }"),
            "no_joystick": ("JOYSTICK BULUNAMADI - TEKRAR DENE", True,
                "QPushButton { background-color: #d20f39; color: white; font-size: 15px; padding: 10px; }"
                "QPushButton:hover { background-color: #ff1144; }"),
            "no_robot": ("ROBOT BAĞLANTI HATASI - TEKRAR DENE", True,
                "QPushButton { background-color: #d20f39; color: white; font-size: 15px; padding: 10px; }"
                "QPushButton:hover { background-color: #ff1144; }"),
        }
        text, enabled, style = styles[state]
        self.btn_start.setText(text)
        self.btn_start.setEnabled(enabled)
        self.btn_start.setStyleSheet(style)

    def _start_worker(self):
        if self.worker_running:
            return
        self._set_start_btn_state("running")
        self.worker_running = True
        threading.Thread(target=self._joystick_loop, daemon=True).start()

    def _joystick_loop(self):
        """Joystick kontrol döngüsü (ayrı thread)"""
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("[HATA] Joystick bulunamadı! Bağlayıp tekrar dene.")
            self.worker_running = False
            self.signals.log.emit("__STATE__:no_joystick")
            pygame.quit()
            return

        js = pygame.joystick.Joystick(0)
        js.init()
        print(f"[OK] Joystick: {js.get_name()}")

        if not self.controller.connect():
            self.worker_running = False
            self.signals.log.emit("__STATE__:no_robot")
            js.quit()
            pygame.quit()
            return

        self.controller.prepare_robot()
        self.controller.running = True
        loop_delay = 1.0 / LOOP_HZ

        try:
            while self.controller.running and self.worker_running:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self.controller._handle_button(event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        self.controller._handle_dpad(event.value)

                self.controller._handle_axes(js)
                time.sleep(loop_delay)

        except Exception as e:
            print(f"[HATA] Joystick döngüsü: {e}")
        finally:
            self.controller._force_stop()
            self.controller.disconnect()
            js.quit()
            pygame.quit()
            self.worker_running = False
            self.signals.log.emit("__STATE__:ready")
            print("[OK] Joystick durduruldu")

    def closeEvent(self, event):
        self.controller.running = False
        self.worker_running = False
        time.sleep(0.3)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#1e1e2e"))
    palette.setColor(QPalette.WindowText, QColor("#cdd6f4"))
    app.setPalette(palette)

    window = RobotGUI()
    window.show()
    sys.exit(app.exec_())

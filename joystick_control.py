"""
Dobot Nova 5 - PS5 DualSense Joystick Kontrol (Çift Mod)
TCP/IP V4 protokolü üzerinden MoveJog komutuyla robot kontrolü.

İki kontrol modu:
  [EKLEM MODU] - Kabaca pozisyonlama (J1-J6)
  [TOOL MODU]  - Hassas ayar, tool noktası etrafında hareket

R3 butonu ile modlar arası geçiş yapılır.

Kontrol Şeması:
  EKLEM MODU:                      TOOL MODU:
  Sol Analog Y : J1 taban          Sol Analog Y : X ileri/geri
  Sol Analog X : J2 omuz           Sol Analog X : Y sol/sağ
  Sağ Analog Y : J3 dirsek         Sağ Analog Y : Z yukarı/aşağı
  Sağ Analog X : J4 bilek 1        Sağ Analog X : Rz dönüş
  L2 / R2      : J5 bilek 2        L2 / R2      : Rx dönüş
  D-Pad Y      : J6 uç dönüş      D-Pad Y      : Ry dönüş

  Butonlar:
    R3             → Mod değiştir (Eklem ↔ Tool)
    X (Cross)      → Hız azalt
    Üçgen          → Hız artır
    Kare           → Robotu durdur
    Daire          → Hataları temizle
    L1             → Robotu devre dışı bırak
    R1             → Robotu etkinleştir
    Options        → Çıkış
    PS (Home)      → Acil durum
"""

import sys
import os

# PyInstaller bundle veya normal Python çalışmasında doğru klasörü bul
def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

_BASE_DIR = _app_dir()
sys.path.insert(0, os.path.join(_BASE_DIR, "TCP-IP-Python-V4"))

import pygame
from dobot_api import DobotApiDashboard
import time


# =============================================================================
# AYARLAR
# =============================================================================

import json as _json

SETTINGS_FILE = os.path.join(_BASE_DIR, "settings.json")
POSITIONS_FILE = os.path.join(_BASE_DIR, "positions.json")

# Varsayılan ayarlar
_DEFAULTS = {
    "robot_ip": "192.168.5.1",
    "dashboard_port": 29999,
    "deadzone": 0.15,
    "loop_hz": 20,
    "speed_default": 30,
    "speed_min": 5,
    "speed_max": 100,
    "speed_step": 1,
    "jog_vel_joint": 50,
    "jog_acc_joint": 30,
    "jog_vel_linear": 50,
    "jog_acc_linear": 30,
    "tool_index": 1,
    "default_tool_distance": 350,
    "movj_speed": 30,
    "min_jog_hold": 0.15,
    "idle_before_stop": 0.15,
    "min_switch_time": 0.15
}

def _load_settings():
    """settings.json'dan ayarları yükle, yoksa varsayılanları kullan ve dosyayı oluştur"""
    settings = dict(_DEFAULTS)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                user = _json.load(f)
            settings.update(user)
        except Exception as e:
            print(f"[AYAR] settings.json okunamadı: {e}")
    else:
        with open(SETTINGS_FILE, 'w') as f:
            _json.dump(_DEFAULTS, f, indent=2)
        print(f"[AYAR] settings.json oluşturuldu: {SETTINGS_FILE}")
    return settings

_S = _load_settings()

ROBOT_IP = _S["robot_ip"]
DASHBOARD_PORT = _S["dashboard_port"]
DEADZONE = _S["deadzone"]
LOOP_HZ = _S["loop_hz"]
SPEED_DEFAULT = _S["speed_default"]
SPEED_MIN = _S["speed_min"]
SPEED_MAX = _S["speed_max"]
SPEED_STEP = _S["speed_step"]
JOG_VEL_JOINT = _S["jog_vel_joint"]
JOG_ACC_JOINT = _S["jog_acc_joint"]
JOG_VEL_LINEAR = _S["jog_vel_linear"]
JOG_ACC_LINEAR = _S["jog_acc_linear"]
TOOL_INDEX = _S["tool_index"]
DEFAULT_TOOL_DISTANCE = _S["default_tool_distance"]
MOVJ_SPEED = _S["movj_speed"]
MIN_JOG_HOLD = _S["min_jog_hold"]
IDLE_BEFORE_STOP = _S["idle_before_stop"]
MIN_SWITCH_TIME = _S["min_switch_time"]

HOME_JOINTS = None
SURGERY_JOINTS = None

# PS5 DualSense buton ve axis indeksleri - Windows / Linux farklı
import platform as _platform
if _platform.system() == "Windows":
    # Windows (pygame 2.6 + DualSense - 17 buton)
    # --- DOĞRULANMIŞ test sonuçları ---
    BTN_CROSS      = 0    # ✓ Hız azalt
    BTN_CIRCLE     = 1    # ✓ Drag modu
    BTN_SQUARE     = 2    # ✓ ACİL STOP
    BTN_TRIANGLE   = 3    # ✓ Hız artır
    BTN_SHARE      = 4    # ✓ Mod değiştir (Linux SHARE: toggle_mode)
    BTN_PS         = 5    # ✓ (atanmamış - kullanıcı isteği)
    BTN_OPTIONS    = 6    # ✓ Durdur (force_stop)
    BTN_L3         = 7    # ✓ Home KAYDET (Linux L3)
    BTN_R3         = 8    # ✓ Ameliyat KAYDET (Linux R3)
    BTN_L1         = 9    # ✓ Disable robot (Linux L1)
    BTN_R1         = 10   # ✓ Enable robot (Linux R1)
    BTN_DPAD_UP    = 11   # ✓ D-Pad Yukarı → J6+ (eklem) / Rz+ (tool)
    BTN_DPAD_DOWN  = 12   # ✓ D-Pad Aşağı  → J6- (eklem) / Rz- (tool)
    BTN_HOME_GO    = 13   # ✓ D-Pad Sol → HOME'a git
    BTN_SURGERY_GO = 14   # ✓ D-Pad Sağ → Ameliyat'a git
    # B15: Touchpad       (atanmamış)
    # B16: Mikrofon       Windows OS yakalıyor, event gelmez
    BTN_L2      = -91     # axis 4, buton olarak yok
    BTN_R2      = -92     # axis 5, buton olarak yok
else:
    # Linux SDL2
    BTN_CROSS      = 0
    BTN_CIRCLE     = 1
    BTN_TRIANGLE   = 2
    BTN_SQUARE     = 3
    BTN_L1         = 4
    BTN_R1         = 5
    BTN_L2         = 6
    BTN_R2         = 7
    BTN_SHARE      = 8
    BTN_OPTIONS    = 9
    BTN_PS         = 10
    BTN_L3         = 11
    BTN_R3         = 12
    BTN_HOME_GO    = -1  # Linux'ta D-Pad (hat) kullanılır
    BTN_SURGERY_GO = -1
    BTN_DPAD_UP    = -1  # Linux'ta hat[1] kullanılır
    BTN_DPAD_DOWN  = -1

# Axis indeksleri - Windows ve Linux farklı mapping kullanır
if _platform.system() == "Windows":
    # Windows: pygame DualSense axis sırası
    AXIS_LX = 0
    AXIS_LY = 1
    AXIS_RX = 2
    AXIS_RY = 3
    AXIS_L2 = 4
    AXIS_R2 = 5
else:
    # Linux SDL2
    AXIS_LX = 0
    AXIS_LY = 1
    AXIS_L2 = 2
    AXIS_RX = 3
    AXIS_RY = 4
    AXIS_R2 = 5

# Modlar
MODE_JOINT = "EKLEM"
MODE_TOOL = "TOOL"


# =============================================================================
# JOYSTICK KONTROL SINIFI
# =============================================================================

class JoystickRobotController:
    def __init__(self, robot_ip=ROBOT_IP):
        self.robot_ip = robot_ip
        self.dashboard = None
        self.speed = SPEED_DEFAULT
        self.running = False
        self.active_jog = ""
        self.last_jog_start = 0
        self.idle_since = 0
        self.error_state = False
        self.mode = MODE_JOINT  # Başlangıç modu
        self.drag_active = False  # Drag modu aktif mi
        self.tool_distance = DEFAULT_TOOL_DISTANCE  # mm
        self.home_joints = None
        self.surgery_joints = None
        self._load_positions()

    def _load_positions(self):
        """Kayıtlı pozisyonları, tool mesafesini ve hızı dosyadan yükle"""
        import json
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE, 'r') as f:
                    data = json.load(f)
                self.home_joints = data.get("home")
                self.surgery_joints = data.get("surgery")
                self.tool_distance = data.get("tool_distance", DEFAULT_TOOL_DISTANCE)
                saved_speed = data.get("speed")
                if saved_speed is not None:
                    self.speed = max(SPEED_MIN, min(SPEED_MAX, int(saved_speed)))
                if self.home_joints:
                    print(f"[POZ] Home yüklendi: {self.home_joints}")
                if self.surgery_joints:
                    print(f"[POZ] Ameliyat yüklendi: {self.surgery_joints}")
                print(f"[POZ] Tool mesafesi: {self.tool_distance}mm ({self.tool_distance/10:.0f}cm)")
                print(f"[POZ] Hız: %{self.speed}")
            except Exception as e:
                print(f"[POZ] Dosya okunamadı: {e}")

    def _save_positions(self):
        """Pozisyonları, tool mesafesini ve hızı dosyaya kaydet"""
        import json
        data = {
            "home": self.home_joints,
            "surgery": self.surgery_joints,
            "tool_distance": self.tool_distance,
            "speed": self.speed,
        }
        try:
            with open(POSITIONS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[POZ] Dosya yazılamadı: {e}")

    def _read_current_joints(self):
        """Mevcut eklem açılarını oku, liste olarak döndür"""
        import re
        resp = str(self._safe_cmd(self.dashboard.GetAngle))
        match = re.search(r'\{([^}]+)\}', resp)
        if match:
            return [round(float(x), 2) for x in match.group(1).split(',')]
        return None

    def save_home(self):
        """Mevcut pozisyonu HOME olarak kaydet"""
        joints = self._read_current_joints()
        if joints:
            self.home_joints = joints
            self._save_positions()
            print(f"\n{'='*50}")
            print(f"  HOME POZİSYONU KAYDEDİLDİ!")
            print(f"  {joints}")
            print(f"{'='*50}\n")
        else:
            print("[UYARI] Pozisyon okunamadı")

    def save_surgery(self):
        """Mevcut pozisyonu AMELİYAT olarak kaydet"""
        joints = self._read_current_joints()
        if joints:
            self.surgery_joints = joints
            self._save_positions()
            print(f"\n{'='*50}")
            print(f"  AMELİYAT POZİSYONU KAYDEDİLDİ!")
            print(f"  {joints}")
            print(f"{'='*50}\n")
        else:
            print("[UYARI] Pozisyon okunamadı")

    def set_tool_distance(self, distance_mm):
        """Tool mesafesini ayarla ve robota gönder"""
        self.tool_distance = int(distance_mm)
        self._save_positions()
        self._apply_tool()
        print(f"[TOOL] Mesafe: {self.tool_distance}mm ({self.tool_distance/10:.0f}cm)")

    def _apply_tool(self):
        """Mevcut tool mesafesini robota uygula"""
        if not self.dashboard:
            return
        tool_cmd = f"SetTool({TOOL_INDEX},{{0.0,0.0,{float(self.tool_distance)},0.0,0.0,0.0}})"
        self._safe_cmd(self.dashboard.sendRecvMsg, tool_cmd)
        self._safe_cmd(self.dashboard.Tool, TOOL_INDEX)

    pass

    def _safe_cmd(self, func, *args):
        if not self.dashboard:
            print("[UYARI] Robot bağlı değil")
            return None
        try:
            return func(*args)
        except (ConnectionError, OSError, BrokenPipeError) as e:
            print(f"[HATA] Bağlantı koptu: {e}")
            self.dashboard = None
            self.active_jog = ""
            return None

    def _parse_error_code(self, resp):
        if resp is None:
            return -999
        try:
            return int(str(resp).split(",")[0])
        except (ValueError, IndexError):
            return -999

    def connect(self):
        try:
            self.dashboard = DobotApiDashboard(self.robot_ip, DASHBOARD_PORT)
            print(f"[OK] Robot bağlantısı kuruldu: {self.robot_ip}")
            return True
        except Exception as e:
            print(f"[HATA] Robot bağlantısı başarısız: {e}")
            return False

    def disconnect(self):
        self._force_stop()
        if self.dashboard:
            self.dashboard.close()
        print("[OK] Robot bağlantısı kapatıldı")

    def _force_stop(self):
        """Koşulsuz durdur"""
        if self.active_jog:
            self._safe_cmd(self.dashboard.MoveJog, "")
            self.active_jog = ""
            self.idle_since = 0

    def prepare_robot(self):
        """Robotu hazırla: hata temizle, enable, hız ayarla, tool tanımla"""
        print("[HAZIRLIK] Robot hazırlanıyor...")

        # Çalışan programı durdur (Mode 7 → Mode 5)
        self._safe_cmd(self.dashboard.Stop)
        time.sleep(0.5)

        self._safe_cmd(self.dashboard.ClearError)
        time.sleep(0.5)
        self._safe_cmd(self.dashboard.SetCollisionLevel, 0)
        time.sleep(0.3)

        resp = self._safe_cmd(self.dashboard.EnableRobot)
        print(f"[HAZIRLIK] EnableRobot: {resp}")
        time.sleep(1)

        self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
        self._safe_cmd(self.dashboard.VelJ, JOG_VEL_JOINT)
        self._safe_cmd(self.dashboard.AccJ, JOG_ACC_JOINT)
        self._safe_cmd(self.dashboard.VelL, JOG_VEL_LINEAR)
        self._safe_cmd(self.dashboard.AccL, JOG_ACC_LINEAR)
        time.sleep(0.3)

        # Tool tanımla
        self._apply_tool()
        time.sleep(0.3)

        # Mod 5 (Idle/hazır) olana kadar bekle — en fazla 3 deneme
        ready = False
        for attempt in range(3):
            for _ in range(10):  # 5 saniye bekle (10 x 0.5)
                mode_resp = str(self._safe_cmd(self.dashboard.RobotMode))
                if ",{5}," in mode_resp:
                    ready = True
                    break
                time.sleep(0.5)
            if ready:
                break
            # Hâlâ Mode 5 değil → ClearError + EnableRobot tekrar
            print(f"[HAZIRLIK] Mod 5'e geçmedi (deneme {attempt+1}), hata temizleniyor...")
            self._safe_cmd(self.dashboard.ClearError)
            time.sleep(0.5)
            self._safe_cmd(self.dashboard.EnableRobot)
            time.sleep(1)

        mode = self._safe_cmd(self.dashboard.RobotMode)
        errors = self._safe_cmd(self.dashboard.GetErrorID)
        print(f"[HAZIRLIK] Mode: {mode} | Errors: {errors}")

        self.error_state = False
        self.active_jog = ""
        print(f"[HAZIRLIK] Hız: %{self.speed} | Tool: {TOOL_INDEX}")
        if ready:
            print("[HAZIRLIK] Robot hazır! (Mode 5 = Idle)")
        else:
            print("[UYARI] Robot Mode 5'e geçmedi. Fiziksel acil durdur butonuna veya"
                  " tablet kontrolde hata varsa temizle; bu mesajdan sonra tekrar dene.")

    def recover_from_error(self):
        print("[KURTARMA] Hata tespit edildi, kurtarılıyor...")
        self.active_jog = ""
        self.prepare_robot()

    def toggle_mode(self):
        """Eklem ↔ Tool modu geçişi"""
        self._force_stop()
        time.sleep(0.1)

        if self.mode == MODE_JOINT:
            self.mode = MODE_TOOL
        else:
            self.mode = MODE_JOINT

        print(f"\n{'='*50}")
        print(f"  MOD DEĞİŞTİ → [{self.mode}]")
        if self.mode == MODE_TOOL:
            print("  Sol Analog : X/Y hareket")
            print("  Sağ Analog : Z hareket + Rz dönüş")
            print("  L2/R2      : Rx dönüş")
            print("  D-Pad      : Ry dönüş")
        else:
            print("  Sol Analog : J1/J2")
            print("  Sağ Analog : J3/J4")
            print("  L2/R2      : J5")
            print("  D-Pad      : J6")
        print(f"{'='*50}\n")

    def enable_robot(self):
        self.prepare_robot()

    def disable_robot(self):
        self._force_stop()
        resp = self._safe_cmd(self.dashboard.DisableRobot)
        print(f"[ROBOT] Disable: {resp}")

    def clear_error(self):
        self.prepare_robot()

    def toggle_drag(self):
        """Drag modu aç/kapat. Kapanınca mevcut pozisyondan +5cm tool ayarla."""
        import re

        if not self.drag_active:
            # DRAG BAŞLAT
            self._force_stop()
            time.sleep(0.1)
            resp = self._safe_cmd(self.dashboard.StartDrag)
            print(f"\n{'='*50}")
            print(f"  DRAG MODU AKTİF - Robotu elle sürükle!")
            print(f"  Bitince tekrar O (Daire) butonuna bas.")
            print(f"  StartDrag: {resp}")
            print(f"{'='*50}\n")
            self.drag_active = True
        else:
            # DRAG DURDUR + TOOL AYARLA
            resp = self._safe_cmd(self.dashboard.StopDrag)
            print(f"[DRAG] StopDrag: {resp}")
            self.drag_active = False
            time.sleep(0.5)

            # Enable robot (drag sonrası disable oluyor)
            self._safe_cmd(self.dashboard.EnableRobot)
            time.sleep(1)

            # Mevcut pozisyonu oku
            pose_resp = str(self._safe_cmd(self.dashboard.GetPose))
            match = re.search(r'\{([^}]+)\}', pose_resp)

            if match:
                pose = [float(x) for x in match.group(1).split(',')]
                print(f"[DRAG] Bırakılan pozisyon: X={pose[0]:.1f} Y={pose[1]:.1f} Z={pose[2]:.1f}")
                print(f"       Rx={pose[3]:.1f} Ry={pose[4]:.1f} Rz={pose[5]:.1f}")

                # Tool ofseti uygula
                self._apply_tool()

                print(f"\n{'='*50}")
                print(f"  TOOL AYARLANDI!")
                print(f"  Flanştan {self.tool_distance}mm ileride ({self.tool_distance/10:.0f}cm)")
                print(f"  Tool modu aktif - joystick bu nokta etrafında döner")
                print(f"{'='*50}\n")

                # Otomatik tool moduna geç
                self.mode = MODE_TOOL
            else:
                print(f"[DRAG] Pozisyon okunamadı: {pose_resp}")

            # Hız/ivme ayarlarını geri yükle
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
            self._safe_cmd(self.dashboard.VelJ, JOG_VEL_JOINT)
            self._safe_cmd(self.dashboard.AccJ, JOG_ACC_JOINT)

    def set_speed(self, speed):
        new_speed = max(SPEED_MIN, min(SPEED_MAX, speed))
        if new_speed == self.speed:
            return
        self.speed = new_speed
        if self.dashboard:
            resp = self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
            print(f"[HIZ] %{self.speed}  ({resp})")
        else:
            print(f"[HIZ] %{self.speed}")
        self._save_positions()

    def print_current_position(self):
        """Mevcut pozisyonu terminale yazdır (kopyala-yapıştır için)"""
        import re
        angle_resp = str(self._safe_cmd(self.dashboard.GetAngle))
        pose_resp = str(self._safe_cmd(self.dashboard.GetPose))

        # {değer1,değer2,...} formatını yakala
        match = re.search(r'\{([^}]+)\}', angle_resp)
        if match:
            nums = [float(x) for x in match.group(1).split(',')]
            if len(nums) >= 6:
                print(f"\n{'='*50}")
                print(f"  MEVCUT POZİSYON")
                print(f"  Eklemler: [{nums[0]}, {nums[1]}, {nums[2]}, {nums[3]}, {nums[4]}, {nums[5]}]")
                print(f"  Pose: {pose_resp}")
                print(f"  Kopyala → HOME_JOINTS veya SURGERY_JOINTS olarak yapıştır")
                print(f"{'='*50}\n")
                return
        print(f"[UYARI] Pozisyon okunamadı: {angle_resp}")

    def go_to_position(self, joints, name):
        """MovJ ile sabit pozisyona git"""
        if joints is None:
            print(f"[UYARI] {name} pozisyonu tanımlı değil! Önce kaydet.")
            return

        if not self.dashboard:
            print(f"[UYARI] Robot bağlı değil!")
            return

        self._force_stop()
        time.sleep(0.1)

        # Çalışan programı durdur + hata temizle (Mode 7 sorunu)
        self._safe_cmd(self.dashboard.Stop)
        time.sleep(0.3)
        self._safe_cmd(self.dashboard.ClearError)
        time.sleep(0.3)
        self._safe_cmd(self.dashboard.EnableRobot)
        time.sleep(0.5)

        # Hız ayarla
        self._safe_cmd(self.dashboard.SpeedFactor, MOVJ_SPEED)
        print(f"[GİT] {name} pozisyonuna gidiliyor (hız: %{MOVJ_SPEED})...")
        print(f"  Hedef: {joints}")

        # MovJ ile eklem koordinatlarına git (coordinateMode=1 = joint)
        resp = self._safe_cmd(
            self.dashboard.MovJ,
            joints[0], joints[1], joints[2],
            joints[3], joints[4], joints[5], 1
        )
        err = self._parse_error_code(resp)
        print(f"[GİT] MovJ: {resp}")

        if err == 0:
            # Hareket tamamlanana kadar bekle
            print(f"[GİT] Hareket devam ediyor...")
            time.sleep(1)
            # RobotMode 5'e dönene kadar bekle (hareket bitti)
            for _ in range(30):  # max 15 saniye
                mode_resp = str(self._safe_cmd(self.dashboard.RobotMode))
                if ",{5}," in mode_resp:
                    break
                time.sleep(0.5)

            print(f"[GİT] {name} pozisyonuna ulaşıldı!")

            # Ameliyat pozisyonuna geldiyse otomatik Tool moduna geç
            if name == "AMELİYAT":
                self.mode = MODE_TOOL
                print(f"\n{'='*50}")
                print(f"  TOOL MODUNA GEÇİLDİ (ameliyat pozisyonu)")
                print(f"  Sol Analog : X/Y hareket")
                print(f"  Sağ Analog : Z hareket + Rz dönüş")
                print(f"  L2/R2      : Rx dönüş")
                print(f"  D-Pad      : Ry dönüş")
                print(f"{'='*50}\n")
            elif name == "HOME":
                self.mode = MODE_JOINT
                print(f"  Eklem moduna geçildi.")

            # Hızı eski haline getir
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)
        else:
            print(f"[GİT] HATA! MovJ başarısız: {err}")
            self._safe_cmd(self.dashboard.SpeedFactor, self.speed)

    def start_jog(self, axis_id):
        """Jog hareketini başlat (moda göre farklı parametre)"""
        self.idle_since = 0

        if axis_id == self.active_jog:
            return

        if self.error_state:
            self.recover_from_error()
            return

        now = time.time()

        if self.active_jog:
            if now - self.last_jog_start < MIN_SWITCH_TIME:
                return
            self._safe_cmd(self.dashboard.MoveJog, "")
            time.sleep(0.05)

        self.active_jog = axis_id
        self.last_jog_start = now

        if self.mode == MODE_JOINT:
            # Eklem modu: coordtype yok
            resp = self._safe_cmd(self.dashboard.MoveJog, axis_id)
        else:
            # Tool modu:
            # Dönüş (Rx/Ry/Rz) → coordtype=1 (user) → TCP noktası sabit, flanş etrafında döner
            # Kaydırma (X/Y/Z) → coordtype=2 (tool) → tool eksenlerinde hareket
            if axis_id.startswith("R"):
                resp = self._safe_cmd(self.dashboard.MoveJog, axis_id, 1, -1, TOOL_INDEX)
            else:
                resp = self._safe_cmd(self.dashboard.MoveJog, axis_id, 2, -1, TOOL_INDEX)

        err = self._parse_error_code(resp)
        print(f"[{self.mode}] MoveJog({axis_id}) -> {resp}")

        if err == -1:
            # -1 = komut reddedildi (meşgul/geçiş sırasında) - tekrar denenecek
            self.active_jog = ""
        elif err != 0 and err != -2:
            # Ciddi hata - kurtarma gerekli
            print(f"[{self.mode}] Ciddi hata: {err}")
            self.active_jog = ""
            self.error_state = True

    def stop_jog(self):
        if not self.active_jog:
            return

        now = time.time()

        if now - self.last_jog_start < MIN_JOG_HOLD:
            return

        if self.idle_since == 0:
            self.idle_since = now
            return

        if now - self.idle_since < IDLE_BEFORE_STOP:
            return

        resp = self._safe_cmd(self.dashboard.MoveJog, "")
        print(f"[{self.mode}] STOP -> {resp}")
        self.active_jog = ""
        self.idle_since = 0

    def run(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("[HATA] Joystick bulunamadı!")
            return

        js = pygame.joystick.Joystick(0)
        js.init()
        print(f"[OK] Joystick: {js.get_name()}")
        print(f"     Axes: {js.get_numaxes()}, Buttons: {js.get_numbuttons()}")

        if not self.connect():
            return

        self.prepare_robot()

        self.running = True
        loop_delay = 1.0 / LOOP_HZ

        home_str = "TANIMLI" if HOME_JOINTS else "YOK"
        surg_str = "TANIMLI" if SURGERY_JOINTS else "YOK"

        print("\n" + "=" * 50)
        print(f"  JOYSTICK KONTROL AKTİF [{self.mode} MODU]")
        print(f"  Home: {home_str} | Ameliyat: {surg_str}")
        print("=" * 50)
        print("  ---  POZİSYON  ---")
        print("  D-Pad Sol    : HOME pozisyonuna git")
        print("  D-Pad Sağ    : AMELİYAT pozisyonuna git")
        print("  L3           : Mevcut pozisyonu yazdır")
        print("  ---  EKLEM MODU  ---")
        print("  Sol Analog   : J1 / J2")
        print("  Sağ Analog   : J3 / J4")
        print("  L2/R2        : J5")
        print("  D-Pad Y      : J6")
        print("  ---  TOOL MODU  ---")
        print("  Sol Analog   : X / Y hareket")
        print("  Sağ Analog   : Z hareket / Rz dönüş")
        print("  L2/R2        : Rx dönüş")
        print("  D-Pad Y      : Ry dönüş")
        print("  ---  BUTONLAR  ---")
        print("  SHARE        : Mod değiştir (Eklem ↔ Tool)")
        print("  Üçgen/X      : Hız artır/azalt")
        print("  Kare         : Durdur")
        print("  R1           : Enable + Hazırla")
        print("  L1           : Disable")
        print("  Options      : Çıkış")
        print("  PS           : ACİL DURDURMA")
        print("=" * 50 + "\n")

        try:
            while self.running:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self._handle_button(event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        self._handle_dpad(event.value)
                    elif event.type == pygame.QUIT:
                        self.running = False

                if not self.running:
                    break

                self._handle_axes(js)
                time.sleep(loop_delay)

        except KeyboardInterrupt:
            print("\n[!] Ctrl+C - Durduruluyor...")
        finally:
            self._force_stop()
            self.disconnect()
            js.quit()
            pygame.quit()
            print("[OK] Program sonlandırıldı")

    def _handle_button(self, button):
        _BTN_NAMES = {}
        # Sadece GEÇERLİ (negatif olmayan) sabitleri isim tablosuna ekle
        for _btn, _lbl in (
            (BTN_CROSS, "× Cross"), (BTN_CIRCLE, "○ Circle"),
            (BTN_SQUARE, "□ Square"), (BTN_TRIANGLE, "△ Triangle"),
            (BTN_L1, "L1"), (BTN_R1, "R1"),
            (BTN_L2, "L2"), (BTN_R2, "R2"),
            (BTN_SHARE, "SHARE"), (BTN_OPTIONS, "OPTIONS"),
            (BTN_L3, "L3"), (BTN_R3, "R3"), (BTN_PS, "PS"),
            (BTN_HOME_GO, "HOME_GO"), (BTN_SURGERY_GO, "SURGERY_GO"),
        ):
            if _btn >= 0 and _btn not in _BTN_NAMES:
                _BTN_NAMES[_btn] = f"{_lbl}(B{_btn})"
        name = _BTN_NAMES.get(button, f"B{button}(atanmamış)")

        # Her eşleşme için butonun geçerli (>=0) olduğunu da kontrol et
        def _is(target):
            return target >= 0 and button == target

        if _is(BTN_SQUARE):
            print(f"[BUTON] {name} → ACİL STOP (Robot Disable)")
            self.disable_robot()
        elif _is(BTN_L1):
            print(f"[BUTON] {name} → Robot Disable (Linux: L1)")
            self.disable_robot()
        elif _is(BTN_R1):
            print(f"[BUTON] {name} → Robot Enable (Linux: R1)")
            self.enable_robot()
        elif _is(BTN_OPTIONS):
            print(f"[BUTON] {name} → Durdur (MoveJog stop)")
            self._force_stop()
        elif _is(BTN_L3):
            print(f"[BUTON] {name} → Home pozisyonu KAYDET")
            self.save_home()
        elif _is(BTN_R3):
            print(f"[BUTON] {name} → Ameliyat pozisyonu KAYDET")
            self.save_surgery()
        elif _is(BTN_SHARE):
            print(f"[BUTON] {name} → Mod değiştir (Eklem ↔ Tool)")
            self.toggle_mode()
        elif _is(BTN_HOME_GO):
            print(f"[BUTON] {name} → HOME pozisyonuna git")
            self.go_to_position(self.home_joints, "HOME")
        elif _is(BTN_SURGERY_GO):
            print(f"[BUTON] {name} → AMELİYAT pozisyonuna git")
            self.go_to_position(self.surgery_joints, "AMELİYAT")
        elif _is(BTN_TRIANGLE):
            print(f"[BUTON] {name} → Hız artır (%{self.speed} → %{min(self.speed+SPEED_STEP, SPEED_MAX)})")
            self.set_speed(self.speed + SPEED_STEP)
        elif _is(BTN_CROSS):
            print(f"[BUTON] {name} → Hız azalt (%{self.speed} → %{max(self.speed-SPEED_STEP, SPEED_MIN)})")
            self.set_speed(self.speed - SPEED_STEP)
        elif _is(BTN_CIRCLE):
            print(f"[BUTON] {name} → Drag modu")
            self.toggle_drag()
        elif _is(BTN_PS):
            print(f"[BUTON] {name} → (devre dışı)")
        elif _is(BTN_DPAD_UP) or _is(BTN_DPAD_DOWN):
            # D-Pad Y, _handle_axes içinde sürekli okunur - ekstra log yok
            pass
        else:
            print(f"[BUTON] B{button} → (atanmamış)")

    def _handle_dpad(self, value):
        """D-Pad olaylarını işle: sol/sağ=pozisyon git, yukarı/aşağı=jog"""
        hat_x, hat_y = value
        if hat_x == -1:
            print("[D-PAD] ◄ Sol → HOME pozisyonuna git")
            self.go_to_position(self.home_joints, "HOME")
        elif hat_x == 1:
            print("[D-PAD] ► Sağ → AMELİYAT pozisyonuna git")
            self.go_to_position(self.surgery_joints, "AMELİYAT")

    def _handle_axes(self, js):
        # Drag modundayken joystick jog gönderme
        if self.drag_active:
            return

        lx = js.get_axis(AXIS_LX)
        ly = js.get_axis(AXIS_LY)
        rx = js.get_axis(AXIS_RX)
        ry = js.get_axis(AXIS_RY)
        l2 = js.get_axis(AXIS_L2)
        r2 = js.get_axis(AXIS_R2)
        hat = js.get_hat(0) if js.get_numhats() > 0 else (0, 0)

        # D-Pad Y (yukarı/aşağı) — platformdan bağımsız sentetik değer:
        # Linux'ta hat[1] gelir, Windows'ta buton (11/12) gelir.
        dpad_y = hat[1]
        if BTN_DPAD_UP >= 0 and js.get_button(BTN_DPAD_UP):
            dpad_y = 1
        elif BTN_DPAD_DOWN >= 0 and js.get_button(BTN_DPAD_DOWN):
            dpad_y = -1

        candidates = []

        if self.mode == MODE_JOINT:
            # --- EKLEM MODU ---
            if abs(ly) > DEADZONE:
                candidates.append(("J1", abs(ly), "J1-" if ly > 0 else "J1+"))
            if abs(lx) > DEADZONE:
                candidates.append(("J2", abs(lx), "J2+" if lx > 0 else "J2-"))
            if abs(ry) > DEADZONE:
                candidates.append(("J3", abs(ry), "J3-" if ry > 0 else "J3+"))
            if abs(rx) > DEADZONE:
                candidates.append(("J4", abs(rx), "J4+" if rx > 0 else "J4-"))

            l2_val = (l2 + 1) / 2
            r2_val = (r2 + 1) / 2
            if l2_val > 0.3:
                candidates.append(("J5+", l2_val, "J5+"))
            if r2_val > 0.3:
                candidates.append(("J5-", r2_val, "J5-"))

            # D-Pad yukarı/aşağı → J6 (sol/sağ artık pozisyon gitme)
            if dpad_y != 0:
                candidates.append(("J6", 1.0, "J6+" if dpad_y > 0 else "J6-"))

        else:
            # --- TOOL MODU ---
            # Sol analog: X/Y kaydırma (tool eksenleri)
            if abs(ly) > DEADZONE:
                candidates.append(("X", abs(ly), "X-" if ly > 0 else "X+"))
            if abs(lx) > DEADZONE:
                candidates.append(("Y", abs(lx), "Y+" if lx > 0 else "Y-"))

            # Sağ analog Y: Z yukarı/aşağı (kaydırma)
            if abs(ry) > DEADZONE:
                candidates.append(("Z", abs(ry), "Z-" if ry > 0 else "Z+"))

            # Sağ analog X: Ry dönüş = kafa sola/sağa (tool noktası sabit)
            if abs(rx) > DEADZONE:
                candidates.append(("Ry", abs(rx), "Ry+" if rx > 0 else "Ry-"))

            # L2/R2: Rx dönüş = kafa yukarı/aşağı (tool noktası sabit)
            l2_val = (l2 + 1) / 2
            r2_val = (r2 + 1) / 2
            if l2_val > 0.3:
                candidates.append(("Rx-", l2_val, "Rx-"))
            if r2_val > 0.3:
                candidates.append(("Rx+", r2_val, "Rx+"))

            # D-Pad Y: Rz dönüş = kafa yatırma
            if dpad_y != 0:
                candidates.append(("Rz", 1.0, "Rz+" if dpad_y > 0 else "Rz-"))

        if candidates:
            candidates.sort(key=lambda c: c[1], reverse=True)
            self.start_jog(candidates[0][2])
        else:
            self.stop_jog()


# =============================================================================
# BAŞLATMA
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Dobot Nova 5 - PS5 Joystick Kontrol")
    print("  Çift Mod: Eklem (J1-J6) + Tool (XYZ/Rotation)")
    print("=" * 50)

    controller = JoystickRobotController(ROBOT_IP)
    controller.run()

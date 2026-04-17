# Dental Robot Controller

Dobot Nova 5 robotunu PS5 DualSense joystick ile kontrol etmek için geliştirilmiş Python arayüzü. Diş sağlığı uygulamaları için tool koordinat sistemi, drag öğretme ve PyQt5 grafik arayüzü içerir.

## Özellikler

- **Çift Kontrol Modu**
  - **Eklem Modu** (J1-J6): Kabaca pozisyonlama, singularity sorunsuz
  - **Tool Modu**: Tool noktası (TCP) etrafında hassas dönüş - hasta yüzüne sabitlenmiş flanş simülasyonu
- **Drag Öğretme**: Robotu elle sürükleyip pozisyon kaydetme
- **Sabit Pozisyonlar**: Home ve Ameliyat pozisyonlarını kaydet, tek tuşla git
- **Tool Mesafesi Ayarı**: 1cm - 50cm arası slider ile runtime ayarı
- **PyQt5 Arayüzü**: Durum göstergesi, hız kontrolü, log ekranı
- **Otomatik Hata Kurtarma**: Singularity, collision, mode 7 sorunlarında otomatik toparlama
- **JSON Konfigürasyon**: Tüm ayarlar `settings.json` üzerinden

## Gereksinimler

- Python 3.10+
- Dobot Nova 5 robot (TCP/IP V4 firmware)
- PS5 DualSense joystick (Linux için)
- Ağ bağlantısı: Robot varsayılan IP 192.168.5.1

## Kurulum

```bash
git clone https://github.com/ahmet-f-gumustas/dental-robot-controller.git
cd dental-robot-controller
pip install -r requirements.txt
```

## Kullanım

### GUI ile (önerilen)

```bash
python3 gui_control.py
```

### Sadece Joystick

```bash
python3 joystick_control.py
```

### Pozisyon Ayarlama Akışı

1. **Joystick Başlat** butonuna tıkla
2. Joystick ile robotu home pozisyonuna getir
3. **[HOME KAYDET]** butonuna tıkla
4. Robotu ameliyat pozisyonuna getir
5. **[AMELİYAT KAYDET]** butonuna tıkla
6. Artık **D-Pad Sol** ile home'a, **D-Pad Sağ** ile ameliyat pozisyonuna tek tuşla gidilir
7. Tool mesafesi slider'ı ile TCP uzaklığını ayarla (varsayılan 35cm)

## Kontrol Şeması

### Eklem Modu
| Kontrol | Fonksiyon |
|---------|-----------|
| Sol Analog Y | J1 (taban) |
| Sol Analog X | J2 (omuz) |
| Sağ Analog Y | J3 (dirsek) |
| Sağ Analog X | J4 (bilek 1) |
| L2 / R2 | J5 (bilek 2) |
| D-Pad Y | J6 (uç) |

### Tool Modu (hastanın yüzü sabit, flanş etrafında döner)
| Kontrol | Fonksiyon |
|---------|-----------|
| Sol Analog | X/Y kaydırma (tool eksenlerinde) |
| Sağ Analog Y | Z kaydırma |
| **Sağ Analog X** | **Ry dönüş** (kafa sola/sağa) |
| **L2 / R2** | **Rx dönüş** (kafa yukarı/aşağı) |
| **D-Pad Y** | **Rz dönüş** (kafa yatırma) |

### Butonlar
| Buton | Fonksiyon |
|-------|-----------|
| SHARE | Mod değiştir (Eklem ↔ Tool) |
| Üçgen / X | Hız +/- |
| Kare | Durdur |
| Daire | Drag modu aç/kapat |
| R1 | Enable |
| L1 | Disable |
| D-Pad Sol/Sağ | Home / Ameliyat pozisyonuna git |
| L3 / R3 | Home / Ameliyat kaydet |
| Options | Çıkış |
| PS | Acil durdurma |

## Konfigürasyon

`settings.json` dosyası ilk çalıştırmada otomatik oluşur:

```json
{
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
```

Pozisyonlar `positions.json` dosyasında saklanır:

```json
{
  "home": [264.97, -6.84, -148.73, 89.19, 89.03, -4.99],
  "surgery": [275.02, -48.85, -66.75, 60.7, 83.34, 5.39],
  "tool_distance": 350
}
```

## Proje Yapısı

```
.
├── gui_control.py          # PyQt5 grafik arayüzü (ana uygulama)
├── joystick_control.py     # Çekirdek kontrol sınıfı + joystick döngüsü
├── robot_diagnose.py       # Robot durumu teşhis scripti
├── tool_test.py            # Tool koordinat sistemi testi
├── joystick_test.py        # PS5 buton/axis haritalama testi
├── robot_config_reader.py  # Tam robot konfigürasyon okuyucu
├── robot_connection_test.py # Basit TCP bağlantı testi
├── collision_close.py      # Collision/SafeSkin kapatma
├── TCP-IP-Python-V4/       # Dobot resmi Python SDK
├── settings.json           # Kullanıcı ayarları (otomatik oluşur)
└── positions.json          # Kaydedilmiş pozisyonlar (otomatik oluşur)
```

## Bilinen Kısıtlamalar

1. **Wrist Singularity**: J5 ≈ 0°/360° pozisyonunda kartezyen/tool jog Error 30 verir. Eklem moduyla J5'i ±45° değerine getirip tool moduna geçin.
2. **Tek Eksen Jog**: Aynı anda tek eksen hareketi (MoveJog sınırı). En baskın eksen seçilir.
3. **DualSense Axis Haritası**: Linux SDL2 standart değildir. Kodda doğru harita tanımlı (Axis 2 = L2, Axis 3 = Sağ X).

## Yaygın Hatalar

| Hata Kodu | Sebep | Çözüm |
|-----------|-------|-------|
| `-1` | Komut reddedildi (meşgul) | Otomatik tekrar dener |
| `-2` | Durduracak bir şey yok | Normal, görmezden gelin |
| `-6` | Eksen/hareket tipi uyuşmuyor | `coordtype` parametresi kontrol |
| `Error 17` | Collision algılandı | `SetCollisionLevel(0)` ile kapatılır |
| `Error 30` | Ters kinematik başarısız | Singularity - eklem joguyla çıkın |
| `Mode 7` | Robot kontrolcüsünde program çalışıyor | `Stop()` ile durdurulur |

## Uyarı

> ⚠️ **Medikal Kullanım Uyarısı**
>
> Bu yazılım araştırma ve geliştirme amaçlıdır. Gerçek hasta üzerinde kullanılmadan önce medikal cihaz onayı (CE/FDA vb.) alınması gerekir. Yazar, bu yazılımın kullanımından doğan hiçbir zarardan sorumlu değildir.

## Lisans

MIT License - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## Donanım

- **Robot**: Dobot Nova 5 (tavana ters asılı - 180° montaj açısı)
- **Joystick**: Sony PS5 DualSense Wireless Controller
- **Bağlantı**: Ethernet, TCP/IP V4 protokolü (port 29999)

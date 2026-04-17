# Dobot Nova 5 - Proje Notları

## Robot Bilgileri
- **Model:** Nova 5 - CCBOX
- **Controller:** 4.6.1.0-stable
- **Software:** 4.6.6.0-stable-x86-64
- **CCBOX IO:** 2.2.2.4
- **Tool IO:** 6.1.3.1
- **J1-J6:** 3.0.2.1
- **Protokol:** TCP-IP V4

## Ağ Ayarları
- **Robot IP:** 192.168.5.1
- **PC IP:** 192.168.201.10 (enp55s0 ethernet)
- **Bağlantı:** Ethernet kablosu ile doğrudan

## Portlar
| Port | Kullanım | Durum |
|------|----------|-------|
| 29999 | Dashboard (komut gönderme + hareket) | Açık |
| 30004 | Realtime Feedback (veri okuma) | Açık |
| 30003 | V3'te Move portu - V4'te kullanılmıyor | Kapalı |

## Önemli Notlar
- Nova 5 + CCBOX = **V4 protokolü** kullanıyor (V3 değil!)
- V4'te tüm hareket komutları (MovJ, MovL vb.) **Dashboard (29999)** üzerinden gönderiliyor
- Port 30003'e gerek yok
- DobotStudio Pro versiyonu (4.6) ile TCP-IP protokol versiyonu (V4) farklı kavramlar
- Robot enable DobotStudio Pro üzerinden yapıldı (komut satırından Mode 5'te kalıyordu)
- SpeedFactor(20) ile %20 hızda güvenli test yapıldı

## Kullanılan Repo
- **Doğru:** TCP-IP-Python-V4 (github.com/Dobot-Arm/TCP-IP-Python-V4)
- **Yanlış:** TCP-IP-Python-V3 (CR/Nova V3 protokolü - bu robot için uygun değil)

## Test Sonuçları (2 Nisan 2026)
- Bağlantı testi: Başarılı
- Enable: Başarılı (DobotStudio Pro üzerinden)
- MovJ hareket testi: Başarılı (Z +50mm yukarı/aşağı)
- Feedback verisi: Başarılı (DI, DO, RobotMode okunuyor)

## Mevcut Pozisyon (son bilinen)
- X: -523.65, Y: 236.58, Z: 430.74
- Rx: 164.50, Ry: 42.37, Rz: 60.39

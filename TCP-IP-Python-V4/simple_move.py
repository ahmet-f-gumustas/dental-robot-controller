from dobot_api import DobotApiDashboard, DobotApiFeedBack
from time import sleep

ip = "192.168.5.1"

print("Robota bağlanılıyor...")
dashboard = DobotApiDashboard(ip, 29999)

print("Mevcut pozisyon alınıyor...")
pose = dashboard.GetPose()
print(f"Pose: {pose}")

# Hızı düşük ayarla (güvenlik)
dashboard.SpeedFactor(20)  # %20 hız
print("Hız %20 olarak ayarlandı")

# Mevcut pozisyondan sadece Z +50mm yukarı
print("\n*** Z ekseninde 50mm YUKARI hareket başlıyor ***")
print("Acil stop hazır tut!")
sleep(2)

result = dashboard.MovJ(-523.65, 236.58, 480.74, 164.50, 42.37, 60.39, 0)
print(f"MovJ sonucu: {result}")

sleep(5)

# Geri dön
print("\n*** Eski pozisyona geri dönülüyor ***")
result = dashboard.MovJ(-523.65, 236.58, 430.74, 164.50, 42.37, 60.39, 0)
print(f"MovJ sonucu: {result}")

sleep(5)
print("\nTamamlandı!")

"""
Test 4: D-Pad (Yön tuşları)

Sırayla bas:
    1. D-Pad Yukarı
    2. D-Pad Aşağı
    3. D-Pad Sol
    4. D-Pad Sağ

NOT: Windows'ta D-Pad BUTON olarak veya HAT olarak gelebilir.
Bu script ikisini de yakalar; hangisi çıkıyorsa onu bildir.

Bittiğinde Ctrl+C.
"""
import time
from _ortak import init_joystick, goodbye
import pygame

js = init_joystick()

print()
print(">>> Her yön tuşuna TEK TEK bas, bırak, sıradakine geç.")
print(">>> Ctrl+C ile çık.")
print()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"[BUTON BASILDI]  button = {event.button}  (D-Pad buton olarak gelmiş)")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"[BUTON BIRAKILDI] button = {event.button}")
            elif event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value
                aciklama = []
                if hat_y == 1: aciklama.append("YUKARI")
                if hat_y == -1: aciklama.append("AŞAĞI")
                if hat_x == -1: aciklama.append("SOL")
                if hat_x == 1: aciklama.append("SAĞ")
                if not aciklama: aciklama.append("MERKEZ/BIRAKILDI")
                print(f"[HAT] hat = {event.hat}  value = {event.value}  -> {' '.join(aciklama)}")
        time.sleep(0.02)
except KeyboardInterrupt:
    goodbye()

"""
Test 5: Share / Options / PS / Touchpad / Mic (Özel butonlar)

Sırayla bas:
    1. SHARE (CREATE) - sol üst küçük buton
    2. OPTIONS        - sağ üst küçük buton
    3. PS (Home)      - ortadaki PlayStation logo
    4. TOUCHPAD       - büyük dokunmatik alana TIKLAMA
    5. MIKROFON       - touchpad altındaki küçük mic butonu

Bittiğinde Ctrl+C.
"""
import time
from _ortak import init_joystick, goodbye
import pygame

js = init_joystick()

print()
print(">>> Her özel butona TEK TEK bas, bırak, sıradakine geç.")
print(">>> Ctrl+C ile çık.")
print()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"[BUTON BASILDI]  button = {event.button}")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"[BUTON BIRAKILDI] button = {event.button}")
        time.sleep(0.02)
except KeyboardInterrupt:
    goodbye()

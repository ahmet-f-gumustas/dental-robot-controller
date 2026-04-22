"""
Test 3: Sol/Sağ Analog Stick hareketleri + L3 / R3 tık

Sırayla yap:
    1. Sol analog yukarı
    2. Sol analog aşağı
    3. Sol analog sol
    4. Sol analog sağ
    5. Sol analog TIK (bas, aşağı it) -> L3
    6. Sağ analog yukarı
    7. Sağ analog aşağı
    8. Sağ analog sol
    9. Sağ analog sağ
   10. Sağ analog TIK -> R3

Bittiğinde Ctrl+C.
"""
import time
from _ortak import init_joystick, goodbye
import pygame

js = init_joystick()

print()
print(">>> Her analog hareketten sonra 1-2 saniye bekle ki çıktı okunsun.")
print(">>> Ctrl+C ile çık.")
print()

last_axis = [0.0] * js.get_numaxes()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"[BUTON BASILDI]  button = {event.button}  (L3 veya R3 olabilir)")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"[BUTON BIRAKILDI] button = {event.button}")
            elif event.type == pygame.JOYAXISMOTION:
                old = last_axis[event.axis]
                if abs(event.value - old) > 0.3:
                    yon = ""
                    if event.value > 0.5:
                        yon = " (POZİTİF yön)"
                    elif event.value < -0.5:
                        yon = " (NEGATİF yön)"
                    print(f"[AXIS]  axis = {event.axis}  value = {event.value:+.2f}{yon}")
                    last_axis[event.axis] = event.value
        time.sleep(0.02)
except KeyboardInterrupt:
    goodbye()

"""
Test 1: L1, R1, L2, R2 (Omuz + Trigger'lar)

Sırayla basılacak:
    1. L1
    2. R1
    3. L2 (yavaşça hafif bas -> tam bas -> bırak)
    4. R2 (yavaşça hafif bas -> tam bas -> bırak)

Bittiğinde Ctrl+C.
"""
import time
from _ortak import init_joystick, goodbye
import pygame

js = init_joystick()

print()
print(">>> Test sırası: L1 -> R1 -> L2 -> R2")
print(">>> L2 ve R2 trigger'lara YAVAŞÇA bas, axis değerinin nasıl değiştiğini izle.")
print(">>> Ctrl+C ile çık.")
print()

last_axis = [0.0] * js.get_numaxes()

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"[BUTON BASILDI ]  button = {event.button}")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"[BUTON BIRAKILDI] button = {event.button}")
            elif event.type == pygame.JOYAXISMOTION:
                # Sadece belirgin değişimleri yazdır
                old = last_axis[event.axis]
                if abs(event.value - old) > 0.25:
                    print(f"[AXIS]  axis = {event.axis}  value = {event.value:+.2f}")
                    last_axis[event.axis] = event.value
        time.sleep(0.02)
except KeyboardInterrupt:
    goodbye()

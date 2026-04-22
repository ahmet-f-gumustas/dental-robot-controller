"""
Test 2: × Cross, ○ Circle, □ Square, △ Triangle (Yüz butonları)

Sırayla basılacak:
    1. × (Cross / alt)
    2. ○ (Circle / sağ)
    3. □ (Square / sol)
    4. △ (Triangle / üst)

Bittiğinde Ctrl+C.
"""
import time
from _ortak import init_joystick, goodbye
import pygame

js = init_joystick()

print()
print(">>> Test sırası: × -> ○ -> □ -> △")
print(">>> Her butona bas, bırak, sıradakine geç.")
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

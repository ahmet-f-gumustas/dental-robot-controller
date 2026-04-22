"""Tüm test scriptleri için ortak yardımcı."""
import pygame
import sys


def init_joystick():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        print("[HATA] Joystick bulunamadı!")
        sys.exit(1)
    js = pygame.joystick.Joystick(0)
    js.init()
    print("=" * 60)
    print(f"  Joystick : {js.get_name()}")
    print(f"  Eksen: {js.get_numaxes()} | Buton: {js.get_numbuttons()} | Hat: {js.get_numhats()}")
    print("=" * 60)
    return js


def goodbye():
    pygame.quit()
    print("\n[ÇIKIŞ] Test sonlandı. Çıktıyı kopyalayıp Claude'a yapıştır.")

"""PS5 DualSense buton/axis haritası testi - basılan her şeyi yazdırır"""
import pygame
import sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Joystick bulunamadı!")
    sys.exit(1)

js = pygame.joystick.Joystick(0)
js.init()
print(f"Joystick: {js.get_name()}")
print(f"Axes: {js.get_numaxes()}, Buttons: {js.get_numbuttons()}, Hats: {js.get_numhats()}")
print("\nBir tuşa bas veya analog çubuğu oynat (Ctrl+C ile çık):\n")

try:
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"  BUTON BASILDI:  index={event.button}")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"  BUTON BIRAKILDI: index={event.button}")
            elif event.type == pygame.JOYHATMOTION:
                print(f"  D-PAD (HAT):    value={event.value}")

        # Axis değerlerini sürekli göster (sadece hareket edenler)
        active = []
        for i in range(js.get_numaxes()):
            val = js.get_axis(i)
            if abs(val) > 0.15:
                active.append(f"Axis{i}={val:+.2f}")
        if active:
            print(f"  AXES: {', '.join(active)}", end="\r")

        clock.tick(30)

except KeyboardInterrupt:
    print("\n\nÇıkış.")
    js.quit()
    pygame.quit()

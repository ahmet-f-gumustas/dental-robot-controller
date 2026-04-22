"""PS5 DualSense button/axis mapping test - prints every input event."""
import pygame
import sys

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick detected!")
    sys.exit(1)

js = pygame.joystick.Joystick(0)
js.init()
print(f"Joystick: {js.get_name()}")
print(f"Axes: {js.get_numaxes()}, Buttons: {js.get_numbuttons()}, Hats: {js.get_numhats()}")
print("\nPress a button or move a stick (Ctrl+C to quit):\n")

try:
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"  BUTTON DOWN:   index={event.button}")
            elif event.type == pygame.JOYBUTTONUP:
                print(f"  BUTTON UP:     index={event.button}")
            elif event.type == pygame.JOYHATMOTION:
                print(f"  D-PAD (HAT):   value={event.value}")

        # Show live axis values (only the ones moved past the deadzone)
        active = []
        for i in range(js.get_numaxes()):
            val = js.get_axis(i)
            if abs(val) > 0.15:
                active.append(f"Axis{i}={val:+.2f}")
        if active:
            print(f"  AXES: {', '.join(active)}", end="\r")

        clock.tick(30)

except KeyboardInterrupt:
    print("\n\nExit.")
    js.quit()
    pygame.quit()

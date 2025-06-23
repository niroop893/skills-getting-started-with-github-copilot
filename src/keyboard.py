from pynput import keyboard
from pynput.keyboard import Key, Controller, Listener
import pystray
from PIL import Image, ImageDraw
import pyperclip
import time
import threading

class RemapperTrayApp:
    def __init__(self):
        self.listener = None
        self.enabled = False
        self.ctrl = Controller()
        self.pressed = set()
        self.alt_held = False
        self.icon = pystray.Icon(
            'KeyRemapper',
            self._create_icon(),
            menu=pystray.Menu(
                pystray.MenuItem('Toggle Remapping (Ctrl+Shift+R)', self.toggle),
                pystray.MenuItem('Exit', self.exit_app)
            )
        )

    def _create_icon(self):
        img = Image.new('RGB', (64, 64), 'white')
        d = ImageDraw.Draw(img)
        d.rectangle((8, 8, 56, 56), outline='black', width=3)
        d.text((16, 20), 'KR', fill='black')
        return img

    def toggle(self, *args):
        if self.enabled:
            self.stop_listener()
            self.icon.title = 'Key Remapper (OFF)'
        else:
            self.start_listener()
            self.icon.title = 'Key Remapper (ON)'
        self.enabled = not self.enabled

    def start_listener(self):
        self.listener = Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=True
        )
        self.listener.start()
        print("[INFO] Remapper enabled.")

    def stop_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("[INFO] Remapper disabled.")

    def on_press(self, key):
        self.pressed.add(key)

        # Toggle with Ctrl + Shift + R
        try:
            if (Key.ctrl_l in self.pressed or Key.ctrl_r in self.pressed) and \
               (Key.shift in self.pressed or Key.shift_r in self.pressed) and \
               key.char.lower() == 'r':
                self.toggle()
                return False
        except AttributeError:
            pass

        # Detect characters
        try:
            chars = {k.char.lower() for k in self.pressed if hasattr(k, 'char') and k.char}
            key_char = key.char.lower() if hasattr(key, 'char') and key.char else ''
        except:
            return

        if 'w' in chars:
            if key_char == 'c':
                threading.Thread(target=self._copy).start()
                return False
            elif key_char == 'v':
                threading.Thread(target=self._paste).start()
                return False
            elif key_char == 'a':
                threading.Thread(target=self._select_all).start()
                return False
            elif key_char == 's':
                threading.Thread(target=self._save).start()
                return False
            elif key_char == 'z':
                threading.Thread(target=self._undo).start()
                return False
            elif key_char == '1':
                if not self.alt_held:
                    print("[ALT] Pressed")
                    self.ctrl.press(Key.alt)
                    self.alt_held = True
                return False
            elif key_char == '2':
                if self.alt_held:
                    print("[TAB] Pressed (with Alt)")
                    self.ctrl.press(Key.tab)
                    time.sleep(0.05)
                    self.ctrl.release(Key.tab)
                return False

    def on_release(self, key):
        self.pressed.discard(key)

        try:
            if self.alt_held and hasattr(key, 'char') and key.char == '1':
                print("[ALT] Released")
                self.ctrl.release(Key.alt)
                self.alt_held = False
        except Exception:
            pass

    def _copy(self):
        with self.ctrl.pressed(Key.ctrl):
            self.ctrl.press('c')
            time.sleep(0.05)
            self.ctrl.release('c')
        time.sleep(0.1)
        try:
            print("[COPY]", pyperclip.paste())
        except Exception as e:
            print("Clipboard read error:", e)

    def _paste(self):
        with self.ctrl.pressed(Key.ctrl):
            self.ctrl.press('v')
            time.sleep(0.05)
            self.ctrl.release('v')

    def _select_all(self):
        with self.ctrl.pressed(Key.ctrl):
            self.ctrl.press('a')
            time.sleep(0.05)
            self.ctrl.release('a')

    def _save(self):
        with self.ctrl.pressed(Key.ctrl):
            self.ctrl.press('s')
            time.sleep(0.05)
            self.ctrl.release('s')

    def _undo(self):
        with self.ctrl.pressed(Key.ctrl):
            self.ctrl.press('z')
            time.sleep(0.05)
            self.ctrl.release('z')

    def exit_app(self, *args):
        self.stop_listener()
        self.icon.stop()

    def run(self):
        self.icon.title = 'Key Remapper (OFF)'
        self.icon.run()

if __name__ == '__main__':
    RemapperTrayApp().run()

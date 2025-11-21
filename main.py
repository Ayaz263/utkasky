import socket
import threading
from kivy.app import App
from kivy.core.window import Window
# Graphics больше не нужны, так как нет пользовательских закруглений
# from kivy.graphics import Color, Rectangle, RoundedRectangle 
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput # Используем стандартный TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition

# Цветовая палитра
# Фон приложения: RGB(50, 25, 0)
APP_BG_COLOR = (50/255.0, 25/255.0, 0/255.0, 1.0) 
# Фон полей ввода: RGB(30, 15, 0) (Очень темный)
INPUT_BG_COLOR = (30/255.0, 15/255.0, 0/255.0, 1.0)
# Цвет текста (242, 242, 242) - должен быть хорошо виден
TEXT_COLOR = (242/255.0, 242/255.0, 242/255.0, 1.0)
# Цвет для текста подсказки (hint text), чуть темнее основного текста
HINT_TEXT_COLOR = (180/255.0, 180/255.0, 180/255.0, 1.0) 

Window.clearcolor = APP_BG_COLOR

# --- Класс RoundedTextInput удален, используем стандартный TextInput ---

# Глобальные переменные для хранения настроек подключения
HOST = ''
PORT = 0

class ConnectScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Используем новый TEXT_COLOR
        layout.add_widget(Label(text="Введите данные сервера", color=TEXT_COLOR))
        
        # Используем стандартный TextInput
        self.ip_input = TextInput(
            hint_text="IP-адрес", 
            text="127.0.0.1", 
            size_hint_y=None, height=dp(40),
            background_color=INPUT_BG_COLOR,
            foreground_color=TEXT_COLOR,
            hint_text_color=HINT_TEXT_COLOR
        )
        self.port_input = TextInput(
            hint_text="Порт", 
            text="65432",
            size_hint_y=None, height=dp(40),
            background_color=INPUT_BG_COLOR,
            foreground_color=TEXT_COLOR,
            hint_text_color=HINT_TEXT_COLOR
        )
        connect_button = Button(text="Подключиться", size_hint_y=None, height=dp(40))
        connect_button.bind(on_press=self.try_connect)
        
        self.status_label = Label(text="", color=TEXT_COLOR)

        layout.add_widget(self.ip_input)
        layout.add_widget(self.port_input)
        layout.add_widget(connect_button)
        self.add_widget(layout)
    
    def try_connect(self, instance):
        global HOST, PORT
        HOST = self.ip_input.text
        try:
            PORT = int(self.port_input.text)
            self.status_label.text = f"Попытка подключения к {HOST}:{PORT}..."
            self.manager.get_screen('chat').connect_to_server()
            self.manager.current = 'chat'
        except ValueError:
            self.status_label.text = "Ошибка: Неверный формат порта (используйте цифры)."
        except Exception as e:
            self.status_label.text = f"Ошибка подключения: {e}"

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_socket = None
        
        self.layout = BoxLayout(orientation='vertical')
        self.message_area_sv = ScrollView()
        
        # Используем новый TEXT_COLOR
        self.message_area = Label(
            text="Ожидание подключения...\n",
            valign='top', padding=(10, 10), size_hint_y=None,
            color=TEXT_COLOR
        )
        self.message_area.bind(size=lambda *args: self.message_area.setter('text_size')(self.message_area, (self.message_area_sv.width, None)))
        self.message_area_sv.add_widget(self.message_area)
        self.layout.add_widget(self.message_area_sv)

        input_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5), padding=dp(5))
        
        # Используем стандартный TextInput
        self.text_input = TextInput(
            hint_text="Введите сообщение...", 
            multiline=False,
            background_color=INPUT_BG_COLOR,
            foreground_color=TEXT_COLOR,
            hint_text_color=HINT_TEXT_COLOR,
        )
        
        send_button = Button(
            size_hint_x=None, width=dp(50), 
            background_normal='ni.png', background_down='pi.png',
            border=(0, 0, 0, 0)
        )
        send_button.bind(on_press=self.send_message)

        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_button)
        self.layout.add_widget(input_layout)
        self.add_widget(self.layout)

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.add_message(f"Успешно подключено к {HOST}:{PORT}")
            threading.Thread(target=self.receive_messages).start()
        except Exception as e:
            self.add_message(f"Ошибка подключения: {e}")
            self.manager.current = 'connect'

    def add_message(self, message):
        def update_label(dt):
            self.message_area.text += f"{message}\n"
            self.message_area.texture_update()
            self.message_area.height = self.message_area.texture_size
            self.message_area_sv.scroll_y = 0
        Clock.schedule_once(update_label)
        
    def send_message(self, instance):
        message = self.text_input.text
        if message and self.client_socket:
            try:
                self.client_socket.send(message.encode('utf-8'))
                self.add_message(f"Вы: {message}")
                self.text_input.text = ""
            except:
                self.add_message("Ошибка отправки. Соединение потеряно.")

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.add_message(f"Друг: {message}")
            except:
                break

    def on_stop(self):
        if self.client_socket:
            self.client_socket.close()

class ChatAppManager(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(ConnectScreen(name='connect'))
        self.sm.add_widget(ChatScreen(name='chat'))
        return self.sm

if __name__ == '__main__':
    ChatAppManager().run()

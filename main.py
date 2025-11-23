import socket
import threading
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.metrics import dp  # Используем dp для масштабирования
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import StringProperty 

# Цветовая палитра
APP_BG_COLOR = (50/255.0, 25/255.0, 0/255.0, 1.0) 
INPUT_BG_COLOR = (30/255.0, 15/255.0, 0/255.0, 1.0)
INPUT_BG_FOCUS_COLOR = (70/255.0, 45/255.0, 20/255.0, 1.0) # Ярче при фокусе
TEXT_COLOR = (242/255.0, 242/255.0, 242/255.0, 1.0)
HINT_TEXT_COLOR = (180/255.0, 180/255.0, 180/255.0, 1.0) 
Window.clearcolor = APP_BG_COLOR

# Глобальные переменные
HOST = ''
PORT = 0
USERNAME = 'Anonymous' 

# Функция для создания контейнера с фоновым изображением
def create_background_layout():
    fl = FloatLayout()
    bg_image = Image(source='ph.png', allow_stretch=True, keep_ratio=False)
    fl.add_widget(bg_image)
    return fl

class ConnectScreen(Screen):
    # Свойство Kivy для динамического текста IP-подсказки
    info_text_ip = StringProperty("например: 192.168.1.6")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root_layout = create_background_layout()
        content_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(0.8, 0.8), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        content_layout.add_widget(Label(text="Введите данные сервера и ваше имя", color=TEXT_COLOR))

        self.isuasd = Label(text="надо писать в ip 192.168.191.125")
        content_layout.add_widget(self.isuasd)
        self.bind(info_text_ip=self.isuasd.setter('text')) 
        
        self.username_input = TextInput(
            hint_text="Ваше имя (nickname)", text="User", size_hint_y=None, height=dp(40),
            background_color=INPUT_BG_COLOR, foreground_color=TEXT_COLOR, hint_text_color=HINT_TEXT_COLOR
        )
        self.ip_input = TextInput(
            hint_text="IP-адрес", text="", size_hint_y=None, height=dp(40),
            background_color=INPUT_BG_COLOR, foreground_color=TEXT_COLOR, hint_text_color=HINT_TEXT_COLOR
        )
        self.port_input = TextInput(
            hint_text="Порт", text="65432", size_hint_y=None, height=dp(40),
            background_color=INPUT_BG_COLOR, foreground_color=TEXT_COLOR, hint_text_color=HINT_TEXT_COLOR
        )

        self.username_input.bind(focus=self.on_focus_input)
        self.ip_input.bind(focus=self.on_focus_input)
        self.port_input.bind(focus=self.on_focus_input)

        connect_button = Button(text="Подключиться", size_hint_y=None, height=dp(40))
        connect_button.bind(on_press=self.try_connect)
        self.status_label = Label(text="", color=TEXT_COLOR)

        content_layout.add_widget(self.username_input) 
        content_layout.add_widget(self.ip_input)
        content_layout.add_widget(self.port_input)
        content_layout.add_widget(connect_button)
        content_layout.add_widget(self.status_label)
        
        root_layout.add_widget(content_layout)
        self.add_widget(root_layout)
    
    def set_info_text_ip(self, new_text):
        self.info_text_ip = new_text

    def on_focus_input(self, instance, value):
        if value:
            instance.background_color = INPUT_BG_FOCUS_COLOR
        else:
            instance.background_color = INPUT_BG_COLOR
    
    def try_connect(self, instance):
        global HOST, PORT, USERNAME
        HOST = self.ip_input.text
        USERNAME = self.username_input.text.strip()
        if not USERNAME:
            self.status_label.text = "Ошибка: Введите имя пользователя."
            return

        try:
            PORT = int(self.port_input.text)
            self.status_label.text = f"Попытка подключения к {HOST}:{PORT} под именем {USERNAME}..."
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
        root_layout = create_background_layout()
        self.layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        title_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5), padding=dp(5))
        self.status_label_chat = Label(text="Статус: Ожидание подключения", color=TEXT_COLOR, size_hint_x=4)
        self.disconnect_button = Button(text="Выйти", size_hint_x=1)
        self.disconnect_button.bind(on_press=self.return_to_connect_screen) 
        title_layout.add_widget(self.status_label_chat)
        title_layout.add_widget(self.disconnect_button)
        self.layout.add_widget(title_layout) 
        self.message_area_sv = ScrollView()
        self.message_area = Label(
            text="Ожидание подключения...\n",
            valign='top', padding=(10, 10), size_hint_y=None,
            color=TEXT_COLOR
        )
        self.message_area.bind(size=lambda *args: self.message_area.setter('text_size')(self.message_area, (self.message_area_sv.width, None)))
        self.message_area_sv.add_widget(self.message_area)
        self.layout.add_widget(self.message_area_sv)
        
        # *** ИЗМЕНЕНИЯ РАЗМЕРОВ ЗДЕСЬ (52dp) ***
        # Высота всего блока ввода
        input_layout = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(5), padding=dp(5))
        self.text_input = TextInput(
            hint_text="Введите сообщение...", 
            multiline=False,
            background_color=INPUT_BG_COLOR,
            foreground_color=TEXT_COLOR,
            hint_text_color=HINT_TEXT_COLOR,
            height=dp(52), # Высота поля ввода 52dp
        )
        self.text_input.bind(focus=self.on_focus_input) 

        self.text_input.bind(on_text_validate=self.send_message)
        
        send_button = Button(
            size_hint_x=None,
            width=dp(52),  # Ширина кнопки 52dp (делает ее квадратной 52х52, так как size_hint_y=None)
            background_normal='ni.png',  # Изображение для обычного состояния
            background_down='ni.png',    # Изображение для нажатого состояния
            border=(0, 0, 0, 0)          # Убираем стандартную рамку
        )
        # *****************************************
        
        send_button.bind(on_press=self.send_message)
        input_layout.add_widget(self.text_input)
        input_layout.add_widget(send_button)
        self.layout.add_widget(input_layout)
        root_layout.add_widget(self.layout)
        self.add_widget(root_layout)

    def on_focus_input(self, instance, value):
        if value:
            instance.background_color = INPUT_BG_FOCUS_COLOR
        else:
            instance.background_color = INPUT_BG_COLOR

    def return_to_connect_screen(self, instance=None):
        self.close_connection()
        self.manager.current = 'connect'

    def connect_to_server(self):
        self.status_label_chat.text = f"Статус: Подключение как {USERNAME}..."
        threading.Thread(target=self._establish_connection, daemon=True).start()

    def _establish_connection(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT)) 
            self.client_socket.send(USERNAME.encode('utf-8'))

            Clock.schedule_once(lambda dt: setattr(self.status_label_chat, 'text', f"Статус: Подключено как {USERNAME}"))
            self.add_message(f"Успешно подключено к {HOST}:{PORT}")
            self.receive_messages() 
        except Exception as e:
            err_msg = str(e) 
            def update_ui_on_error(dt):
                self.status_label_chat.text = "Статус: Ошибка подключения"
                self.add_message(f"Ошибка подключения: {err_msg}") 
            Clock.schedule_once(update_ui_on_error)
            self.close_connection()

    def add_message(self, message):
        def update_label(dt):
            self.message_area.text += f"{message}\n"
            self.message_area.texture_update()
            self.message_area.height = self.message_area.texture_size[1]
            self.message_area_sv.scroll_y = 0
        Clock.schedule_once(update_label)
        
    def send_message(self, instance):
        message_text = self.text_input.text
        if message_text and self.client_socket:
            try:
                self.client_socket.send(message_text.encode('utf-8')) 
                self.add_message(f"Вы: {message_text}")
                self.text_input.text = ""
            except:
                self.add_message("Ошибка отправки. Соединение потеряно.")
                Clock.schedule_once(lambda dt: setattr(self.status_label_chat, 'text', "Статус: Отключено"))
                self.close_connection() 

    def receive_messages(self):
        while self.client_socket:
            try:
                data = self.client_socket.recv(1024)
                if not data:
                    self.add_message("Соединение закрыто сервером.")
                    break
                message = data.decode('utf-8')
                
                # НОВОЕ: Обработка команды изменения подсказки IP
                if message.startswith("#HINT#"):
                    new_hint_text = message[len("#HINT#"):].strip()
                    connect_screen = self.manager.get_screen('connect')
                    Clock.schedule_once(lambda dt: connect_screen.set_info_text_ip(new_hint_text))
                    self.add_message(f"[SERVER]: Подсказка IP обновлена.")
                else:
                    self.add_message(message) 
            except:
                self.add_message("Произошла ошибка при приеме данных.")
                break
        
        Clock.schedule_once(lambda dt: setattr(self.status_label_chat, 'text', "Статус: Отключено"))
        self.close_connection()

    def close_connection(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None


class ChatAppManager(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.sm.add_widget(ConnectScreen(name='connect'))
        self.sm.add_widget(ChatScreen(name='chat'))
        return self.sm

    def on_stop(self):
        chat_screen = self.sm.get_screen('chat')
        chat_screen.close_connection()

if __name__ == '__main__':
    ChatAppManager().run()

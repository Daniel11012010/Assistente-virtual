from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.uix.label import Label
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.gridlayout import GridLayout
import json
import os
import datetime
import threading
import time
import re
import webbrowser
import wikipedia
from gtts import gTTS
import pygame
from deep_translator import GoogleTranslator
import uuid
import math
import base64
from urllib.parse import quote_plus
import requests
import speech_recognition as sr
from threading import Thread
import tempfile
from pathlib import Path
import psutil
import pyautogui
import random
import sqlite3
from contextlib import contextmanager
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

MEMORY_FILE = "jarvis_memoria.json"
PATTERNS_FILE = "jarvis_patterns.json"
USAGE_FILE = "jarvis_usage.json"

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

DIAS_PT = [
    "segunda-feira", "terça-feira", "quarta-feira",
    "quinta-feira", "sexta-feira", "sábado", "domingo"
]

class AudioManager:
    def __init__(self):
        self.audio_files = []
        self.lock = threading.Lock()
        
    def generate_audio_file(self, text, lang='pt-br'):
        """Gera arquivo de áudio e retorna o caminho"""
        try:
            tts = gTTS(text=text, lang=lang)
            
            temp_dir = Path(tempfile.gettempdir()) / "jarvis_audio"
            temp_dir.mkdir(exist_ok=True)
            
            filename = f"jarvis_{int(time.time())}_{hash(text) & 0xFFFFFFFF}.mp3"
            filepath = temp_dir / filename
            
            tts.save(str(filepath))
            
            with self.lock:
                self.audio_files.append(str(filepath))
                
            return str(filepath)
            
        except Exception as e:
            logging.error(f"Erro ao gerar áudio: {e}")
            return None
            
    def cleanup_old_files(self):
        """Limpa arquivos antigos em segundo plano"""
        def cleanup():
            temp_dir = Path(tempfile.gettempdir()) / "jarvis_audio"
            if temp_dir.exists():
                try:
                    current_time = time.time()
                    for file_path in temp_dir.glob("jarvis_*.mp3"):
                        if current_time - file_path.stat().st_mtime > 3600:
                            try:
                                file_path.unlink()
                            except:
                                pass
                except Exception as e:
                    logging.error(f"Erro na limpeza de áudios: {e}")
                    
        threading.Thread(target=cleanup, daemon=True).start()
        
    def immediate_cleanup(self, filepath):
        """Tenta remover arquivo imediatamente após uso"""
        def remove_file(path):
            try:
                if os.path.exists(path):
                    os.unlink(path)
                    logging.info(f"Arquivo de áudio removido: {path}")
                    
                with self.lock:
                    if path in self.audio_files:
                        self.audio_files.remove(path)
                        
            except Exception as e:
                logging.error(f"Erro ao remover {path}: {e}")
                Clock.schedule_once(lambda dt: remove_file(path), 5)
                
        threading.Thread(target=remove_file, args=(filepath,), daemon=True).start()
        
    def cleanup_all(self):
        """Limpeza total de todos os arquivos"""
        with self.lock:
            for filepath in self.audio_files[:]:
                self.immediate_cleanup(filepath)

class LearningSystem:
    def __init__(self):
        self.patterns_file = PATTERNS_FILE
        self.patterns = self.load_patterns()
        
    def load_patterns(self):
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_patterns(self):
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erro ao salvar padrões: {e}")
    
    def learn_response(self, trigger, response):
        self.patterns[trigger.lower()] = response
        self.save_patterns()
        return f"Aprendi: quando você disser '{trigger}', responderei '{response}'"
    
    def get_learned_response(self, query):
        return self.patterns.get(query.lower())
    
    def forget_pattern(self, trigger):
        if trigger.lower() in self.patterns:
            del self.patterns[trigger.lower()]
            self.save_patterns()
            return f"Esqueci o padrão para '{trigger}'"
        return f"Padrão '{trigger}' não encontrado"
    
    def list_patterns(self):
        if not self.patterns:
            return "Nenhum padrão aprendido ainda"
        return "Padrões aprendidos: " + ", ".join([f"'{k}'=>'{v}'" for k, v in self.patterns.items()])

class SystemControl:
    def __init__(self):
        self.apps = {
            'calculadora': 'calc' if os.name == 'nt' else 'gnome-calculator',
            'bloco de notas': 'notepad' if os.name == 'nt' else 'gedit',
            'paint': 'mspaint' if os.name == 'nt' else 'kolourpaint',
            'explorer': 'explorer' if os.name == 'nt' else 'nautilus',
            'terminal': 'cmd' if os.name == 'nt' else 'gnome-terminal',
            'navegador': 'start chrome' if os.name == 'nt' else 'google-chrome',
            'word': 'winword' if os.name == 'nt' else 'libreoffice',
            'excel': 'excel' if os.name == 'nt' else 'libreoffice',
            'powerpoint': 'powerpnt' if os.name == 'nt' else 'libreoffice',
            'gerenciador de tarefas': 'taskmgr' if os.name == 'nt' else 'gnome-system-monitor',
            'configurações': 'start ms-settings:' if os.name == 'nt' else 'gnome-control-center',
        }
        
    def get_system_info(self):
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            info = f"CPU: {cpu}% | Memória: {memory}% | Disco: {disk}%"
            
            # Informações de bateria (se disponível)
            try:
                battery = psutil.sensors_battery()
                if battery:
                    status = "carregando" if battery.power_plugged else "descarregando"
                    info += f" | Bateria: {battery.percent}% ({status})"
            except:
                pass
                
            return info
        except Exception as e:
            return f"Erro ao obter informações do sistema: {str(e)}"
    
    def take_screenshot(self):
        try:
            screenshot = pyautogui.screenshot()
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot.save(filename)
            return f"Captura de tela salva como {filename}"
        except Exception as e:
            return f"Erro ao capturar tela: {str(e)}"
    
    def open_application(self, app_name):
        app_name_lower = app_name.lower().strip()
        
        # Busca exata primeiro
        if app_name_lower in self.apps:
            try:
                os.system(self.apps[app_name_lower])
                return f"Abrindo {app_name}"
            except Exception as e:
                return f"Erro ao abrir {app_name}: {str(e)}"
        
        # Busca parcial
        for app_key, app_command in self.apps.items():
            if app_name_lower in app_key:
                try:
                    os.system(app_command)
                    return f"Abrindo {app_key}"
                except Exception as e:
                    return f"Erro ao abrir {app_key}: {str(e)}"
        
        return f"Aplicativo '{app_name}' não encontrado. Diga 'lista de aplicativos' para ver os disponíveis."
    
    def list_applications(self):
        apps_list = ", ".join([f"'{app}'" for app in self.apps.keys()])
        return f"Aplicativos disponíveis: {apps_list}"

class UsageAnalytics:
    def __init__(self):
        self.usage_file = USAGE_FILE
        self.usage_data = self.load_usage_data()
        
    def load_usage_data(self):
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"commands": {}, "sessions": 0, "total_time": 0, "first_use": datetime.datetime.now().isoformat()}
        return {"commands": {}, "sessions": 0, "total_time": 0, "first_use": datetime.datetime.now().isoformat()}
    
    def save_usage_data(self):
        try:
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Erro ao salvar dados de uso: {e}")
    
    def log_command(self, command):
        try:
            if command.strip():
                # Usa as primeiras 2 palavras como chave do comando
                words = command.lower().split()[:2]
                cmd_key = ' '.join(words) if words else "unknown"
                
                self.usage_data["commands"][cmd_key] = self.usage_data["commands"].get(cmd_key, 0) + 1
                self.usage_data["sessions"] = self.usage_data.get("sessions", 0) + 1
                self.save_usage_data()
        except Exception as e:
            logging.error(f"Erro ao registrar comando: {e}")
    
    def get_usage_stats(self):
        try:
            total_commands = sum(self.usage_data["commands"].values())
            if not total_commands:
                return "Nenhum comando registrado ainda"
                
            most_used = max(self.usage_data["commands"].items(), key=lambda x: x[1], default=("Nenhum", 0))
            
            # Calcular tempo desde primeiro uso
            first_use = datetime.datetime.fromisoformat(self.usage_data["first_use"])
            days_used = (datetime.datetime.now() - first_use).days
            
            stats = [
                f"Total de comandos: {total_commands}",
                f"Comando mais usado: '{most_used[0]}' ({most_used[1]} vezes)",
                f"Dias em uso: {days_used}",
                f"Sessões registradas: {self.usage_data['sessions']}"
            ]
            
            return " | ".join(stats)
        except Exception as e:
            return f"Erro ao gerar estatísticas: {str(e)}"

class AIServices:
    def __init__(self):
        self.responses = {
            "como você está": ["Estou funcionando perfeitamente!", "Ótimo! Pronto para ajudar.", "Melhor que nunca!"],
            "quem é você": ["Sou o Jarvis, seu assistente pessoal inteligente!", "Jarvis ao seu serviço!"],
            "obrigado": ["De nada! Estou aqui para ajudar.", "Por nada! Fico feliz em ajudar."],
            "piada": [
                "Por que o Python foi para a terapia? Porque tinha muitos issues!",
                "Qual é o café favorito do desenvolvedor? Java!",
                "Por que o computador foi para o médico? Porque tinha um vírus!"
            ],
            "conselho": [
                "Sempre faça backup do seu trabalho!",
                "Um código limpo é um código feliz!",
                "A prática leva à perfeição - continue programando!"
            ]
        }
    
    def get_ai_response(self, query):
        query_lower = query.lower()
        
        # Busca resposta nos padrões
        for pattern, responses in self.responses.items():
            if pattern in query_lower:
                return random.choice(responses)
        
        # Respostas padrão para perguntas comuns
        if any(word in query_lower for word in ["como", "funciona"]):
            return "Posso ajudar com tarefas, informações, entretenimento e muito mais! Diga 'ajuda' para ver todas as opções."
        
        elif any(word in query_lower for word in ["por que", "motivo"]):
            return "Estou programado para ser útil e eficiente em várias tarefas!"
        
        elif any(word in query_lower for word in ["onde", "local"]):
            return "Estou rodando neste dispositivo, pronto para ajudá-lo onde precisar!"
        
        # Resposta criativa padrão
        creative_responses = [
            "Essa é uma pergunta interessante! No momento, estou focado em ajudá-lo com tarefas práticas.",
            "Hmm, vou precisar de mais informações para responder isso adequadamente.",
            "Que pergunta curiosa! Minha especialidade é ajudar com tarefas do dia a dia.",
            "Interessante! No momento, posso ajudá-lo com pesquisas, organização, entretenimento e muito mais."
        ]
        
        return random.choice(creative_responses)

class SecurityManager:
    def __init__(self):
        self.sensitive_commands = [
            "formatar", "deletar", "apagar", "desinstalar", "reiniciar", 
            "desligar", "shutdown", "remover", "excluir"
        ]
        
    def requires_confirmation(self, command):
        command_lower = command.lower()
        return any(cmd in command_lower for cmd in self.sensitive_commands)
    
    def confirm_action(self, command, callback):
        def confirmed(instance):
            callback(True)
            self.dialog.dismiss()
            
        def cancelled(instance):
            callback(False)
            self.dialog.dismiss()
        
        self.dialog = MDDialog(
            title="🔒 Confirmação de Segurança",
            text=f"Tem certeza que deseja executar: '{command}'?\nEsta ação pode ser irreversível.",
            buttons=[
                MDFlatButton(text="❌ Cancelar", on_release=cancelled),
                MDRaisedButton(text="✅ Confirmar", on_release=confirmed),
            ]
        )
        self.dialog.open()

class ThemeManager:
    def __init__(self):
        self.themes = {
            "padrão": {"primary": "Blue", "accent": "LightBlue", "bg_color": [0.1, 0.1, 0.2, 1]},
            "escuro": {"primary": "DeepPurple", "accent": "Amber", "bg_color": [0.05, 0.05, 0.1, 1]},
            "tecnológico": {"primary": "Cyan", "accent": "Teal", "bg_color": [0.08, 0.15, 0.25, 1]},
            "natureza": {"primary": "Green", "accent": "LightGreen", "bg_color": [0.1, 0.2, 0.1, 1]},
            "fogo": {"primary": "Orange", "accent": "Red", "bg_color": [0.2, 0.1, 0.05, 1]},
        }
        self.current_theme = "padrão"
    
    def change_theme(self, theme_name, app):
        if theme_name.lower() in self.themes:
            self.current_theme = theme_name.lower()
            theme = self.themes[self.current_theme]
            
            app.theme_cls.primary_palette = theme["primary"]
            app.theme_cls.accent_palette = theme["accent"]
            app.theme_cls.theme_style = "Dark"
            
            return f"🎨 Tema alterado para '{theme_name}'"
        return f"Tema '{theme_name}' não encontrado. Temas disponíveis: {', '.join(self.themes.keys())}"
    
    def get_current_theme(self):
        return self.current_theme
    
    def list_themes(self):
        return "Temas disponíveis: " + ", ".join([f"'{theme}'" for theme in self.themes.keys()])

class AdvancedHUD(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle = 0
        self.pulse_scale = 1.0
        self.pulse_growing = True
        self.is_speaking = False
        self.size_hint = (1, 0.25)
        self.pos_hint = {'top': 1}
        self.animation_variation = 0
        self.speech_duration = 0
        self.performance_data = {
            'cpu': 0,
            'memory': 0,
            'disk': 0
        }

        # Fundo limpo
        with self.canvas.before:
            Color(0.05, 0.05, 0.1, 0.9)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Elementos do HUD organizados
        self.draw_interface_limpa()
        self.create_info_widgets()
        self.create_performance_widgets()
        self.create_status_indicators()

        # Inicia animações
        Clock.schedule_interval(self.update_animation, 1 / 60)
        Clock.schedule_interval(self.atualizar_hora_data, 1)
        Clock.schedule_interval(self.update_performance_metrics, 3)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def draw_interface_limpa(self):
        """Interface limpa e organizada"""
        with self.canvas:
            # Círculo central simplificado
            Color(0, 0.8, 1, 0.3)
            Line(circle=(self.center_x, self.center_y + 30, 35), width=1.5)
            
            # Núcleo pulsante
            Color(0, 1, 1, 0.8)
            self.nucleo = Ellipse(pos=(self.center_x - 8, self.center_y + 22), size=(16, 16))

    def create_info_widgets(self):
        """Cria labels de hora e data"""
        
        # Hora
        self.hora_label = Label(
            text="--:--:--",
            font_size=16,
            bold=True,
            color=(0, 1, 1, 1),
            size_hint=(None, None),
            size=(100, 25),
            pos_hint={'x': 0.02, 'top': 0.95}
        )
        self.add_widget(self.hora_label)

        # Data
        self.data_label = Label(
            text="--/--/----",
            font_size=11,
            color=(0.7, 0.7, 1, 0.8),
            size_hint=(None, None),
            size=(100, 20),
            pos_hint={'x': 0.02, 'top': 0.80}
        )
        self.add_widget(self.data_label)

    def create_performance_widgets(self):
        """Widgets de desempenho compactos"""
        
        # CPU
        self.cpu_label = Label(
            text="CPU: --%",
            font_size=10,
            color=(0, 1, 0, 1),
            size_hint=(None, None),
            size=(70, 18),
            pos_hint={'right': 0.98, 'top': 0.95}
        )
        self.add_widget(self.cpu_label)
        
        # Memória
        self.memory_label = Label(
            text="RAM: --%",
            font_size=10,
            color=(1, 1, 0, 1),
            size_hint=(None, None),
            size=(70, 18),
            pos_hint={'right': 0.98, 'top': 0.85}
        )
        self.add_widget(self.memory_label)
        
        # Disco
        self.disk_label = Label(
            text="DISK: --%",
            font_size=10,
            color=(1, 0.5, 0, 1),
            size_hint=(None, None),
            size=(70, 18),
            pos_hint={'right': 0.98, 'top': 0.75}
        )
        self.add_widget(self.disk_label)

    def create_status_indicators(self):
        """Indicadores de status organizados"""
        
        # Status do Jarvis (centro)
        self.status_label = Label(
            text="● ONLINE",
            font_size=11,
            color=(0, 1, 0, 1),
            size_hint=(None, None),
            size=(80, 20),
            pos_hint={'center_x': 0.5, 'top': 0.95}
        )
        self.add_widget(self.status_label)
        
        # Contador de comandos
        self.commands_label = Label(
            text="Comandos: 0",
            font_size=9,
            color=(1, 1, 1, 0.6),
            size_hint=(None, None),
            size=(90, 18),
            pos_hint={'center_x': 0.5, 'top': 0.80}
        )
        self.add_widget(self.commands_label)

    def update_performance_metrics(self, dt):
        """Atualiza métricas de desempenho"""
        try:
            # CPU
            cpu = psutil.cpu_percent()
            self.performance_data['cpu'] = cpu
            
            # Memória
            memory = psutil.virtual_memory().percent
            self.performance_data['memory'] = memory
            
            # Disco
            disk = psutil.disk_usage('/').percent
            self.performance_data['disk'] = disk
            
            # Atualizar labels
            self.cpu_label.text = f"CPU: {cpu:.0f}%"
            self.memory_label.text = f"RAM: {memory:.0f}%"
            self.disk_label.text = f"DSK: {disk:.0f}%"
            
            # Atualizar cores
            self.update_metric_colors()
            
        except Exception as e:
            logging.error(f"Erro atualizando métricas: {e}")

    def update_metric_colors(self):
        """Atualiza cores baseadas nos valores"""
        cpu = self.performance_data['cpu']
        memory = self.performance_data['memory']
        disk = self.performance_data['disk']
        
        # Cores baseadas em thresholds
        self.cpu_label.color = (0, 1, 0, 1) if cpu < 70 else (1, 1, 0, 1) if cpu < 90 else (1, 0, 0, 1)
        self.memory_label.color = (1, 1, 0, 1) if memory < 70 else (1, 0.5, 0, 1) if memory < 90 else (1, 0, 0, 1)
        self.disk_label.color = (1, 0.5, 0, 1) if disk < 70 else (1, 0.3, 0, 1) if disk < 90 else (1, 0, 0, 1)

    def update_animation(self, dt):
        """Animação suave"""
        self.rotation_angle = (self.rotation_angle + 30 * dt) % 360

        # Pulsação durante fala
        if self.is_speaking:
            pulse_variation = math.sin(self.animation_variation * 4) * 0.15
            self.animation_variation += dt * 2
            
            if self.pulse_growing:
                self.pulse_scale += 2 * dt
                if self.pulse_scale >= 1.2 + pulse_variation:
                    self.pulse_growing = False
            else:
                self.pulse_scale -= 2 * dt
                if self.pulse_scale <= 0.8 + pulse_variation:
                    self.pulse_growing = True
        else:
            # Retornar suavemente ao normal
            self.pulse_scale += (1 - self.pulse_scale) * 0.1

        # Aplicar escala ao núcleo
        size = 16 * self.pulse_scale
        self.nucleo.size = (size, size)
        self.nucleo.pos = (self.center_x - size/2, self.center_y + 30 - size/2)

    def atualizar_hora_data(self, dt):
        """Atualiza hora e data"""
        agora = datetime.datetime.now()
        self.hora_label.text = agora.strftime("%H:%M:%S")
        self.data_label.text = agora.strftime("%d/%m/%Y")

    def update_command_count(self, count):
        """Atualiza contador de comandos"""
        self.commands_label.text = f"Cmd: {count}"

    def iniciar_fala(self, duracao_estimada):
        """Inicia animação de fala"""
        self.is_speaking = True
        self.status_label.text = "● FALANDO"
        self.status_label.color = (0, 1, 1, 1)

    def parar_fala(self):
        """Para animação de fala"""
        self.is_speaking = False
        self.status_label.text = "● ONLINE"
        self.status_label.color = (0, 1, 0, 1)

    def animar_entrada(self):
        """Animação de entrada suave"""
        self.opacity = 0
        anim = Animation(opacity=1, duration=0.5)
        anim.start(self)

class JarvisVoiceAssistant:
    def __init__(self, set_text_callback, feedback_callback=None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.set_text_callback = set_text_callback
        self.feedback_callback = feedback_callback
        self.listening_passive = False
        self.energy_threshold = 300
        self.pause_threshold = 0.8

    def calibrar_microfone(self):
        """Calibração mais robusta do microfone"""
        try:
            with self.microphone as source:
                logging.info("Calibrando microfone... Aguarde 3 segundos de silêncio.")
                self.recognizer.adjust_for_ambient_noise(source, duration=3)
                logging.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
        except Exception as e:
            logging.error(f"Erro na calibração: {e}")

    def start(self):
        self.calibrar_microfone()
        self.listening_passive = True
        thread = Thread(target=self._passive_listen_loop, daemon=True)
        thread.start()

    def stop(self):
        self.listening_passive = False

    def _passive_listen_loop(self):
        with self.microphone as source:
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_adjustment_ratio = 1.5
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        logging.info("Escutando palavra-chave (modo passivo)...")

        while self.listening_passive:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                phrase = self.recognizer.recognize_google(audio, language='pt-BR')
                logging.info(f"Ouvi (passivo): {phrase}")
                frase_lower = phrase.lower().strip()
                
                # Palavras-chave mais abrangentes
                keywords = ["jarvis", "javis", "jarvys", "jar", "assistente", "computador"]
                if any(k in frase_lower for k in keywords):
                    logging.info("Palavra-chave detectada!")
                    if self.feedback_callback:
                        Clock.schedule_once(lambda dt: self.feedback_callback("Estou ouvindo..."))
                    self._active_listen()
                    
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                logging.error(f"[Erro passivo] {e}")

    def _active_listen(self):
        try:
            with self.microphone as source:
                logging.info("Escutando comando (ativo)...")
                audio = self.recognizer.listen(source, phrase_time_limit=10)
            command = self.recognizer.recognize_google(audio, language='pt-BR')
            logging.info(f"Comando reconhecido (ativo): {command}")
            if self.set_text_callback:
                self.set_text_callback(command)
        except sr.UnknownValueError:
            logging.warning("Não entendi o que foi dito.")
        except Exception as e:
            logging.error(f"[Erro ativo] {e}")

class JarvisLayout(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=5, padding=5, **kwargs)
        
        # Inicializar logger
        self.logger = logging.getLogger('Jarvis')
        
        # Carregar memória
        self.memoria = self.carregar_memoria()
        self.sites_personalizados = self.memoria.get("sites_personalizados", {})
        self.alarmes = self.memoria.get("alarmes", [])
        self.lembretes = self.memoria.get("lembretes", [])
        self.anotacoes = self.memoria.get("anotacoes", [])
        self.modo_silencioso = self.memoria.get('modo_silencioso', False)
        self.estado_memoria = 'nome' if 'nome' not in self.memoria else 'normal'
        self.falando = False
        self.encerrando = False
        self.estado = 'normal'
        self.repo_url = "https://api.github.com/repos/Daniel11012010/Testando_Jarvis"
        self.ultima_verificacao = None
        self.atualizacao_pendente = False
        self.ultimo_commit_conhecido = self.memoria.get("ultimo_commit_conhecido", None)
        self.command_count = 0

        # Inicializar serviços
        self.audio_manager = AudioManager()
        self.learning_system = LearningSystem()
        self.system_control = SystemControl()
        self.usage_analytics = UsageAnalytics()
        self.ai_services = AIServices()
        self.security_manager = SecurityManager()
        self.theme_manager = ThemeManager()
        
        # Limpar arquivos antigos na inicialização
        self.audio_manager.cleanup_old_files()

        # HUD AVANÇADO
        self.hud = AdvancedHUD()
        self.add_widget(self.hud)

        # Barra superior
        self.toolbar = MDTopAppBar(
            title="Jarvis - Assistente IA",
            md_bg_color=(0.1, 0.1, 0.3, 1),
            elevation=2,
            right_action_items=[
                ["memory", lambda x: self.abrir_editor_memoria()],
                ["cog", lambda x: self.abrir_configuracoes()],
            ]
        )
        self.add_widget(self.toolbar)

        # Área de histórico de mensagens
        self.scrollview = MDScrollView(size_hint=(1, 0.65))
        self.hist = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=8, padding=8)
        self.hist.bind(minimum_height=self.hist.setter('height'))
        self.scrollview.add_widget(self.hist)
        self.add_widget(self.scrollview)

        # Área de input
        self.input_area = RelativeLayout(size_hint=(1, 0.1))
        self.text_input = MDTextField(
            hint_text="Digite seu comando...",
            multiline=False,
            size_hint=(0.78, None),
            height=dp(44),
            pos_hint={'center_y': 0.5, 'x': 0.01}
        )
        self.button = MDRaisedButton(
            text="Enviar",
            size_hint=(0.2, None),
            height=dp(44),
            pos_hint={'center_y': 0.5, 'right': 0.99}
        )
        self.button.bind(on_press=self.executar_comandos)
        self.text_input.bind(on_text_validate=lambda x: self.executar_comandos(None))
        self.input_area.add_widget(self.text_input)
        self.input_area.add_widget(self.button)
        self.add_widget(self.input_area)

        # Inicializar pygame mixer para som
        try:
            pygame.mixer.init()
        except Exception as e:
            self.logger.error(f"Erro ao iniciar mixer: {e}")

        # Agendar verificações periódicas
        Clock.schedule_interval(self.verifica_alarmes, 1)
        Clock.schedule_interval(self.verifica_lembretes, 1)
        Clock.schedule_interval(lambda dt: self.audio_manager.cleanup_old_files(), 1800)

        # Animação de entrada
        Clock.schedule_once(lambda dt: self.hud.animar_entrada(), 0.5)

        # Saudação inicial conforme estado da memória
        if self.estado_memoria == 'nome':
            self.falar("Olá! Qual é o seu nome?")
        else:
            nome = self.memoria.get('apelido', self.memoria.get('nome', 'usuário'))
            cidade = self.memoria.get('cidade', None)
            if cidade:
                self.falar(f"Olá, {nome}! Tudo certo em {cidade}?")
            else:
                self.falar(f"Olá, {nome}! Como posso ajudar?")

        # Inicializar assistente de voz
        self.voice_assistant = JarvisVoiceAssistant(
            set_text_callback=self.definir_input_de_texto,
            feedback_callback=self.falar
        )
        self.voice_assistant.start()
        
        self.logger.info("Jarvis inicializado com sucesso!")

    def carregar_memoria(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Erro ao carregar memória: {e}")
                return {}
        return {}

    def salvar_memoria(self):
        try:
            self.memoria["sites_personalizados"] = self.sites_personalizados
            self.memoria["alarmes"] = self.alarmes
            self.memoria["lembretes"] = self.lembretes
            self.memoria["anotacoes"] = self.anotacoes
            self.memoria["ultimo_commit_conhecido"] = self.ultimo_commit_conhecido
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.memoria, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"Erro ao salvar memória: {e}")

    def definir_input_de_texto(self, texto):
        def preencher_e_executar(dt):
            self.text_input.text = texto
            self.executar_comandos(None)

        Clock.schedule_once(preencher_e_executar, 0.1)

    def adicionar_msg(self, remetente, texto):
        cor = (0.1, 0.5, 0.8, 1) if remetente == "Jarvis" else (0.3, 0.3, 0.3, 1)
        card = MDCard(orientation='vertical', size_hint=(1, None), padding=10, md_bg_color=cor, radius=[12])
        label = MDLabel(
            text=f"[b]{remetente}:[/b] {texto}",
            markup=True,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            halign="left",
            size_hint_y=None
        )
        label.bind(
            width=lambda inst, val: setattr(inst, 'text_size', (val, None)),
            texture_size=lambda inst, val: (
                setattr(inst, "height", val[1]),
                setattr(card, "height", val[1] + 20)
            )
        )
        card.add_widget(label)
        self.hist.add_widget(card)
        Clock.schedule_once(lambda dt: setattr(self.scrollview, 'scroll_y', 0))

    def abrir_editor_memoria(self):
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))
        self.campos_memoria = {}

        for chave, valor in self.memoria.items():
            box = MDBoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=dp(48))
            campo = MDTextField(text=str(valor), hint_text=chave, size_hint_x=0.8)
            botao_excluir = MDFlatButton(text="🗑️", size_hint_x=0.2)

            def remover_chave(btn, k=chave):
                if k in self.memoria:
                    del self.memoria[k]
                    self.dialog_memoria.dismiss()
                    self.falar(f"'{k}' removido.")
                    Clock.schedule_once(lambda dt: self.abrir_editor_memoria(), 0.3)

            botao_excluir.bind(on_release=remover_chave)
            box.add_widget(campo)
            box.add_widget(botao_excluir)
            layout.add_widget(box)
            self.campos_memoria[chave] = campo

        nova_chave = MDTextField(hint_text="Nova chave", size_hint_y=None, height=dp(48))
        novo_valor = MDTextField(hint_text="Novo valor", size_hint_y=None, height=dp(48))
        layout.add_widget(nova_chave)
        layout.add_widget(novo_valor)

        def salvar_edicoes(*_):
            for chave, campo in self.campos_memoria.items():
                self.memoria[chave] = campo.text
            if nova_chave.text and novo_valor.text:
                self.memoria[nova_chave.text] = novo_valor.text
            self.salvar_memoria()
            self.falar("Memória atualizada com sucesso!")
            self.dialog_memoria.dismiss()

        def cancelar_edicao(*_):
            self.dialog_memoria.dismiss()

        self.dialog_memoria = MDDialog(
            title="🧠 Editor de Memória",
            type="custom",
            content_cls=layout,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=cancelar_edicao),
                MDFlatButton(text="Salvar", on_release=salvar_edicoes),
            ]
        )
        self.dialog_memoria.open()

    def abrir_configuracoes(self):
        """Abre diálogo de configurações"""
        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter("height"))
        
        # Botão para ver status do sistema
        btn_status = MDRaisedButton(
            text="📊 Status do Sistema",
            size_hint_y=None,
            height=dp(40)
        )
        btn_status.bind(on_release=lambda x: self.ver_status_sistema())
        layout.add_widget(btn_status)
        
        # Botão para estatísticas de uso
        btn_stats = MDFlatButton(
            text="📈 Estatísticas de Uso",
            size_hint_y=None,
            height=dp(40)
        )
        btn_stats.bind(on_release=lambda x: self.ver_estatisticas())
        layout.add_widget(btn_stats)

        self.dialog_config = MDDialog(
            title="⚙️ Configurações",
            type="custom",
            content_cls=layout,
            buttons=[
                MDFlatButton(text="Fechar", on_release=lambda x: self.dialog_config.dismiss()),
            ]
        )
        self.dialog_config.open()

    def ver_status_sistema(self):
        """Mostra status do sistema"""
        info = self.system_control.get_system_info()
        self.falar(f"Status do sistema: {info}")
        self.dialog_config.dismiss()

    def ver_estatisticas(self):
        """Mostra estatísticas de uso"""
        stats = self.usage_analytics.get_usage_stats()
        self.falar(stats)
        self.dialog_config.dismiss()

    def falar(self, texto):
        texto = self.substituir_variaveis(texto)
        self.adicionar_msg("Jarvis", texto)

        duracao_estimada = min(max(len(texto.split()) * 0.5, 1.5), 10)
        self.hud.iniciar_fala(duracao_estimada)

        if self.modo_silencioso:
            self.logger.info("[Modo Silencioso] Jarvis respondeu apenas com texto.")
            self.hud.parar_fala()
            return

        def play_audio():
            self.falando = True
            filepath = None
            
            try:
                # Gerar arquivo de áudio
                filepath = self.audio_manager.generate_audio_file(texto)
                
                if not filepath or not os.path.exists(filepath):
                    self.falando = False
                    self.hud.parar_fala()
                    return

                # Carregar e reproduzir
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()

                # Aguardar término da reprodução
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
            except Exception as e:
                self.logger.error(f"Erro na reprodução de áudio: {e}")
                
            finally:
                # SEMPRE tentar limpar o arquivo
                if filepath:
                    self.audio_manager.immediate_cleanup(filepath)
                    
                self.falando = False
                self.hud.parar_fala()

        # Iniciar reprodução em thread separada
        audio_thread = threading.Thread(target=play_audio, daemon=True)
        audio_thread.start()

    def executar_comandos(self, inst):
        try:
            comando = self.text_input.text.strip()
            self.text_input.text = ""
            if not comando:
                return

            self.adicionar_msg("Você", comando)
            self.usage_analytics.log_command(comando)
            self.command_count += 1
            self.hud.update_command_count(self.command_count)

            # Verificar se é um comando sensível
            if self.security_manager.requires_confirmation(comando):
                def confirmation_callback(confirmed):
                    if confirmed:
                        self.processar_comando(comando)
                    else:
                        self.falar("Ação cancelada pelo usuário.")
                
                self.security_manager.confirm_action(comando, confirmation_callback)
                return

            comandos = [parte.strip() for parte in re.split(r' e | então | depois ', comando)]

            for i, cmd in enumerate(comandos):
                Clock.schedule_once(lambda dt, c=cmd: self.processar_comando(c), 0.2 * (i + 1))
                
        except Exception as e:
            self.logger.error(f"Erro em executar_comandos: {e}")
            self.falar("Ocorreu um erro ao processar o comando.")

    def processar_comando(self, comando):
        comando_lower = comando.lower()
        
        # Registrar comando para analytics
        self.usage_analytics.log_command(comando)

        # Verificar respostas aprendidas
        resposta_aprendida = self.learning_system.get_learned_response(comando)
        if resposta_aprendida:
            self.falar(resposta_aprendida)
            return

        # Setup inicial: coletar nome, apelido, cidade
        if self.estado_memoria == 'nome':
            self.memoria['nome'] = comando
            self.estado_memoria = 'apelido'
            self.salvar_memoria()
            self.falar(f"Prazer, {comando}! Como gostaria que eu te chamasse?")
            return

        if self.estado_memoria == 'apelido':
            self.memoria['apelido'] = comando
            self.estado_memoria = 'cidade'
            self.salvar_memoria()
            self.falar(f"Certo! Qual cidade você mora?")
            return

        if self.estado_memoria == 'cidade':
            self.memoria['cidade'] = comando
            self.estado_memoria = 'normal'
            self.salvar_memoria()
            self.falar(f"Perfeito! Agora posso te ajudar melhor.")
            return

        # Abrir sites desconhecidos
        if self.estado_memoria == 'adicionar_site':
            url = comando.strip()
            if not url.startswith("http"):
                url = "https://" + url

            self.sites_personalizados[self.site_a_adicionar] = url
            self.salvar_memoria()
            self.estado_memoria = 'normal'
            self.site_a_adicionar = None
            self.falar(f"Site adicionado! Da próxima vez, abrirei {url}.")
            return

        # COMANDOS DE APRENDIZADO
        if comando_lower.startswith("aprenda que ") and " é " in comando_lower:
            try:
                partes = comando_lower.replace("aprenda que ", "").split(" é ")
                if len(partes) == 2:
                    trigger, response = partes
                    resultado = self.learning_system.learn_response(trigger.strip(), response.strip())
                    self.falar(resultado)
                else:
                    self.falar("Formato: 'aprenda que [pergunta] é [resposta]'")
            except Exception as e:
                self.falar("Erro ao aprender o padrão")
            return

        if comando_lower.startswith("esqueça ") or comando_lower.startswith("apague "):
            trigger = comando_lower.replace("esqueça", "").replace("apague", "").strip()
            resultado = self.learning_system.forget_pattern(trigger)
            self.falar(resultado)
            return

        if "listar padrões" in comando_lower or "padrões aprendidos" in comando_lower:
            resultado = self.learning_system.list_patterns()
            self.falar(resultado)
            return

        # COMANDOS DE SISTEMA
        if any(palavra in comando_lower for palavra in ["sistema", "estatísticas do sistema", "info sistema"]):
            info = self.system_control.get_system_info()
            self.falar(info)
            return

        if "captura de tela" in comando_lower or "print" in comando_lower or "screenshot" in comando_lower:
            resultado = self.system_control.take_screenshot()
            self.falar(resultado)
            return

        # COMANDOS PARA ABRIR APLICATIVOS
        if comando_lower.startswith("abrir aplicativo ") or comando_lower.startswith("executar "):
            app = comando_lower.replace("abrir aplicativo", "").replace("executar", "").strip()
            if app:
                resultado = self.system_control.open_application(app)
                self.falar(resultado)
            else:
                self.falar("Qual aplicativo você quer abrir?")
            return

        if "lista de aplicativos" in comando_lower or "aplicativos disponíveis" in comando_lower:
            resultado = self.system_control.list_applications()
            self.falar(resultado)
            return

        # COMANDOS DE ANÁLISE
        if "estatísticas de uso" in comando_lower or "estatísticas jarvis" in comando_lower:
            stats = self.usage_analytics.get_usage_stats()
            self.falar(stats)
            return

        # COMANDOS DE TEMA
        if comando_lower.startswith("mudar tema para "):
            tema = comando_lower.replace("mudar tema para ", "").strip()
            resultado = self.theme_manager.change_theme(tema, MDApp.get_running_app())
            self.falar(resultado)
            return

        if "listar temas" in comando_lower or "temas disponíveis" in comando_lower:
            resultado = self.theme_manager.list_themes()
            self.falar(resultado)
            return

        # RESPOSTAS IA
        if any(palavra in comando_lower for palavra in ["como você está", "quem é você", "piada", "conselho"]):
            resposta = self.ai_services.get_ai_response(comando)
            self.falar(resposta)
            return

        # COMANDOS BÁSICOS
        if "horas" in comando_lower:
            agora = datetime.datetime.now().strftime('%H:%M')
            self.falar(f"Agora são {agora}")
            return

        if "definir alarme" in comando_lower:
            hora = self.extrair_hora(comando_lower)
            recorrente = "diário" in comando_lower
            if hora:
                for al in self.alarmes:
                    if al['hora'] == hora and al['recorrente'] == recorrente:
                        self.falar("Esse alarme já está definido.")
                        return
                msg = re.findall(r'mensagem (.+)', comando_lower)
                self.alarmes.append({
                    'hora': hora,
                    'msg': msg[0] if msg else "",
                    'recorrente': recorrente
                })
                self.salvar_memoria()
                self.falar(f"Alarme definido para {hora}{' (recorrente)' if recorrente else ''}.")
            else:
                self.falar("Use o formato: definir alarme para HH:MM, opcional 'diário' para recorrência.")
            return

        if "remover alarme" in comando_lower or "cancelar alarme" in comando_lower:
            hora = self.extrair_hora(comando_lower)
            if hora:
                antes = len(self.alarmes)
                self.alarmes = [a for a in self.alarmes if a['hora'] != hora]
                if len(self.alarmes) < antes:
                    self.salvar_memoria()
                    self.falar(f"Alarme das {hora} removido.")
                else:
                    self.falar("Alarme não encontrado.")
            else:
                self.falar("Informe o horário do alarme para remover.")
            return

        if "listar alarmes" in comando_lower or "ver alarmes" in comando_lower:
            if self.alarmes:
                lista = ', '.join([f"{a['hora']}{' (recorrente)' if a['recorrente'] else ''}" for a in self.alarmes])
                self.falar(f"Alarmes ativos: {lista}")
            else:
                self.falar("Você não tem alarmes definidos.")
            return

        if "definir lembrete" in comando_lower:
            texto = comando_lower.replace("definir lembrete", "").strip()
            if texto:
                hora = self.extrair_hora(comando_lower)
                self.lembretes.append({'texto': texto, 'hora': hora})
                self.salvar_memoria()
                self.falar("Lembrete definido.")
            else:
                self.falar("Diga o que deseja lembrar.")
            return

        if "listar lembretes" in comando_lower:
            if self.lembretes:
                msgs = [f"{l['texto']} às {l['hora']}" if l['hora'] else l['texto'] for l in self.lembretes]
                self.falar("Seus lembretes: " + "; ".join(msgs))
            else:
                self.falar("Você não tem lembretes.")
            return

        if comando_lower.startswith("anotar "):
            texto = comando[7:].strip()
            if texto:
                self.anotacoes.append({'texto': texto, 'data': datetime.datetime.now().strftime("%d/%m/%Y %H:%M")})
                self.salvar_memoria()
                self.falar("Anotação salva.")
            else:
                self.falar("O que você quer anotar?")
            return

        if "listar anotações" in comando_lower:
            if self.anotacoes:
                notas = [f"{a['data']}: {a['texto']}" for a in self.anotacoes]
                self.falar("Suas anotações: " + " | ".join(notas))
            else:
                self.falar("Você não tem anotações.")
            return

        if any(p in comando_lower for p in ['wikipedia', 'quem é', 'o que é']):
            try:
                wikipedia.set_lang("pt")
                termo = comando_lower
                for palavra in ['wikipedia', 'quem é', 'o que é']:
                    termo = termo.replace(palavra, '')
                termo = termo.strip()
                if not termo:
                    self.falar("Sobre o que você quer saber na Wikipedia?")
                    return
                resumo = wikipedia.summary(termo, sentences=2)
                self.falar(resumo)
            except Exception as e:
                self.falar("Erro ao buscar na Wikipedia.")
                self.logger.error(f"Erro Wikipedia: {e}")
            return

        if comando_lower.startswith("pesquisar "):
            termo = comando_lower.replace("pesquisar", "").strip()
            if termo:
                self.pesquisar_google(termo)
            else:
                self.falar("O que você quer pesquisar?")
            return

        # COMANDOS PARA ABRIR SITES
        if comando_lower.startswith("abrir site ") or (comando_lower.startswith("abrir ") and not "aplicativo" in comando_lower):
            nome = comando_lower.replace("abrir site", "").replace("abrir", "").strip()
            if nome:
                self.abrir_site_por_nome(nome)
            else:
                self.falar("Qual site você quer abrir?")
            return

        if comando_lower.startswith("tocar "):
            termo = comando_lower.replace("tocar", "").strip()
            if termo:
                self.pesquisar_youtube(termo)
            else:
                self.falar("O que você quer ouvir no YouTube?")
            return

        if comando_lower.startswith("traduzir "):
            texto = comando_lower.replace("traduzir", "").strip()
            if texto:
                self.traduzir(texto)
            else:
                self.falar("O que você quer traduzir?")
            return

        if comando_lower in ['sair', 'desligar', 'tchau', 'encerrar']:
            self.encerrar_jarvis()
            return

        if comando_lower.startswith("fale ") or comando_lower.startswith("diga "):
            frase = re.sub(r'^(fale|diga)\s*', '', comando_lower).strip()
            if frase:
                self.falar(frase)
            else:
                self.falar("O que você quer que eu diga?")
            return

        if comando_lower in ["ativar modo silencioso", "modo silencioso"]:
            self.modo_silencioso = True
            self.memoria['modo_silencioso'] = True
            self.salvar_memoria()
            self.falar("Modo silencioso ativado. Agora só responderei por texto.")
            return

        if comando_lower in ["desativar modo silencioso", "desligar modo silencioso", "pode falar"]:
            self.modo_silencioso = False
            self.memoria['modo_silencioso'] = False
            self.salvar_memoria()
            self.falar("Modo silencioso desativado. Voltarei a falar normalmente.")
            return

        if comando_lower in ["ajuda", "menu", "comandos", "o que você faz"]:
            ajuda = (
                "🤖 **JARVIS - SISTEMA COMPLETO**\\n\\n"
                "💻 **CONTROLE DO SISTEMA**\\n"
                "• 'sistema' - Informações de CPU, memória, disco\\n"
                "• 'captura de tela' - Tira print da tela\\n"
                "• 'abrir aplicativo calculadora' - Abre aplicativos\\n"
                "• 'lista de aplicativos' - Mostra apps disponíveis\\n\\n"
                "🎨 **PERSONALIZAÇÃO**\\n"
                "• 'mudar tema para escuro' - Altera aparência\\n"
                "• 'listar temas' - Mostra temas disponíveis\\n\\n"
                "⏰ **GERENCIAMENTO DE TEMPO**\\n"
                "• 'horas' - Mostra a hora atual\\n"
                "• 'definir alarme para 07:30' - Cria alarme\\n"
                "• 'definir alarme para 07:30 diário' - Alarme recorrente\\n\\n"
                "🌍 **PESQUISAS E SITES**\\n"
                "• 'pesquisar receita de bolo' - Busca no Google\\n"
                "• 'quem é Albert Einstein' - Wikipedia\\n"
                "• 'abrir site YouTube' - Abre site\\n\\n"
                "📚 **APRENDIZADO**\\n"
                "• 'aprenda que bom dia é olá' - Ensina respostas\\n"
                "• 'listar padrões' - Mostra o que aprendeu\\n\\n"
                "⚙️ **CONFIGURAÇÕES**\\n"
                "• Clique na engrenagem ⚙️ para configurações\\n"
                "• Editor de memória com ícone de memória 🧠\\n"
            )
            self.falar(ajuda)
            return

        # Se não reconheceu nenhum comando, usar IA para resposta criativa
        resposta = self.ai_services.get_ai_response(comando)
        self.falar(resposta)

    # Métodos auxiliares
    def substituir_variaveis(self, texto):
        agora_dt = datetime.datetime.now()
        nome = self.memoria.get("apelido") or self.memoria.get("nome") or "usuário"
        cidade = self.memoria.get("cidade") or "sua cidade"

        def dia_semana_pt(dia_ingles):
            mapping = {
                "Monday": "segunda-feira",
                "Tuesday": "terça-feira",
                "Wednesday": "quarta-feira",
                "Thursday": "quinta-feira",
                "Friday": "sexta-feira",
                "Saturday": "sábado",
                "Sunday": "domingo",
            }
            return mapping.get(dia_ingles, dia_ingles)

        base_vars = {
            "nome": nome,
            "cidade": cidade,
            "ano": agora_dt.year,
            "mês": MESES_PT[agora_dt.month - 1],
            "mes": MESES_PT[agora_dt.month - 1],
            "dia": agora_dt.day,
            "dia_semana": dia_semana_pt(agora_dt.strftime("%A")),
            "agora": agora_dt.strftime("%H:%M"),
        }

        padrao = re.compile(r"\{(\w+)([+\-]\d{1,2}(:\d{2})?)?\}")

        def aplicar_operacao(var, op):
            if op is None:
                return var

            sinal = op[0]
            valor = op[1:]

            if isinstance(var, int):
                try:
                    delta = int(valor)
                except:
                    return var
                return var + delta if sinal == "+" else var - delta

            if isinstance(var, str):
                if var.count(":") == 1 and re.match(r"\d{2}:\d{2}", var):
                    try:
                        horas, minutos = map(int, var.split(":"))
                        dt = datetime.datetime(2000, 1, 1, horas, minutos)
                        if ":" in valor:
                            minutos_delta = int(valor.split(":")[0]) * 60 + int(valor.split(":")[1])
                        else:
                            minutos_delta = int(valor)
                        dt2 = dt + datetime.timedelta(
                            minutes=minutos_delta) if sinal == "+" else dt - datetime.timedelta(minutes=minutos_delta)
                        return dt2.strftime("%H:%M")
                    except:
                        return var
                lista = None
                if var in MESES_PT:
                    lista = MESES_PT
                elif var in DIAS_PT:
                    lista = DIAS_PT

                if lista:
                    try:
                        idx = lista.index(var)
                        delta = int(valor)
                        idx2 = (idx + delta) % len(lista) if sinal == "+" else (idx - delta) % len(lista)
                        return lista[idx2]
                    except:
                        return var
                return var

            return var

        def substituir(match):
            var = match.group(1)
            op = match.group(2)
            val = base_vars.get(var)
            if val is None:
                return match.group(0)

            val2 = aplicar_operacao(val, op)
            return str(val2)

        try:
            return padrao.sub(substituir, texto)
        except Exception as e:
            self.logger.error(f"Erro na substituição de variáveis: {e}")
            return texto

    def extrair_hora(self, texto):
        match = re.search(r'([01]?\d|2[0-3]):([0-5]\d)', texto)
        if match:
            return match.group(0)
        return None

    def traduzir(self, texto):
        try:
            texto = self.substituir_variaveis(texto)
            translator = GoogleTranslator(source='auto', target='en')
            traducao = translator.translate(texto)
            self.falar(f"Tradução: {traducao}")
        except Exception as e:
            self.logger.error(f"Erro na tradução: {e}")
            self.falar("Não consegui traduzir o texto.")

    def abrir_site_por_nome(self, nome):
        nome = nome.lower()

        sites_padrao = {
            'youtube': 'https://www.youtube.com',
            'gmail': 'https://mail.google.com',
            'notícias': 'https://www.google.com/news',
            'google drive': 'https://drive.google.com',
            'whatsapp web': 'https://web.whatsapp.com',
            'google': 'https://www.google.com',
            'facebook': 'https://www.facebook.com',
            'instagram': 'https://www.instagram.com',
            'twitter': 'https://www.twitter.com',
            'linkedin': 'https://www.linkedin.com',
            'github': 'https://www.github.com',
            'netflix': 'https://www.netflix.com',
            'spotify': 'https://www.spotify.com',
        }

        url = sites_padrao.get(nome) or self.sites_personalizados.get(nome)

        if url:
            self.falar(f"Abrindo {nome}...")
            while self.falando:
                time.sleep(0.1)
            webbrowser.open(url)
        else:
            self.falar(f"Eu não conheço o site {nome}. Qual é o link completo?")
            self.estado_memoria = 'adicionar_site'
            self.site_a_adicionar = nome

    def pesquisar_youtube(self, termo):
        try:
            termo = termo.strip()
            if not termo:
                self.falar("O que você quer ouvir no YouTube?")
                return

            self.falar(f"Procurando {termo} no YouTube...")

            while self.falando:
                time.sleep(0.1)

            video_url = self.find_youtube_video(termo)

            if video_url:
                webbrowser.open(video_url)
            else:
                search_url = f"https://www.youtube.com/results?search_query={termo.replace(' ', '+')}"
                webbrowser.open(search_url)

        except Exception as e:
            self.logger.error(f"Erro ao pesquisar no YouTube: {e}")
            self.falar("Não consegui acessar o YouTube no momento.")

    def find_youtube_video(self, search_term):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_term)}&sp=EgIQAQ%253D%253D"

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            video_ids = re.findall(r'watch\?v=(\S{11})', response.text)
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"

        except Exception as e:
            self.logger.error(f"Erro ao buscar vídeo: {e}")

        return None

    def pesquisar_google(self, termo):
        termo = termo.strip()
        if not termo:
            self.falar("O que você quer pesquisar?")
            return

        self.falar(f"Pesquisando {termo} no Google...")

        while self.falando:
            time.sleep(0.1)

        if re.match(r'^(https?://)?[\w\-]+\.[a-z]{2,}(/.*)?$', termo):
            if not termo.startswith("http"):
                termo = "https://" + termo
            webbrowser.open(termo)
        else:
            query = termo.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={query}")

    def verifica_alarmes(self, dt):
        agora = datetime.datetime.now().strftime('%H:%M')
        for alarme in self.alarmes:
            if alarme['hora'] == agora:
                self.falar(f"Alarme: {alarme['msg'] or 'Hora marcada!'}")
                if not alarme['recorrente']:
                    self.alarmes.remove(alarme)
                    self.salvar_memoria()

    def verifica_lembretes(self, dt):
        agora = datetime.datetime.now().strftime('%H:%M')
        for lembrete in list(self.lembretes):
            if lembrete['hora'] == agora and lembrete['hora'] is not None:
                self.falar(f"Lembrete: {lembrete['texto']}")
                self.lembretes.remove(lembrete)
                self.salvar_memoria()

    def encerrar_jarvis(self):
        if self.encerrando:
            return

        self.encerrando = True
        self.falar("Desligando o programa... Até logo!")

        def fechar_apos_falar():
            # Parar assistente de voz
            if hasattr(self, 'voice_assistant'):
                self.voice_assistant.stop()
                
            # Aguardar término de fala atual
            while self.falando:
                time.sleep(0.1)
                
            # Limpar TODOS os arquivos de áudio
            if hasattr(self, 'audio_manager'):
                self.audio_manager.cleanup_all()
                
            # Parar mixer do pygame
            try:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
            except:
                pass
                
            # Salvar configurações
            self.salvar_memoria()
            
            # Animação de saída
            self.hud.animar_saida()
            Clock.schedule_once(lambda dt: MDApp.get_running_app().stop(), 0.8)

        threading.Thread(target=fechar_apos_falar, daemon=True).start()

class JarvisApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "LightBlue"
        return JarvisLayout()

if __name__ == '__main__':
    JarvisApp().run()

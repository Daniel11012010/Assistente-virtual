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
from urllib.parse import quote_plus
import requests
import speech_recognition as sr
from threading import Thread
from kivy.clock import Clock


MEMORY_FILE = "jarvis_memoria.json"

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

DIAS_PT = [
    "segunda-feira", "terça-feira", "quarta-feira",
    "quinta-feira", "sexta-feira", "sábado", "domingo"
]

class JarvisVoiceAssistant:
    def __init__(self, set_text_callback, feedback_callback=None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.set_text_callback = set_text_callback  # Atualiza o campo de texto
        self.feedback_callback = feedback_callback  # Fala algo como “estou ouvindo”
        self.listening_passive = False

    def start(self):
        self.listening_passive = True
        thread = Thread(target=self._passive_listen_loop, daemon=True)
        thread.start()

    def stop(self):
        self.listening_passive = False

    def _passive_listen_loop(self):
        with self.microphone as source:
            self.recognizer.energy_threshold = 300  # ajuste manual, teste e ajuste
            self.recognizer.dynamic_energy_adjustment_ratio = 0.5
            self.recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Escutando palavra-chave (modo passivo)...")

        while self.listening_passive:
            try:
                with self.microphone as source:
                    print("Escutando (passivo)...")
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                phrase = self.recognizer.recognize_google(audio, language='pt-BR')
                print(f"Ouvi (passivo): {phrase}")
                frase_lower = phrase.lower().strip()
                if any(k in frase_lower for k in ["jarvis", "javis", "jarvys"]):
                    print("Palavra-chave 'Jarvis' detectada!")
                    if self.feedback_callback:
                        Clock.schedule_once(lambda dt: self.feedback_callback("Estou ouvindo..."))
                    self._active_listen()
            except sr.WaitTimeoutError:
                # Timeout esperando fala, ignora e continua o loop
                pass
            except sr.UnknownValueError:
                pass
            except Exception as e:
                print(f"[Erro passivo] {e}")

    def _active_listen(self):
        with self.microphone as source:
            print("Escutando comando (ativo)...")
            audio = self.recognizer.listen(source, phrase_time_limit=7)
        try:
            command = self.recognizer.recognize_google(audio, language='pt-BR')
            print(f"Comando reconhecido (ativo): {command}")
            if self.set_text_callback:
                self.set_text_callback(command)
        except sr.UnknownValueError:
            print("Não entendi o que foi dito.")
        except Exception as e:
            print(f"[Erro ativo] {e}")


# Seu programa principal segue rodando, a escuta passiva fica rodando em thread separada

class JarvisHUD(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rotation_angle = 0
        self.pulse_scale = 1.0
        self.pulse_growing = True
        self.is_speaking = False
        self.size_hint = (1, 0.4)
        self.pos_hint = {'top': 1}
        self.animation_variation = 0
        self.speech_duration = 0

        with self.canvas.before:
            Color(0.03, 0.03, 0.07, 0.95)
            self.bg = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_bg, pos=self.update_bg)

        # Elementos do HUD
        self.draw_circulos_concentricos()
        self.draw_nucleo_pulsante()
        self.create_orbitals()

        # Labels de informação (movidos para canto superior esquerdo)
        self.hora_label = Label(
            text="",
            font_size=16,
            color=(0, 1, 1, 1),
            size_hint=(None, None),
            size=(120, 30),
            pos_hint={'x': 0.02, 'top': 0.95}
        )
        self.add_widget(self.hora_label)

        self.data_label = Label(
            text="",
            font_size=14,
            color=(0, 1, 1, 0.7),
            size_hint=(None, None),
            size=(140, 25),
            pos_hint={'x': 0.02, 'top': 0.9}
        )
        self.add_widget(self.data_label)

        # Inicia animações
        Clock.schedule_interval(self.update_animation, 1 / 60)
        Clock.schedule_interval(self.atualizar_hora_data, 1)

    def update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def draw_circulos_concentricos(self):
        with self.canvas:
            Color(0, 1, 1, 0.3)
            self.circulo1 = Line(circle=(self.center_x, self.center_y + 100, 100), width=1.3)
            Color(0, 1, 1, 0.65)
            self.circulo2 = Line(circle=(self.center_x, self.center_y + 100, 60), width=1.3)

    def draw_nucleo_pulsante(self):
        with self.canvas:
            Color(0, 1, 1, 1)
            self.nucleo = Ellipse(pos=(self.center_x - 15, self.center_y + 85), size=(30, 30))

    def create_orbitals(self):
        self.orbitals = []
        self.num_orbitals = 6
        with self.canvas:
            Color(0, 1, 1, 1)
            for i in range(self.num_orbitals):
                angle = math.radians(i * (360 / self.num_orbitals))
                orb = Ellipse(pos=(self.center_x + math.cos(angle) * 100 - 5,
                                   self.center_y + 100 + math.sin(angle) * 100 - 5),
                              size=(10, 10))
                self.orbitals.append(orb)

    def update_animation(self, dt):
        self.rotation_angle += 60 * dt
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

        # Variação mais orgânica no pulso
        if self.is_speaking:
            self.animation_variation = (self.animation_variation + dt * 2) % (2 * math.pi)
            pulse_variation = math.sin(self.animation_variation * 3) * 0.1
            pulse_speed = 2.5 + math.sin(self.animation_variation * 2)

            if self.pulse_growing:
                self.pulse_scale += pulse_speed * dt
                if self.pulse_scale >= 1.3 + pulse_variation:
                    self.pulse_growing = False
            else:
                self.pulse_scale -= pulse_speed * dt
                if self.pulse_scale <= 0.9 + pulse_variation:
                    self.pulse_growing = True
        else:
            self.pulse_scale += (1 - self.pulse_scale) * 0.1

        size = 30 * self.pulse_scale
        self.nucleo.size = (size, size)
        self.nucleo.pos = (self.center_x - size / 2, self.center_y + 100 - size / 2)

        self.circulo1.circle = (self.center_x, self.center_y + 100, 100)
        self.circulo2.circle = (self.center_x, self.center_y + 100, 60)

        for i, orb in enumerate(self.orbitals):
            angle = math.radians(i * (360 / self.num_orbitals) + self.rotation_angle)
            orb.pos = (self.center_x + math.cos(angle) * 100 - 5,
                       self.center_y + 100 + math.sin(angle) * 100 - 5)

    def atualizar_hora_data(self, dt):
        agora = datetime.datetime.now()
        self.hora_label.text = agora.strftime("%H:%M:%S")
        self.data_label.text = agora.strftime("%d/%m/%Y")

    def iniciar_fala(self, duracao_estimada):
        self.is_speaking = True
        self.speech_duration = duracao_estimada
        self.animation_variation = 0

    def parar_fala(self):
        self.is_speaking = False

    def animar_entrada(self):
        self.opacity = 0
        self.scale = 0.1
        anim = Animation(opacity=1, scale=1, duration=0.8, t='out_back')
        anim.start(self)

    def animar_saida(self):
        anim = Animation(opacity=0, scale=0.1, duration=0.8, t='in_back')
        anim.bind(on_complete=lambda *x: setattr(self.parent, 'opacity', 0))
        anim.start(self)


class JarvisLayout(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=10, padding=10, **kwargs)

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

        # HUD visual no topo
        self.hud = JarvisHUD()
        self.add_widget(self.hud)

        # Barra superior com botão de edição de memória
        self.toolbar = MDTopAppBar(
            title="Jarvis - Assistente IA",
            md_bg_color=(0.2, 0.2, 0.6, 1),
            elevation=4,
            right_action_items=[["pencil", lambda x: self.abrir_editor_memoria()]]
        )
        self.add_widget(self.toolbar)

        # Área de histórico de mensagens (scroll)
        self.scrollview = MDScrollView(size_hint=(1, 0.5))
        self.hist = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=5, padding=5)
        self.hist.bind(minimum_height=self.hist.setter('height'))
        self.scrollview.add_widget(self.hist)
        self.add_widget(self.scrollview)

        # Área de input com texto e botão enviar
        self.input_area = RelativeLayout(size_hint=(1, 0.1))
        self.text_input = MDTextField(
            hint_text="Digite seu comando...",
            multiline=False,
            size_hint=(0.75, None),
            height=dp(48),
            pos_hint={'center_y': 0.5, 'x': 0.02}
        )
        self.button = MDRaisedButton(
            text="Enviar",
            size_hint=(0.2, None),
            height=dp(48),
            pos_hint={'center_y': 0.5, 'right': 0.98}
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
            print("Erro ao iniciar mixer:", e)

        # Agendar verificações periódicas de alarmes e lembretes
        Clock.schedule_interval(self.verifica_alarmes, 1)
        Clock.schedule_interval(self.verifica_lembretes, 1)

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

        self.voice_assistant = JarvisVoiceAssistant(
            set_text_callback=self.definir_input_de_texto,
            feedback_callback=self.falar
        )
        self.voice_assistant.start()

    def ativar_chat_por_voz(self):
        self.falar("Estou ouvindo...")

    def transcrever_no_input(self, texto):
        if texto:
            self.text_input.text = texto
            Clock.schedule_once(lambda dt: self.executar_comandos(None), 0.5)
        else:
            self.falar("Desculpe, não entendi.")

    def carregar_memoria(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def definir_input_de_texto(self, texto):
        def preencher_e_executar(dt):
            self.text_input.text = texto
            self.executar_comandos(None)

        Clock.schedule_once(preencher_e_executar, 0.1)


    def salvar_memoria(self):
        self.memoria["sites_personalizados"] = self.sites_personalizados
        self.memoria["alarmes"] = self.alarmes
        self.memoria["lembretes"] = self.lembretes
        self.memoria["anotacoes"] = self.anotacoes
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.memoria, f, ensure_ascii=False, indent=4)

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

    def falar(self, texto):
        texto = self.substituir_variaveis(texto)
        self.adicionar_msg("Jarvis", texto)

        # Estima a duração da fala (1.5 segundos por "linha" de texto)
        duracao_estimada = min(max(len(texto.split()) * 0.5, 1.5), 10)
        self.hud.iniciar_fala(duracao_estimada)

        if self.modo_silencioso:
            print("[Modo Silencioso] Jarvis respondeu apenas com texto.")
            self.hud.parar_fala()
            return

        def play_audio():
            self.falando = True
            try:
                tts = gTTS(text=texto, lang='pt-br')
                filename = f"resposta_{uuid.uuid4()}.mp3"
                tts.save(filename)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                os.remove(filename)
            except Exception as e:
                print("Erro ao reproduzir áudio:", e)

            self.falando = False
            self.hud.parar_fala()

        threading.Thread(target=play_audio, daemon=True).start()

    def abrir_site_por_nome(self, nome):
        nome = nome.lower()

        sites_padrao = {
            'youtube': 'https://www.youtube.com',
            'gmail': 'https://mail.google.com',
            'notícias': 'https://www.google.com/news',
            'google drive': 'https://drive.google.com',
            'whatsapp web': 'https://web.whatsapp.com'
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
            self.site_a_adicionar = nome  # salva para usar depois

    def pesquisar_youtube(self, termo):
        try:
            termo = termo.strip()
            if not termo:
                self.falar("O que você quer ouvir no YouTube?")
                return

            self.falar(f"Procurando {termo} no YouTube...")

            # Espera a fala terminar antes de abrir o navegador
            while self.falando:
                time.sleep(0.1)

            video_url = self.find_youtube_video(termo)

            if video_url:
                webbrowser.open(video_url)
            else:
                search_url = f"https://www.youtube.com/results?search_query={termo.replace(' ', '+')}"
                webbrowser.open(search_url)

        except Exception as e:
            print("Erro ao pesquisar no YouTube:", e)
            self.falar("Não consegui acessar o YouTube no momento.")

    def find_youtube_video(self, search_term):
        """Método melhorado para encontrar vídeos no YouTube sem API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
            }

            search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_term)}&sp=EgIQAQ%253D%253D"

            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Extrai o primeiro vídeo da página de resultados
            video_ids = re.findall(r'watch\?v=(\S{11})', response.text)
            if video_ids:
                return f"https://www.youtube.com/watch?v={video_ids[0]}"

        except Exception as e:
            print("Erro ao buscar vídeo:", e)

        return None

    def pesquisar_google(self, termo):
        termo = termo.strip()
        if not termo:
            self.falar("O que você quer pesquisar?")
            return

        self.falar(f"Pesquisando {termo} no Google...")

        # Espera a fala terminar antes de abrir o navegador
        while self.falando:
            time.sleep(0.1)

        if re.match(r'^(https?://)?[\w\-]+\.[a-z]{2,}(/.*)?$', termo):
            if not termo.startswith("http"):
                termo = "https://" + termo
            webbrowser.open(termo)
        else:
            query = termo.replace(" ", "+")
            webbrowser.open(f"https://www.google.com/search?q={query}")

    def encerrar_jarvis(self):
        if self.encerrando:
            return

        self.encerrando = True
        self.falar("Desligando o programa... Até logo!")

        def fechar_apos_falar():
            while self.falando:
                time.sleep(0.1)
            self.hud.animar_saida()
            Clock.schedule_once(lambda dt: MDApp.get_running_app().stop(), 0.8)

        threading.Thread(target=fechar_apos_falar, daemon=True).start()

    def executar_comandos(self, inst):
        comando = self.text_input.text.strip()
        self.text_input.text = ""
        if not comando:
            return

        self.adicionar_msg("Você", comando)

        comandos = [parte.strip() for parte in re.split(r' e | então | depois ', comando)]

        for cmd in comandos:
            Clock.schedule_once(lambda dt, c=cmd: self.processar_comando(c), 0.2)

    def processar_comando(self, comando):
        comando_lower = comando.lower()

#Abrir sites desconhecidos
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

        # Comandos gerais
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
                print("Erro Wikipedia:", e)
            return

        if comando_lower.startswith("pesquisar "):
            termo = comando_lower.replace("pesquisar", "").strip()
            if termo:
                self.pesquisar_google(termo)
            else:
                self.falar("O que você quer pesquisar?")
            return

        if comando_lower.startswith("abrir "):
            nome = comando_lower.replace("abrir", "").strip()
            if nome:
                self.abrir_site_por_nome(nome)
            else:
                self.falar("Qual aplicativo ou site você quer abrir?")
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

        if comando_lower in ['sair', 'desligar', 'tchau']:
            self.encerrar_jarvis()
            return

        if comando_lower.startswith("fale ") or comando_lower.startswith("diga "):
            frase = re.sub(r'^(fale|diga)\s*', '', comando_lower).strip()
            if frase:
                self.falar(frase)
            else:
                self.falar("O que você quer que eu diga?")
            return

        comando_lower = comando.lower().strip()

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

        if comando_lower in ["ajuda", "menu"]:
            ajuda = (
                "[b]📘 Ajuda do Jarvis – Assistente Inteligente[/b]\n\n"
                "Bem-vindo ao Jarvis! Aqui estão os comandos e funcionalidades que você pode usar para aproveitar ao máximo seu assistente.\n\n"

                "[b]🕒 Horário e Data[/b]\n"
                "• 'horas' : mostra a hora atual\n"
                "• Use variáveis como {[b]nome[/b]}, {[b]cidade[/b]}, {[b]dia_semana[/b]} para respostas personalizadas\n\n"

                "[b]🔔 Alarmes[/b]\n"
                "• 'definir alarme para HH:MM' : cria um alarme\n"
                "• 'definir alarme para HH:MM diário' : cria alarme recorrente\n"
                "• 'remover alarme HH:MM' : apaga alarme\n"
                "• 'listar alarmes' : mostra alarmes ativos\n\n"

                "[b]📝 Lembretes[/b]\n"
                "• 'definir lembrete <texto> [HH:MM]' : cria lembrete\n"
                "• 'listar lembretes' : mostra seus lembretes\n\n"

                "[b]🗒️ Anotações[/b]\n"
                "• 'anotar <texto>' : salva anotação\n"
                "• 'listar anotações' : mostra todas as anotações\n\n"

                "[b]🗣️ Voz e Comunicação[/b]\n"
                "• 'fale <texto>' ou 'diga <texto>' : Jarvis fala o texto\n\n"

                "[b]🌐 Pesquisa e Informação[/b]\n"
                "• 'pesquisar <termo>' : pesquisa no Google\n"
                "• 'quem é <termo>' ou 'o que é <termo>' : resumo da Wikipedia\n"
                "• 'tocar <termo>' : pesquisa e abre vídeo no YouTube\n\n"

                "[b]🔤 Tradução[/b]\n"
                "• 'traduzir <texto>' : traduz texto para o português\n\n"

                "[b]⚙️ Personalização[/b]\n"
                "• Clique no ícone ✏️ para editar nome, apelido, cidade e outras memórias\n\n"

                "[b]❌ Encerrar Jarvis[/b]\n"
                "• 'sair', 'desligar', 'tchau' : encerra o programa\n\n"

                "[b]💡 Exemplos Rápidos[/b]\n"
                "definir alarme para 06:45 diário\n"
                "definir lembrete ligar para João às 15:00\n"
                "anotar ideias para projeto\n"
                "quem é Ada Lovelace\n"
                "pesquisar receita de bolo\n"
                "tocar vídeo gato fofo\n"
                "traduzir bom dia\n"
                "fale Estou aqui para ajudar!\n\n"

                "[b]💡 Dicas[/b]\n"
                "• Separe múltiplos comandos com 'e', 'então' ou 'depois'\n"
                "• Use variáveis nas respostas: 'Oii, {[b]nome[/b]}! Hoje é {[b]dia_semana[/b]}, {[b]dia[/b]} de {[b]mes[/b]}.'\n\n"

                "Digite 'ajuda' a qualquer momento para ver esta mensagem."
            )
            self.falar(ajuda)
            return

        # Caso não reconheça o comando
        self.falar("Desculpe, não entendi esse comando. Digite 'ajuda' para ver a lista de comandos.")

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
            print("Erro na substituição de variáveis:", e)
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
            print("Erro na tradução:", e)
            self.falar("Não consegui traduzir o texto.")

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


class JarvisApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        return JarvisLayout()


if __name__ == '__main__':
    JarvisApp().run()

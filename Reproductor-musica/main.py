import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow,
                             QLabel, QPushButton, QDockWidget,
                             QStatusBar, QTabWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QListWidget, QFileDialog, QListWidgetItem, QSlider, QComboBox)
import os

from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

from PyQt6.QtGui import QPixmap, QAction, QKeySequence, QIcon
from PyQt6.QtCore import Qt, QStandardPaths

import random
from pydub import AudioSegment
from pydub.playback import play
import tempfile
from pydub.effects import normalize
import numpy as np
import io
from audio_processor import EqualizerPlayer, AudioProcessor

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initialize_ui()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.current_music_folder = ""
        self.equalizer_player = EqualizerPlayer()
        with open("styles.css", "r") as file:
            style = file.read()
        self.setStyleSheet(style)
        self.playing_reproductor = False
        self.is_randomized = False  
        self.playlist_order = []  
        self.current_index = -1
        self.is_repeat_mode = False 
        self.is_changing_track = False 
        self.audioOutput = QAudioOutput()  
        self.audioOutput.setVolume(1.0)
        
        
    def initialize_ui(self):
        self.setGeometry(100, 100, 800, 500)
        self.setWindowTitle("Reproductor de musica")
        self.generate_main_window()
        self.create_dock()
        self.create_action()
        self.create_menu()
        self.show()
        
    def generate_main_window(self):
        tab_bar = QTabWidget(self)
        self.reproductor_container = QWidget()
        self.settings_container = QWidget()
        tab_bar.addTab(self.reproductor_container,
                       "Reproductor")
        tab_bar.addTab(self.settings_container,
                       "Settings")
        
        self.generate_reproductor_tab()
        self.generate_settings_tab()
        
        tab_h_box = QHBoxLayout()
        tab_h_box.addWidget(tab_bar)
        
        main_container = QWidget()
        main_container.setLayout(tab_h_box)
        self.setCentralWidget(main_container)
        
    def generate_reproductor_tab(self):
        
        main_v_box = QVBoxLayout()
        buttons_h_box = QHBoxLayout()
        
        song_image = QLabel()
        pixmap = QPixmap("img/music.gif").scaled(512, 512)
        song_image.setPixmap(pixmap)
        song_image.setScaledContents(True)
        
        self.button_repeat = QPushButton()
        self.button_repeat.setObjectName("button_repeat")
        self.button_before = QPushButton()
        self.button_before.setObjectName("button_before")
        self.button_play = QPushButton()
        self.button_play.setObjectName("button_play")
        self.button_next = QPushButton()
        self.button_next.setObjectName("button_next")
        self.button_random = QPushButton()
        self.button_random.setObjectName("button_random")
        self.button_repeat.setFixedSize(40,40)
        self.button_before.setFixedSize(40,40)
        self.button_play.setFixedSize(50,50)
        self.button_next.setFixedSize(40,40)
        self.button_random.setFixedSize(40,40)
        buttons_h_box.addWidget(self.button_repeat)
        buttons_h_box.addWidget(self.button_before)
        buttons_h_box.addWidget(self.button_play)
        buttons_h_box.addWidget(self.button_next)
        buttons_h_box.addWidget(self.button_random)
        buttons_container = QWidget()
        buttons_container.setLayout(buttons_h_box)
        
        main_v_box.addWidget(song_image)
        main_v_box.addWidget(buttons_container)
        
        self.reproductor_container.setLayout(main_v_box)
        
        # Implementacion botones
        self.button_play.clicked.connect(self.play_pause_song)
        self.button_next.clicked.connect(self.next_song)
        self.button_before.clicked.connect(self.previous_song)
        self.button_random.clicked.connect(self.toggle_randomize)
        self.button_repeat.clicked.connect(self.toggle_repeat_mode)
        
        
    def create_action(self):
        self.listar_musica_action = QAction("Listar Musica",self, checkable=True)
        self.listar_musica_action.setShortcut(QKeySequence("Ctrl+L"))
        self.listar_musica_action.setStatusTip("Aqui puedes listar la musica a reproducir")
        self.listar_musica_action.triggered.connect(self.list_music)
        self.listar_musica_action.setChecked(True)
        
        self.open_folder_music_action = QAction("Abrir Carpeta",self)
        self.open_folder_music_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_folder_music_action.setStatusTip("Aqui puedes Abrir una carpeta con la musica a reproducir")
        self.open_folder_music_action.triggered.connect(self.open_folder_music)
        
    def create_menu(self):
        self.menuBar()
        
        menu_file = self.menuBar().addMenu("File")
        menu_file.addAction(self.open_folder_music_action)
        
        menu_view = self.menuBar().addMenu("View")
        menu_view.addAction(self.listar_musica_action)
        
    def create_dock(self):
        self.songs_list = QListWidget()
        self.dock = QDockWidget()
        self.dock.setWindowTitle("Lista de Reproduccion")
        self.dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.songs_list.itemSelectionChanged.connect(self.handle_song_selection)
        self.dock.setWidget(self.songs_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock)
        
        
    def open_folder_music(self):
        initial_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.MusicLocation
        )
        selected_folder = QFileDialog.getExistingDirectory(None, "Seleccione una Carpeta", initial_dir)
        if not selected_folder:
            self.status_bar.showMessage("No se seleccionó ninguna carpeta", 5000)
            return

        self.current_music_folder = selected_folder
        self.playlist_order = []
        icon = QIcon("img/mp3.png")
        self.songs_list.clear()
        for archivo in os.listdir(self.current_music_folder):
            ruta_archivo = os.path.join(self.current_music_folder, archivo)
            if ruta_archivo.endswith(".mp3") or ruta_archivo.endswith(".wav"):
                item = QListWidgetItem(archivo)
                item.setIcon(icon)
                self.songs_list.addItem(item)
                self.playlist_order.append(ruta_archivo)

        self.initialize_playlist_order()  
                

    def list_music(self):
        if self.listar_musica_action.isChecked():
            self.dock.show()
        else:
            self.dock.hide()
            
            
    def create_player(self): 
        if hasattr(self, 'equalizer_player'):
            self.equalizer_player.media_player.stop()
        self.equalizer_player = EqualizerPlayer()
            
    # Slot Handling
    def play_pause_song(self):
        if not hasattr(self, 'equalizer_player'):
            self.status_bar.showMessage("Seleccione una cancion antes para reproducir", 5000)
            return
        
        if self.playing_reproductor:
            self.button_play.setStyleSheet("image: url(img/stop-icon.png)")
            self.equalizer_player.media_player.pause()
            self.playing_reproductor = False
        else:
            self.button_play.setStyleSheet("image: url(img/play-icon.png)")
            self.equalizer_player.media_player.play()
            self.playing_reproductor = True
    

    def media_status_changed(self, status):
        if self.is_changing_track:
            return
        print(f"Status: {status} - Playback state: {self.equalizer_player.media_player.playbackState()}")
    
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.is_changing_track = True
            if self.is_repeat_mode:
                self.equalizer_player.media_player.setPosition(0)
                self.equalizer_player.media_player.play()
            else:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self.next_song)
            self.is_changing_track = False
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.status_bar.showMessage("Error al cargar el archivo de audio", 5000)
        elif status == QMediaPlayer.MediaStatus.LoadingMedia:
            print("Cargando archivo...")
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            print("Archivo cargado correctamente.")
        elif status == QMediaPlayer.MediaStatus.BufferingMedia:
            print("Bufferizando audio...")


            
            
    def handle_song_selection(self):
        selected_item = self.songs_list.currentItem()
        if selected_item:
            self.current_index = self.songs_list.currentRow()
            song_name = selected_item.data(0)
            song_folder_path = os.path.join(self.current_music_folder, song_name)
            
            if hasattr(self, 'equalizer_player'):
                self.equalizer_player.media_player.stop()
                self.equalizer_player.media_player.setSource(QUrl())

            self.create_player()
            source = QUrl.fromLocalFile(song_folder_path)
            self.equalizer_player.play(source)
            
            self.equalizer_player.media_player.mediaStatusChanged.connect(self.media_status_changed)

            self.playing_reproductor = True
            print(f"Reproduciendo: {song_folder_path}")
            self.button_play.setStyleSheet("image: url(img/play-icon.png)")
            
            
    def next_song(self):
        if not self.playlist_order or self.current_index == -1:
            self.status_bar.showMessage("Seleccione una canción primero", 5000)
            return
        
        if self.is_randomized:
            current_position = self.playlist_order.index(self.current_index)
            next_position = (current_position + 1) % len(self.playlist_order)
            self.current_index = self.playlist_order[next_position]
        else:
            next_index = (self.current_index + 1) % self.songs_list.count()
            self.current_index = next_index

        print(f"Reproduciendo canción siguiente: indice {self.current_index}")
        self.songs_list.setCurrentRow(self.current_index)
        self.handle_song_selection()


    def previous_song(self):
        if self.current_index == -1:
            self.status_bar.showMessage("Seleccione una canción primero", 5000)
            return
        if self.is_randomized:
            current_position = self.playlist_order.index(self.current_index)
            previous_position = (current_position - 1) % len(self.playlist_order)
            self.current_index = self.playlist_order[previous_position]
        else:
            previous_index = (self.current_index - 1) % self.songs_list.count()
            self.current_index = previous_index
        
        print(f"Reproduciendo canción previa: indice {self.current_index}")
        self.songs_list.setCurrentRow(self.current_index)
        self.handle_song_selection()
        
        
    # randomizar lista
    def toggle_randomize(self):
        if not self.current_music_folder:
            self.status_bar.showMessage("Primero abre una carpeta de música", 5000)
            return

        self.is_randomized = not self.is_randomized

        if self.is_randomized:
            random.shuffle(self.playlist_order)  
            self.status_bar.showMessage("Modo aleatorio activado", 5000)
            self.button_random.setStyleSheet("image: url(img/random-icon.png)")
        else:
            self.playlist_order = list(range(self.songs_list.count()))  
            self.status_bar.showMessage("Modo aleatorio desactivado", 5000)
            self.button_random.setStyleSheet("image: url(img/random-off-icon.png)")

    def initialize_playlist_order(self):
        self.playlist_order = list(range(self.songs_list.count()))
        
        
    #repetir cancion
    def toggle_repeat_mode(self):
        if not self.current_music_folder:
            self.status_bar.showMessage("Primero abre una carpeta de música", 5000)
            return
        
        self.is_repeat_mode = not self.is_repeat_mode
        if self.is_repeat_mode:
            self.button_repeat.setStyleSheet("image: url(img/icon-repeat.png)")
            self.status_bar.showMessage("Modo repetir activado", 5000)
        else:
            self.button_repeat.setStyleSheet("image: url(img/repeat-off-icon.png)")
            self.status_bar.showMessage("Modo repetir desactivado", 5000)
            
    
    # SETTINGS
    def generate_settings_tab(self):
        main_v_box = QVBoxLayout()

        # Volumen
        volume_label = QLabel("Volumen:")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)  
        self.volume_slider.valueChanged.connect(self.update_default_volume)

        # Ecualizador
        equalizer_label = QLabel("Ecualizador:")
        self.bass_slider, bass_label = self.create_equalizer_slider("Graves")
        self.mid_slider, mid_label = self.create_equalizer_slider("Medios")
        self.treble_slider, treble_label = self.create_equalizer_slider("Agudos")

        equalizer_layout = QVBoxLayout()
        equalizer_layout.addWidget(equalizer_label)
        for label, slider in [(bass_label, self.bass_slider), (mid_label, self.mid_slider), (treble_label, self.treble_slider)]:
            equalizer_layout.addWidget(label)
            equalizer_layout.addWidget(slider)

        main_v_box.addWidget(volume_label)
        main_v_box.addWidget(self.volume_slider)
        main_v_box.addLayout(equalizer_layout)

        self.settings_container.setLayout(main_v_box)
        
        

    def update_default_volume(self, value):  
        if hasattr(self, 'equalizer_player'):
            self.equalizer_player.audio_output.setVolume(value / 100.0)
        self.status_bar.showMessage(f"Volumen predeterminado actualizado a {value}%")
     

    def create_equalizer_slider(self, label_text):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(-10, 10)
        slider.setValue(0)
        slider.valueChanged.connect(self.update_equalizer_settings)
        label = QLabel(label_text)
        return slider, label

    def update_equalizer_settings(self):
        if not hasattr(self, 'equalizer_player'):
            self.status_bar.showMessage("No hay archivo de audio cargado para aplicar el ecualizador.", 3000)
            return

        bass_boost = self.bass_slider.value()
        mid_boost = self.mid_slider.value()
        treble_boost = self.treble_slider.value()
        
        self.equalizer_player.set_equalizer(bass_boost, mid_boost, treble_boost)
        print(f"Ajustes del ecualizador - Graves: {bass_boost}, Medios: {mid_boost}, Agudos: {treble_boost}")
                
                
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
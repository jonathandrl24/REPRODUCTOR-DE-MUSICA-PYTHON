import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow,
                             QLabel, QPushButton, QDockWidget,
                             QStatusBar, QTabWidget, QWidget, QHBoxLayout,
                             QVBoxLayout, QListWidget)

from PyQt6.QtGui import QPixmap

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initialize_ui()
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
    def initialize_ui(self):
        self.setGeometry(100, 100, 800, 500)
        self.setWindowTitle("Reproductor de musica")
        self.generate_main_window()
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
        #self.generate_settings_tab()
        
        tab_h_box = QHBoxLayout()
        tab_h_box.addWidget(tab_bar)
        
        main_container = QWidget()
        main_container.setLayout(tab_h_box)
        self.setCentralWidget(main_container)
        
    def generate_reproductor_tab(self):
        
        main_v_box = QVBoxLayout()
        buttons_h_box = QHBoxLayout()
        
        song_image = QLabel()
        pixmap = QPixmap("img/music.gif")
        song_image.setPixmap(pixmap)
        song_image.setScaledContents(True)
        
        button_repeat = QPushButton("🔁")
        button_before = QPushButton("⏪")
        button_play = QPushButton("▶️")
        button_next = QPushButton("⏭️")
        button_random = QPushButton("🔀")
        buttons_h_box.addWidget(button_repeat)
        buttons_h_box.addWidget(button_before)
        buttons_h_box.addWidget(button_play)
        buttons_h_box.addWidget(button_next)
        buttons_h_box.addWidget(button_random)
        buttons_container = QWidget()
        buttons_container.setLayout(buttons_h_box)
        
        main_v_box.addWidget(song_image)
        main_v_box.addWidget(buttons_container)
        
        self.reproductor_container.setLayout(main_v_box)
    
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
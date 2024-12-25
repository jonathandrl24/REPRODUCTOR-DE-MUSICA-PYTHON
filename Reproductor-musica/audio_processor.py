from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaFormat
from PyQt6.QtCore import QUrl

class EqualizerPlayer:
    def __init__(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        
        self.supported_formats = self.check_supported_formats()
        
    def check_supported_formats(self):
        supported = {}
        
        format = QMediaFormat()
        format.setFileFormat(QMediaFormat.FileFormat.MP3)
        supported['mp3'] = format.isSupported(QMediaFormat.ConversionMode.Decode)
        
        format.setFileFormat(QMediaFormat.FileFormat.Wave)
        supported['wav'] = format.isSupported(QMediaFormat.ConversionMode.Decode)
        
        print("Supported formats:", supported)
        return supported
        
    def play(self, url):
        if isinstance(url, str):
            url = QUrl(url)
            
        self.media_player.setSource(url)
        self.media_player.play()
        return True
        
    def stop(self):
        self.media_player.stop()
        
    def pause(self):
        self.media_player.pause()
        
    def set_equalizer(self, bass, mid, treble):
        self.bass_gain = bass
        self.mid_gain = mid
        self.treble_gain = treble
        print(f"Equalizer settings updated - Bass: {bass}, Mid: {mid}, Treble: {treble}")
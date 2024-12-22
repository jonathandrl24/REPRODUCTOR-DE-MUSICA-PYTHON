import numpy as np
from PyQt6.QtMultimedia import (QMediaPlayer, QAudioOutput, QMediaDevices, 
                               QAudioSink, QAudioFormat, QAudioBuffer)
from PyQt6.QtCore import QByteArray, QIODevice
from scipy.signal import butter, sosfilt
import array

class AudioProcessor(QIODevice):
    def __init__(self, format, parent=None):
        super().__init__(parent)
        self.format = format
        self.bass_gain = 0
        self.mid_gain = 0
        self.treble_gain = 0
        
        self.sample_rate = format.sampleRate()
        self.setup_filters()
        
    def setup_filters(self):
        self.bass_sos = []  
        
        self.mid_sos = []  
        
        self.treble_sos = []
        
    def start(self):
        self.open(QIODevice.OpenModeFlag.ReadWrite)
        
    def stop(self):
        self.close()
        
    def set_gains(self, bass, mid, treble):
        self.bass_gain = 10 ** (bass / 20)  
        self.mid_gain = 10 ** (mid / 20)
        self.treble_gain = 10 ** (treble / 20)
        
    def process_audio(self, data):
        samples = array.array('h', data)
        audio_data = np.array(samples, dtype=np.float32) / 32768.0
        
        bass = sosfilt(self.bass_sos, audio_data) * self.bass_gain
        mid = sosfilt(self.mid_sos, audio_data) * self.mid_gain
        treble = sosfilt(self.treble_sos, audio_data) * self.treble_gain
        
        mixed = np.clip(bass + mid + treble, -1.0, 1.0)
        
        processed = (mixed * 32768).astype(np.int16)
        return QByteArray(processed.tobytes())
        
    def readData(self, maxlen):
        return self.process_audio(self.player.read(maxlen))
        
    def writeData(self, data):
        self.player.write(data)
        return len(data)

class EqualizerPlayer:
    def __init__(self):
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.audio_output.setVolume(1.0)
        
        self.format = QAudioFormat()
        self.format.setSampleRate(44100)
        self.format.setChannelCount(2)
        self.format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        
        self.processor = AudioProcessor(self.format)
        
    def set_equalizer(self, bass, mid, treble):
        self.processor.set_gains(bass, mid, treble)
        
    def play(self, url):
        self.media_player.setSource(url)
        self.media_player.play()
        
    def stop(self):
        self.media_player.stop()
        
    def pause(self):
        self.media_player.pause()
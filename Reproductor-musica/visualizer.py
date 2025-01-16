import pygame
import numpy as np
import colorsys
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QImage
import array
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class VisualizerConfig:
    width: int = 800
    height: int = 600
    chunk_size: int = 512
    fps: int = 60
    num_bright_spirals: int = 15
    num_dark_spirals: int = 15
    background_darkness: float = 0.5
    background_saturation: float = 1
    beat_threshold: float = 1.3
    beat_decay: float = 0.95
    bass_freq_range: Tuple[int, int] = (0, 50)


class LightningBolt:
    def __init__(self, angle: float, intensity: float = 1.0, screen_size: Tuple[int, int] = (800, 600)):
        self.angle = angle
        max_length = min(screen_size[0], screen_size[1] * 0.75)
        self.length = random.randint(int(max_length), int(max_length))
        self.lifetime = random.randint(5, 15)
        self.width = random.uniform(0.15, 0.25) * intensity
        self.alpha = 255 * intensity
        self.branches = self._generate_branches(intensity)
        self.flicker_state = random.random()
        self.color = self._generate_color(intensity)

    def _generate_color(self, intensity: float) -> Tuple[int, int, int]:
        base_color = (217, 217, 217)
        variation = random.randint(-100, 100)
        color = tuple(max(0, min(255, int((c + variation) * intensity))) for c in base_color)
        return color

    def _generate_branches(self, intensity: float) -> List[Tuple[float, float, float]]:
        branches = []
        num_branches = random.randint(2, 3 if intensity > 1.5 else 2)
        
        for _ in range(num_branches):
            angle_variance = random.uniform(-45, 45) * intensity
            branches.append((
                self.angle + angle_variance,
                self.length * random.uniform(0.5, 1) * intensity,
                random.uniform(0.3, 0.7)
            ))
        return branches

    def update(self) -> bool:
        self.lifetime -= 1
        self.flicker_state = random.random()
        self.alpha = int((self.lifetime * 255) // 15 * (0.7 + 0.3 * self.flicker_state))
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, center: Tuple[int, int]):
        for branch in self.branches:
            branch_angle, branch_length, _ = branch
            branch_radians = np.radians(branch_angle)
            end_pos = (
                int(center[0] + branch_length * np.cos(branch_radians)),
                int(center[1] + branch_length * np.sin(branch_radians))
            )
            self._draw_lightning_segment(surface, center, end_pos)

    def _draw_lightning_segment(self, surface: pygame.Surface, start_pos: Tuple[int, int], 
                              end_pos: Tuple[int, int]):
        points = self._generate_lightning_points(start_pos, end_pos)
        
        for layer in range(3):
            width = self.width * (5 - layer)
            alpha = int(self.alpha * (0.8 ** layer) * self.flicker_state)
            color = (*self.color, alpha)
            
            for i in range(len(points) - 1):
                pygame.draw.line(surface, color, points[i], points[i + 1], int(width))

    def _generate_lightning_points(self, start_pos: Tuple[int, int], 
                                 end_pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        points = [start_pos]
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        dist = np.sqrt(dx*dx + dy*dy)
        num_segments = 8
        
        for i in range(num_segments):
            progress = (i + 1) / (num_segments + 1)
            zigzag_amount = (1 - progress) * dist * 0.2
            
            x = start_pos[0] + dx * progress
            y = start_pos[1] + dy * progress
            
            offset = random.uniform(-zigzag_amount, zigzag_amount)
            angle = random.uniform(0, 2 * np.pi)
            
            x += np.cos(angle) * offset
            y += np.sin(angle) * offset
            points.append((int(x), int(y)))
        
        points.append(end_pos)
        return points


class AudioVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = VisualizerConfig()
        pygame.init()
        
        self.hue_offset = 0.0
        self.time = 0
        self.energy_history = []
        self.current_beat_energy = 0
        self.last_beat_time = 0
        self.spiral_rays = []
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // self.config.fps)
        
        self.audio_buffer = array.array('h')
        self.fft_data = np.zeros(self.config.chunk_size // 2)
        
        # Create blur surfaces
        self.blur_scale = 4
        self._create_surfaces()

    def _create_surfaces(self):
        """Create or recreate surfaces based on current window size"""
        self.blur_surface = pygame.Surface((self.width(), self.height()), pygame.SRCALPHA)
        self.small_surface = pygame.Surface(
            (self.width() // self.blur_scale, self.height() // self.blur_scale),
            pygame.SRCALPHA
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._create_surfaces()
        
    def process_audio_data(self, data):
        """Process incoming audio data"""
        if isinstance(data, (bytes, bytearray)):
            temp_buffer = array.array('h')
            temp_buffer.frombytes(data)
            self.audio_buffer.extend(temp_buffer)
        
        if len(self.audio_buffer) >= self.config.chunk_size:
            chunk = np.array(self.audio_buffer[-self.config.chunk_size:])
            self.fft_data = np.abs(np.fft.rfft(chunk)) / self.config.chunk_size
            self.fft_data = self.fft_data / np.max(self.fft_data) if np.max(self.fft_data) > 0 else self.fft_data
            self.audio_buffer = array.array('h', self.audio_buffer[-self.config.chunk_size:])
            
    def detect_beat(self) -> Tuple[bool, float]:
        """Detect beats in the audio"""
        bass_range = slice(self.config.bass_freq_range[0],
                         min(self.config.bass_freq_range[1], len(self.fft_data)))
        bass_energy = np.sum(self.fft_data[bass_range])
        
        self.energy_history.append(bass_energy)
        if len(self.energy_history) > 50:
            self.energy_history.pop(0)
            
        avg_energy = np.mean(self.energy_history) if self.energy_history else bass_energy
        self.current_beat_energy *= self.config.beat_decay
        
        is_beat = False
        intensity = 1.0
        
        if bass_energy > avg_energy * self.config.beat_threshold:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_beat_time > 100:
                is_beat = True
                self.last_beat_time = current_time
                intensity = bass_energy / avg_energy
                self.current_beat_energy = intensity
        
        return is_beat, max(intensity, self.current_beat_energy)

    def apply_fast_blur(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply a fast blur effect to the surface"""
        small_surface = pygame.transform.smoothscale(
            surface,
            (surface.get_width() // self.blur_scale, surface.get_height() // self.blur_scale)
        )
        return pygame.transform.smoothscale(
            small_surface,
            (surface.get_width(), surface.get_height())
        )

    def paintEvent(self, event):
        """Handle the paint event to draw the visualization"""
        painter = QPainter(self)
        
        # Clear blur surfaces
        self.blur_surface.fill((0, 0, 0, 0))
        self.small_surface.fill((0, 0, 0, 0))
        
        # Draw visualization elements
        self._draw_background(self.blur_surface)
        self._draw_visualization(self.blur_surface)
        
        # Apply blur and draw lightning
        blurred = self.apply_fast_blur(self.blur_surface)
        
        # Convert pygame surface to QImage and draw
        buffer = blurred.get_buffer().raw
        image = QImage(buffer, blurred.get_width(), blurred.get_height(),
                      blurred.get_pitch(), QImage.Format.Format_ARGB32)
        painter.drawImage(0, 0, image)
        
        # Update visualization parameters
        self.hue_offset = (self.hue_offset + 0.005) % 1.0
        self.time += 0.05

    def _draw_background(self, surface: pygame.Surface):
        """Draw the visualization background"""
        background_hue = (self.hue_offset + 0.1) % 1.0
        bg_color = colorsys.hsv_to_rgb(
            background_hue,
            self.config.background_saturation,
            self.config.background_darkness
        )
        bg_color = tuple(int(c * 255) for c in bg_color)
        surface.fill(bg_color)

    def _draw_visualization(self, surface: pygame.Surface):
        """Draw the main visualization elements"""
        center = (self.width() // 2, self.height() // 2)
        max_radius = min(self.width(), self.height()) // 2
        
        self._draw_spirals(surface, center, max_radius)
        self._handle_lightning(surface, center)

    def _draw_spirals(self, surface: pygame.Surface, center: Tuple[int, int], max_radius: float):
        """Draw spiral visualization elements"""
        # Draw bright spirals
        self._draw_spiral_type(surface, center, max_radius, 
                             self.config.num_bright_spirals, True)
        
        # Draw dark spirals
        self._draw_spiral_type(surface, center, max_radius, 
                             self.config.num_dark_spirals, False)

    def _draw_spiral_type(self, surface: pygame.Surface, center: Tuple[int, int], 
                         max_radius: float, num_spirals: int, bright: bool):
        """Draw a specific type of spiral (bright or dark)"""
        row_spacing = max_radius // (num_spirals // 2)
        
        for spiral in range(num_spirals):
            spiral_offset = (spiral * row_spacing * (1.5 if bright else 3))
            if not bright:
                spiral_offset += row_spacing * self.config.num_bright_spirals
            
            radius = max_radius + spiral_offset
            
            for i, amplitude in enumerate(self.fft_data):
                angle = (i * (360 / len(self.fft_data))) + (self.hue_offset * 360) + spiral_offset * 0.5
                pos = self._calculate_point_position(center, angle, amplitude * radius)
                
                if bright:
                    self._draw_bright_point(surface, pos, i, len(self.fft_data), amplitude, spiral_offset)
                else:
                    self._draw_dark_point(surface, pos, i, len(self.fft_data), amplitude, spiral_offset)

    def _calculate_point_position(self, center: Tuple[int, int], angle: float, 
                                radius: float) -> Tuple[int, int]:
        """Calculate the position of a point in the spiral"""
        radians = np.radians(angle)
        return (
            int(center[0] + radius * np.cos(radians)),
            int(center[1] + radius * np.sin(radians))
        )

    def _draw_bright_point(self, surface: pygame.Surface, pos: Tuple[int, int], 
                          i: int, total_points: int, amplitude: float, spiral_offset: float):
        """Draw a bright point in the visualization"""
        color = colorsys.hsv_to_rgb(
            (self.hue_offset + (i / total_points) + spiral_offset) % 1.0,
            1,
            min(amplitude * 1.5, 1)
        )
        color = tuple(int(c * 255) for c in color)
        pygame.draw.circle(surface, color, pos, int(5 + amplitude * 15))

    def _draw_dark_point(self, surface: pygame.Surface, pos: Tuple[int, int], 
                        i: int, total_points: int, amplitude: float, spiral_offset: float):
        """Draw a dark point in the visualization"""
        color = colorsys.hsv_to_rgb(
            (self.hue_offset + (i / total_points) + spiral_offset) % 1.0,
            0.3,
            0.2 if random.random() > 0.3 else 0
        )
        color = tuple(int(c * 115) for c in color)
        pygame.draw.circle(surface, color, pos, int(3 + amplitude * 10))

    def _handle_lightning(self, surface: pygame.Surface, center: Tuple[int, int]):
        """Handle lightning effects"""
        is_beat, intensity = self.detect_beat()
        
        if is_beat:
            num_bolts = random.randint(1, max(1, int(intensity)))
            for _ in range(num_bolts):
                angle = random.uniform(0, 360)
                self.spiral_rays.append(
                    LightningBolt(angle, intensity, (self.width(), self.height()))
                )
        
        # Update and draw existing lightning bolts
        self.spiral_rays = [bolt for bolt in self.spiral_rays if bolt.update()]
        for bolt in self.spiral_rays:
            bolt.draw(surface, center)
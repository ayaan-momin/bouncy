import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QImage, QFont, QLinearGradient
import time
import random

class Hazard:
    def __init__(self, x, y, size, speed, direction):
        self.x = x
        self.y = y
        self.size = size
        self.speed_x = speed if direction in ['left', 'right'] else 0
        self.speed_y = speed if direction == 'down' else 0
        self.direction = direction
        self.active = True

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 25
        self.speed_x = 0
        self.speed_y = 0
        self.last_bounce_time = 0
        self.alive = True
        self.trail_positions = []
        self.max_trail_length = 3
        
    def update(self, window_velocity):
        if not self.alive:
            return
            
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > self.max_trail_length:
            self.trail_positions.pop(0)
            
        self.speed_x += window_velocity[0] * 0.15
        
        if window_velocity[1] < 0:
            self.speed_y += window_velocity[1] * 0.15
        
        self.speed_y += 0.75
        
        self.x += self.speed_x
        self.y += self.speed_y
        
        self.speed_x *= 0.99
        
    def bounce(self, width, height, window_velocity):
        if not self.alive:
            return
            
        current_time = time.time()
        BOUNCE_FACTOR = 0.86
        
        impact_velocity = abs(window_velocity[1])
        force_multiplier = 1 + (impact_velocity * 0.1)
        
        if self.y + self.size > height:
            self.y = height - self.size
            bounce_velocity = -self.speed_y * BOUNCE_FACTOR * force_multiplier
            MIN_BOUNCE = -10
            self.speed_y = min(bounce_velocity, MIN_BOUNCE * force_multiplier)
            self.last_bounce_time = current_time
            
        if self.y < 30:
            self.y = 30
            self.speed_y = -self.speed_y * BOUNCE_FACTOR
            
        if self.x + self.size > width:
            self.x = width - self.size
            self.speed_x = -self.speed_x * BOUNCE_FACTOR
            
        if self.x < 0:
            self.x = 0
            self.speed_x = -self.speed_x * BOUNCE_FACTOR

    def check_collision(self, hazard):
        ball_center_x = self.x + self.size / 2
        ball_center_y = self.y + self.size / 2
        
        if (ball_center_x > hazard.x and 
            ball_center_x < hazard.x + hazard.size and
            ball_center_y > hazard.y and 
            ball_center_y < hazard.y + hazard.size):
            return True
        return False

class PhysicsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.width = 600
        self.height = 370
        self.resize(self.width, self.height)
        self.setWindowTitle("Undertale-inspired Physics Game")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.buffer = QImage(self.width, self.height, QImage.Format_ARGB32)
        self.buffer.fill(Qt.transparent)
        self.gradient_top = QColor(40, 40, 60)
        self.gradient_bottom = QColor(20, 20, 30)
        self.ball = Ball(self.width//2, 50)
        self.hazards = []
        self.spawn_timer = 0
        self.score = 0
        self.start_time = time.time()
        self.last_pos = self.pos()
        self.window_velocity = [0, 0]
        self.dragging = False
        self.drag_offset = QPoint()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)
        self.last_time = time.time()
        self.game_paused = False
        self.hazard_delay_passed = False
        self.hazard_delay_timer = QTimer()
        self.hazard_delay_timer.setSingleShot(True)
        self.hazard_delay_timer.timeout.connect(self.enable_hazard_spawning)
        self.hazard_delay_timer.start(5000)

    def enable_hazard_spawning(self):
        self.hazard_delay_passed = True

    def spawn_hazard(self):
        SQUARE_SIZE = 30
        SPEED = 3
        spawn_type = random.choice(['left', 'right', 'top'])
        
        if spawn_type == 'left':
            hazard = Hazard(-SQUARE_SIZE, random.randint(50, self.height - SQUARE_SIZE), SQUARE_SIZE, SPEED, 'right')
        elif spawn_type == 'right':
            hazard = Hazard(self.width, random.randint(50, self.height - SQUARE_SIZE), SQUARE_SIZE, -SPEED, 'left')
        else:
            hazard = Hazard(random.randint(0, self.width - SQUARE_SIZE), 30, SQUARE_SIZE, SPEED, 'down')
            
        self.hazards.append(hazard)

    def paintEvent(self, event):
        buffer_painter = QPainter(self.buffer)
        buffer_painter.setRenderHint(QPainter.Antialiasing)
        self.buffer.fill(Qt.transparent)
        
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, self.gradient_top)
        gradient.setColorAt(1, self.gradient_bottom)
        buffer_painter.fillRect(0, 0, self.width, self.height, gradient)
        
        top_gradient = QLinearGradient(0, 0, 0, 30)
        top_gradient.setColorAt(0, QColor(60, 60, 80))
        top_gradient.setColorAt(1, QColor(50, 50, 70))
        buffer_painter.fillRect(0, 0, self.width, 30, top_gradient)

        buffer_painter.setBrush(QColor(50, 200, 50))
        buffer_painter.setPen(Qt.NoPen)
        buffer_painter.drawEllipse(self.width - 90, 5, 20, 20)
        buffer_painter.setBrush(QColor(255, 255, 0))
        buffer_painter.drawEllipse(self.width - 60, 5, 20, 20)
        buffer_painter.setBrush(QColor(200, 50, 50))
        buffer_painter.drawEllipse(self.width - 30, 5, 20, 20)

        buffer_painter.setFont(QFont('Arial', 12))
        buffer_painter.setPen(QColor(255, 255, 255))
        if self.ball.alive:
            self.score = int(time.time() - self.start_time)
        score_text = f"Score: {self.score}"
        buffer_painter.drawText(10, 20, score_text)
        
        buffer_painter.setBrush(QColor(255, 140, 0))
        buffer_painter.setPen(Qt.NoPen)
        for hazard in self.hazards:
            if hazard.active:
                buffer_painter.drawRect(int(hazard.x), int(hazard.y), hazard.size, hazard.size)
        
        if self.ball.alive:
            for i, (trail_x, trail_y) in enumerate(self.ball.trail_positions):
                alpha = int(255 * (i + 1) / len(self.ball.trail_positions) * 0.3)
                trail_color = QColor(255, 100, 100, alpha)
                buffer_painter.setBrush(trail_color)
                buffer_painter.setPen(Qt.NoPen)
                buffer_painter.drawEllipse(int(trail_x), int(trail_y), self.ball.size, self.ball.size)
        
        if self.ball.alive:
            buffer_painter.setBrush(QColor(255, 100, 100))
        else:
            buffer_painter.setBrush(QColor(100, 100, 100))
        buffer_painter.drawEllipse(int(self.ball.x), int(self.ball.y), self.ball.size, self.ball.size)
        
        buffer_painter.end()
        window_painter = QPainter(self)
        window_painter.drawImage(0, 0, self.buffer)
    
    def update_physics(self):
        if self.game_paused:
            return
        
        current_time = time.time()
        delta = current_time - self.last_time
        self.last_time = current_time
        
        if self.hazard_delay_passed:
            self.spawn_timer += delta
            if self.spawn_timer > 1.5:
                self.spawn_hazard()
                self.spawn_timer = 0
        
        for hazard in self.hazards:
            if not hazard.active:
                continue
                
            hazard.x += hazard.speed_x
            hazard.y += hazard.speed_y
            
            if (hazard.x + hazard.size < 0 or hazard.x > self.width or hazard.y > self.height):
                hazard.active = False
            
            if self.ball.alive and hazard.active and self.ball.check_collision(hazard):
                self.ball.alive = False
        
        self.hazards = [h for h in self.hazards if h.active]
        
        current_pos = self.pos()
        self.window_velocity = [
            (current_pos.x() - self.last_pos.x()) * 0.3,
            (current_pos.y() - self.last_pos.y()) * 0.3
        ]
        self.last_pos = current_pos
        
        self.ball.update(self.window_velocity)
        self.ball.bounce(self.width, self.height, self.window_velocity)
        
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if (event.x() > self.width - 30 and event.x() < self.width - 10 and 
                event.y() > 5 and event.y() < 25):
                QApplication.quit()
            elif (event.x() > self.width - 60 and event.x() < self.width - 40 and 
                  event.y() > 5 and event.y() < 25):
                self.restart_game()
            elif (event.x() > self.width - 90 and event.x() < self.width - 70 and 
                  event.y() > 5 and event.y() < 25):
                self.toggle_pause()
            elif event.y() < 30:
                self.dragging = True
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_offset)

    def restart_game(self):
        self.ball = Ball(self.width // 2, 50)
        self.hazards = []
        self.spawn_timer = 0
        self.score = 0
        self.start_time = time.time()
        self.ball.alive = True
        self.hazard_delay_passed = False
        self.hazard_delay_timer.start(5000)

    def toggle_pause(self):
        self.game_paused = not self.game_paused

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhysicsWindow()
    window.show()
    sys.exit(app.exec_())
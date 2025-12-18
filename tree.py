import sys
import os
import random
import math
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QFileDialog
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QRadialGradient, QPixmap, QPolygonF, QAction

def resource_path(relative_path):
    """ PyInstaller paketlemesi sonrası dosya yolunu fixler """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class UltimateChristmasTree(QWidget):
    def __init__(self, start_snow=False):
        super().__init__()
        # Pencere ayarları: Çerçevesiz, her zaman üstte, görev çubuğunda görünmez tool window
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Dosya yolu (PyInstaller uyumlu)
        self.tree_path = resource_path("tree.png")
        self.current_width = 350
        self.show_snow = start_snow
        self.snowflakes = []
        self.old_pos = None
        self.dragging_top_light = False 
        
        # Resim yükleme ve hata kontrolü
        self.load_image(self.tree_path)
        
        # İlk kurulum
        self.update_tree_size(self.current_width)
        self.init_snow()

        # Animasyon döngüsü (30 FPS civarı)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(35)

    def load_image(self, path):
        self.original_pixmap = QPixmap(path)
        if self.original_pixmap.isNull():
            # Eğer resim yoksa fallback olarak boş şeffaf alan oluşturur
            self.original_pixmap = QPixmap(500, 500)
            self.original_pixmap.fill(Qt.GlobalColor.transparent)

    def update_tree_size(self, width):
        self.current_width = width
        self.pixmap = self.original_pixmap.scaled(width, width + 150, 
                                            Qt.AspectRatioMode.KeepAspectRatio, 
                                            Qt.TransformationMode.SmoothTransformation)
        self.resize(self.pixmap.size())
        w, h = self.width(), self.height()
        
        # Işıklar için hayali ağaç sınırları
        self.tree_boundary = QPolygonF([
            QPointF(w/2, h*0.05),
            QPointF(w*0.1, h*0.9),
            QPointF(w*0.9, h*0.9)
        ])
        
        # Tepe ışığı default konumu
        self.top_light_pos = QPointF(w/2, h*0.12)
        
        # Rastgele ışıkları aralıklı diz
        self.lights = []
        min_dist = width / 11
        attempts = 0
        while len(self.lights) < 18 and attempts < 1000:
            attempts += 1
            test_pos = QPointF(random.uniform(0, w), random.uniform(h*0.2, h*0.85))
            if self.tree_boundary.containsPoint(test_pos, Qt.FillRule.OddEvenFill):
                if all(math.hypot(test_pos.x()-l["pos"].x(), test_pos.y()-l["pos"].y()) > min_dist for l in self.lights):
                    self.lights.append({
                        "pos": test_pos, 
                        "color": random.choice(["#FF3D00", "#FFEA00", "#00E5FF", "#FF4081", "#76FF03"])
                    })
        if self.show_snow: self.init_snow()

    def select_custom_tree(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Ağaç Resmini Seç", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.load_image(file_path)
            self.update_tree_size(self.current_width)

    def init_snow(self):
        count = int(self.current_width / 5)
        self.snowflakes = [self.reset_snowflake() for _ in range(count)] if self.show_snow else []

    def toggle_snow(self):
        self.show_snow = not self.show_snow
        self.init_snow()

    def reset_snowflake(self):
        return {"x": random.uniform(0, self.width()), "y": random.uniform(-100, 0), 
                "speed": random.uniform(0.8, 2.2), "size": random.uniform(1, 3)}

    def update_animation(self):
        if self.show_snow:
            for s in self.snowflakes:
                s["y"] += s["speed"]
                if s["y"] > self.height(): s.update(self.reset_snowflake())
        self.update()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1e1e1e; color: white; border: 1px solid #444; } QMenu::item:selected { background-color: #333; }")
        
        change_act = QAction("🖼 Ağaç Resmini Değiştir", self)
        change_act.triggered.connect(self.select_custom_tree)
        
        snow_label = "❄ Karı Durdur" if self.show_snow else "❄ Karı Başlat"
        snow_act = QAction(snow_label, self)
        snow_act.triggered.connect(self.toggle_snow)
        
        size_menu = menu.addMenu("📐 Boyutu Ayarla")
        for label, val in [("Küçük", 200), ("Orta", 350), ("Büyük", 550)]:
            a = QAction(label, self)
            a.triggered.connect(lambda ch, v=val: self.update_tree_size(v))
            size_menu.addAction(a)

        exit_act = QAction("❌ Kapat", self)
        exit_act.triggered.connect(QApplication.instance().quit)
        
        menu.addActions([change_act, snow_act])
        menu.addSeparator()
        menu.addAction(exit_act)
        menu.exec(event.globalPos())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen) # Beyaz çember hatasını çözen satır

        # 1. Kar Yağışı
        if self.show_snow:
            painter.setBrush(QColor(255, 255, 255, 160))
            for s in self.snowflakes:
                painter.drawEllipse(QPointF(s["x"], s["y"]), s["size"], s["size"])

        # 2. Ağaç Resmi
        painter.drawPixmap(0, 0, self.pixmap)

        # 3. Işıklar
        g_size = self.current_width / 14
        
        # Tepe Işığı
        color = "#FFF176" if not self.dragging_top_light else "#FFFFFF"
        top_glow = QRadialGradient(self.top_light_pos, g_size)
        top_glow.setColorAt(0, QColor(color))
        top_glow.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(top_glow)
        painter.drawEllipse(self.top_light_pos, g_size*0.8, g_size*0.8)

        # Küçük Işıklar
        for light in self.lights:
            if random.random() > 0.15:
                l_glow = QRadialGradient(light["pos"], g_size/2)
                l_glow.setColorAt(0, QColor(light["color"]))
                l_glow.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setBrush(l_glow)
                painter.drawEllipse(light["pos"], g_size/2.5, g_size/2.5)

    def mousePressEvent(self, event):
        # CTRL + Sol Tık: Tepe ışığını taşı
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if math.hypot(event.position().x() - self.top_light_pos.x(), event.position().y() - self.top_light_pos.y()) < 30:
                self.dragging_top_light = True
        # Normal Sol Tık: Pencereyi taşı
        elif event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.dragging_top_light:
            self.top_light_pos = event.position()
        elif self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.dragging_top_light = False
        self.old_pos = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Başlangıçta kar yağsın mı? (--snow varsa veya True yaparsan)
    window = UltimateChristmasTree(start_snow="--snow" in sys.argv)
    window.show()
    sys.exit(app.exec())            
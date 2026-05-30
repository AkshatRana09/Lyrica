# import sys
# import os
# import math
# import requests
# import threading
# from pathlib import Path

# from PyQt6.QtWidgets import (
#     QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
#     QLabel, QPushButton, QSlider, QScrollArea, QFileDialog,
#     QFrame, QSizePolicy, QGraphicsOpacityEffect
# )
# from PyQt6.QtCore import (
#     Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
#     QEasingCurve, QPointF, QRectF, QSize
# )
# from PyQt6.QtGui import (
#     QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
#     QLinearGradient, QRadialGradient, QPainterPath,
#     QPixmap, QImage, QPalette, QConicalGradient
# )

# try:
#     from mutagen.mp3 import MP3
#     from mutagen.id3 import ID3, APIC
#     from mutagen.flac import FLAC
#     MUTAGEN_OK = True
# except ImportError:
#     MUTAGEN_OK = False

# try:
#     import pygame
#     pygame.mixer.init()
#     PYGAME_OK = True
# except ImportError:
#     PYGAME_OK = False


# # ── Palette ──────────────────────────────────────────────────────────────────
# BG       = QColor("#0a0a0a")
# BG2      = QColor("#0f0f0f")
# BG3      = QColor("#141414")
# RED      = QColor("#c0392b")
# RED2     = QColor("#e74c3c")
# WHITE    = QColor("#ffffff")
# GRAY1    = QColor("#222222")
# GRAY2    = QColor("#333333")
# GRAY3    = QColor("#555555")
# GRAY4    = QColor("#888888")


# # ── LRC Fetcher ───────────────────────────────────────────────────────────────
# import re as _re

# def clean_title(title):
#     """Strip YouTube/download junk from song titles."""
#     # Remove anything after | or ( that looks like channel/label noise
#     junk_patterns = [
#         r'\s*\|.*$',                          # | Karan Aujla | Four You EP ...
#         r'\s*\(Official\s*(Video|Audio|Music Video|Lyric Video)[^)]*\)',
#         r'\s*\[Official\s*(Video|Audio|Music Video)[^\]]*\]',
#         r'\s*\(Lyrics?\)',
#         r'\s*\[Lyrics?\]',
#         r'\s*ft\..*$',
#         r'\s*feat\..*$',
#         r'\s*-\s*(Official|HD|HQ|4K|Audio|Video|Lyric).*$',
#         r'\s*\(HD\)|\s*\[HD\]',
#         r'\s*\d{4}\s*$',                      # trailing year like 2023
#         r'\s*Latest\s+Punjabi\s+Songs.*$',
#         r'\s*New\s+Punjabi\s+Song.*$',
#     ]
#     t = title
#     for pat in junk_patterns:
#         t = _re.sub(pat, '', t, flags=_re.IGNORECASE).strip()
#     t = _re.sub(r'\s{2,}', ' ', t)
#     return t.strip(' -|')

# def clean_artist(artist):
#     """Extract just the first artist name."""
#     # Split on | , / & and take first chunk
#     for sep in ['|', ',', '/', '&', ' x ', ' X ']:
#         if sep in artist:
#             artist = artist.split(sep)[0]
#     return artist.strip()


# class LyricsFetcher(QThread):
#     done = pyqtSignal(list)   # list of (ms, text)
#     error = pyqtSignal(str)

#     def __init__(self, title, artist):
#         super().__init__()
#         self.title = clean_title(title)
#         self.artist = clean_artist(artist)

#     def run(self):
#         try:
#             # Try with both title+artist, then fallback to title only
#             for query in [
#                 f"{self.artist} {self.title}",
#                 self.title,
#             ]:
#                 url = "https://lrclib.net/api/search"
#                 r = requests.get(url, params={"q": query}, timeout=8)
#                 data = r.json()
#                 if data:
#                     break
#             if not data:
#                 self.error.emit("No lyrics found — try renaming the file with clean title + artist")
#                 return
#             entry = data[0]
#             synced = entry.get("syncedLyrics") or ""
#             if synced:
#                 lines = self._parse_lrc(synced)
#                 self.done.emit(lines)
#             else:
#                 plain = entry.get("plainLyrics", "")
#                 lines = [(i * 3000, l) for i, l in enumerate(plain.split("\n")) if l.strip()]
#                 self.done.emit(lines)
#         except Exception as e:
#             self.error.emit(str(e))

#     def _parse_lrc(self, lrc):
#         lines = []
#         for line in lrc.split("\n"):
#             line = line.strip()
#             if line.startswith("[") and "]" in line:
#                 try:
#                     tag = line[1:line.index("]")]
#                     text = line[line.index("]")+1:].strip()
#                     parts = tag.split(":")
#                     if len(parts) == 2:
#                         mins = int(parts[0])
#                         secs = float(parts[1])
#                         ms = int((mins * 60 + secs) * 1000)
#                         lines.append((ms, text))
#                 except Exception:
#                     pass
#         return sorted(lines, key=lambda x: x[0])


# # ── Spinning Vinyl Widget ─────────────────────────────────────────────────────
# class VinylWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.angle = 0.0
#         self.spinning = False
#         self.target_speed = 0.0
#         self.current_speed = 0.0
#         self.album_pixmap = None
#         self.setFixedSize(280, 280)

#         self._timer = QTimer(self)
#         self._timer.timeout.connect(self._tick)
#         # Timer starts only when spinning begins

#     def set_album_art(self, pixmap):
#         self.album_pixmap = pixmap
#         self.update()

#     def set_spinning(self, on):
#         self.spinning = on
#         self.target_speed = 1.8 if on else 0.0
#         if on:
#             self._timer.start(16)

#     def _tick(self):
#         diff = self.target_speed - self.current_speed
#         self.current_speed += diff * 0.05
#         if not self.spinning and self.current_speed < 0.01:
#             self.current_speed = 0.0
#             self._timer.stop()
#             self.update()
#             return
#         self.angle = (self.angle + self.current_speed) % 360
#         self.update()

#     def paintEvent(self, event):
#         p = QPainter(self)
#         p.setRenderHint(QPainter.RenderHint.Antialiasing)

#         cx, cy = self.width() / 2, self.height() / 2
#         r = min(cx, cy) - 8

#         p.save()
#         p.translate(cx, cy)
#         p.rotate(self.angle)

#         # Outer vinyl body
#         pen = QPen(QColor("#1a1a1a"), 1)
#         p.setPen(pen)
#         p.setBrush(QBrush(QColor("#111111")))
#         p.drawEllipse(QRectF(-r, -r, r*2, r*2))

#         # Groove rings
#         for i in range(30, int(r)-2, 6):
#             alpha = int(40 - i * 0.3)
#             alpha = max(4, alpha)
#             groove_color = QColor(255, 255, 255, alpha)
#             if i % 18 == 0:
#                 groove_color = QColor(192, 57, 43, 60)
#                 p.setPen(QPen(groove_color, 0.8))
#             else:
#                 p.setPen(QPen(groove_color, 0.4))
#             p.setBrush(Qt.BrushStyle.NoBrush)
#             p.drawEllipse(QRectF(-i, -i, i*2, i*2))

#         # Center label circle
#         label_r = r * 0.30
#         if self.album_pixmap:
#             p.setClipRect(QRectF(-label_r, -label_r, label_r*2, label_r*2))
#             clip_path = QPainterPath()
#             clip_path.addEllipse(QRectF(-label_r, -label_r, label_r*2, label_r*2))
#             p.setClipPath(clip_path)
#             scaled = self.album_pixmap.scaled(
#                 int(label_r*2), int(label_r*2),
#                 Qt.AspectRatioMode.KeepAspectRatioByExpanding,
#                 Qt.TransformationMode.SmoothTransformation
#             )
#             p.drawPixmap(int(-label_r), int(-label_r), scaled)
#             p.setClipping(False)
#         else:
#             p.setBrush(QBrush(QColor("#1a0808")))
#             p.setPen(QPen(QColor("#2a0808"), 1))
#             p.drawEllipse(QRectF(-label_r, -label_r, label_r*2, label_r*2))

#         # Specular highlight arc
#         p.setBrush(Qt.BrushStyle.NoBrush)
#         p.setPen(QPen(QColor(255, 255, 255, 18), 3))
#         p.drawArc(QRectF(-r+4, -r+4, (r-4)*2, (r-4)*2), 30*16, 80*16)

#         # Center spindle hole
#         p.setBrush(QBrush(QColor("#0a0a0a")))
#         p.setPen(Qt.PenStyle.NoPen)
#         p.drawEllipse(QRectF(-5, -5, 10, 10))

#         p.restore()

#         # Outer glow ring (static, not rotated)
#         glow = QPen(QColor(192, 57, 43, 30), 3)
#         p.setPen(glow)
#         p.setBrush(Qt.BrushStyle.NoBrush)
#         p.drawEllipse(QRectF(cx-r-1, cy-r-1, (r+1)*2, (r+1)*2))


# # ── Waveform Widget ───────────────────────────────────────────────────────────
# class WaveformWidget(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.setFixedHeight(36)
#         self.progress = 0.0  # 0.0 to 1.0
#         self.bars = self._generate_bars()
#         self._anim_offset = 0
#         t = QTimer(self)
#         t.timeout.connect(self._tick)
#         t.start(80)

#     def _generate_bars(self):
#         import random
#         random.seed(42)
#         pattern = []
#         for _ in range(60):
#             h = random.randint(4, 28)
#             pattern.append(h)
#         return pattern

#     def set_progress(self, p):
#         self.progress = p
#         self.update()

#     def _tick(self):
#         self._anim_offset = (self._anim_offset + 1) % len(self.bars)
#         self.update()

#     def paintEvent(self, e):
#         p = QPainter(self)
#         p.setRenderHint(QPainter.RenderHint.Antialiasing)
#         w, h = self.width(), self.height()
#         bar_w = 3
#         gap = 2
#         total = bar_w + gap
#         count = w // total

#         for i in range(count):
#             idx = (i + self._anim_offset) % len(self.bars)
#             bh = self.bars[idx]
#             x = i * total
#             y = (h - bh) // 2
#             frac = i / count
#             if frac < self.progress:
#                 color = RED if frac > self.progress - 0.05 else QColor(139, 30, 20)
#             else:
#                 color = QColor(30, 30, 30)
#             p.setBrush(QBrush(color))
#             p.setPen(Qt.PenStyle.NoPen)
#             p.drawRoundedRect(x, y, bar_w, bh, 1.5, 1.5)


# # ── Lyrics Display ────────────────────────────────────────────────────────────
# class LyricsDisplay(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.lines = []        # list of (ms, text)
#         self.current_idx = -1
#         self._layout = QVBoxLayout(self)
#         self._layout.setContentsMargins(32, 24, 32, 24)
#         self._layout.setSpacing(0)
#         self._layout.addStretch()
#         self._labels = []
#         self.setStyleSheet("background: transparent;")
#         self._placeholder()

#     def _placeholder(self):
#         self._clear_labels()
#         lbl = QLabel("Open a song to see lyrics")
#         lbl.setStyleSheet("color: #333; font-size: 14px; letter-spacing: 2px;")
#         lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
#         self._layout.addWidget(lbl)
#         self._layout.addStretch()
#         self._labels.append(lbl)

#     def _clear_labels(self):
#         for lbl in self._labels:
#             self._layout.removeWidget(lbl)
#             lbl.deleteLater()
#         self._labels.clear()
#         # remove stretches
#         while self._layout.count():
#             item = self._layout.takeAt(0)
#             if item.widget():
#                 item.widget().deleteLater()

#     def set_lines(self, lines):
#         self.lines = lines
#         self.current_idx = -1
#         self._rebuild(-1)

#     def update_position(self, ms):
#         if not self.lines:
#             return
#         idx = 0
#         for i, (t, _) in enumerate(self.lines):
#             if t <= ms:
#                 idx = i
#             else:
#                 break
#         if idx != self.current_idx:
#             self.current_idx = idx
#             self._rebuild(idx)

#     def _rebuild(self, active):
#         self._clear_labels()
#         if not self.lines:
#             self._placeholder()
#             return

#         self._layout.addStretch(2)

#         # Show window: 2 past, active, 4 upcoming
#         start = max(0, active - 2)
#         end = min(len(self.lines), active + 5)

#         for i in range(start, end):
#             _, text = self.lines[i]
#             if not text.strip():
#                 continue
#             lbl = QLabel(text)
#             lbl.setWordWrap(True)

#             dist = i - active
#             if dist < 0:
#                 # past
#                 opacity = max(0.08, 0.2 + dist * 0.06)
#                 lbl.setStyleSheet(f"""
#                     color: rgba(255,255,255,{int(opacity*255)});
#                     font-size: 12px;
#                     font-weight: 400;
#                     letter-spacing: 0.5px;
#                     padding: 3px 0;
#                 """)
#             elif dist == 0:
#                 # active - BIG
#                 lbl.setStyleSheet("""
#                     color: #ffffff;
#                     font-size: 30px;
#                     font-weight: 700;
#                     letter-spacing: -0.5px;
#                     padding: 8px 0 12px 0;
#                     line-height: 1.2;
#                 """)
#             elif dist == 1:
#                 lbl.setStyleSheet("""
#                     color: #555555;
#                     font-size: 16px;
#                     font-weight: 500;
#                     padding: 4px 0;
#                 """)
#             elif dist == 2:
#                 lbl.setStyleSheet("""
#                     color: #333333;
#                     font-size: 13px;
#                     font-weight: 400;
#                     padding: 3px 0;
#                 """)
#             else:
#                 lbl.setStyleSheet("""
#                     color: #222222;
#                     font-size: 11px;
#                     font-weight: 400;
#                     padding: 2px 0;
#                 """)

#             self._layout.addWidget(lbl)
#             self._labels.append(lbl)

#         self._layout.addStretch(3)


# # ── Sidebar ───────────────────────────────────────────────────────────────────
# class Sidebar(QWidget):
#     open_file = pyqtSignal()
#     play_pause = pyqtSignal()
#     seek = pyqtSignal(float)   # 0.0-1.0

#     def __init__(self):
#         super().__init__()
#         self.setFixedWidth(260)
#         self.setStyleSheet(f"background: {BG2.name()};")
#         self._playing = False
#         self._duration = 0
#         self._build()

#     def _build(self):
#         lay = QVBoxLayout(self)
#         lay.setContentsMargins(0, 0, 0, 0)
#         lay.setSpacing(0)

#         # Logo
#         logo = QLabel("LYRICA")
#         logo.setStyleSheet("color:#1e1e1e; font-size:10px; letter-spacing:4px; padding:20px 20px 12px;")
#         lay.addWidget(logo)

#         # Vinyl
#         self.vinyl = VinylWidget()
#         vbox = QVBoxLayout()
#         vbox.setContentsMargins(16, 0, 16, 0)
#         vbox.addWidget(self.vinyl, alignment=Qt.AlignmentFlag.AlignCenter)
#         lay.addLayout(vbox)

#         # Song info
#         self.title_lbl = QLabel("No song loaded")
#         self.title_lbl.setStyleSheet("color:#fff;font-size:13px;font-weight:700;padding:12px 20px 2px;")
#         self.title_lbl.setWordWrap(True)
#         self.artist_lbl = QLabel("Open a file to start")
#         self.artist_lbl.setStyleSheet("color:#444;font-size:10px;letter-spacing:1px;padding:0 20px 10px;")
#         lay.addWidget(self.title_lbl)
#         lay.addWidget(self.artist_lbl)

#         # Progress
#         prog_wrap = QWidget()
#         prog_wrap.setStyleSheet("background:transparent;")
#         pl = QVBoxLayout(prog_wrap)
#         pl.setContentsMargins(20, 0, 20, 8)
#         pl.setSpacing(4)
#         self.progress_slider = QSlider(Qt.Orientation.Horizontal)
#         self.progress_slider.setRange(0, 1000)
#         self.progress_slider.setStyleSheet("""
#             QSlider::groove:horizontal {
#                 height: 2px; background: #1e1e1e; border-radius: 1px;
#             }
#             QSlider::sub-page:horizontal {
#                 background: #c0392b; border-radius: 1px;
#             }
#             QSlider::handle:horizontal {
#                 width: 10px; height: 10px; margin: -4px 0;
#                 background: #e74c3c; border-radius: 5px;
#             }
#         """)
#         self.progress_slider.sliderMoved.connect(lambda v: self.seek.emit(v / 1000))
#         pl.addWidget(self.progress_slider)
#         time_row = QHBoxLayout()
#         self.time_cur = QLabel("0:00")
#         self.time_dur = QLabel("0:00")
#         for t in [self.time_cur, self.time_dur]:
#             t.setStyleSheet("color:#333;font-size:10px;")
#         time_row.addWidget(self.time_cur)
#         time_row.addStretch()
#         time_row.addWidget(self.time_dur)
#         pl.addLayout(time_row)
#         lay.addWidget(prog_wrap)

#         # Controls
#         ctrl = QHBoxLayout()
#         ctrl.setContentsMargins(20, 0, 20, 16)
#         ctrl.setSpacing(0)

#         open_btn = self._icon_btn("ti-folder-open", self.open_file.emit, size=18)
#         self.play_btn = QPushButton("▶")
#         self.play_btn.setFixedSize(44, 44)
#         self.play_btn.setStyleSheet("""
#             QPushButton {
#                 background: #150808;
#                 border: 1px solid #2a0808;
#                 border-radius: 22px;
#                 color: #e74c3c;
#                 font-size: 16px;
#             }
#             QPushButton:hover { background: #1e0a0a; border-color: #c0392b; }
#         """)
#         self.play_btn.clicked.connect(self.play_pause.emit)
#         ctrl.addWidget(open_btn)
#         ctrl.addStretch()
#         ctrl.addWidget(self.play_btn)
#         ctrl.addStretch()
#         lay.addLayout(ctrl)

#         # Divider
#         div = QFrame()
#         div.setFrameShape(QFrame.Shape.HLine)
#         div.setStyleSheet("color:#1a1a1a;")
#         lay.addWidget(div)

#         # Nav
#         for label, icon in [("Now playing","ti-music"),("Library","ti-list"),("Favourites","ti-heart"),("Settings","ti-settings")]:
#             btn = self._nav_btn(label, icon, label=="Now playing")
#             lay.addWidget(btn)

#         lay.addStretch()

#         # Version tag
#         ver = QLabel("v1.0  ·  lrclib powered")
#         ver.setStyleSheet("color:#1e1e1e;font-size:9px;letter-spacing:1px;padding:8px 20px;")
#         lay.addWidget(ver)

#     def _icon_btn(self, icon_cls, cb, size=16, accent=False):
#         btn = QPushButton()
#         btn.setFixedSize(38, 38)
#         if accent:
#             btn.setStyleSheet(f"""
#                 QPushButton {{
#                     background: #150808;
#                     border: 1px solid #2a0808;
#                     border-radius: 19px;
#                     color: #e74c3c;
#                     font-family: 'tabler-icons';
#                     font-size: {size}px;
#                 }}
#                 QPushButton:hover {{ background: #1e0a0a; }}
#             """)
#         else:
#             btn.setStyleSheet(f"""
#                 QPushButton {{
#                     background: transparent;
#                     border: none;
#                     color: #444;
#                     font-family: 'tabler-icons';
#                     font-size: {size}px;
#                     border-radius: 6px;
#                 }}
#                 QPushButton:hover {{ color: #888; }}
#             """)
#         btn.clicked.connect(cb)
#         return btn

#     def _nav_btn(self, label, icon_cls, active=False):
#         btn = QPushButton(f"  {label}")
#         btn.setFixedHeight(36)
#         c = "#e74c3c" if active else "#333"
#         bg = "#150808" if active else "transparent"
#         btn.setStyleSheet(f"""
#             QPushButton {{
#                 background: {bg};
#                 border: none;
#                 color: {c};
#                 font-size: 12px;
#                 text-align: left;
#                 padding-left: 20px;
#             }}
#             QPushButton:hover {{ color: #888; background: #111; }}
#         """)
#         return btn

#     def set_track(self, title, artist, pixmap=None):
#         self.title_lbl.setText(title)
#         self.artist_lbl.setText(artist.upper())
#         if pixmap:
#             self.vinyl.set_album_art(pixmap)
#         else:
#             self.vinyl.set_album_art(None)

#     def set_playing(self, on):
#         self._playing = on
#         self.vinyl.set_spinning(on)
#         self.play_btn.setText("⏸" if on else "▶")

#     def set_position(self, ms, duration_ms):
#         self._duration = duration_ms
#         if duration_ms > 0:
#             frac = ms / duration_ms
#             self.progress_slider.setValue(int(frac * 1000))
#             self.time_cur.setText(self._fmt(ms))
#             self.time_dur.setText(self._fmt(duration_ms))

#     def _fmt(self, ms):
#         s = ms // 1000
#         return f"{s//60}:{s%60:02d}"


# # ── Main Window ───────────────────────────────────────────────────────────────
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Lyrica")
#         self.setMinimumSize(900, 620)
#         self.resize(1100, 680)
#         self._file_path = None
#         self._lyrics = []
#         self._position_ms = 0
#         self._duration_ms = 0
#         self._playing = False
#         self._fetcher = None

#         self._build_ui()
#         self._setup_timer()
#         self._apply_global_style()

#     def _apply_global_style(self):
#         self.setStyleSheet(f"""
#             QMainWindow, QWidget {{ background: {BG.name()}; }}
#             QScrollBar:vertical {{
#                 background: #0f0f0f; width: 4px; border-radius: 2px;
#             }}
#             QScrollBar::handle:vertical {{
#                 background: #2a2a2a; border-radius: 2px;
#             }}
#             QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
#         """)

#     def _build_ui(self):
#         central = QWidget()
#         self.setCentralWidget(central)
#         root = QHBoxLayout(central)
#         root.setContentsMargins(0, 0, 0, 0)
#         root.setSpacing(0)

#         # Sidebar
#         self.sidebar = Sidebar()
#         self.sidebar.open_file.connect(self._open_file)
#         self.sidebar.play_pause.connect(self._toggle_play)
#         self.sidebar.seek.connect(self._seek)
#         root.addWidget(self.sidebar)

#         # Red accent stripe
#         stripe = QFrame()
#         stripe.setFixedWidth(2)
#         stripe.setStyleSheet("background: #c0392b;")
#         root.addWidget(stripe)

#         # Right panel
#         right = QWidget()
#         right.setStyleSheet(f"background: {BG.name()};")
#         rl = QVBoxLayout(right)
#         rl.setContentsMargins(0, 0, 0, 0)
#         rl.setSpacing(0)

#         # Top bar
#         topbar = QWidget()
#         topbar.setFixedHeight(50)
#         topbar.setStyleSheet(f"background: {BG.name()}; border-bottom: 1px solid #111;")
#         tbl = QHBoxLayout(topbar)
#         tbl.setContentsMargins(28, 0, 28, 0)

#         self.status_lbl = QLabel("Open a song to begin")
#         self.status_lbl.setStyleSheet("color:#333;font-size:11px;letter-spacing:2px;")
#         tbl.addWidget(self.status_lbl)
#         tbl.addStretch()

#         # Pill tabs
#         for name in ["Lyrics", "Visualiser", "Info"]:
#             pill = QPushButton(name)
#             active = name == "Lyrics"
#             pill.setStyleSheet(f"""
#                 QPushButton {{
#                     background: {'#150808' if active else 'transparent'};
#                     border: 1px solid {'#c0392b' if active else '#1e1e1e'};
#                     border-radius: 12px;
#                     color: {'#e74c3c' if active else '#333'};
#                     font-size: 10px;
#                     letter-spacing: 1px;
#                     padding: 4px 12px;
#                     margin-left: 6px;
#                 }}
#                 QPushButton:hover {{ color: #888; }}
#             """)
#             tbl.addWidget(pill)

#         rl.addWidget(topbar)

#         # Lyrics scroll area
#         scroll = QScrollArea()
#         scroll.setWidgetResizable(True)
#         scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
#         scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
#         scroll.setStyleSheet("background: transparent; border: none;")

#         self.lyrics = LyricsDisplay()
#         self.lyrics.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
#         scroll.setWidget(self.lyrics)
#         rl.addWidget(scroll, 1)

#         # Waveform bottom bar
#         bottom = QWidget()
#         bottom.setFixedHeight(52)
#         bottom.setStyleSheet(f"background:{BG.name()}; border-top: 1px solid #111;")
#         bl = QHBoxLayout(bottom)
#         bl.setContentsMargins(28, 0, 28, 0)
#         bl.setSpacing(16)

#         self.waveform = WaveformWidget()
#         bl.addWidget(self.waveform, 1)

#         for tag, hot in [("BPM",""), ("Pop","hot"), ("Live","")]:
#             t = QLabel(tag)
#             c = "#c0392b" if hot else "#2a2a2a"
#             bc = "#4a1010" if hot else "#1a1a1a"
#             t.setStyleSheet(f"color:{c};font-size:9px;letter-spacing:1px;border:1px solid {bc};border-radius:4px;padding:2px 8px;")
#             bl.addWidget(t)

#         rl.addWidget(bottom)
#         root.addWidget(right, 1)

#     def _setup_timer(self):
#         self._timer = QTimer(self)
#         self._timer.timeout.connect(self._tick)
#         self._timer.start(250)

#     def _tick(self):
#         if not PYGAME_OK or not self._playing:
#             return
#         try:
#             pos = pygame.mixer.music.get_pos()
#             if pos >= 0:
#                 self._position_ms = pos
#                 self.sidebar.set_position(pos, self._duration_ms)
#                 self.lyrics.update_position(pos)
#                 self.waveform.set_progress(pos / max(self._duration_ms, 1))
#         except Exception:
#             pass

#     def _open_file(self):
#         path, _ = QFileDialog.getOpenFileName(
#             self, "Open Audio File", "",
#             "Audio Files (*.mp3 *.flac *.wav *.ogg)"
#         )
#         if not path:
#             return
#         self._file_path = path
#         self._load_file(path)

#     def _load_file(self, path):
#         title = Path(path).stem
#         artist = "Unknown Artist"
#         pixmap = None
#         duration_ms = 0

#         if MUTAGEN_OK:
#             try:
#                 if path.lower().endswith(".mp3"):
#                     audio = MP3(path)
#                     duration_ms = int(audio.info.length * 1000)
#                     tags = ID3(path)
#                     if "TIT2" in tags:
#                         title = str(tags["TIT2"])
#                     if "TPE1" in tags:
#                         artist = str(tags["TPE1"])
#                     for key in tags.keys():
#                         if key.startswith("APIC"):
#                             apic = tags[key]
#                             img = QImage.fromData(apic.data)
#                             pixmap = QPixmap.fromImage(img)
#                             break
#                 elif path.lower().endswith(".flac"):
#                     audio = FLAC(path)
#                     duration_ms = int(audio.info.length * 1000)
#                     if audio.get("title"):
#                         title = audio["title"][0]
#                     if audio.get("artist"):
#                         artist = audio["artist"][0]
#             except Exception:
#                 pass

#         self._duration_ms = duration_ms
#         self.sidebar.set_track(title, artist, pixmap)
#         self.status_lbl.setText(f"{title}  ·  {artist}")

#         if PYGAME_OK:
#             try:
#                 pygame.mixer.music.load(path)
#                 pygame.mixer.music.play()
#                 self._playing = True
#                 self.sidebar.set_playing(True)
#             except Exception as e:
#                 self.status_lbl.setText(f"Playback error: {e}")

#         # Fetch lyrics
#         self.lyrics.set_lines([])
#         self.status_lbl.setText(f"Fetching lyrics for '{title}'...")
#         self._fetcher = LyricsFetcher(title, artist)
#         self._fetcher.done.connect(self._on_lyrics)
#         self._fetcher.error.connect(self._on_lyrics_error)
#         self._fetcher.start()

#     def _on_lyrics(self, lines):
#         self.lyrics.set_lines(lines)
#         self.status_lbl.setText(f"{Path(self._file_path).stem}  ·  {len(lines)} lines")

#     def _on_lyrics_error(self, msg):
#         self.status_lbl.setText(f"Lyrics: {msg}")

#     def _toggle_play(self):
#         if not PYGAME_OK or not self._file_path:
#             self._open_file()
#             return
#         try:
#             if self._playing:
#                 pygame.mixer.music.pause()
#                 self._playing = False
#                 self.sidebar.set_playing(False)
#             else:
#                 pygame.mixer.music.unpause()
#                 self._playing = True
#                 self.sidebar.set_playing(True)
#         except Exception:
#             pass

#     def _seek(self, frac):
#         if not PYGAME_OK or self._duration_ms == 0:
#             return
#         try:
#             secs = frac * self._duration_ms / 1000
#             pygame.mixer.music.play(start=secs)
#             self._position_ms = int(secs * 1000)
#         except Exception:
#             pass


# def main():
#     app = QApplication(sys.argv)
#     app.setApplicationName("Lyrica")

#     # Try to load Space Grotesk if available
#     font = QFont("Space Grotesk", 11)
#     if not font.exactMatch():
#         font = QFont("Segoe UI", 11)
#     app.setFont(font)

#     win = MainWindow()
#     win.show()
#     sys.exit(app.exec())


# if __name__ == "__main__":
#     main()
import sys, os, re as _re, math, random, json
from pathlib import Path

import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QSlider, QScrollArea, QFileDialog,
    QFrame, QSizePolicy, QStackedWidget, QListWidget, QListWidgetItem,
    QGraphicsBlurEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPainterPath,
    QPixmap, QImage, QLinearGradient, QRadialGradient
)

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen.flac import FLAC
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False

try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    PYGAME_OK = True
except ImportError:
    PYGAME_OK = False

# ── Theme ─────────────────────────────────────────────────────────────────────
T = {
    "bg":       "#0d0d14",
    "bg2":      "#12121c",
    "bg3":      "#1a1a28",
    "accent":   "#7c6af7",
    "accent2":  "#a594f9",
    "accent3":  "#4f3fd4",
    "text":     "#e8e8f0",
    "text2":    "#6b6b8a",
    "text3":    "#2e2e45",
    "border":   "#1e1e30",
}

SETTINGS_FILE = Path.home() / ".lyrica_settings.json"

# ── Helpers ───────────────────────────────────────────────────────────────────
def clean_title(title):
    patterns = [
        r'\s*\|.*$', r'\s*\(Official\s*(Video|Audio|Music Video|Lyric Video)[^)]*\)',
        r'\s*\[Official\s*(Video|Audio|Music Video)[^\]]*\]',
        r'\s*\(Lyrics?\)', r'\s*\[Lyrics?\]', r'\s*ft\..*$', r'\s*feat\..*$',
        r'\s*-\s*(Official|HD|HQ|4K|Audio|Video|Lyric).*$',
        r'\s*\(HD\)|\s*\[HD\]', r'\s*\d{4}\s*$',
        r'\s*Latest\s+Punjabi\s+Songs.*$', r'\s*New\s+Punjabi\s+Song.*$',
    ]
    t = title
    for p in patterns:
        t = _re.sub(p, '', t, flags=_re.IGNORECASE).strip()
    return _re.sub(r'\s{2,}', ' ', t).strip(' -|')

def clean_artist(artist):
    for sep in ['|', ',', '/', '&', ' x ', ' X ']:
        if sep in artist:
            artist = artist.split(sep)[0]
    return artist.strip()

def ms_to_str(ms):
    s = max(0, ms) // 1000
    return f"{s//60}:{s%60:02d}"

# ── Lyrics Fetcher ────────────────────────────────────────────────────────────
class LyricsFetcher(QThread):
    done  = pyqtSignal(list, str, str)   # lines, title, artist
    error = pyqtSignal(str)

    def __init__(self, title, artist):
        super().__init__()
        self.raw_title  = title
        self.raw_artist = artist
        self.title  = clean_title(title)
        self.artist = clean_artist(artist)

    def run(self):
        try:
            data = []
            for q in [f"{self.artist} {self.title}", self.title]:
                r = requests.get("https://lrclib.net/api/search",
                                 params={"q": q}, timeout=10)
                data = r.json()
                if data:
                    break
            if not data:
                self.error.emit("No lyrics found on lrclib")
                return
            entry = data[0]
            synced = entry.get("syncedLyrics") or ""
            if synced:
                lines = self._parse_lrc(synced)
            else:
                plain = entry.get("plainLyrics", "")
                lines = [(i*3000, l) for i,l in enumerate(plain.split("\n")) if l.strip()]
            self.done.emit(lines, self.title, self.artist)
        except Exception as e:
            self.error.emit(str(e))

    def _parse_lrc(self, lrc):
        lines = []
        for line in lrc.split("\n"):
            line = line.strip()
            if line.startswith("[") and "]" in line:
                try:
                    tag  = line[1:line.index("]")]
                    text = line[line.index("]")+1:].strip()
                    parts = tag.split(":")
                    if len(parts) == 2:
                        ms = int((int(parts[0])*60 + float(parts[1])) * 1000)
                        lines.append((ms, text))
                except Exception:
                    pass
        return sorted(lines, key=lambda x: x[0])

# ── Vinyl Widget ──────────────────────────────────────────────────────────────
class VinylWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.angle = 0.0
        self.target_speed = 0.0
        self.current_speed = 0.0
        self.album_pixmap = None
        self.setFixedSize(240, 240)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def set_album_art(self, px): self.album_pixmap = px; self.update()

    def set_spinning(self, on):
        self.target_speed = 1.6 if on else 0.0
        if on: self._timer.start(16)

    def _tick(self):
        self.current_speed += (self.target_speed - self.current_speed) * 0.06
        if self.target_speed == 0 and self.current_speed < 0.01:
            self.current_speed = 0.0
            self._timer.stop()
        self.angle = (self.angle + self.current_speed) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width()/2, self.height()/2
        r = min(cx, cy) - 6
        p.save(); p.translate(cx, cy); p.rotate(self.angle)

        # Body
        p.setBrush(QBrush(QColor("#0e0e1a"))); p.setPen(QPen(QColor("#1e1e30"), 1))
        p.drawEllipse(QRectF(-r,-r,r*2,r*2))

        # Grooves
        for i in range(28, int(r)-2, 5):
            if i % 15 == 0:
                p.setPen(QPen(QColor(124,106,247, 55), 0.8))
            else:
                p.setPen(QPen(QColor(255,255,255, 8), 0.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(-i,-i,i*2,i*2))

        # Center label
        lr = r * 0.32
        if self.album_pixmap:
            path = QPainterPath()
            path.addEllipse(QRectF(-lr,-lr,lr*2,lr*2))
            p.setClipPath(path)
            sc = self.album_pixmap.scaled(int(lr*2),int(lr*2),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            p.drawPixmap(int(-lr),int(-lr),sc)
            p.setClipping(False)
        else:
            p.setBrush(QBrush(QColor("#1a1a2e"))); p.setPen(QPen(QColor("#2a2a45"),1))
            p.drawEllipse(QRectF(-lr,-lr,lr*2,lr*2))

        # Highlight
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255,255,255,14),3))
        p.drawArc(QRectF(-r+4,-r+4,(r-4)*2,(r-4)*2), 20*16, 90*16)

        # Spindle
        p.setBrush(QBrush(QColor("#0d0d14"))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(-4,-4,8,8))
        p.restore()

        # Static outer ring
        p.setPen(QPen(QColor(124,106,247,25),2)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx-r-1,cy-r-1,(r+1)*2,(r+1)*2))

# ── Visualiser Widget ─────────────────────────────────────────────────────────
class VisualiserWidget(QWidget):
    def __init__(self):
        super().__init__()
        random.seed(99)
        self._bars  = [random.uniform(0.05, 0.9) for _ in range(64)]
        self._phase = 0.0
        self._playing = False
        self._t = QTimer(self); self._t.timeout.connect(self._tick); self._t.start(40)

    def set_playing(self, on): self._playing = on

    def _tick(self):
        if self._playing:
            self._phase += 0.08
            for i in range(len(self._bars)):
                target = abs(math.sin(self._phase + i*0.4)) * random.uniform(0.3,1.0)
                self._bars[i] += (target - self._bars[i]) * 0.18
        else:
            for i in range(len(self._bars)):
                self._bars[i] *= 0.92
        self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        n = len(self._bars)
        bar_w = max(2, w // n - 2)
        gap   = max(1, (w - n*bar_w) // (n+1))
        cx    = w / 2

        for i, v in enumerate(self._bars):
            bh   = max(2, int(v * h * 0.85))
            x    = gap + i * (bar_w + gap)
            y    = (h - bh) // 2
            dist = abs(x + bar_w/2 - cx) / (w/2)
            alpha = int(220 - dist * 120)
            r2 = int(124 + (165-124)*v)
            g2 = int(106 + (100-106)*v)
            b2 = int(247 + (200-247)*v)
            p.setBrush(QBrush(QColor(r2, g2, b2, alpha)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x, y, bar_w, bh, bar_w//2, bar_w//2)

# ── Waveform Bar ──────────────────────────────────────────────────────────────
class WaveformWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(32)
        random.seed(42)
        self._bars    = [random.randint(3,26) for _ in range(80)]
        self._offset  = 0
        self._progress = 0.0
        self._playing  = False
        t = QTimer(self); t.timeout.connect(self._tick); t.start(70)

    def set_progress(self, v): self._progress = v; self.update()
    def set_playing(self, on): self._playing = on

    def _tick(self):
        if self._playing:
            self._offset = (self._offset+1) % len(self._bars)
            self.update()

    def paintEvent(self, _):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bw, gap = 3, 2
        total = bw+gap
        count = w//total
        for i in range(count):
            idx = (i+self._offset) % len(self._bars)
            bh  = self._bars[idx]
            x   = i*total; y = (h-bh)//2
            frac = i/count
            if frac < self._progress:
                c = QColor(124,106,247) if frac > self._progress-0.05 else QColor(70,55,160)
            else:
                c = QColor(30,30,50)
            p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(x,y,bw,bh,1.5,1.5)

# ── Lyrics Display ────────────────────────────────────────────────────────────
class LyricsDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.current_idx = -1
        self.setStyleSheet("background:transparent;")
        self._lo = QVBoxLayout(self)
        self._lo.setContentsMargins(40,24,40,24)
        self._lo.setSpacing(0)
        self._labels = []
        self._show_placeholder()

    def _show_placeholder(self):
        self._clear()
        lbl = QLabel("open a song to see lyrics")
        lbl.setStyleSheet(f"color:{T['text3']};font-size:13px;letter-spacing:3px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lo.addStretch(1); self._lo.addWidget(lbl); self._lo.addStretch(1)
        self._labels.append(lbl)

    def _clear(self):
        while self._lo.count():
            item = self._lo.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._labels.clear()

    def set_lines(self, lines):
        self.lines = lines
        self.current_idx = -1
        self._rebuild(-1)

    def update_position(self, ms):
        if not self.lines: return
        idx = 0
        for i,(t,_) in enumerate(self.lines):
            if t <= ms: idx = i
            else: break
        if idx != self.current_idx:
            self.current_idx = idx
            self._rebuild(idx)

    def _rebuild(self, active):
        self._clear()
        if not self.lines:
            self._show_placeholder(); return

        self._lo.addStretch(3)
        start = max(0, active-3)
        end   = min(len(self.lines), active+6)

        for i in range(start, end):
            _, text = self.lines[i]
            if not text.strip(): continue
            d = i - active
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            if d < 0:
                op = max(0.06, 0.18 + d*0.05)
                lbl.setStyleSheet(f"color:rgba(232,232,240,{int(op*255)});font-size:12px;padding:2px 0;")
            elif d == 0:
                lbl.setStyleSheet(f"color:{T['text']};font-size:32px;font-weight:700;letter-spacing:-0.5px;padding:10px 0 14px;")
            elif d == 1:
                lbl.setStyleSheet(f"color:{T['accent2']};font-size:17px;font-weight:500;padding:4px 0;")
            elif d == 2:
                lbl.setStyleSheet(f"color:{T['text2']};font-size:13px;padding:3px 0;")
            else:
                lbl.setStyleSheet(f"color:{T['text3']};font-size:11px;padding:2px 0;")
            self._lo.addWidget(lbl)
            self._labels.append(lbl)
        self._lo.addStretch(4)

# ── Info Panel ────────────────────────────────────────────────────────────────
class InfoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        lo = QVBoxLayout(self)
        lo.setContentsMargins(40,40,40,40); lo.setSpacing(16)

        lo.addStretch(1)
        self._art = QLabel(); self._art.setFixedSize(180,180)
        self._art.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._art.setStyleSheet(f"background:{T['bg3']};border-radius:12px;")
        lo.addWidget(self._art, alignment=Qt.AlignmentFlag.AlignCenter)

        for attr in ["_title","_artist","_album","_duration","_file"]:
            lbl = QLabel("—")
            lbl.setWordWrap(True)
            setattr(self, attr, lbl)
            lo.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self._title.setStyleSheet(f"color:{T['text']};font-size:20px;font-weight:700;")
        self._artist.setStyleSheet(f"color:{T['accent2']};font-size:14px;")
        self._album.setStyleSheet(f"color:{T['text2']};font-size:12px;")
        self._duration.setStyleSheet(f"color:{T['text2']};font-size:11px;letter-spacing:1px;")
        self._file.setStyleSheet(f"color:{T['text3']};font-size:10px;")
        lo.addStretch(1)

    def update_info(self, title, artist, album, dur_ms, path, pixmap):
        self._title.setText(title)
        self._artist.setText(artist)
        self._album.setText(album or "Unknown Album")
        self._duration.setText(ms_to_str(dur_ms))
        self._file.setText(str(Path(path).name) if path else "")
        if pixmap:
            self._art.setPixmap(pixmap.scaled(180,180,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation))
        else:
            self._art.clear()
            self._art.setText("No Art")

# ── Library Panel ─────────────────────────────────────────────────────────────
class LibraryPanel(QWidget):
    play_track = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        lo = QVBoxLayout(self)
        lo.setContentsMargins(24,24,24,24); lo.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("Library")
        title.setStyleSheet(f"color:{T['text']};font-size:16px;font-weight:700;")
        top.addWidget(title); top.addStretch()
        add_btn = QPushButton("+ Add Folder")
        add_btn.setStyleSheet(f"""
            QPushButton{{background:{T['bg3']};border:1px solid {T['border']};
            border-radius:8px;color:{T['accent2']};font-size:11px;padding:6px 14px;}}
            QPushButton:hover{{background:{T['accent3']};color:white;}}""")
        add_btn.clicked.connect(self._add_folder)
        top.addWidget(add_btn)
        lo.addLayout(top)

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget{{background:{T['bg2']};border:1px solid {T['border']};
            border-radius:10px;color:{T['text']};font-size:13px;outline:none;}}
            QListWidget::item{{padding:10px 16px;border-bottom:1px solid {T['border']};}}
            QListWidget::item:selected{{background:{T['accent3']};color:white;border-radius:6px;}}
            QListWidget::item:hover{{background:{T['bg3']};}}""")
        self._list.itemDoubleClicked.connect(lambda item: self.play_track.emit(item.data(Qt.ItemDataRole.UserRole)))
        lo.addWidget(self._list)

        hint = QLabel("double-click a track to play")
        hint.setStyleSheet(f"color:{T['text3']};font-size:10px;letter-spacing:1px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(hint)

        self._tracks = []
        self._load_settings()

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder: return
        exts = {'.mp3','.flac','.wav','.ogg','.m4a'}
        new = [str(p) for p in Path(folder).rglob("*") if p.suffix.lower() in exts]
        added = 0
        for f in new:
            if f not in self._tracks:
                self._tracks.append(f); added += 1
        self._refresh_list()
        self._save_settings()

    def _refresh_list(self):
        self._list.clear()
        for path in self._tracks:
            item = QListWidgetItem(Path(path).stem)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self._list.addItem(item)

    def add_track(self, path):
        if path not in self._tracks:
            self._tracks.append(path)
            self._refresh_list()
            self._save_settings()

    def _save_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text()) if SETTINGS_FILE.exists() else {}
            data["library"] = self._tracks
            SETTINGS_FILE.write_text(json.dumps(data, indent=2))
        except Exception: pass

    def _load_settings(self):
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text())
                self._tracks = data.get("library", [])
                self._refresh_list()
        except Exception: pass

# ── Settings Panel ────────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background:transparent;")
        lo = QVBoxLayout(self)
        lo.setContentsMargins(40,32,40,32); lo.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet(f"color:{T['text']};font-size:18px;font-weight:700;")
        lo.addWidget(title)

        self._settings = {}
        options = [
            ("Sync offset (ms)", "offset", "0",
             "Adjust if lyrics feel early (negative) or late (positive)"),
            ("Default search artist", "def_artist", "",
             "Prefill artist for better lyric matching"),
        ]
        for label, key, default, hint in options:
            lo.addWidget(self._section(label, key, default, hint))

        # Theme toggle row
        row = QWidget()
        row.setStyleSheet(f"background:{T['bg2']};border-radius:10px;")
        rl = QHBoxLayout(row); rl.setContentsMargins(16,14,16,14)
        lbl = QLabel("Compact sidebar")
        lbl.setStyleSheet(f"color:{T['text']};font-size:13px;")
        rl.addWidget(lbl); rl.addStretch()
        self._compact_btn = QPushButton("OFF")
        self._compact_btn.setFixedSize(52,26)
        self._compact_btn.setStyleSheet(f"""QPushButton{{background:{T['bg3']};border:1px solid {T['border']};
            border-radius:13px;color:{T['text2']};font-size:10px;}}
            QPushButton:hover{{background:{T['accent3']};color:white;}}""")
        rl.addWidget(self._compact_btn)
        lo.addWidget(row)

        lo.addStretch()
        ver = QLabel("Lyrica v1.0  ·  lrclib.net  ·  PyQt6")
        ver.setStyleSheet(f"color:{T['text3']};font-size:10px;letter-spacing:1px;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(ver)
        self._load()

    def _section(self, label, key, default, hint):
        w = QWidget(); w.setStyleSheet(f"background:{T['bg2']};border-radius:10px;")
        lo = QVBoxLayout(w); lo.setContentsMargins(16,12,16,12); lo.setSpacing(6)
        lbl = QLabel(label); lbl.setStyleSheet(f"color:{T['text']};font-size:13px;")
        inp = QPushButton(default)
        inp.setStyleSheet(f"""QPushButton{{background:{T['bg3']};border:1px solid {T['border']};
            border-radius:6px;color:{T['text']};font-size:12px;padding:6px 12px;text-align:left;}}""")
        h = QLabel(hint); h.setStyleSheet(f"color:{T['text2']};font-size:10px;")
        lo.addWidget(lbl); lo.addWidget(inp); lo.addWidget(h)
        self._settings[key] = inp
        return w

    def get_offset(self):
        try: return int(self._settings["offset"].text())
        except: return 0

    def _save(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text()) if SETTINGS_FILE.exists() else {}
            data["offset"] = self._settings["offset"].text()
            SETTINGS_FILE.write_text(json.dumps(data, indent=2))
        except Exception: pass

    def _load(self):
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text())
                if "offset" in data:
                    self._settings["offset"].setText(str(data["offset"]))
        except Exception: pass

# ── Sidebar ───────────────────────────────────────────────────────────────────
class Sidebar(QWidget):
    open_file  = pyqtSignal()
    play_pause = pyqtSignal()
    seek       = pyqtSignal(float)
    prev_track = pyqtSignal()
    next_track = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(260)
        self.setStyleSheet(f"background:{T['bg2']};")
        self._playing = False
        self._build()

    def _build(self):
        lo = QVBoxLayout(self); lo.setContentsMargins(0,0,0,0); lo.setSpacing(0)

        logo = QLabel("LYRICA")
        logo.setStyleSheet(f"color:{T['text3']};font-size:9px;letter-spacing:5px;padding:18px 20px 10px;")
        lo.addWidget(logo)

        # Vinyl
        vbox = QVBoxLayout(); vbox.setContentsMargins(10,0,10,0)
        self.vinyl = VinylWidget()
        vbox.addWidget(self.vinyl, alignment=Qt.AlignmentFlag.AlignCenter)
        lo.addLayout(vbox)

        # Track info
        self.title_lbl = QLabel("No song loaded")
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setStyleSheet(f"color:{T['text']};font-size:13px;font-weight:700;padding:10px 18px 2px;")
        self.artist_lbl = QLabel("open a file to begin")
        self.artist_lbl.setStyleSheet(f"color:{T['text2']};font-size:10px;letter-spacing:1px;padding:0 18px 10px;")
        lo.addWidget(self.title_lbl); lo.addWidget(self.artist_lbl)

        # Progress
        pw = QWidget(); pw.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(pw); pl.setContentsMargins(18,0,18,8); pl.setSpacing(4)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0,1000)
        self.slider.setStyleSheet(f"""
            QSlider::groove:horizontal{{height:2px;background:{T['bg3']};border-radius:1px;}}
            QSlider::sub-page:horizontal{{background:{T['accent']};border-radius:1px;}}
            QSlider::handle:horizontal{{width:10px;height:10px;margin:-4px 0;
                background:{T['accent2']};border-radius:5px;}}""")
        self.slider.sliderMoved.connect(lambda v: self.seek.emit(v/1000))
        pl.addWidget(self.slider)
        tr = QHBoxLayout()
        self.time_cur = QLabel("0:00"); self.time_dur = QLabel("0:00")
        for t in [self.time_cur, self.time_dur]:
            t.setStyleSheet(f"color:{T['text3']};font-size:9px;")
        tr.addWidget(self.time_cur); tr.addStretch(); tr.addWidget(self.time_dur)
        pl.addLayout(tr)
        lo.addWidget(pw)

        # Controls
        ctrl = QHBoxLayout(); ctrl.setContentsMargins(18,0,18,14); ctrl.setSpacing(0)
        self._open_btn = self._btn("⊞", self.open_file.emit, 16)
        self._prev_btn = self._btn("⏮", self.prev_track.emit, 16)
        self.play_btn  = self._btn("▶", self.play_pause.emit, 18, accent=True)
        self._next_btn = self._btn("⏭", self.next_track.emit, 16)
        ctrl.addWidget(self._open_btn); ctrl.addStretch()
        ctrl.addWidget(self._prev_btn)
        ctrl.addWidget(self.play_btn)
        ctrl.addWidget(self._next_btn)
        ctrl.addStretch()
        lo.addLayout(ctrl)

        # Divider
        div = QFrame(); div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color:{T['border']};"); lo.addWidget(div)
        lo.addSpacing(4)

        # Nav
        self._nav_btns = {}
        for label in ["Now playing","Library","Visualiser","Info","Settings"]:
            btn = QPushButton(f"   {label}")
            btn.setFixedHeight(36)
            btn.setStyleSheet(self._nav_style(False))
            self._nav_btns[label] = btn
            lo.addWidget(btn)

        lo.addStretch()
        ver = QLabel("lrclib.net powered")
        ver.setStyleSheet(f"color:{T['text3']};font-size:9px;letter-spacing:1px;padding:8px 18px;")
        lo.addWidget(ver)

    def _btn(self, icon, cb, size=15, accent=False):
        btn = QPushButton(icon)
        btn.setFixedSize(38,38)
        if accent:
            btn.setStyleSheet(f"""QPushButton{{background:{T['bg3']};border:1px solid {T['border']};
                border-radius:19px;color:{T['accent2']};font-size:{size}px;}}
                QPushButton:hover{{background:{T['accent3']};color:white;border-color:{T['accent']};}}""")
        else:
            btn.setStyleSheet(f"""QPushButton{{background:transparent;border:none;
                color:{T['text2']};font-size:{size}px;border-radius:6px;}}
                QPushButton:hover{{color:{T['text']};}}""")
        btn.clicked.connect(cb)
        return btn

    def _nav_style(self, active):
        if active:
            return f"""QPushButton{{background:{T['bg3']};border:none;color:{T['accent2']};
                font-size:12px;text-align:left;padding-left:20px;border-left:2px solid {T['accent']};}}"""
        return f"""QPushButton{{background:transparent;border:none;color:{T['text2']};
            font-size:12px;text-align:left;padding-left:22px;}}
            QPushButton:hover{{color:{T['text']};background:{T['bg3']};}}"""

    def set_active_nav(self, label):
        for k, btn in self._nav_btns.items():
            btn.setStyleSheet(self._nav_style(k == label))

    def set_track(self, title, artist, pixmap=None):
        self.title_lbl.setText(title)
        self.artist_lbl.setText(artist.upper())
        self.vinyl.set_album_art(pixmap)

    def set_playing(self, on):
        self._playing = on
        self.vinyl.set_spinning(on)
        self.play_btn.setText("⏸" if on else "▶")

    def set_position(self, ms, dur):
        if dur > 0:
            self.slider.setValue(int(ms/dur*1000))
            self.time_cur.setText(ms_to_str(ms))
            self.time_dur.setText(ms_to_str(dur))

# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lyrica")
        self.setMinimumSize(860,580); self.resize(1080,660)
        self._file_path  = None
        self._lyrics     = []
        self._pos_ms     = 0
        self._dur_ms     = 0
        self._seek_base  = 0   # position when seek was done
        self._seek_time  = 0   # pygame time when seek was done
        self._playing    = False
        self._fetcher    = None
        self._info       = {"title":"","artist":"","album":"","pixmap":None}
        self._build(); self._setup_timer()
        self.setStyleSheet(f"""
            QMainWindow,QWidget{{background:{T['bg']};color:{T['text']};}}
            QScrollBar:vertical{{background:{T['bg2']};width:4px;border-radius:2px;}}
            QScrollBar::handle:vertical{{background:{T['border']};border-radius:2px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}""")

    def _build(self):
        c = QWidget(); self.setCentralWidget(c)
        root = QHBoxLayout(c); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.open_file.connect(self._open_file)
        self.sidebar.play_pause.connect(self._toggle_play)
        self.sidebar.seek.connect(self._seek)
        self.sidebar.prev_track.connect(self._prev)
        self.sidebar.next_track.connect(self._next)
        root.addWidget(self.sidebar)

        # Connect nav buttons
        panel_map = {
            "Now playing": 0, "Library": 1,
            "Visualiser": 2, "Info": 3, "Settings": 4
        }
        for label, idx in panel_map.items():
            self.sidebar._nav_btns[label].clicked.connect(
                lambda _, i=idx, l=label: self._switch_panel(i, l))

        # Stripe
        stripe = QFrame(); stripe.setFixedWidth(2)
        stripe.setStyleSheet(f"background:{T['accent3']};"); root.addWidget(stripe)

        # Right side
        right = QWidget(); right.setStyleSheet(f"background:{T['bg']};")
        rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0); rl.setSpacing(0)

        # Topbar
        top = QWidget(); top.setFixedHeight(48)
        top.setStyleSheet(f"background:{T['bg']};border-bottom:1px solid {T['border']};")
        tl = QHBoxLayout(top); tl.setContentsMargins(28,0,28,0)
        self.status_lbl = QLabel("open a song to begin")
        self.status_lbl.setStyleSheet(f"color:{T['text2']};font-size:11px;letter-spacing:1px;")
        tl.addWidget(self.status_lbl); tl.addStretch()
        rl.addWidget(top)

        # Stacked panels
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")

        # 0: Lyrics
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent;border:none;")
        self.lyrics_display = LyricsDisplay()
        scroll.setWidget(self.lyrics_display)
        self.stack.addWidget(scroll)

        # 1: Library
        self.library = LibraryPanel()
        self.library.play_track.connect(self._load_file)
        self.stack.addWidget(self.library)

        # 2: Visualiser
        vis_wrap = QWidget(); vis_wrap.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(vis_wrap); vl.setContentsMargins(32,32,32,32)
        lbl = QLabel("audio visualiser"); lbl.setStyleSheet(f"color:{T['text3']};font-size:10px;letter-spacing:2px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(lbl)
        self.visualiser = VisualiserWidget()
        vl.addWidget(self.visualiser, 1)
        self.stack.addWidget(vis_wrap)

        # 3: Info
        self.info_panel = InfoPanel()
        info_scroll = QScrollArea(); info_scroll.setWidgetResizable(True)
        info_scroll.setStyleSheet("background:transparent;border:none;")
        info_scroll.setWidget(self.info_panel)
        self.stack.addWidget(info_scroll)

        # 4: Settings
        self.settings_panel = SettingsPanel()
        self.stack.addWidget(self.settings_panel)

        rl.addWidget(self.stack, 1)

        # Bottom waveform bar
        bot = QWidget(); bot.setFixedHeight(50)
        bot.setStyleSheet(f"background:{T['bg']};border-top:1px solid {T['border']};")
        bl = QHBoxLayout(bot); bl.setContentsMargins(28,0,28,0); bl.setSpacing(14)
        self.waveform = WaveformWidget()
        bl.addWidget(self.waveform, 1)
        for tag,hot in [("Lyrics",""), ("Sync","hot"), ("lrclib","")]:
            t = QLabel(tag)
            c  = T['accent2'] if hot else T['text3']
            bc = T['accent3'] if hot else T['border']
            t.setStyleSheet(f"color:{c};font-size:9px;letter-spacing:1px;border:1px solid {bc};border-radius:4px;padding:2px 8px;")
            bl.addWidget(t)
        rl.addWidget(bot)
        root.addWidget(right, 1)

        self.sidebar.set_active_nav("Now playing")

    def _switch_panel(self, idx, label):
        self.stack.setCurrentIndex(idx)
        self.sidebar.set_active_nav(label)

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)   # 100ms = smooth sync

    def _tick(self):
        if not PYGAME_OK or not self._playing: return
        try:
            raw = pygame.mixer.music.get_pos()
            if raw < 0: return
            # Correct position using seek base offset
            pos = self._seek_base + raw - self._seek_time
            pos = max(0, pos)
            self._pos_ms = pos
            self.sidebar.set_position(pos, self._dur_ms)
            self.lyrics_display.update_position(pos)
            self.waveform.set_progress(pos / max(self._dur_ms, 1))
        except Exception:
            pass

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio", "",
            "Audio (*.mp3 *.flac *.wav *.ogg *.m4a)")
        if path: self._load_file(path)

    def _load_file(self, path):
        self._file_path = path
        title  = Path(path).stem
        artist = "Unknown Artist"
        album  = ""
        pixmap = None
        dur_ms = 0

        if MUTAGEN_OK:
            try:
                if path.lower().endswith(".mp3"):
                    audio = MP3(path); dur_ms = int(audio.info.length*1000)
                    tags  = ID3(path)
                    if "TIT2" in tags: title  = str(tags["TIT2"])
                    if "TPE1" in tags: artist = str(tags["TPE1"])
                    if "TALB" in tags: album  = str(tags["TALB"])
                    for k in tags.keys():
                        if k.startswith("APIC"):
                            img = QImage.fromData(tags[k].data)
                            pixmap = QPixmap.fromImage(img); break
                elif path.lower().endswith(".flac"):
                    audio = FLAC(path); dur_ms = int(audio.info.length*1000)
                    if audio.get("title"):  title  = audio["title"][0]
                    if audio.get("artist"): artist = audio["artist"][0]
                    if audio.get("album"):  album  = audio["album"][0]
            except Exception: pass

        self._dur_ms = dur_ms
        self._info   = {"title":title,"artist":artist,"album":album,"pixmap":pixmap}
        self.sidebar.set_track(title, artist, pixmap)
        self.info_panel.update_info(title, artist, album, dur_ms, path, pixmap)
        self.library.add_track(path)
        self.status_lbl.setText(f"{title}  ·  {artist}")

        if PYGAME_OK:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play()
                self._seek_base = 0
                self._seek_time = 0
                self._playing = True
                self.sidebar.set_playing(True)
                self.visualiser.set_playing(True)
                self.waveform.set_playing(True)
            except Exception as e:
                self.status_lbl.setText(f"Error: {e}"); return

        self.lyrics_display.set_lines([])
        self.status_lbl.setText(f"Fetching lyrics…")
        if self._fetcher and self._fetcher.isRunning(): self._fetcher.quit()
        self._fetcher = LyricsFetcher(title, artist)
        self._fetcher.done.connect(self._on_lyrics)
        self._fetcher.error.connect(lambda m: self.status_lbl.setText(f"Lyrics: {m}"))
        self._fetcher.start()

    def _on_lyrics(self, lines, title, artist):
        self.lyrics_display.set_lines(lines)
        self.status_lbl.setText(f"{title}  ·  {len(lines)} lines synced")

    def _toggle_play(self):
        if not self._file_path:
            self._open_file(); return
        if not PYGAME_OK: return
        try:
            if self._playing:
                # Save position before pause
                raw = pygame.mixer.music.get_pos()
                self._pause_pos = self._seek_base + raw - self._seek_time
                pygame.mixer.music.pause()
                self._playing = False
            else:
                pygame.mixer.music.unpause()
                # Reset seek tracking so position continues from pause_pos
                self._seek_base = getattr(self, '_pause_pos', 0)
                self._seek_time = pygame.mixer.music.get_pos()
                self._playing = True
            self.sidebar.set_playing(self._playing)
            self.visualiser.set_playing(self._playing)
            self.waveform.set_playing(self._playing)
        except Exception: pass

    def _seek(self, frac):
        if not PYGAME_OK or self._dur_ms == 0: return
        try:
            secs = frac * self._dur_ms / 1000
            pygame.mixer.music.play(start=secs)
            self._seek_base = int(secs * 1000)
            self._seek_time = pygame.mixer.music.get_pos()
            if not self._playing:
                pygame.mixer.music.pause()
        except Exception: pass

    def _prev(self): pass   # extend with library playlist later
    def _next(self): pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lyrica")
    font = QFont("Segoe UI", 11)
    app.setFont(font)
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

# LMP - Lumina Music Player (Qt6 Version)
# pip install PyQt6 mutagen pillow

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QFileDialog, QSlider
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from mutagen import File as MutagenFile
from PIL import Image
from io import BytesIO

SUPPORTED_AUDIO = (".mp3", ".wav", ".flac", ".ogg", ".m4a")
COVER_NAMES = ["cover.jpg", "folder.jpg", "front.jpg", "cover.png", "folder.png"]


class LMP(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lumina Music Player 2.0")
        self.resize(800, 600)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        self.current_index = -1
        self.playlist = []

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        self.title_label = QLabel("Sin reproducción")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Sans Serif", 14))
        main_layout.addWidget(self.title_label)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(250, 250)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.set_placeholder_cover()

        self.list_widget = QListWidget()
        main_layout.addWidget(self.list_widget)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        main_layout.addWidget(self.slider)

        controls = QHBoxLayout()

        self.btn_open = QPushButton("Abrir")
        self.btn_prev = QPushButton("<<")
        self.btn_play = QPushButton("Play")
        self.btn_stop = QPushButton("Stop")
        self.btn_next = QPushButton(">>")

        controls.addWidget(self.btn_open)
        controls.addStretch()
        controls.addWidget(self.btn_prev)
        controls.addWidget(self.btn_play)
        controls.addWidget(self.btn_stop)
        controls.addWidget(self.btn_next)

        main_layout.addLayout(controls)

    def connect_signals(self):
        self.btn_open.clicked.connect(self.open_files)
        self.btn_play.clicked.connect(self.play_pause)
        self.btn_stop.clicked.connect(self.stop)
        self.btn_next.clicked.connect(self.next_track)
        self.btn_prev.clicked.connect(self.prev_track)

        self.list_widget.itemDoubleClicked.connect(self.play_selected)

        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.slider.sliderMoved.connect(self.player.setPosition)

        self.player.mediaStatusChanged.connect(self.handle_status)

    def open_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Abrir audio", "", "Audio (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )
        for file in files:
            if file.lower().endswith(SUPPORTED_AUDIO):
                self.playlist.append(file)
                self.list_widget.addItem(self.get_display_name(file))

    def play_selected(self):
        self.current_index = self.list_widget.currentRow()
        self.load_track(self.current_index)
        self.player.play()
        self.btn_play.setText("Pause")

    def load_track(self, index):
        if 0 <= index < len(self.playlist):
            path = self.playlist[index]
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(path))
            self.title_label.setText(self.get_display_name(path))
            self.load_cover(path)

    def play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("Play")
        else:
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.load_track(self.current_index)
            self.player.play()
            self.btn_play.setText("Pause")

    def stop(self):
        self.player.stop()
        self.btn_play.setText("Play")

    def next_track(self):
        if self.current_index + 1 < len(self.playlist):
            self.current_index += 1
            self.load_track(self.current_index)
            self.player.play()

    def prev_track(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_track(self.current_index)
            self.player.play()

    def update_position(self, position):
        self.slider.setValue(position)

    def update_duration(self, duration):
        self.slider.setRange(0, duration)

    def handle_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()

    def get_display_name(self, path):
        try:
            audio = MutagenFile(path, easy=True)
            if audio and "title" in audio:
                return audio["title"][0]
        except:
            pass
        return os.path.splitext(os.path.basename(path))[0]

    def load_cover(self, path):
        try:
            audio = MutagenFile(path)
            if audio and hasattr(audio, "tags"):
                for tag in audio.tags.values():
                    if tag.__class__.__name__ == "APIC":
                        image = Image.open(BytesIO(tag.data))
                        self.set_cover_from_image(image)
                        return
        except:
            pass

        folder = os.path.dirname(path)
        for name in COVER_NAMES:
            cover_path = os.path.join(folder, name)
            if os.path.exists(cover_path):
                self.set_cover_from_file(cover_path)
                return

        self.set_placeholder_cover()

    def set_cover_from_image(self, image):
        image = image.resize((250, 250))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        self.cover_label.setPixmap(pixmap)

    def set_cover_from_file(self, path):
        pixmap = QPixmap(path)
        pixmap = pixmap.scaled(250, 250)
        self.cover_label.setPixmap(pixmap)

    def set_placeholder_cover(self):
        pixmap = QPixmap(250, 250)
        pixmap.fill(Qt.GlobalColor.darkGray)
        self.cover_label.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LMP()
    window.show()
    sys.exit(app.exec())

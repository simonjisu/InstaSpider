# references: 
# https://wikidocs.net/21923
# https://wikidocs.net/35490
import sys
from pathlib import Path

from .database import Database
from .utils import load_settings
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QWidget, QAction, \
    QLabel, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTextBrowser, \
    QSlider, QComboBox, qApp
    

class Labeler(QMainWindow):

    def __init__(self, settings_path: str):
        r"""
        Database will be automatically loaded by `db_settings`
        """
        super().__init__()
        conf = load_settings(settings_path)
        self.conf_db = conf["db_settings"]
        self.conf_spider = conf["spider_settings"]
        
        self.db = Database(**self.conf_db)
        self.split_tag = self.db.IMG_SPLIT_TAG
        self.output_path = Path(self.conf_spider["output_path"])
        self.icon_path = Path("./icons")

        self.widgets = {}
        self.img_height = 640
        self.img_width = 640
        self.w = QWidget()
        self.setCentralWidget(self.w)
        self.initUI()

    def initUI(self):
        # exit
        exit_action = self.create_exit()

        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Ready")

        self.toolbar = self.addToolBar("Exit")
        self.toolbar.addAction(exit_action)
        
        
        hbox_top_widgets = self.create_top_widgets()
        hbox_select = self.create_labeler()
        hbox_post = self.create_post_ui()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_top_widgets)
        vbox.addLayout(hbox_select)
        vbox.addLayout(hbox_post)
        vbox.setAlignment(Qt.AlignTop)
        self.w.setLayout(vbox)
        
        self.setWindowTitle("Labeler")
        self.resize(1280, 720) # width hight
        self.center_window()
        
        self.show()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def create_exit(self):
        exit_action = QAction(
            QIcon(str(self.icon_path / "exit.png")), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(qApp.quit)
        return exit_action

    def create_top_widgets(self):
        label_str = """Select one of Label(A: Advertisement / R: Real Life)"""
        label = QLabel(label_str, self)
        
        self.widgets["tags"] = QComboBox()
        self.widgets["tags"].addItem("<SELECT>")
        tags = self.get_avaiable_tags()
        for tag in tags:
            self.widgets["tags"].addItem(tag)
        self.widgets["tags"].currentTextChanged.connect(
            self.on_combo_tags_changed
        )

            
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Avaiable tags:", self))
        vbox.addWidget(self.widgets["tags"])
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addLayout(vbox)
        return hbox

    def create_labeler(self):
        btn_labels = ["AA", "AR", "RA", "RR"]
        btn_location = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for l in btn_labels:
            self.widgets[f"btn_{l}"] = QPushButton(l, self)
            self.widgets[f"btn_{l}"].setFixedSize(80, 30)

        self.widgets["btn_prev"] = QPushButton("Prev", self)
        self.widgets["btn_prev"].setFixedSize(80, 70)
        self.widgets["btn_next"] = QPushButton("Next", self)
        self.widgets["btn_next"].setFixedSize(80, 70)
        
        layout_grid = QGridLayout()
        for l, (loc_x, loc_y) in zip(btn_labels, btn_location):
            layout_grid.addWidget(self.widgets[f"btn_{l}"], loc_x, loc_y)
        
        hbox = QHBoxLayout()
        hbox.addLayout(layout_grid)
        hbox.addWidget(self.widgets["btn_prev"])
        hbox.addWidget(self.widgets["btn_next"])
        hbox.setAlignment(Qt.AlignLeft)
        return hbox

    def create_post_ui(self):
        vbox1 = QVBoxLayout() # slider + image
        vbox2 = QVBoxLayout() # id + post
        hbox = QHBoxLayout()  # vbox1 + vbox2

        post_img = QPixmap()
        self.widgets["post_img_label"] = QLabel("<IMG>", self)
        self.widgets["post_img_label"].setPixmap(post_img)
        self.widgets["post_img_label"].setFixedSize(
            self.img_width, self.img_height)

        self.widgets["post_slider"] = QSlider(Qt.Horizontal, self)
        self.widgets["post_slider"].setRange(0, 0)
        self.widgets["post_slider"].setSingleStep(1)

        self.post_label_str = '<b><p style="font-size: 16px">Post ID: {}</p></b>'
        self.widgets["post_id"] = QLabel(self.post_label_str.format(""), self)
        self.widgets["post_text"] = QTextBrowser()

        vbox1.addWidget(self.widgets["post_slider"])
        vbox1.addWidget(self.widgets["post_img_label"])
        vbox2.addWidget(self.widgets["post_id"])
        vbox2.addWidget(self.widgets["post_text"])
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        hbox.setAlignment(Qt.AlignCenter)
        return hbox

    def get_avaiable_tags(self):
        c = self.db.get_cursor()
        sql = f"""SELECT DISTINCT tag FROM {self.db.table_name}"""
        res = c.execute(sql).fetchall()
        tags = list(map(lambda x: x[0], res))
        c.close()
        return tags

    def on_combo_tags_changed(self, value):
        self.statusBar.showMessage(f"tag: {value} Selected")
        c = self.db.get_cursor()
        # get first id
        sql = f"""SELECT MIN(id) FROM {self.db.table_name}
            WHERE tag='{value}'
            """
        res = c.execute(sql).fetchone()[0]
        self.widgets["post_id"].setText(
            self.post_label_str.format(res)
        )
        
# post_img = post_img.scaledToHeight(480)
# post_img = post_img.scaledToWidth(480)
# self.widgets["post_text"].setPlainText("")
# references: 
# https://wikidocs.net/21923
# https://wikidocs.net/35490
import io
import re
import pickle
from PIL import Image
from pathlib import Path
from .database import Database
from .utils import load_settings
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QWidget, QAction, \
    QLabel, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout, QTextBrowser, \
    QSlider, QComboBox, QMessageBox, QTextEdit, QShortcut, QProgressBar, QFrame, qApp

class Labeler(QMainWindow):
    TAG_CONTAINER_NAME = "{}_tag_container.pickle"
    TAG_BASE = "<SELECT>"
    HASHTAG_PATTERN = r"#.*?(?=\s|$) "
    EXTRACT_FILE_NAME = "{}_label.txt"
    def __init__(self, settings_path: str):
        r"""
        Database will be automatically loaded by `db_settings`
        """
        super().__init__()
        conf = load_settings(settings_path)
        self.conf_db = conf["db_settings"]
        self.conf_spider = conf["spider_settings"]
        
        self.db = Database(**self.conf_db)
        
        self.output_path = Path(self.conf_spider["output_path"])
        self.icon_path = Path("./icons")

        self.img_split_tag = self.db.IMG_SPLIT_TAG
        self.hashtag_compiler = re.compile(self.HASHTAG_PATTERN)

        self.widgets = {}
        self.imgs = None
        self.img_height = 640
        self.img_width = 640
        self.w = QWidget()
        self.label_container = {}  # dictionary
        self.setCentralWidget(self.w)
        self.c = self.db.get_cursor()
        self.initUI()

    def check_path(self, path: Path, typ: str="dir"):
        if not isinstance(path, Path):
            path = Path(path)
        if typ == "dir" and not path.exists():
            path.mkdir(parents=True)
            print(f"[INFO] Path: {path} Created!")
            return None
        elif typ == "file":
            return path.exists()
        else:
            return None

    def initUI(self):
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # toolbars
        exit_action, save_action, ex_action = self.create_toolbars()
        self.toolbar = self.addToolBar("Toolbar")
        self.toolbar.addAction(exit_action)
        self.toolbar.addAction(save_action)
        self.toolbar.addAction(ex_action)

        # widgets
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
        # self.center_window()
        
        self.show()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def create_toolbars(self):
        # exit
        exit_action = QAction(
            QIcon(str(self.icon_path / "exit.png")), "Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application(Ctrl + Q)")
        exit_action.triggered.connect(self.exit)
        # save
        save_action = QAction(
            QIcon(str(self.icon_path / "save.png")), "Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save Current Label Container(Ctrl + S)")
        save_action.triggered.connect(self.save_label_container)
        # extract
        ex_action = QAction(
            QIcon(str(self.icon_path / "extract.png")), "Extract", self)
        ex_action.setShortcut("Ctrl+E")
        ex_action.setStatusTip("Extract Current Label Container(Ctrl + E)")
        ex_action.triggered.connect(self.extract)
        return exit_action, save_action, ex_action

    def create_top_widgets(self):
        label_str = "1. Select Tag 2. Select one of Label(A: Advertisement / R: Real Life)"
        label_str += "\nWhen select the tag at first time, please save it first to create picklefile."
        label = QLabel(label_str, self)
        
        self.widgets["tags"] = QComboBox()
        self.widgets["tags"].setShortcutEnabled(False)
        self.widgets["tags"].addItem(self.TAG_BASE)
        tags = self.get_avaiable_tags()
        for tag in tags:
            self.widgets["tags"].addItem(tag)
        self.widgets["tags"].currentTextChanged.connect(
            self._tags_clicked
        )
            
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel("Avaiable tags:", self))
        vbox.addWidget(self.widgets["tags"])
        hbox = QHBoxLayout()
        hbox.addWidget(label)
        hbox.addLayout(vbox)
        return hbox

    def create_labeler(self):
        # Label
        btn_labels = ["AA", "AR", "RA", "RR"]
        btn_locations = [(0, 0), (0, 1), (1, 0), (1, 1)]
        btn_shortcut_key = [("T", Qt.Key_T), ("Y", Qt.Key_Y), ("G", Qt.Key_G), ("H", Qt.Key_H)]
        btn_links = [
            self._btn_AA_clicked, self._btn_AR_clicked, 
            self._btn_RA_clicked, self._btn_RR_clicked
        ]
        for l, link, (key_name, key) in zip(btn_labels, btn_links, btn_shortcut_key):
            self.widgets[f"btn_{l}"] = QPushButton(f"{l}({key_name})", self)
            self.widgets[f"btn_{l}"].setFixedSize(80, 30)
            self.widgets[f"btn_{l}"].clicked.connect(link)
            self.widgets[f"btn_{l}"].setShortcut(key)

        layout_grid = QGridLayout()
        for l, (loc_x, loc_y) in zip(btn_labels, btn_locations):
            layout_grid.addWidget(self.widgets[f"btn_{l}"], loc_x, loc_y)

        # Next, Prev
        self.widgets["btn_prev"] = QPushButton("Prev", self)
        self.widgets["btn_prev"].setFixedSize(80, 70)
        self.widgets["btn_prev"].clicked.connect(self._btn_prev_clicked)
        self.widgets["btn_prev"].setShortcut(Qt.Key_Left)
        self.widgets["btn_next"] = QPushButton("Next", self)
        self.widgets["btn_next"].setFixedSize(80, 70)
        self.widgets["btn_next"].clicked.connect(self._btn_next_clicked)
        self.widgets["btn_next"].setShortcut(Qt.Key_Right)

        # Current Label
        vbox_label = QVBoxLayout()
        current_label = QLabel("Current Label", self)
        current_label.setFixedSize(90, 30)
        current_label.setAlignment(Qt.AlignCenter)
        vbox_label.addWidget(current_label)
        self.widgets["label_current"] = QTextBrowser()
        self.widgets["label_current"].setFixedSize(90, 30)
        self.widgets['label_current'].setAlignment(Qt.AlignCenter)
        vbox_label.addWidget(self.widgets["label_current"])
        vbox_label.setAlignment(Qt.AlignCenter)
        
        # Jump to
        hbox_jump = QHBoxLayout()
        vbox_jump = QVBoxLayout()
        label_information = QLabel("Last blank label", self)
        label_information.setFixedSize(90, 30)
        label_information.setAlignment(Qt.AlignCenter)
        self.widgets["label_blank"] = QTextEdit()
        self.widgets["label_blank"].setFixedSize(90, 30)
        self.widgets['label_blank'].setAlignment(Qt.AlignCenter)
        vbox_jump.addWidget(label_information)
        vbox_jump.addWidget(self.widgets["label_blank"])
        vbox_jump.setAlignment(Qt.AlignCenter)
        self.widgets["btn_jump"] = QPushButton("Jump", self)
        self.widgets["btn_jump"].setFixedSize(80, 70)
        self.widgets["btn_jump"].clicked.connect(self._btn_jump_clicked)
        hbox_jump.addLayout(vbox_jump)
        hbox_jump.addWidget(self.widgets["btn_jump"])
        hbox_jump.setAlignment(Qt.AlignCenter)

        # Delete
        self.widgets["btn_del"] = QPushButton("Delete", self)
        self.widgets["btn_del"].setFixedSize(80, 70)
        self.widgets["btn_del"].clicked.connect(self._btn_del_clicked)

        # Total boxes
        hbox = QHBoxLayout()
        hbox.addLayout(layout_grid)
        hbox.addWidget(self.widgets["btn_prev"])
        hbox.addWidget(self.widgets["btn_next"])
        hbox.addLayout(vbox_label)
        hbox.addWidget(self.widgets["btn_del"])
        hbox.addStretch(2)
        hbox.addLayout(hbox_jump)
        hbox.setAlignment(Qt.AlignLeft)
        return hbox

    def create_post_ui(self):
        hbox_slider_number = QHBoxLayout()  # slider + current img idx
        hbox_label_id = QHBoxLayout()  # post_id_label + id
        vbox1 = QVBoxLayout()  # hbox_slider_number + image
        vbox2 = QVBoxLayout()  # id + post
        hbox = QHBoxLayout()  # vbox1 + vbox2

        self.widgets["post_slider"] = QSlider(Qt.Horizontal, self)
        self.widgets["post_slider"].setRange(0, 0)
        self.widgets["post_slider"].setSingleStep(1)
        self.widgets["post_slider"].valueChanged.connect(self._post_slider_clicked)
        self.widgets['post_slider_label'] = QLabel(f"{self.widgets['post_slider'].value()}", self)
        self.widgets['post_slider_label'].setFixedSize(30, 20)
        self.widgets['post_slider_label'].setAlignment(Qt.AlignCenter)

        post_img = QPixmap()
        self.widgets["post_img_label"] = QLabel("<IMG>", self)
        self.widgets["post_img_label"].setPixmap(post_img)
        self.widgets["post_img_label"].setFixedSize(
            self.img_width, self.img_height)
        
        post_label_str = '<b><p style="font-size: 16px">Post ID: </p></b>'
        post_id_label = QLabel(post_label_str, self)
        post_id_label.setFixedSize(100, 30)
        self.widgets["post_id"] = QTextBrowser()
        self.widgets['post_id'].setFixedSize(40, 30)
        self.widgets['post_id'].setAlignment(Qt.AlignCenter)

        self.widgets["post_text"] = QTextBrowser()
        self.widgets["post_text"].setAcceptRichText(True)
        self.widgets["post_text"].setFont(QFont("arial"))

        hbox_slider_number.addWidget(self.widgets["post_slider"])
        hbox_slider_number.addWidget(self.widgets["post_slider_label"])
        hbox_label_id.addWidget(post_id_label)
        hbox_label_id.addWidget(self.widgets["post_id"])
        hbox_label_id.setAlignment(Qt.AlignLeft)
        vbox1.addLayout(hbox_slider_number)
        vbox1.addWidget(self.widgets["post_img_label"])
        vbox2.addLayout(hbox_label_id)
        vbox2.addWidget(self.widgets["post_text"])
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)
        hbox.setAlignment(Qt.AlignCenter)
        return hbox

    def get_avaiable_tags(self):
        sql = f"""SELECT DISTINCT tag FROM {self.db.table_name}"""
        res = self.c.execute(sql).fetchall()
        tags = list(map(lambda x: x[0], res))
        return tags

    def get_avaiable_ids(self, tag):
        sql = f"""SELECT id FROM {self.db.table_name} WHERE tag = '{tag}'"""
        res = self.c.execute(sql).fetchall()
        ids = list(map(lambda x: x[0], res))
        return ids

    def extract(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            self.status_bar.showMessage("Cannot extract at <SELECT> tag")
        else:
            extract_path = self.output_path / self.EXTRACT_FILE_NAME.format(current_tag)
            if self.check_path(extract_path, "file"):
                # ask if want to overwrite
                msg = f"Are you sure to overwrite to {extract_path}?"
                reply = QMessageBox.question(self, "Message", msg,
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self._extract(path=extract_path)
                else:
                    pass
            else:
                self._extract(path=extract_path)

    def _extract(self, path):
        pbar = QProgressBar(self)
        pbar.setAlignment(Qt.AlignCenter)
        pbar.setGeometry(30, 40, 200, 25)
        self.status_bar.addWidget(pbar)
        
        n = len(self.label_container)
        with path.open("w", encoding="utf-8") as file:
            for i, (k, v) in enumerate(self.label_container.items(), 1):
                print(f"{k}\t{v}", file=file)
                step = int((i/n)*100)
                pbar.setValue(step)

    def exit(self):
        self.save_label_container()
        qApp.quit()

    def reset(self):
        self.widgets["post_slider"].setRange(0, 0)
        self.widgets["post_slider"].setSingleStep(1)
        self.widgets["post_img_label"].setPixmap(QPixmap())
        self.widgets["post_text"].setPlainText("")
        self.widgets["post_id"].setPlainText("")
        self.widgets["label_current"].setPlainText("")
        self.widgets['label_blank'].setPlainText("")

    def load_data(self, db_id: int):
        self.widgets["post_id"].setText(f"{db_id}")

        if self.label_container.get(db_id):
            self.widgets["label_current"].setText(
                self.label_container.get(db_id)
            )
        else:
            self.widgets["label_current"].setText("")

        sql = f"""SELECT post, imgs FROM {self.db.table_name}
            WHERE id={db_id}
            """
        post, imgs = self.c.execute(sql).fetchone()
        self.widgets["post_text"].setText(
            self._process_post(post)
        )

        self.imgs = self._set_post_img_label(imgs)
        self.widgets["post_img_label"].setPixmap(
            self._open_image(self.imgs[0])
        )

    def load_label_container(self, tag: str):
        tag_path = self.output_path / tag
        self.check_path(tag_path, "dir")
        container_path = tag_path / self.TAG_CONTAINER_NAME.format(tag)
        if self.check_path(container_path, "file"):
            with container_path.open("rb") as file:
                self.label_container = pickle.load(file)
        else:
            self.label_container = {}
            warning_str = "New label container created. Please Save it after labeling."
            QMessageBox.warning(None, "Message", warning_str)

    def save_label_container(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            self.status_bar.showMessage("Cannot save at <SELECT> tag")
        else:
            tag_path = self.output_path / current_tag
            self.check_path(tag_path, "dir")
            container_path = tag_path / self.TAG_CONTAINER_NAME.format(current_tag)
            with container_path.open("wb") as file:
                x_sorted = dict(sorted(self.label_container.items(), key=lambda x: x[0]))
                pickle.dump(x_sorted, file)
            self.status_bar.showMessage(f"Saved: {container_path}")

    def _get_blank_id(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            self.widgets['label_blank'].setPlainText("")
        else:
            ids = self.get_avaiable_ids(current_tag)
            for i in sorted(ids):
                if self.label_container.get(i) is None:
                    break
            self.widgets['label_blank'].setPlainText(f"{i}")     

    def _tags_clicked(self, value: str):
        self.status_bar.showMessage(f"tag: {value} Selected")
        if value == self.TAG_BASE:
            self.reset()
        else:
            self.load_label_container(value)
            # get first id
            sql = f"""SELECT MIN(id) FROM {self.db.table_name}
                WHERE tag='{value}'
                """
            res = self.c.execute(sql).fetchone()
            if res:
                first_id = res[0]
                self.load_data(first_id)
                self.status_bar.showMessage("")
            else:
                self.status_bar.showMessage("Data is not exists.")
            self._get_blank_id()

    def _set_post_img_label(self, imgs: bytes):
        r"""Please always return to `self.imgs`"""
        imgs = imgs.split(self.img_split_tag)
        self.widgets["post_slider"].setMaximum(len(imgs)-1)
        self.widgets["post_slider_label"].setText(f"{1}")
        return imgs

    def _open_image(self, image_byte):
        if image_byte == b"":
            qmap = QPixmap()
            self.status_bar.showMessage("Images are all videos")
        else:
            qmap = Image.open(io.BytesIO(image_byte)).toqpixmap()
            qmap = qmap.scaled(self.img_width, self.img_height)
        return qmap

    def _process_post(self, post):
        processed_post = post[:] + " "
        hash_tags = list(self.hashtag_compiler.findall(processed_post))
        for tag in hash_tags:
            processed_post = re.sub(tag, f"<span style='color: #000080'>{tag}</span>", processed_post)
        return processed_post

    def _get_current_post_id(self):
        current_id = int(self.widgets["post_id"].toPlainText())
        return current_id

    def _get_current_tag(self):
        current_tag = self.widgets["tags"].currentText()
        return current_tag

    def _post_slider_clicked(self, value: int):
        self.widgets["post_img_label"].setPixmap(
            self._open_image(self.imgs[value])
        )
        self.widgets["post_slider_label"].setText(f"{value+1}")

    def _btn_AA_clicked(self):
        txt = "AA"
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            self.widgets["label_current"].setText(txt)
            current_id = self._get_current_post_id()
            self.label_container[current_id] = txt
            self.status_bar.showMessage("")

    def _btn_AR_clicked(self):
        txt = "AR"
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            self.widgets["label_current"].setText(txt)
            current_id = self._get_current_post_id()
            self.label_container[current_id] = txt
            self.status_bar.showMessage("")

    def _btn_RA_clicked(self):
        txt = "RA"
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            self.widgets["label_current"].setText(txt)
            current_id = self._get_current_post_id()
            self.label_container[current_id] = txt
            self.status_bar.showMessage("")

    def _btn_RR_clicked(self):
        txt = "RR"
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            self.widgets["label_current"].setText(txt)
            current_id = self._get_current_post_id()
            self.label_container[current_id] = txt
            self.status_bar.showMessage("")

    def _btn_next_clicked(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            current_id = self._get_current_post_id()
            sql = f"""SELECT id FROM {self.db.table_name} 
                WHERE id = {current_id+1} AND tag = '{current_tag}'
                """
            res = self.c.execute(sql).fetchone()
            if res:
                next_id = res[0]
                self.load_data(next_id)
            else:
                self.status_bar.showMessage("Next Image is not exists.")
            self._get_blank_id()

    def _btn_prev_clicked(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            current_id = self._get_current_post_id()
            sql = f"""SELECT id FROM {self.db.table_name} 
                WHERE id = {current_id-1} AND tag = '{current_tag}'
                """
            res = self.c.execute(sql).fetchone()
            if res:
                next_id = res[0]
                self.load_data(next_id)
            else:
                self.status_bar.showMessage("Previous Image is not exists.")
            self._get_blank_id()

    def _btn_jump_clicked(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            txt = self.widgets["label_blank"].toPlainText()
            try: 
                blank_id = int(txt)
                ids = self.get_avaiable_ids(current_tag)
                if blank_id in ids:
                    self.load_data(blank_id)
                else:
                    self.status_bar.showMessage("Cannot Jump, number is not exists.")
            except ValueError:
                self.status_bar.showMessage("Cannot Jump, since there is no number inserted")

    def _btn_del_clicked(self):
        current_tag = self._get_current_tag()
        if current_tag == self.TAG_BASE:
            pass
        else:
            current_id = self._get_current_post_id()
            if self.label_container.get(current_id):
                self.label_container.pop(current_id)
                self.widgets["label_current"].setPlainText("")
            else:
                self.status_bar.showMessage("No such id to delete in label container")
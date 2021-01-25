import sys
import argparse
from PyQt5.QtWidgets import QApplication
from src import Labeler

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Example")
    parser.add_argument("--settings_path", type=str, default="./settings.yaml",
        help="settings path")
    args = parser.parse_args()
    app = QApplication(sys.argv)
    ex = Labeler(args.settings_path)
    sys.exit(app.exec_())
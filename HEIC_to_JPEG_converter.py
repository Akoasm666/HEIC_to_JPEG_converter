import os
import shutil
import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QProgressBar,
    QLabel,
    QFileDialog,
    QHBoxLayout,
)
from pillow_heif import register_heif_opener
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal


class ConversionThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, input_path, lang_dict, current_lang, is_file):
        super().__init__()
        self.input_path = input_path
        self.lang = lang_dict
        self.current_lang = current_lang
        self.is_file = is_file

    def get_unique_output_folder(self, base_path):
        folder_name = "converted_imgs"
        output_path = os.path.join(base_path, folder_name)
        counter = 1

        while os.path.exists(output_path):
            folder_name = f"converted_imgs{counter}"
            output_path = os.path.join(base_path, folder_name)
            counter += 1

        return output_path

    def run(self):
        try:
            register_heif_opener()
            lang = self.lang[self.current_lang]

            if self.is_file:
                # Double check file extension before processing
                if not self.input_path.lower().endswith((".heic", ".heif")):
                    self.status_updated.emit(lang["invalid_file"])
                    return

                # Handle single file conversion
                output_folder = os.path.dirname(self.input_path)
                output_filename = (
                    os.path.splitext(os.path.basename(self.input_path))[0] + ".jpg"
                )
                output_path = os.path.join(output_folder, output_filename)

                try:
                    with Image.open(self.input_path) as img:
                        if img.mode in ("RGBA", "LA"):
                            img = img.convert("RGB")
                        img.save(output_path, "JPEG", quality=95)
                    self.status_updated.emit(
                        f"{lang['single_converted']} {output_path}"
                    )
                except Exception as e:
                    self.status_updated.emit(f"{lang['single_convert_error']} {str(e)}")

                self.progress_updated.emit(100)

            else:
                # Existing folder conversion code
                self.status_updated.emit(f"{lang['input_folder']}: {self.input_path}")
                output_folder = self.get_unique_output_folder(
                    os.path.dirname(self.input_path)
                )
                self.status_updated.emit(f"{lang['output_folder']}: {output_folder}")

                os.makedirs(output_folder, exist_ok=True)

                files = os.listdir(self.input_path)
                heic_files = []
                other_files = []

                for f in files:
                    if os.path.isdir(os.path.join(self.input_path, f)):
                        continue
                    if f.lower().endswith((".heic", ".heif")):
                        heic_files.append(f)
                    else:
                        other_files.append(f)

                self.status_updated.emit(
                    lang["found_files"].format(len(heic_files), len(other_files))
                )

                total_files = len(heic_files) + len(other_files)
                processed_files = 0

                if total_files == 0:
                    self.status_updated.emit(lang["no_files"])
                    return

                for file in other_files:
                    try:
                        src = os.path.join(self.input_path, file)
                        dst = os.path.join(output_folder, file)
                        shutil.copy2(src, dst)
                        self.status_updated.emit(f"{lang['copied']}: {file}")
                    except Exception as e:
                        self.status_updated.emit(f"{lang['copy_error']}: {str(e)}")

                    processed_files += 1
                    self.progress_updated.emit(
                        int((processed_files / total_files) * 100)
                    )

                for heic_file in heic_files:
                    try:
                        input_path = os.path.join(self.input_path, heic_file)
                        output_filename = os.path.splitext(heic_file)[0] + ".jpg"
                        output_path = os.path.join(output_folder, output_filename)

                        with Image.open(input_path) as img:
                            if img.mode in ("RGBA", "LA"):
                                img = img.convert("RGB")
                            img.save(output_path, "JPEG", quality=95)
                        self.status_updated.emit(f"{lang['converted']}: {heic_file}")
                    except Exception as e:
                        self.status_updated.emit(f"{lang['convert_error']}: {str(e)}")

                    processed_files += 1
                    self.progress_updated.emit(
                        int((processed_files / total_files) * 100)
                    )

                self.status_updated.emit(f"{lang['complete']}: {output_folder}")

        except Exception as e:
            self.status_updated.emit(f"Error: {str(e)}")

        finally:
            self.finished.emit()


class HeicConverter(QMainWindow):
    def __init__(self):
        super().__init__()

        # Add valid image extensions to class
        self.valid_extensions = (".heic", ".heif")

        # Update language dictionary to include new strings
        self.lang = {
            "zh": {
                "window_title": "HEIC转JPEG转换器",
                "select_file": "选择一个HEIC/HEIF文件",
                "select_folder": "选择一个图片文件夹",
                "start_prompt": "选择一个文件或文件夹开始",
                "ready_convert": "准备转换",
                "convert": "转换",
                "input_folder": "输入文件夹",
                "output_folder": "输出文件夹将会是",
                "found_files": "找到 {} 个HEIC文件和 {} 个其他文件",
                "no_files": "没有找到需要处理的文件！",
                "copied": "已复制",
                "copy_error": "复制 {} 时出错",
                "converted": "已转换",
                "convert_error": "转换 {} 时出错",
                "complete": "转换完成！文件已保存到",
                "file_filter": "HEIC/HEIF图片 (*.heic *.heif)",
                "single_converted": "单个文件已转换到：",
                "single_convert_error": "转换文件时出错：",
                "invalid_file": "请选择HEIC或HEIF格式的图片文件",
            },
            "en": {
                "window_title": "HEIC to JPEG Converter",
                "select_file": "Select a HEIC/HEIF file",
                "select_folder": "Select a folder of images",
                "start_prompt": "Select a file or folder to start",
                "ready_convert": "Ready to convert",
                "convert": "Convert",
                "input_folder": "Input folder",
                "output_folder": "Output folder will be",
                "found_files": "Found {} HEIC files and {} other files",
                "no_files": "No files found to process!",
                "copied": "Copied",
                "copy_error": "Error copying {}",
                "converted": "Converted",
                "convert_error": "Error converting {}",
                "complete": "Conversion complete! Files saved to",
                "file_filter": "HEIC/HEIF Images (*.heic *.heif)",
                "single_converted": "Single file converted to:",
                "single_convert_error": "Error converting file:",
                "invalid_file": "Please select a HEIC or HEIF image file",
            },
        }
        self.current_lang = "zh"  # Default to Chinese

        self.setWindowTitle(self.tr(self.lang[self.current_lang]["window_title"]))
        self.setGeometry(100, 100, 500, 300)
        self.setFixedSize(500, 300)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create button layout for file/folder selection
        button_layout = QHBoxLayout()

        # Create select file button
        self.select_file_button = QPushButton(
            self.tr(self.lang[self.current_lang]["select_file"])
        )
        self.select_file_button.clicked.connect(self.select_file)

        # Update select folder button name
        self.select_folder_button = QPushButton(
            self.tr(self.lang[self.current_lang]["select_folder"])
        )
        self.select_folder_button.clicked.connect(self.select_folder)

        # Add buttons to horizontal layout
        button_layout.addWidget(self.select_file_button)
        button_layout.addWidget(self.select_folder_button)

        # Add language switch button
        self.lang_button = QPushButton(
            "Switch to English" if self.current_lang == "zh" else "切换到中文"
        )
        self.lang_button.clicked.connect(self.switch_language)

        self.status_label = QLabel(
            self.tr(self.lang[self.current_lang]["start_prompt"])
        )
        self.progress_bar = QProgressBar()
        self.convert_button = QPushButton(
            self.tr(self.lang[self.current_lang]["convert"])
        )
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)

        # Update layout
        layout.addWidget(self.lang_button)
        layout.addLayout(button_layout)  # Add the horizontal button layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.convert_button)

        self.input_path = None
        self.is_file = False
        self.is_converting = False
        self.conversion_thread = None

    def switch_language(self):
        self.current_lang = "en" if self.current_lang == "zh" else "zh"

        # Update UI text including new buttons
        self.setWindowTitle(self.lang[self.current_lang]["window_title"])
        self.select_file_button.setText(self.lang[self.current_lang]["select_file"])
        self.select_folder_button.setText(self.lang[self.current_lang]["select_folder"])
        self.convert_button.setText(self.lang[self.current_lang]["convert"])
        self.lang_button.setText(
            "Switch to English" if self.current_lang == "zh" else "切换到中文"
        )

        if self.input_path:
            self.count_files() if not self.is_file else None
        else:
            self.status_label.setText(self.lang[self.current_lang]["start_prompt"])

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.lang[self.current_lang]["select_file"],
            "",
            "HEIC/HEIF (*.heic *.heif)",  # Fixed filter format
        )
        if file_path:
            # Check if file has valid extension
            if file_path.lower().endswith(self.valid_extensions):
                self.input_path = file_path
                self.is_file = True
                self.progress_bar.setValue(0)
                self.status_label.setText(
                    f"{self.lang[self.current_lang]['ready_convert']}: {file_path}"
                )
                self.convert_button.setEnabled(True)
            else:
                self.status_label.setText(self.lang[self.current_lang]["invalid_file"])
                self.convert_button.setEnabled(False)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.lang[self.current_lang]["select_folder"]
        )
        if folder:
            self.input_path = folder
            self.is_file = False
            self.progress_bar.setValue(0)
            self.count_files()
            self.convert_button.setEnabled(True)

    def count_files(self):
        files = os.listdir(self.input_path)
        heic_count = len([f for f in files if f.lower().endswith((".heic", ".heif"))])
        other_count = len(
            [
                f
                for f in files
                if not f.lower().endswith((".heic", ".heif"))
                and not os.path.isdir(os.path.join(self.input_path, f))
            ]
        )
        self.status_label.setText(
            self.lang[self.current_lang]["found_files"].format(heic_count, other_count)
        )

    def start_conversion(self):
        if not self.input_path or self.is_converting:
            return

        self.is_converting = True
        self.convert_button.setEnabled(False)
        self.select_file_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)

        self.conversion_thread = ConversionThread(
            self.input_path, self.lang, self.current_lang, self.is_file
        )
        self.conversion_thread.progress_updated.connect(self.progress_bar.setValue)
        self.conversion_thread.status_updated.connect(self.status_label.setText)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()

    def conversion_finished(self):
        self.is_converting = False
        self.convert_button.setEnabled(True)
        self.select_file_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = HeicConverter()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

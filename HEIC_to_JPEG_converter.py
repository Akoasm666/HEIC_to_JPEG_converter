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
)
from pillow_heif import register_heif_opener
from PIL import Image
from PyQt5.QtCore import QThread, pyqtSignal


class ConversionThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, input_folder):
        super().__init__()
        self.input_folder = input_folder

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

            # Print input folder path
            self.status_updated.emit(f"输入文件夹: {self.input_folder}")

            # Get unique output folder name
            output_folder = self.get_unique_output_folder(
                os.path.dirname(self.input_folder)
            )
            # Print output folder path
            self.status_updated.emit(f"输出文件夹将会是: {output_folder}")

            os.makedirs(output_folder, exist_ok=True)

            files = os.listdir(self.input_folder)
            heic_files = []
            other_files = []

            for f in files:
                if os.path.isdir(os.path.join(self.input_folder, f)):
                    continue
                if f.lower().endswith((".heic", ".heif")):
                    heic_files.append(f)
                else:
                    other_files.append(f)

            # Print found files
            self.status_updated.emit(
                f"找到 {len(heic_files)} 个HEIC文件和 {len(other_files)} 个其他文件"
            )

            total_files = len(heic_files) + len(other_files)
            processed_files = 0

            if total_files == 0:
                self.status_updated.emit("没有找到需要处理的文件！")
                return

            # Copy other files
            for file in other_files:
                try:
                    src = os.path.join(self.input_folder, file)
                    dst = os.path.join(output_folder, file)
                    shutil.copy2(src, dst)
                    self.status_updated.emit(f"已复制: {file}")
                except Exception as e:
                    self.status_updated.emit(f"复制 {file} 时出错: {str(e)}")

                processed_files += 1
                self.progress_updated.emit(int((processed_files / total_files) * 100))

            # Convert HEIC files
            for heic_file in heic_files:
                try:
                    input_path = os.path.join(self.input_folder, heic_file)
                    output_filename = os.path.splitext(heic_file)[0] + ".jpg"
                    output_path = os.path.join(output_folder, output_filename)

                    with Image.open(input_path) as img:
                        if img.mode in ("RGBA", "LA"):
                            img = img.convert("RGB")
                        img.save(output_path, "JPEG", quality=95)
                    self.status_updated.emit(f"已转换: {heic_file}")
                except Exception as e:
                    self.status_updated.emit(f"转换 {heic_file} 时出错: {str(e)}")

                processed_files += 1
                self.progress_updated.emit(int((processed_files / total_files) * 100))

            self.status_updated.emit(
                f"转换完成！文件已保存到: {output_folder}"
            )

        except Exception as e:
            self.status_updated.emit(f"错误: {str(e)}")

        finally:
            self.finished.emit()


class HeicConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HEIC转JPEG转换器")
        self.setGeometry(100, 100, 500, 300)  # x, y, width, height
        self.setFixedSize(500, 300)  # Makes window size fixed

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create widgets
        self.select_button = QPushButton("选择文件夹")
        self.select_button.clicked.connect(self.select_folder)

        self.status_label = QLabel("选择一个文件夹开始")
        self.progress_bar = QProgressBar()
        self.convert_button = QPushButton("转换")
        self.convert_button.clicked.connect(self.start_conversion)
        self.convert_button.setEnabled(False)

        # Add widgets to layout
        layout.addWidget(self.select_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.convert_button)

        self.input_folder = None
        self.is_converting = False
        self.conversion_thread = None

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            # Reset progress bar and status for new folder
            self.progress_bar.setValue(0)
            self.status_label.setText("准备转换")

            self.input_folder = folder
            self.count_files()
            self.convert_button.setEnabled(True)

    def count_files(self):
        files = os.listdir(self.input_folder)
        heic_count = len([f for f in files if f.lower().endswith((".heic", ".heif"))])
        other_count = len(
            [
                f
                for f in files
                if not f.lower().endswith((".heic", ".heif"))
                and not os.path.isdir(os.path.join(self.input_folder, f))
            ]
        )
        self.status_label.setText(
            f"找到 {heic_count} 个HEIC文件和 {other_count} 个其他文件"
        )

    def start_conversion(self):
        if not self.input_folder or self.is_converting:
            return

        self.is_converting = True
        self.convert_button.setEnabled(False)
        self.select_button.setEnabled(False)

        self.conversion_thread = ConversionThread(self.input_folder)
        self.conversion_thread.progress_updated.connect(self.progress_bar.setValue)
        self.conversion_thread.status_updated.connect(self.status_label.setText)
        self.conversion_thread.finished.connect(self.conversion_finished)
        self.conversion_thread.start()

    def conversion_finished(self):
        self.is_converting = False
        self.convert_button.setEnabled(True)
        self.select_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = HeicConverter()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

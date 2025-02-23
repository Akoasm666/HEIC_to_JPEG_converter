# HEIC to JPEG Converter

A simple application to convert HEIC/HEIF images to JPEG format and copy other files to a new folder.

## Features

- Converts HEIC/HEIF images to JPEG format
- Preserves other files by copying them to the output folder
- Shows progress bars for conversion and copying
- Creates a new folder for all converted and copied files

## How to Use

1. Download and run the executable
2. When prompted, enter the full path to the folder containing your HEIC images
3. Wait for the conversion to complete
4. Find your converted images in a new folder called "converted_imgs" next to your source folder

## Building from Source

If you want to build the application yourself:

1. Install Python 3.7 or later
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
4. Build the executable:
   ```
   pyinstaller --onefile --name heic_converter HEIC_to_JPEG_convertor.py
   ```

## Notes

- The original files are not modified
- Converted HEIC/HEIF files will be saved as high-quality (95%) JPEG files
- All other files are copied without modification

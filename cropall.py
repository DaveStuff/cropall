#! /usr/bin/env python
#
# cropall: a tiny batch image processing app to crop pictures in less clicks
#
# Copyright (C) 2015-2024 Pyarelal Knowles
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import error_handler
import argparse
import configparser
import pathlib
import shutil

logger = error_handler.activate("cropall")

default_config_file = pathlib.Path("cropall_default.ini")
config_file = pathlib.Path("cropall.ini")

# dependencies are in a subdirectory when packaged with pyinstaller
if hasattr(sys, "_MEIPASS"):
    internal_dir = pathlib.Path(sys._MEIPASS)
    default_config_file = internal_dir / pathlib.Path("cropall_default.ini")
    config_file = internal_dir / config_file

    # ImageMagick directories
    os.environ["MAGICK_HOME"] = str(internal_dir)
    os.environ["MAGICK_CODER_FILTER_PATH"] = str(internal_dir / "modules/filters")
    os.environ["MAGICK_CODER_MODULE_PATH"] = str(internal_dir / "modules/coders")

    # Add the above paths PATH for wand/imagemagick on windows
    if sys.platform == "win32":
        os.environ["PATH"] += os.pathsep + os.environ["MAGICK_HOME"]
        os.environ["PATH"] += os.pathsep + os.environ["MAGICK_CODER_FILTER_PATH"]
        os.environ["PATH"] += os.pathsep + os.environ["MAGICK_CODER_MODULE_PATH"]

config = configparser.ConfigParser()
config.read(default_config_file)
if os.path.exists(config_file):
    config.read(config_file)

# Forces confirm_overwrite to False if append_suffix is True, regardless of the value in the config file
if config["cropall"].getboolean("append_suffix"):
    config["cropper"]["confirm_overwrite"] = "False"

parser = argparse.ArgumentParser()
parser.add_argument(
    "input_folder",
    type=pathlib.Path,
    nargs="?",
    help="Directories for source photos",
)


def getImages(config, dir):
    logger.info("Scanning {}".format(dir))
    extensions = config["image_extensions"].split()
    images = []
    for filename in os.listdir(dir):
        basename, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            logger.info("  Found {}".format(filename))
            images += [filename]
    logger.info("Found {} images".format(len(images)))
    return images


def get_output_filename(input_filename, config):
    cropall_config = config["cropall"]
    basename, ext = os.path.splitext(input_filename)
    if cropall_config.getboolean("append_suffix"):
        suffix = cropall_config.get("output_suffix", "-crop")
        basename += suffix
    return basename + ext
    

if __name__ == "__main__":
    cropall_config = config["cropall"]
    cropall_config["first_run"] = "False"
    args = parser.parse_args()
    if args.input_folder:
        input_folder = str(args.input_folder)
    else:
        # Ask for the input directory
        import tkinter.filedialog

        input_folder = tkinter.filedialog.askdirectory(
            initialdir=cropall_config["input_folder"], title="Please select a directory"
        )
    if not len(input_folder):
        raise ValueError("No directory selected. Exiting.")
    input_folder = pathlib.Path(os.path.normpath(input_folder))
    images = getImages(cropall_config, input_folder)
    if not len(images):
        raise SystemExit("No images found in '{}'. Exiting.".format(input_folder))
    cropall_config["input_folder"] = str(input_folder)

    output_folder = input_folder / pathlib.Path(cropall_config["output_folder"])
    if not os.path.exists(output_folder):
        logger.info("Creating output directory, '{}'".format(output_folder))
        os.makedirs(output_folder)

    import cropper

    cropper = cropper.Cropper(config)

    import gui

    app = gui.App(config, cropper, input_folder, images, output_folder)
    app.mainloop()

    with open(config_file, "w") as filehandle:
        config.write(filehandle)

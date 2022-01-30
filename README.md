# ci4tool

Tool for creating N64 CI4 (color indexed / palette) textures
Copyright (C) 2022 Sauraen, sauraen@gmail.com
Licensed under the GPL3, see LICENSE

# Setup

Make sure you are using python3. Then `pip install pillow`.

# Command-line use

Usage: python3 ci4tool.py [args]
- `-i`, `--input`:    Input PNG file
- `-o`, `--output`:   Output .c / .inc file
- `-p`, `--palette`:  PNG file representing palette (e.g. 16x1)
- `-c`, `--contents`: Image to generate palette from unique colors used
- `-m`, `--pltname`:  Name of palette array in C
- `-n`, `--idxname`:  Name of color-index (image) array in C
- `-x`, `--pltonly`:  Only convert palette, no -i image
- `-y`, `--nopltc`:   Do not emit palette into output C, only CI array

# Scripting use

You may include ci4tool as a Python module and call the following functions:
- `load_palette_from_im`
- `load_palette_from_png`
- `create_palette_from_im_contents`
- `create_palette_from_png_contents`
- `apply_palette_to_im`
- `apply_palette_to_png`
- `palette_to_c`
- `indexes_to_c`
For details see the comments in each function.

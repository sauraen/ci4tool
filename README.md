# ci4tool

Tool for creating N64 CI4 (color indexed / palette) textures \
Copyright (C) 2022 Sauraen, sauraen@gmail.com \
Licensed under the GPL3, see LICENSE

## Basic info

[ZAPD](https://github.com/zeldaret/zapd) does not fully support CI4 textures for
modding purposes. It can convert PNG to C for CI4 textures, but only if the PNG
is itself indexed. Furthermore, it completely ignores the palette data within
the PNG, simply writing the indexes in the PNG as the same indexes in C with no
intelligence to the conversion. If this texture is intended to use its own,
unique palette, the user has to manually extract the palette colors into a
separate PNG file for ZAPD to convert to C. And if this palette is intended to
be shared by multiple textures, the user must ensure that not only are the
colors identical in all the textures, but that they are stored in the PNG
palettes in those textures in the same order.

For modding, we would like to be able to
- convert any input PNG, including ones using much more than 16 different
  colors, to use a given palette
- extract the colors used in a PNG with <= 16 colors (i.e. a texture drawn to
  use only 16 colors, whether saved as RGB / RGBA format or as indexed) into a
  palette, which can then be applied to itself or another texture

These two features are exactly what ci4tool provides, in both command-line and
scriptable form.

## Setup

Make sure you are using python3. Then `pip install pillow`.

## Command-line use

Usage: `python3 ci4tool.py [args]`
- `-i`, `--input`:    Input PNG file
- `-o`, `--output`:   Output .c / .inc file
- `-p`, `--palette`:  PNG file representing palette (e.g. 16x1, 4x4)
- `-c`, `--contents`: Image to generate palette from unique colors used
- `-m`, `--pltname`:  Name of palette array in C
- `-n`, `--idxname`:  Name of color-index (image) array in C
- `-x`, `--pltonly`:  Only convert palette, no -i image
- `-y`, `--nopltc`:   Do not emit palette into output C, only CI array

## Scripting use

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

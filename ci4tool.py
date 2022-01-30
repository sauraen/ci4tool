import sys, os, struct
from pathlib import Path
from PIL import Image # pip install pillow

def load_palette_from_im(im, check_alpha_fmt=False):
    '''
    Loads pixels from a given pillow image as a palette. This must be up to 16
    pixels (e.g. 13x1, 4x4), and it must be either RGB or RGBA. If
    check_alpha_fmt, the first pixel must have zero or full alpha, and all the
    others must have full alpha. Returns a byte string length 4*num_colors
    containing the palette colors (RGBA).
    '''
    num_colors = im.size[0] * im.size[1]
    assert num_colors <= 16
    if len(im.getbands()) == 4:
        ib = im.tobytes()
        assert len(ib) == 4 * num_colors
        if check_alpha_fmt:
            assert ib[3] in {0, 255}
            for i in range(1, num_colors):
                assert ib[4*i+3] == 255
        return ib
    elif len(im.getbands()) == 3:
        ib = im.tobytes()
        assert len(ib) == 3 * num_colors
        ret = b''
        for i in range(num_colors):
            ret += ib[3*i:3*(i+1)]
            ret += b'\xFF'
        return ret
    else:
        raise RuntimeError('Palette PNG ' + p_file + ' must be RGB or RGBA')
    
def create_palette_from_im_contents(im):
    '''
    Creates a palette representing the colors used in an RGB / RGBA image.
    The image must use a maximum of 16 different colors. Alpha of < 128 is
    considered fully transparent (and all the same color); alpha of >= 128 is
    considered fully opaque.
    '''
    if len(im.getbands()) == 1:
        im = im.convert()
    bands = len(im.getbands())
    assert bands in {3, 4}
    ib = im.tobytes()
    b = b''
    hasalpha = False
    for i in range(len(ib)//bands):
        if bands == 4:
            r, g, b, a = struct.unpack('BBBB', ib[bands*i:bands*(i+1)])
        else:
            r, g, b = struct.unpack('BBB', ib[bands*i:bands*(i+1)])
            a = 255
        if a < 128:
            if not hasalpha:
                b = '\x00\x00\x00\x00' + b
                hasalpha = True
        else:
            a = 255
            px = struct.pack('BBBB', r, g, b, a)
            for j in range(len(b)//4):
                if px == b[4*j:4*(j+1)]:
                    break
            else:
                b += px
    if len(b) > 64:
        raise RuntimeError('Image has ' + str(len(b)//4) + ' colors, max of 16 for CI4')
    return b

def apply_palette_to_im(im, plt):
    '''
    Converts an input pillow image to color-indexed / palettized. The input
    palette must come from one of the functions above (i.e. the only palette
    entry which may have zero alpha is the first one). Each pixel is assigned to
    the palette entry which is closest to it. Returns a list of palette indexes,
    one per input pixel.
    '''
    bands = len(im.getbands())
    assert bands in {3, 4}
    ib = im.tobytes()
    assert (len(plt) & 3) == 0
    num_colors = len(plt) // 4
    assert num_colors <= 16
    plt_has_alpha = plt[3] == 0
    d = []
    for i in range(len(ib)//bands):
        if bands == 4:
            r, g, b, a = struct.unpack('BBBB', ib[bands*i:bands*(i+1)])
        else:
            r, g, b = struct.unpack('BBB', ib[bands*i:bands*(i+1)])
            a = 255
        if a < 128:
            if not plt_has_alpha:
                raise RuntimeError('Need alpha but palette does not have it')
            d.append(0)
        else:
            bestscore = 100000000
            bestq = -1
            for q in range(0, num_colors):
                if plt_has_alpha and q == 0:
                    continue
                pr, pg, pb = struct.unpack('BBB', plt[4*q:4*q+3])
                score = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
                if score < bestscore:
                    bestq = q
                    bestscore = score
            assert bestq >= 0 and bestq < num_colors
            d.append(bestq)
    assert len(d) == im.size[0] * im.size[1]
    return d

def load_palette_from_png(p_file, check_alpha_fmt=False):
    '''
    Loads a PNG file representing a palette. Wrapper for palette_from_im.
    '''
    with Image.open(p_file) as im:
        return load_palette_from_im(im, check_alpha_fmt)

def create_palette_from_png_contents(p_file):
    '''
    Loads a PNG file, wrapper for create_palette_from_im_contents.
    '''
    with Image.open(p_file) as im:
        return create_palette_from_im_contents(im)

def apply_palette_to_png(p_file, plt):
    '''
    Loads a PNG file and converts it to color-indexed. Wrapper for
    apply_palette_to_im.
    '''
    with Image.open(p_file) as im:
        return apply_palette_to_im(im, plt)

def palette_to_c(plt, array_name=None, comment=None):
    num_colors = len(plt)//4
    assert num_colors <= 16
    ret = ''
    if array_name is not None:
        ret += '__attribute__((aligned(16))) u16 ' + array_name + '[] = {\n'
    if comment is not None:
        ret += '    // ' + comment + '\n'
    ret += '    '
    for i in range(num_colors):
        val = ((plt[4*i+0] >> 3) << 11) | ((plt[4*i+1] >> 3) << 6) | \
            ((plt[4*i+2] >> 3) << 1) | (plt[4*i+3] >> 7)
        ret += '0x' + format(val, '04x')
        if i < num_colors-1: ret += ', '
    ret += '\n'
    if array_name is not None:
        ret += '};\n'
    return ret

def indexes_to_c(d, array_name=None, comment=None):
    '''
    Writes a C array containing the indexes for a color-indexed image as
    returned by apply_palette_to_im / apply_palette_to_png. Optionally writes
    the array definition (rather than just the contents), and an optional
    comment (e.g. for the input filename).
    '''
    assert (len(d) & 15) == 0
    ret = ''
    if array_name is not None:
        ret += '__attribute__((aligned(16))) u64 ' + array_name + '[] = {\n'
    if comment is not None:
        ret += '    // ' + comment + '\n'
    i = 0
    while i < len(d):
        ret += '    '
        for _ in range(4):
            ret += '0x'
            for _ in range(16):
                ret += format(d[i], 'x')
                i += 1
            if i >= len(d): break
            ret += ', '
        ret += '\n'
    if array_name is not None:
        ret += '};\n'
    return ret

if __name__ == '__main__':
    infile, outfile, pltfile, contentsfile = None, None, None, None
    pltname, idxname = None, None
    pltonly = False
    nopltc = False
    def get_next_arg():
        global i
        if i == len(sys.argv):
            raise RuntimeError('Expected argument for \'' + arg + '\', got (end)')
        a = sys.argv[i]
        i += 1
        if a[0] == '-':
            raise RuntimeError('Expected argument for \'' + arg + '\', got ' + a)
        return a
    def get_file_arg(isoutput=False):
        a = get_next_arg()
        try:
            with open(a, 'w' if isoutput else 'rb') as _:
                pass
            if isoutput: os.remove(a)
        except:
            raise RuntimeError('Could not open file ' + a)
        return a
    def show_help():
        print('\nci4tool - Copyright (C) 2022 Sauraen - GPL3 licensed\n' +
            'Usage: python3 ci4tool [args]\n'
            '-i, --input:    Input PNG file\n'
            '-o, --output:   Output .c / .inc file\n'
            '-p, --palette:  PNG file representing palette (e.g. 16x1)\n'
            '-c, --contents: Image to generate palette from unique colors used\n'
            '-m, --pltname:  Name of palette array in C\n'
            '-n, --idxname:  Name of color-index (image) array in C\n'
            '-x, --pltonly:  Only convert palette, no -i image\n'
            '-y, --nopltc:   Do not emit palette into output C, only CI array')
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        i += 1
        if arg in {'-i', '--input'}:
            infile = get_file_arg()
        elif arg in {'-o', '--output'}:
            outfile = get_file_arg(True)
        elif arg in {'-p', '--palette'}:
            pltfile = get_file_arg()
        elif arg in {'-c', '--contents'}:
            contentsfile = get_file_arg()
        elif arg == {'-m', '--pltname'}:
            pltname = get_next_arg()
        elif arg == {'-n', '--idxname'}:
            idxname = get_next_arg()
        elif arg in {'-x', '--pltonly'}:
            pltonly = True
        elif arg == {'-y', '--nopltc'}:
            nopltc = True
        else:
            print('Invalid command-line argument ' + arg)
            show_help()
            sys.exit(1)
    errored = False
    if infile is None and not pltonly:
        errored = True
        print('Missing input file (-i)')
    if outfile is None:
        errored = True
        print('Missing output file (-o)')
    if pltfile is None and contentsfile is None:
        errored = True
        print('Must specify either palette (-p) or image to extract colors from as palette (-c)')
    elif pltfile is not None and contentsfile is not None:
        errored = True
        print('Cannot specify both palette file and contents file')
    if pltonly and nopltc:
        errored = True
        print('Cannot specify palette only and no palette in C')
    def toAlnum(name):
        # From fast64, https://github.com/Fast-64/fast64, also GPL3 licensed
    	if name is None or name == '':
    		return None
    	for i in range(len(name)):
    		if not name[i].isalnum():
    			name = name[:i] + '_' + name[i+1:]
    	if name[0].isdigit():
    		name = '_' + name
    	return name
    pltsrcfile = pltfile if pltfile is not None else contentsfile
    if not errored:
        if pltname is None:
            pltname = toAlnum(Path(pltsrcfile).stem) + '_plt'
        else:
            if pltname != toAlnum(pltname):
                errored = True
                print(pltname + ' is not a valid C name')
        if idxname is None and not pltonly:
            idxname = toAlnum(Path(infile).stem) + '_ci4'
        else:
            if idxname != toAlnum(idxname):
                errored = True
                print(idxname + ' is not a valid C name')
    if errored:
        show_help()
        sys.exit(1)
    if pltfile is not None:
        plt = load_palette_from_png(pltfile)
    else:
        plt = create_palette_from_png_contents(contentsfile)
    with open(outfile, 'w') as o:
        if not nopltc:
            o.write(palette_to_c(plt, pltname, Path(pltsrcfile).name))
        if not pltonly:
            d = apply_palette_to_png(infile, plt)
            o.write(indexes_to_c(d, idxname, Path(infile).name))
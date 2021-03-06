import sys
sys.path.append('..')

from chowdren.converter import Converter
import argparse

def main():
    parser = argparse.ArgumentParser(
        description = 'Chowdren - MMF to C++ converter')
    parser.add_argument('filenames', type = str,
        help = 'input files to convert (should be an EXE or CCN file)',
        nargs = '+')
    parser.add_argument('outdir', type = str, help = 'destination directory')
    parser.add_argument('--imagefile', type = str, action = 'store',
        default = 'Sprites.dat', help = 'destination file for images')
    parser.add_argument('--noimages', action='store_true',
        help = 'turns off image writing')
    # parser.add_argument('--wiiu', action='store_true',
    #     help = 'turns on generation of Wii U-specific data')
    parser.add_argument('--shaders', action='store_true',
        help = 'copy shaders to destination directory')
    parser.add_argument('--base', action='store_true',
        help = 'only copy base dir')
    parser.add_argument('--ico', type = str, action = 'store', default = None,
        help = 'icon to use for Windows')
    parser.add_argument('--icns', type = str, action = 'store', default = None,
        help = 'icon to use for OS X')
    parser.add_argument('--version', type = str, action = 'store',
        default = None, help = 'version to set in executable')
    parser.add_argument('--company', type = str, action = 'store',
        default = None, help = 'company to set in executable')
    parser.add_argument('--copyright', type = str, action = 'store',
        default = None, help = 'copyright to set in executable')
    args = parser.parse_args()
    if args.noimages:
        image_file = None
    else:
        image_file = args.imagefile
    Converter(args.filenames, args.outdir, image_file = image_file,
              win_ico = args.ico, mac_icns = args.icns, version = args.version,
              company = args.company, copyright = args.copyright,
              base_only = args.base, copy_shaders= args.shaders)

if __name__ == '__main__':
    main()
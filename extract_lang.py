import os
import sys
import zipfile


def extract_lang(path: str):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith('.lang'):
                zip_ref.extract(file, '.')


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    for filename in os.listdir(path):
        if filename.endswith('.jar'):
            extract_lang(f'{path}/{filename}')


if __name__ == '__main__':
    main()

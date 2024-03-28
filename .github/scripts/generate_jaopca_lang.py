import json
import os
import re

from case_convert import pascal_case


def main():
    lang = {}
    for filename in os.listdir('sources/config/jaopca/materials'):
        if filename.endswith('.toml'):
            name = filename[:-5]
            lang[f'jaopca.material.{pascal_case(name)}'] = re.sub(r'[A-Z]', lambda p: " " + p.group(0), pascal_case(name)).lstrip()
    with open('sources/config/jaopca/lang/en_us.json', 'w', encoding='utf-8') as f:
        json.dump(lang, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main()

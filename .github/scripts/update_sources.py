import asyncio
import json
import os
import re
from typing import Optional

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9743

paratranz_files = []

MAX_RETRY = 3


async def get_project_files():
    global paratranz_files
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f'https://paratranz.cn/api/projects/{PROJECT_ID}/files',
            headers={'Authorization': PARATRANZ_TOKEN}
        )
    response.raise_for_status()
    paratranz_files = response.json()


def get_fileid_in_project(path: str) -> Optional[int]:
    for file in paratranz_files:
        if file['name'] == path:
            return file['id']
    return None


async def upload_project_file(path: str):
    path = path.replace('\\', '/')
    file_id = get_fileid_in_project(path[8:])
    if file_id is None:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files'
    else:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files/{file_id}'
    async with httpx.AsyncClient() as client:
        for retry in range(MAX_RETRY):
            try:
                response = await client.post(
                    url,
                    headers={'Authorization': PARATRANZ_TOKEN},
                    data={'path': os.path.dirname(path)[8:]},
                    files={'file': (os.path.basename(path), open(path, 'rb'))}
                )
                response.raise_for_status()
                print(f'{path} 上传成功')
                break
            except Exception:
                print(f'{path} 上传失败, 再尝试 {MAX_RETRY - retry - 1} 次')
            await asyncio.sleep(0.7)


def covert_lang_to_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    return dict(
        re.sub(r'\\u([0-9a-fA-F]{4})', lambda x: chr(int(x.group(1), 16)), line.strip('\n')).replace('\\n', '\n').split('=', maxsplit=1)
        for line in lines
        if '=' in line and not line.startswith('#')
    )


async def main():
    await get_project_files()
    for root, dirs, files in os.walk("sources"):
        for file in files:
            if file.endswith(".lang"):
                pz = covert_lang_to_json(f'{root}/{file}')
                with open(f"{root}/{file}.json", 'w', encoding='utf-8') as f:
                    json.dump(pz, f, ensure_ascii=False, indent=4)
                await upload_project_file(f"{root}/{file}.json")
            if file.endswith('.json'):
                await upload_project_file(f'{root}/{file}')


if __name__ == '__main__':
    asyncio.run(main())

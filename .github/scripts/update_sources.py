import asyncio
import json
import os
import re
from typing import Optional

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9743
MAX_RETRY = 3

paratranz_files = []

# 设置超时时间，比如30秒
TIMEOUT = httpx.Timeout(30.0, read=30.0)


async def get_project_files(client: httpx.AsyncClient):
    global paratranz_files
    response = await client.get(
        f'https://paratranz.cn/api/projects/{PROJECT_ID}/files',
        headers={'Authorization': f'PotatoChampion {PARATRANZ_TOKEN}'},
        timeout=TIMEOUT
    )
    response.raise_for_status()
    paratranz_files = response.json()


def get_fileid_in_project(path: str) -> Optional[int]:
    for file in paratranz_files:
        if file['name'] == path:
            return file['id']
    return None


async def upload_project_file(client: httpx.AsyncClient, path: str):
    path = path.replace('\\', '/')
    # 去除 'sources/' 前缀以匹配项目文件路径
    relative_path = path[8:] if path.startswith('sources/') else path
    file_id = get_fileid_in_project(relative_path)
    if file_id is None:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files'
    else:
        url = f'https://paratranz.cn/api/projects/{PROJECT_ID}/files/{file_id}'

    for retry in range(MAX_RETRY):
        try:
            with open(path, 'rb') as file_obj:
                response = await client.post(
                    url,
                    headers={'Authorization': f'PotatoChampion {PARATRANZ_TOKEN}'},
                    data={'path': os.path.dirname(relative_path)},
                    files={'file': (os.path.basename(path), file_obj)},
                    timeout=TIMEOUT
                )
            response.raise_for_status()
            print(f'{path} 上传成功')
            break
        except (httpx.ReadTimeout, httpx.RequestError) as e:
            print(f'{path} 上传失败 ({e}), 再尝试 {MAX_RETRY - retry - 1} 次')
            await asyncio.sleep(1)
        except Exception as e:
            print(f'{path} 上传失败，错误: {e}')
            break


def covert_lang_to_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    return dict(
        re.sub(r'\\u([0-9a-fA-F]{4})', lambda x: chr(int(x.group(1), 16)), line.strip('\n')).replace('\\n', '\n').split('=', maxsplit=1)
        for line in lines
        if '=' in line and not line.startswith('#')
    )


async def main():
    async with httpx.AsyncClient() as client:
        await get_project_files(client)
        for root, dirs, files in os.walk("sources"):
            for file in files:
                full_path = os.path.join(root, file)
                if file.endswith(".lang"):
                    pz = covert_lang_to_json(full_path)
                    json_path = f"{full_path}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(pz, f, ensure_ascii=False, indent=4)
                    await upload_project_file(client, json_path)
                elif file.endswith('.json'):
                    await upload_project_file(client, full_path)


if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import json
import os
import shutil
import zipfile

import httpx

PARATRANZ_TOKEN = os.environ.get('PARATRANZ_TOKEN')
PROJECT_ID = 9743


async def download_project() -> bool:
    for retry in range(3):
        try:
            print(f"尝试下载第 {retry + 1} 次")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts',
                    headers={'Authorization': f'PotatoChampion {PARATRANZ_TOKEN}'}
                )
                response.raise_for_status()

                response = await client.get(
                    f'https://paratranz.cn/api/projects/{PROJECT_ID}/artifacts/download',
                    headers={'Authorization': f'PotatoChampion {PARATRANZ_TOKEN}'},
                    follow_redirects=True
                )
                response.raise_for_status()

                with open('artifacts.zip', 'wb') as file:
                    file.write(response.content)

            print("✅ 下载成功")
            return True
        except Exception as e:
            print(f'❌ 下载失败，错误：{e}')
    return False


def covert_paratranz_json_to_lang(json_file: str) -> str:
    with open(json_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)

    return '\n'.join(
        [f'{t["key"]}={t["translation"] if t["translation"] != "" else t["original"]}' for t in translated]
    )


def covert_paratranz_json_to_json(json_file: str) -> dict:
    with open(json_file, 'r', encoding='utf-8') as f:
        translated = json.load(f)
    return {t["key"]: t["translation"] if t["translation"] != "" else t["original"] for t in translated}


async def main():
    print("开始下载项目翻译数据...")
    success = await download_project()
    if not success:
        print("下载失败，退出程序。")
        return

    if not os.path.exists('artifacts.zip'):
        print("没有找到 artifacts.zip，退出程序。")
        return

    print("解压缩 artifacts.zip...")
    with zipfile.ZipFile('artifacts.zip', 'r') as zip_ref:
        zip_ref.extractall('temp/')

    print("开始转换翻译文件...")
    for root, dirs, files in os.walk('temp/utf8'):
        for file in files:
            path = os.path.join(root, file).replace('\\', '/')
            new_path = 'translated' + path.replace('temp/utf8', '')
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            if file.endswith('.lang.json'):
                lang = covert_paratranz_json_to_lang(path).replace('\\n', '%n')
                with open(f'{os.path.dirname(new_path)}/zh_cn.lang', 'w', encoding='utf-8') as f:
                    f.write(lang)
            elif file.endswith('.json') and '.lang' not in file:
                lang = covert_paratranz_json_to_json(path)
                with open(f'{os.path.dirname(new_path)}/zh_cn.json', 'w', encoding='utf-8') as f:
                    json.dump(lang, f, ensure_ascii=False, indent=4)

    # 清理临时文件夹
    shutil.rmtree('temp')

    print("转换完成，翻译文件已保存到 translated 文件夹。")


if __name__ == '__main__':
    asyncio.run(main())

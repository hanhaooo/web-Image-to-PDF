#v1.0正式版，指定下载url、下载保存地址，并支持将图片直接保存为PDF文件。
import os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from PIL import Image  # 新增：用于合成PDF

def download_images(url, save_dir, pdf_name="combined.pdf"):
    """
    下载网页中的所有图片，并合并为一个PDF。
    :param url: 目标网页URL
    :param save_dir: 保存图片和PDF的文件夹路径
    :param pdf_name: 输出的PDF文件名，默认 combined.pdf
    """
    os.makedirs(save_dir, exist_ok=True)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
    except requests.RequestException as e:
        print(f"获取网页失败: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # 懒加载属性
    lazy_attrs = ['data-src', 'data-original', 'data-lazy-src', 'data-srcset', 'data-url']
    img_tags = soup.find_all('img')

    img_urls = []
    for img in img_tags:
        src = None
        for attr in lazy_attrs:
            if img.get(attr):
                src = img.get(attr)
                break
        if not src:
            src = img.get('src')

        if not src or src.startswith('data:'):
            continue

        abs_url = urljoin(url, src)
        img_urls.append(abs_url)

    if not img_urls:
        print("未找到任何图片链接")
        return

    print(f"共找到 {len(img_urls)} 个图片链接，开始下载...")

    downloaded_files = []  # 记录成功下载的图片路径
    for idx, img_url in enumerate(img_urls, start=1):
        try:
            print(f"下载第 {idx} 张: {img_url}")
            img_response = requests.get(img_url, headers=headers, timeout=10, stream=True)
            img_response.raise_for_status()

            ext = get_extension(img_url, img_response.headers.get('content-type', ''))
            filename = f"{idx:03d}{ext}"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            downloaded_files.append(filepath)
            print(f"已保存: {filename}")

        except requests.RequestException as e:
            print(f"下载失败 {img_url}: {e}")
            continue

    print(f"下载完成，成功 {len(downloaded_files)} 张。")

    if downloaded_files:
        pdf_path = os.path.join(save_dir, pdf_name)
        print("正在合并为PDF...")
        images_to_pdf(downloaded_files, pdf_path)
        print(f"PDF已生成: {pdf_path}")
    else:
        print("没有下载到任何图片，无法生成PDF。")


def get_extension(url, content_type):
    """从URL或Content-Type获取扩展名"""
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']:
        return ext

    if content_type:
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'
        elif 'svg' in content_type:
            return '.svg'

    return '.jpg'


def images_to_pdf(image_paths, pdf_path):
    """
    将多张图片按顺序合并为一个PDF文件。
    :param image_paths: 图片路径列表（已按序号排序）
    :param pdf_path: 输出的PDF路径
    """
    image_list = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            # 如果图片有透明通道，转换为RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            image_list.append(img)
        except Exception as e:
            print(f"无法打开图片 {img_path}: {e}，已跳过")

    if not image_list:
        print("没有可用的图片用于生成PDF")
        return

    # 使用第一张图片作为基准，其他图片追加
    image_list[0].save(
        pdf_path,
        save_all=True,
        append_images=image_list[1:],
        resolution=100.0,        # 可调整分辨率
        optimize=True
    )
    print(f"PDF合并成功，共 {len(image_list)} 页")


if __name__ == "__main__":
    # ★★★ 请直接修改下面的网页链接和保存路径 ★★★
    target_url = "【链接URL地址】"        # 目标网页
    save_folder = r"【保存目录】"       # 图片和PDF保存目录
    output_pdf = "【pdf文件名称】"               # 生成的PDF文件名

    download_images(target_url, save_folder, output_pdf)
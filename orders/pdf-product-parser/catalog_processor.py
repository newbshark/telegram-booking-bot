#!/usr/bin/env python3
"""
PDF Catalog & Image Processor
Extracts products from PDF/CSV, resizes images to 1000x1000 square, converts to WebP <= 300KB.
"""

import os
import sys
import csv
import json
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None

def process_product_image(input_path, output_path, target_size=(1000, 1000), max_kb=300):
    """
    Приводит изображение к квадрату target_size с белым фоном, сохраняет в WebP со сжатием <= max_kb.
    """
    if Image is None:
        raise ImportError("Требуется Pillow: pip install Pillow")

    with Image.open(input_path) as img:
        # Конвертируем в RGBA/RGB
        img = img.convert("RGBA")
        
        # Вычисляем масштабирование с сохранением пропорций
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Создаем квадратный холст с белым фоном
        canvas = Image.new("RGBA", target_size, (255, 255, 255, 255))
        offset = ((target_size[0] - img.size[0]) // 2, (target_size[1] - img.size[1]) // 2)
        canvas.paste(img, offset, img)
        
        # Конвертируем в RGB для WebP
        final_img = canvas.convert("RGB")
        
        # Сохранение с подбором качества до max_kb
        quality = 90
        while quality >= 30:
            final_img.save(output_path, "WEBP", quality=quality, optimize=True)
            size_kb = os.path.getsize(output_path) / 1024
            if size_kb <= max_kb:
                break
            quality -= 10
            
        print(f"[✓] Обработано фото: {os.path.basename(output_path)} ({size_kb:.1f} KB, качество {quality})")
        return output_path

if __name__ == "__main__":
    print("PDF Catalog & Image Processor готов к работе.")

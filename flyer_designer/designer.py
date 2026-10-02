#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
import requests
import os

class RIOFlyerDesigner:
    def __init__(self):
        self.base_dir = Path("/root/.hermes/rio_research/rio-affiliate-engine")
        self.output_dir = self.base_dir / "flyer_designer" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("FLYER_DESIGNER_API_KEY", os.getenv("BEDROCK_API_KEY"))
        
    def fetch_product_image(self, product_url):
        """Fetch product image from user-provided URL"""
        try:
            response = requests.get(product_url, timeout=10)
            if response.status_code == 200:
                return product_url
        except:
            pass
        return None
    
    def create_flyer(self, product_data, product_image_url=None):
        w, h = 1080, 1350
        img = Image.new("RGB", (w, h), color="#1a1a2e")
        draw = ImageDraw.Draw(img)
        
        for y in range(h):
            r = 139 - int(50*y/h)
            draw.line([(0, y), (w, y)], fill=(r, 0, 0))
        
        draw.rectangle([0, 50, w, 150], fill="#e94560", width=5)
        draw.text((440, 65), "RIO", fill="#ffffff", font_size=60)
        
        if product_image_url:
            try:
                img_response = requests.get(product_image_url, timeout=10)
                if img_response.status_code == 200:
                    from io import BytesIO
                    product_img = Image.open(BytesIO(img_response.content))
                    max_width = 400
                    max_height = 400
                    product_img.thumbnail((max_width, max_height), Image.LANCZOS)
                    px, py = product_img.size
                    img.paste(product_img, (w//2 - px//2, 200))
                    print(f"Added product image: {product_image_url[:50]}...")
            except Exception as e:
                print(f"Image download failed: {e}")
        
        draw.text((60, 650), product_data.get("title", "Product"), fill="#ffffff", font_size=35)
        draw.text((60, 720), f" Price: {product_data.get('price', '₹0')}", fill="#ffffff", font_size=30)
        draw.text((60, 780), f" commission", fill="#e94560", font_size=30)
        draw.rectangle([50, 850, w-50, 950], width=3)
        draw.text((200, 885), "Amazon Associate Earn Commissions", fill="#000", font_size=28)
        
        btn_w, btn_h = 200, 60
        draw.rectangle([(w-60-btn_w), 100, (w-60), (100+btn_h)], fill="#e94560")
        draw.text((w-btn_w-60, 120), "SHOP NOW", fill="#fff", font_size=25)
        
        filename = f"rio_flyer_{product_data.get('id', 'unknown')}.png"
        filepath = self.output_dir / filename
        img.save(filepath, "PNG", quality=100)
        
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        
        return str(filepath), b64

if __name__ == "__main__":
    designer = RIOFlyerDesigner()
    products = [
        {"id": "AFF001", "title": "Wireless Bluetooth Headphones", "price": "₹1,299", "commission": "15%"},
    ]
    print("=== RIO FLYER DESIGNER ===")
    for product in products:
        filepath, b64 = designer.create_flyer(product, None)
        print(f"Created: {Path(filepath).name}")
    print(f"Output: {designer.output_dir}")

#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import base64
import requests

class RIOFlyerDesigner:
    def __init__(self):
        self.base_dir = Path("/root/.hermes/rio_research/rio-affiliate-engine")
        self.output_dir = self.base_dir / "flyer_designer" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("FLYER_DESIGNER_API_KEY")
        
    def create_flyer(self, product_data):
        w, h = 1080, 1350
        img = Image.new("RGB", (w, h), color="#1a1a2e")
        draw = ImageDraw.Draw(img)
        for y in range(h):
            r = 139 - int(50*y/h)
            draw.line([(0, y), (w, y)], fill=(r, 0, 0))
        draw.rectangle([0, 50, w, 150], fill="#e94560", width=5)
        draw.text((440, 65), "RIO", fill="#ffffff")
        draw.text((60, 250), product_data.get("title", "Product"), fill="#ffffff", font_size=40)
        draw.text((60, 350), f" Price: {product_data.get('price', '0')}", fill="#ffffff", font_size=35)
        draw.text((60, 420), f" commission", fill="#e94560", font_size=35)
        draw.rectangle([50, 550, w-50, 650], width=3)
        draw.text((200, 585), "Amazon Associate Earn Commissions", fill="#000", font_size=30)
        btn_w = 180
        btn_h = 60
        draw.rectangle([(w-60-btn_w), 100, (w-60), (100+btn_h)], fill="#e94560")
        draw.text((w-btn_w-50, 120), "SHOP NOW", fill="#fff", font_size=25)
        filename = f"rio_flyer_{product_data.get('id', 'unknown')}.png"
        filepath = self.output_dir / filename
        img.save(filepath, "PNG", quality=100)
        with open(filepath, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return str(filepath), b64

if __name__ == "__main__":
    designer = RIOFlyerDesigner()
    products = [
        {"id": "AFF001", "title": "Wireless Bluetooth Headphones", "price": "1299", "commission": "15%"},
        {"id": "AFF002", "title": "Mechanical Keyboard", "price": "3499", "commission": "12%"},
        {"id": "AFF003", "title": "Laptop Stand Adjustable", "price": "899", "commission": "18%"},
    ]
    print("=== RIO FLYER DESIGNER ===")
    for product in products:
        filepath, b64 = designer.create_flyer(product)
        print(f"Created: {Path(filepath).name}")
    print(f"Output: {designer.output_dir}")

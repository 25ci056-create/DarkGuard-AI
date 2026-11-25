"""Generate sample test screenshots for DarkGuard AI demo/testing."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

OUT_DIR = Path(__file__).parent.parent / "tests" / "sample_screenshots"
OUT_DIR.mkdir(exist_ok=True)


def _font(size=16):
    """Return a basic font (falls back to default if no system fonts)."""
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def make_product_page():
    """Product page – shows ₹499."""
    img = Image.new("RGB", (400, 700), "#FFFFFF")
    d = ImageDraw.Draw(img)
    # Header
    d.rectangle([0, 0, 400, 50], fill="#FB641B")
    d.text((16, 14), "flipkart", fill="white", font=_font(22))
    # Product image placeholder
    d.rectangle([20, 70, 380, 300], fill="#F0F0F0", outline="#DDD")
    d.text((160, 175), "🖼️", fill="#AAA", font=_font(40))
    # Price
    d.text((20, 320), "Wireless Headphones - Black", fill="#212121", font=_font(18))
    d.text((20, 360), "₹499", fill="#212121", font=_font(28))
    d.text((100, 367), "₹999", fill="#878787", font=_font(16))
    d.line([(100, 376), (145, 376)], fill="#878787", width=1)
    d.text((155, 362), "50% off", fill="#388E3C", font=_font(14))
    # Urgency
    d.rectangle([20, 410, 380, 440], fill="#FFF3E0", outline="#FF9800")
    d.text((25, 418), "⚡ Deal ends in  02:34:17  · Only 3 left!", fill="#E65100", font=_font(13))
    # Delivery
    d.text((20, 460), "Free delivery by Tomorrow", fill="#388E3C", font=_font(13))
    # Add to cart button
    d.rectangle([20, 520, 185, 560], fill="#FF9F00", outline="#FF9F00")
    d.text((52, 532), "ADD TO CART", fill="white", font=_font(14))
    d.rectangle([200, 520, 380, 560], fill="#FB641B", outline="#FB641B")
    d.text((248, 532), "BUY NOW", fill="white", font=_font(14))
    img.save(OUT_DIR / "1_product_page.jpg", quality=92)
    print("✓ Created 1_product_page.jpg")


def make_cart_page():
    """Cart page – same ₹499, no extra fees yet."""
    img = Image.new("RGB", (400, 700), "#FFFFFF")
    d = ImageDraw.Draw(img)
    # Header
    d.rectangle([0, 0, 400, 50], fill="#FB641B")
    d.text((16, 14), "flipkart · My Cart (1 item)", fill="white", font=_font(16))
    # Cart item
    d.rectangle([16, 70, 384, 170], fill="#FFFFFF", outline="#E0E0E0")
    d.rectangle([26, 80, 100, 160], fill="#F0F0F0")
    d.text((32, 112), "🎧", fill="#AAA", font=_font(24))
    d.text((112, 85), "Wireless Headphones - Black", fill="#212121", font=_font(13))
    d.text((112, 108), "₹499", fill="#212121", font=_font(18))
    d.text((112, 132), "Qty: 1", fill="#878787", font=_font(12))
    # Order summary
    d.rectangle([16, 190, 384, 350], fill="#FFFFFF", outline="#E0E0E0")
    d.text((24, 200), "PRICE DETAILS", fill="#212121", font=_font(14))
    d.text((24, 230), "Price (1 item)", fill="#212121", font=_font(13))
    d.text((300, 230), "₹499", fill="#212121", font=_font(13))
    d.text((24, 258), "Delivery Charges", fill="#212121", font=_font(13))
    d.text((270, 258), "FREE", fill="#388E3C", font=_font(13))
    d.line([(24, 282), (376, 282)], fill="#E0E0E0", width=1)
    d.text((24, 294), "Total Amount", fill="#212121", font=_font(14))
    d.text((296, 294), "₹499", fill="#212121", font=_font(14))
    d.text((24, 320), "You will save ₹500 on this order", fill="#388E3C", font=_font(11))
    # Add-ons (basket sneaking – pre-ticked)
    d.rectangle([16, 370, 384, 430], fill="#FFF8E1", outline="#FFD54F")
    d.text((24, 378), "☑  Complete Mobile Protection  ₹149", fill="#212121", font=_font(13))
    d.text((24, 400), "   (auto-added for your safety)", fill="#878787", font=_font(11))
    # Place order button
    d.rectangle([16, 620, 384, 665], fill="#FB641B", outline="#FB641B")
    d.text((128, 633), "PLACE ORDER", fill="white", font=_font(16))
    img.save(OUT_DIR / "2_cart_page.jpg", quality=92)
    print("✓ Created 2_cart_page.jpg")


def make_payment_page():
    """Payment page – ₹49 platform fee appears here for the first time."""
    img = Image.new("RGB", (400, 700), "#FFFFFF")
    d = ImageDraw.Draw(img)
    # Header
    d.rectangle([0, 0, 400, 50], fill="#FB641B")
    d.text((16, 14), "flipkart · Payment", fill="white", font=_font(16))
    # Order summary
    d.rectangle([16, 60, 384, 320], fill="#FFFFFF", outline="#E0E0E0")
    d.text((24, 72), "ORDER SUMMARY", fill="#212121", font=_font(14))
    d.text((24, 100), "Wireless Headphones - Black", fill="#212121", font=_font(12))
    d.text((296, 100), "₹499", fill="#212121", font=_font(12))
    d.text((24, 125), "Delivery Charges", fill="#212121", font=_font(12))
    d.text((270, 125), "FREE", fill="#388E3C", font=_font(12))
    d.text((24, 150), "Complete Mobile Protection", fill="#212121", font=_font(12))
    d.text((296, 150), "₹149", fill="#212121", font=_font(12))
    # Drip pricing – new fee
    d.rectangle([16, 180, 384, 212], fill="#FFEBEE", outline="#EF9A9A")
    d.text((24, 191), "Platform fee", fill="#B71C1C", font=_font(13))
    d.text((296, 191), "₹49", fill="#B71C1C", font=_font(13))
    d.line([(24, 220), (376, 220)], fill="#E0E0E0", width=1)
    d.text((24, 232), "Total Amount", fill="#212121", font=_font(14))
    d.text((270, 232), "₹697", fill="#212121", font=_font(14))
    d.text((24, 258), "(Increased from ₹499 shown earlier)", fill="#B71C1C", font=_font(10))
    # Payment methods
    d.rectangle([16, 340, 384, 500], fill="#FFFFFF", outline="#E0E0E0")
    d.text((24, 352), "PAYMENT METHOD", fill="#212121", font=_font(14))
    d.text((24, 380), "○  UPI", fill="#212121", font=_font(13))
    d.text((24, 408), "○  Credit / Debit Card", fill="#212121", font=_font(13))
    d.text((24, 436), "●  Cash on Delivery  (+₹25 COD charge)", fill="#212121", font=_font(12))
    # Pay button
    d.rectangle([16, 620, 384, 665], fill="#FB641B", outline="#FB641B")
    d.text((90, 633), "PAY ₹697 SECURELY", fill="white", font=_font(16))
    img.save(OUT_DIR / "3_payment_page.jpg", quality=92)
    print("✓ Created 3_payment_page.jpg")


if __name__ == "__main__":
    make_product_page()
    make_cart_page()
    make_payment_page()
    print(f"\nSample screenshots saved to: {OUT_DIR}")

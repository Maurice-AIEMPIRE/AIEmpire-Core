#!/usr/bin/env python3
"""
Stripe Product & Payment Link Creator for AIEmpire.
Creates all products, prices, and payment links for Maurice's revenue streams.
Uses Stripe CLI for operations.
"""

import subprocess
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    name: str
    description: str
    price_eur: int  # in cents
    product_type: str  # "one_time" or "recurring"
    interval: Optional[str] = None  # "month" or "year" for recurring

# ═══════════════════════════════════════════════════
# ALL PRODUCTS FROM DOCS
# ═══════════════════════════════════════════════════

PRODUCTS = [
    # Gumroad Products
    Product(
        name="BMA Profi-Checklisten Pack",
        description="20+ professionelle Checklisten & Protokolle für Brandmeldeanlagen - DIN 14675 konform. Von einem Meister mit 16 Jahren Erfahrung.",
        price_eur=2700,  # 27.00 EUR
        product_type="one_time"
    ),
    Product(
        name="BMA Video-Schulungspaket",
        description="Brandmeldeanlage-Meisterklasse: Esser & Hekatron in der Praxis. 3-5 Stunden Video-Tutorials.",
        price_eur=4700,  # 47.00 EUR
        product_type="one_time"
    ),
    Product(
        name="BMA Troubleshooting-Kompass",
        description="Die 50 häufigsten BMA-Fehler und Lösungen. Spare Servicezeit und finde Fehler in Minuten.",
        price_eur=3700,  # 37.00 EUR
        product_type="one_time"
    ),
    Product(
        name="AI Agent Blueprint - Starter",
        description="Dein erstes AI Agent Framework. Step-by-step Anleitung für den Einstieg in AI Automation.",
        price_eur=4700,  # 47.00 EUR
        product_type="one_time"
    ),
    Product(
        name="AI Side Hustle Playbook",
        description="Die komplette Playbook für 5 AI Side Hustles in 2026 - mit Pricings, Tools, Beispielen.",
        price_eur=9700,  # 97.00 EUR
        product_type="one_time"
    ),
    
    # Fiverr-Style Services (as Stripe Products)
    Product(
        name="AI Automation Setup - Basic",
        description="1 automation task setup with simple chatbot or email sequence.",
        price_eur=3000,  # 30.00 EUR
        product_type="one_time"
    ),
    Product(
        name="AI Automation Setup - Standard",
        description="2-3 moderate automation workflows with AI chatbot and smart email sequences.",
        price_eur=15000,  # 150.00 EUR
        product_type="one_time"
    ),
    Product(
        name="AI Automation Setup - Premium",
        description="4-5 complex automation workflows with full ecosystem integration.",
        price_eur=50000,  # 500.00 EUR
        product_type="one_time"
    ),
    Product(
        name="BMA Expert Consulting - Basic",
        description="1-hour fire alarm system consulting session with basic compliance check.",
        price_eur=20000,  # 200.00 EUR
        product_type="one_time"
    ),
    Product(
        name="BMA Expert Consulting - Standard",
        description="3-hour comprehensive BMA system review with full regulatory assessment.",
        price_eur=75000,  # 750.00 EUR
        product_type="one_time"
    ),
    Product(
        name="BMA Expert Consulting - Premium",
        description="8 hours strategic transformation consulting with AI-powered analysis.",
        price_eur=200000,  # 2000.00 EUR
        product_type="one_time"
    ),
    Product(
        name="Custom AI Agent - Basic",
        description="Single-purpose AI agent with 1-2 core functions and basic NLP.",
        price_eur=50000,  # 500.00 EUR
        product_type="one_time"
    ),
    Product(
        name="Custom AI Agent - Standard",
        description="Multi-purpose AI agent with 3-4 functions and advanced NLP.",
        price_eur=200000,  # 2000.00 EUR
        product_type="one_time"
    ),
    Product(
        name="Custom AI Agent - Premium",
        description="Complex enterprise AI agent with 5+ functions and white-label capability.",
        price_eur=500000,  # 5000.00 EUR
        product_type="one_time"
    ),
]


def run_stripe_cmd(args: list) -> dict:
    """Run a stripe CLI command and return parsed JSON output."""
    cmd = ["stripe"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"  ❌ Stripe error: {result.stderr[:300]}")
            return {}
    except json.JSONDecodeError:
        print(f"  ⚠️ Non-JSON response: {result.stdout[:200]}")
        return {}
    except Exception as e:
        print(f"  ❌ Command failed: {e}")
        return {}


def create_product(product: Product) -> dict:
    """Create a Stripe product with price."""
    print(f"\n📦 Creating: {product.name} (€{product.price_eur/100:.2f})")
    
    # Create product
    prod_result = run_stripe_cmd([
        "products", "create",
        f"--name={product.name}",
        f"--description={product.description}"
    ])
    
    if not prod_result or "id" not in prod_result:
        print("  ❌ Failed to create product")
        return {}
    
    product_id = prod_result["id"]
    print(f"  ✅ Product: {product_id}")
    
    # Create price  
    price_args = [
        "prices", "create",
        f"--product={product_id}",
        f"--unit-amount={product.price_eur}",
        "--currency=eur"
    ]
    
    if product.product_type == "recurring" and product.interval:
        price_args.append(f"--recurring[interval]={product.interval}")
    
    price_result = run_stripe_cmd(price_args)
    
    if not price_result or "id" not in price_result:
        print("  ❌ Failed to create price")
        return {"product_id": product_id}
    
    price_id = price_result["id"]
    print(f"  ✅ Price: {price_id}")
    
    # Create payment link
    link_result = run_stripe_cmd([
        "payment_links", "create",
        "-d", f"line_items[0][price]={price_id}",
        "-d", "line_items[0][quantity]=1"
    ])
    
    payment_url = link_result.get("url", "N/A") if link_result else "N/A"
    print(f"  🔗 Payment Link: {payment_url}")
    
    return {
        "name": product.name,
        "product_id": product_id,
        "price_id": price_id,
        "price_eur": product.price_eur / 100,
        "payment_url": payment_url
    }


def create_all_products():
    """Create all AIEmpire products on Stripe."""
    print("=" * 60)
    print("🚀 AIEmpire Stripe Product Creator")
    print("=" * 60)
    
    results = []
    for product in PRODUCTS:
        result = create_product(product)
        if result:
            results.append(result)
    
    # Save results
    output_file = "stripe_products_live.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 60}")
    print(f"✅ Created {len(results)}/{len(PRODUCTS)} products")
    print(f"📄 Saved to: {output_file}")
    print(f"{'=' * 60}")
    
    # Print summary
    print("\n📊 PAYMENT LINKS SUMMARY:")
    for r in results:
        print(f"  €{r.get('price_eur', 0):>8.2f}  {r.get('name', 'Unknown'):40s}  {r.get('payment_url', 'N/A')}")
    
    return results


if __name__ == "__main__":
    create_all_products()

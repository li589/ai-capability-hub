---
name: geo-visual-opportunity-engine
description: Use when the user wants to turn a product and keyword opportunity into AI-generated visuals, structured product data, localized commerce copy, or publish-ready outputs for Shopify and WooCommerce. Trigger for product image generation, product listing automation, GEO-aware commerce content, Shopify publishing, WooCommerce publishing, or AI-native visual content workflows.
metadata:
  author: GEO-SEO
  version: 3.0.4
  homepage: https://github.com/GEO-SEO/geo-visual-opportunity-engine
  primaryEnv: GOOGLE_API_KEY
  requires:
    env:
      - GOOGLE_API_KEY
      - SHOPIFY_STORE_URL
      - SHOPIFY_ACCESS_TOKEN
      - WOOCOMMERCE_STORE_URL
      - WOOCOMMERCE_CONSUMER_KEY
      - WOOCOMMERCE_CONSUMER_SECRET
    bins:
      - python3
install_source: official
install_method: download
skill_id: official_5LD9X6bp
enabled_at: 1787231137505
version: 1.0.0
name_zh: GEO视觉机会引擎
---

# GEO Visual Opportunity Engine

Use this skill to turn a product and keyword opportunity into AI-generated visuals, structured product data, localized commerce copy, and optional Shopify or WooCommerce publishing.

## Overview

This skill connects GEO opportunity analysis, image generation, product-data synthesis, localization, and commerce publishing in one workflow.

## Best For

- DTC and Shopify teams producing AI-generated product assets at scale
- commerce operators testing product narratives for search and AI-native discovery
- agencies managing cross-market visual content and listing workflows
- teams that want product analysis, visuals, and publishing in one system

## Start With

```text
Generate AI product visuals and commerce copy for this product opportunity
```

```text
Run GEO analysis for this product and keyword before generating assets
```

```text
Create publish-ready Shopify or WooCommerce assets for this product
```

## Core Workflow

GEO Visual Opportunity Engine is an AI-powered commerce workflow that can generate product images using Nano Banana 2 (Google Gemini) and can optionally publish products to Shopify or WooCommerce when publishing is explicitly enabled.

## External Access And Minimum Credentials

This workflow uses external services. Required credentials depend on the actions you enable:

- `GOOGLE_API_KEY`: required for Nano Banana 2 / Gemini image generation
- `SHOPIFY_STORE_URL` and `SHOPIFY_ACCESS_TOKEN`: required only when publishing to Shopify
- `WOOCOMMERCE_STORE_URL`, `WOOCOMMERCE_CONSUMER_KEY`, and `WOOCOMMERCE_CONSUMER_SECRET`: required only when publishing to WooCommerce
- `python3`: required to run the packaged automation code

If publishing credentials are absent:

- the skill can still stop at opportunity analysis, product data synthesis, and image generation
- do not claim live publishing or platform write access unless the matching credentials are present

## Access Policy

Safe default: this skill should stop at analysis, asset generation, and product-data output unless store publishing is explicitly enabled.

- image generation can run independently of commerce publishing
- Shopify publishing is optional and must be explicitly enabled
- WooCommerce publishing is optional and must be explicitly enabled
- do not claim store write access or completed publication unless the matching credentials are present and the publish flags are turned on

## Features

- **Product Data Synthesis**: Auto-generate product titles, descriptions, SKU, prices, inventory
- **AI Image Generation**: Automatically calls Nano Banana 2 to generate product images
- **Multi-Platform Support**: Publish to Shopify and WooCommerce simultaneously
- **Three Image Styles**: White info, lifestyle, and hero images for each product
- **GEO Opportunity Analysis**: Identifies high-priority visual content opportunities

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from src.main import EcommerceAutomator

# Initialize with API key
automator = EcommerceAutomator(google_api_key="your-google-api-key")

# Run complete workflow - one input to finish everything
result = automator.run_complete_workflow(
    product_input="wireless bluetooth headphones",
    country="us",
    language="en",
    generate_images=True,
    publish_to_shopify=False,
    publish_to_woocommerce=False
)

print(result['product_data']['title'])
print(result['status'])
```

### GEO Analysis Only

```python
from src.main import EcommerceAutomator

automator = EcommerceAutomator()

# Run GEO opportunity analysis
result = automator.run_geo_analysis(
    brand="AcmeWatch",
    product="Acme DivePro 5",
    core_keyword="smartwatch water resistance",
    country="us",
    language="en",
    generate_images=True
)

print(f"Found {len(result['opportunities'])} opportunities")
```

### Create Product with Publishing

```python
from src.main import EcommerceAutomator

automator = EcommerceAutomator(
    google_api_key="your-google-api-key",
    shopify_store_url="your-store.myshopify.com",
    shopify_access_token="your-access-token"
)

# Create a product package and optionally publish it
result = automator.create_product(
    product_name="Wireless Bluetooth Headphones Pro",
    category="Electronics",
    base_price=79.99,
    generate_images=True,
    image_style="white_info",
    publish_to_shopify=True,
    publish_to_woocommerce=False
)
```

## API Reference

### EcommerceAutomator

Main class for e-commerce automation.

#### `__init__(google_api_key, shopify_store_url, shopify_access_token, woo_store_url, woo_consumer_key, woo_consumer_secret)`

Initialize the automator with API credentials.

#### `run_complete_workflow(product_input, country='us', language='en', generate_images=True, publish_to_shopify=False, publish_to_woocommerce=False, output_dir='output')`

**Unified workflow** - One input completes the entire process:
1. Analyze GEO opportunities
2. Synthesize product data (title, description, SKU, price)
3. Generate AI images
4. Publish to e-commerce platforms

#### `run_geo_analysis(brand, product, core_keyword, country, language, competitors, platform_focus, generate_images)`

Run GEO opportunity analysis with image generation.

#### `create_product(product_name, category, base_price, description, language, target_platforms, generate_images, image_style, publish_to_shopify, publish_to_woocommerce)`

Complete e-commerce product creation workflow.

## Configuration

### Environment Variables

- `GOOGLE_API_KEY` - Google API Key for Nano Banana 2 image generation
- `SHOPIFY_STORE_URL` - Shopify store URL
- `SHOPIFY_ACCESS_TOKEN` - Shopify Admin API access token
- `WOOCOMMERCE_STORE_URL` - WooCommerce store URL
- `WOOCOMMERCE_CONSUMER_KEY` - WooCommerce API consumer key
- `WOOCOMMERCE_CONSUMER_SECRET` - WooCommerce API consumer secret

## Image Styles

- **white_info**: Clean white background, product-focused infographic
- **lifestyle**: Real-world场景 with human interaction, photorealistic
- **hero**: Dramatic hero shot with commercial photography quality

## Version

3.0.0

## Author

Tim (sales@dageno.ai)

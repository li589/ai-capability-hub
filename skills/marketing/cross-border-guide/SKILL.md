---
name: cross-border-guide
description: Navigate cross-border ecommerce shipping requirements, customs documentation, duties estimation, and carrier selection for international order fulfillment.
install_source: official
install_method: download
skill_id: official_5Ykht0E1
enabled_at: 1787231040898
version: 1.0.0
name_zh: 跨境指南
---

# Cross-Border Guide

Selling internationally means dealing with customs declarations, import duties, carrier restrictions, and documentation requirements that vary by destination country. Getting any of these wrong leads to shipments held at customs, unexpected duty charges billed to customers, or outright package seizures. This skill helps ecommerce sellers plan and execute cross-border fulfillment by walking through the specific requirements for their product type, origin, and destination markets.

## Use when

- You are expanding your ecommerce store to ship internationally for the first time and need to understand customs documentation, HS codes, and duty estimation for your product categories
- A customer in another country placed an order and you need to determine the correct shipping method, required customs forms, and estimated landed cost including duties and taxes before fulfilling
- You are evaluating whether to use DDP (Delivered Duty Paid) or DDU (Delivered Duty Unpaid) shipping terms for a new international market and need to understand the cost and customer experience tradeoffs
- Your cross-border shipments are getting held at customs repeatedly and you want to audit your commercial invoices, packing lists, and HS code classifications to identify what is causing delays

## What this skill does

This skill analyzes your product details, shipping origin, and destination market to generate a comprehensive cross-border fulfillment plan. It covers HS code classification guidance for your product type, estimated duty and tax rates for the destination country, required documentation (commercial invoice fields, certificates of origin, regulatory declarations), carrier options ranked by cost, speed, and customs clearance reliability, and packaging and labeling requirements specific to the destination. The analysis accounts for de minimis thresholds, restricted and prohibited item lists, and common compliance pitfalls that cause shipment delays or returns.

## Inputs required

- **Product description** (required): What you are shipping — include materials, function, and value. For example, "stainless steel insulated water bottle, unit cost $12, retail $29.99." The more specific you are, the more accurate the HS code and duty estimate.
- **Origin country** (required): The country from which the shipment will be dispatched (e.g., China, United States, Vietnam).
- **Destination country** (required): The country where the customer or warehouse will receive the goods (e.g., United Kingdom, Australia, Canada).
- **Shipment value and quantity** (required): Total declared value and number of units per shipment — this determines whether de minimis thresholds apply and affects duty calculations.
- **Shipping preference** (optional): Whether you prefer express courier (DHL, FedEx, UPS), postal service, or freight forwarding. Helps tailor carrier recommendations to your budget and speed requirements.

## Output format

The output is organized into five sections. First, an HS code recommendation with the suggested 6-digit or 8-digit harmonized code, a plain-language explanation of why that classification applies, and notes on common misclassification risks for similar products. Second, a duty and tax estimate showing the applicable tariff rate, estimated VAT or GST, and total landed cost calculation with a breakdown of each component. Third, a documentation checklist listing every required form and field for the origin-destination pair, including commercial invoice requirements, certificates of origin, and any product-specific regulatory declarations. Fourth, a carrier comparison table ranking 3-4 carrier options by estimated cost, transit time, customs clearance support level, and tracking quality. Fifth, a compliance alert section flagging any restricted item concerns, labeling requirements, or recent regulatory changes for the destination market that could affect the shipment.

## Scope

- Designed for: Ecommerce operators, DTC brands, and marketplace sellers shipping internationally
- Platform context: Platform-agnostic (applicable to Shopify, Amazon, TikTok Shop, and independent stores)
- Language: English

## Limitations

- Duty and tax estimates are based on published tariff schedules and may not reflect temporary trade agreements, anti-dumping duties, or very recent tariff changes
- HS code suggestions are guidance only and should be verified with a licensed customs broker for high-value or high-volume shipments
- Carrier pricing is estimated based on general rate structures and does not reflect your specific negotiated rates or account discounts

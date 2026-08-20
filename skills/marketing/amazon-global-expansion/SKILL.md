---
name: amazon-global-expansion
description: "Amazon global marketplace expansion agent. Plan your entry into UK, EU (Germany, France, Italy, Spain), Japan, Canada, and other Amazon markets. Covers VAT registration, compliance requirements, listing localization, currency strategy, and market sizing. Triggers: amazon global, amazon uk, amazon europe, amazon germany, amazon japan, amazon canada, international expansion, vat registration, eu compliance, marketplace expansion, amazon eu, amazon fba europe, global selling, amazon international, cross-border ecommerce"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-global-expansion
install_source: official
install_method: download
skill_id: official_ASLbkNTa
enabled_at: 1787231101878
version: 1.0.0
name_zh: 亚马逊全球市场扩张助手
---

# Amazon Global Marketplace Expansion

Expand beyond Amazon US into UK, EU, Japan, Canada, and more. Get market entry plans, compliance requirements, localization strategy, and VAT guidance for each marketplace.

## Commands

```
expand analyze [market]         # full market entry analysis for a country
expand vat [country]            # VAT/tax registration requirements
expand listing [product] [lang] # localization checklist for target market
expand compare [market1] [market2]  # compare two markets for expansion
expand checklist [market]       # pre-launch compliance checklist
expand currency                 # multi-currency pricing strategy
expand roadmap                  # prioritized global expansion roadmap
expand fees [market]            # FBA fees and referral rates by market
```

## What Data to Provide

- **Current market** — where you sell now (usually US)
- **Product category** — for market-specific compliance
- **Monthly revenue** — to estimate expansion ROI
- **Target markets** — which countries interest you
- **Team capacity** — can you handle customer service in other languages?

## Market Overview

### Amazon EU Marketplaces

| Market | Language | Market Size | Entry Difficulty |
|--------|----------|------------|-----------------|
| Germany (DE) | German | Largest EU Amazon | Medium (strict compliance) |
| UK | English | 2nd largest | Low (English, Brexit compliance) |
| France (FR) | French | 3rd largest | Medium |
| Italy (IT) | Italian | Growing fast | Medium |
| Spain (ES) | Spanish | Growing | Low-Medium |
| Netherlands (NL) | Dutch | New, growing | Low |
| Sweden (SE) | Swedish | New | Low |

### Other Major Markets

| Market | Notes | Entry Difficulty |
|--------|-------|-----------------|
| Canada (CA) | English/French, close to US ops | Very Low |
| Japan (JP) | Huge market, unique consumer behavior | High |
| Australia (AU) | Growing, English | Low-Medium |
| UAE/Saudi (ME) | Emerging, strong growth | Medium |
| India (IN) | Domestic sellers preferred | High |
| Brazil (BR) | Complex tax structure | Very High |

## Market Entry Priority Framework

Score each market:
1. **Market size** (1-3): Revenue potential
2. **Competition** (1-3): How saturated is your category?
3. **Operational ease** (1-3): Language, compliance, logistics complexity
4. **Synergy with current ops** (1-3): Can you reuse existing inventory/listings?

**Start with highest total score.**

**Typical recommended sequence:**
1. Canada (lowest effort, shares US FBA network via NARF)
2. UK (English, large market, EU-independent post-Brexit)
3. Germany (largest EU market)
4. France -> Italy -> Spain (bundle via Pan-European FBA)

## VAT Requirements by Market

### European Union
- **Threshold eliminated** since July 2021 -- VAT required from first sale
- Register in each country OR use OSS (One Stop Shop) for B2C sales <=10,000/market
- If using Pan-European FBA: must register in all countries where Amazon stores your inventory (typically DE, FR, IT, ES, PL, CZ)
- **Required documents**: Business registration, proof of trading

**Recommended services**: Taxjar, Avalara, Hellotax, SimplyVAT

### United Kingdom
- UK VAT separate from EU post-Brexit
- Register if sales >85,000/year OR if using Amazon FBA in UK (storage = nexus)
- HMRC registration: https://www.gov.uk/vat-registration
- **UK EORI number** required for importing goods

### Canada
- GST/HST registration required if revenue >CAD $30,000/year
- Quebec has separate QST
- Much simpler than EU -- single federal system

### Japan
- Consumption Tax (10%) registration required
- Japanese business address or local representative may be needed
- JCT registration via NTA (National Tax Agency)

## Listing Localization Requirements

### Germany (Most Important EU Market)
- **Language**: Must be in German -- Google Translate quality is NOT acceptable
- **Legal requirements**:
  - Manufacturer address in Germany/EU (or authorized rep)
  - CE marking mandatory for electronics, toys, PPE
  - WEEE registration (for electronics)
  - Extended Producer Responsibility (EPR) for packaging
- **Cultural notes**: Germans value technical precision, certifications, thoroughness

### Japan (Unique Requirements)
- Japanese listing required (not just translation -- cultural adaptation)
- PSE mark for electronics (mandatory)
- Many product-specific certifications (food contact materials, cosmetics)
- Customer service response time expectations: within 24 hours, in Japanese
- Returns policy: Japanese customers expect hassle-free returns

### UK (Post-Brexit)
- **UKCA mark** replacing CE mark for many products
- UK Responsible Person required for regulated products
- UK EPR for packaging

## Pan-European FBA vs. Multi-Country Inventory

| Strategy | Pros | Cons |
|----------|------|------|
| **Pan-EU FBA** | Amazon distributes inventory, faster delivery | VAT in 5-7 countries required |
| **EFN (European Fulfillment Network)** | Single country storage | Slower delivery, higher fees cross-border |
| **Multi-Country Inventory** | Control where stock goes | Manage inbound to each country |

**Recommendation for beginners**: Start with EFN (one country) -> upgrade to Pan-EU once VAT registered everywhere.

## Currency & Pricing Strategy

- Never just convert USD price to local currency (e.g., $29.99 -> 29.99 is wrong)
- Research local competitor pricing -- markets have different price points
- Factor in: local FBA fees (vary by market), VAT (included in displayed price in EU/UK), exchange rate fluctuation
- Price in "charm pricing" for local market: 24.99, 27.99, 2,980 yen

## Pre-Launch Checklist by Market

### Universal
- [ ] VAT/tax registration complete
- [ ] Listing translated by native speaker (not machine translation)
- [ ] Local compliance requirements researched
- [ ] Customer service coverage in local language (or English for UK/CA)
- [ ] Pricing set at local market rates
- [ ] Inbound shipping route established

### EU-Specific
- [ ] CE/UKCA/other product certification
- [ ] EPR packaging registration
- [ ] WEEE/battery registration (if applicable)
- [ ] Authorized EU Representative named on packaging

### Japan-Specific
- [ ] PSE mark (electronics)
- [ ] Japanese listing by professional translator
- [ ] Returns policy matches JP customer expectations

## Output Format

1. **Market Entry Analysis** -- opportunity size, competition, compliance overview
2. **VAT Registration Roadmap** -- step-by-step for target market
3. **Localization Checklist** -- listing, packaging, compliance
4. **Pricing Recommendation** -- local market pricing strategy
5. **Launch Sequence** -- prioritized order to enter multiple markets

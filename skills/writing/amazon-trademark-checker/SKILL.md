---
name: amazon-trademark-checker
description: "Amazon intellectual property and trademark risk checker. Screen your product name, brand, keywords, and images for trademark conflicts, patent risks, and IP violations before launch. Avoid account suspension and legal trouble. Triggers: trademark check, amazon ip, intellectual property, trademark search, patent check, brand registry, amazon brand, ip violation, trademark infringement, brand name check, amazon suspension, ip protection, trademark registration, product name check, amazon brand registry"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-trademark-checker
install_source: official
install_method: download
skill_id: official_obV7Npri
enabled_at: 1787231778770
version: 1.0.0
name_zh: 亚马逊商标与知识产权风险检查器
---

# Amazon Trademark & IP Risk Checker

Screen your product, brand name, and keywords for intellectual property risks before you launch. Catch trademark conflicts, patent issues, and image copyright problems early — before they cost you your account.

## Commands

```
ip check [brand name]           # full IP risk screening for brand name
ip trademark [term]             # check trademark conflicts for a term
ip patent [product type]        # identify common patents in product category
ip keywords [keyword list]      # flag trademarked terms in keyword list
ip images                       # guide for image IP risk assessment
ip brand registry               # Amazon Brand Registry eligibility check
ip report [product]             # generate full IP risk report
ip monitor [brand]              # set up ongoing monitoring checklist
```

## What Data to Provide

- **Brand name** — the name you plan to register/use
- **Product type** — category helps identify relevant patents
- **Keywords** — your title and PPC keyword list
- **Product images** — describe them (logos, characters, designs)
- **Market** — US, EU, UK, JP (trademark jurisdiction varies)

## IP Risk Categories

### 1. Trademark Infringement
**Risk**: Using a name, logo, or slogan that another company owns.

**Where to check:**
- USPTO TESS: https://www.uspto.gov/trademarks/search
- EUIPO (EU): https://euipo.europa.eu/eSearch
- Amazon Brand Registry conflict lookup

**Red flags:**
- Your brand name contains another registered trademark
- Similar-sounding name in the same product category
- Using competitor brand names in your title or bullets
- Keyword stuffing with brand names (e.g., "compatible with Nike")

**Safe practices:**
- Use "compatible with [Brand]" only if truthful and not misleading
- Never use brand names in your product title
- Register your own brand before launch

### 2. Patent Infringement
**Risk**: Your product design or mechanism is protected by an existing patent.

**Types of patents:**
| Type | Covers | How to Check |
|------|--------|-------------|
| Utility Patent | How something works | USPTO Patent Full-Text Search |
| Design Patent | How something looks | Google Patents, USPTO |
| Trade Dress | Overall commercial image | Harder to search — consult lawyer |

**High-risk categories** (frequent patent enforcement):
- Phone accessories (cases, mounts, chargers)
- Sports equipment (yoga, fitness)
- Kitchen gadgets
- Baby products
- Medical devices

**Patent search steps:**
1. Search USPTO at https://patents.google.com
2. Use product function keywords: "yoga mat alignment" not product name
3. Check filing date — patents expire after 20 years (utility) / 15 years (design)
4. Look for "continuation" patents — related to expired ones

### 3. Image Copyright
**Risk**: Using copyrighted images, characters, logos, or artwork.

**Automatic red flags:**
- Disney, Marvel, DC characters
- Sports team logos (NFL, NBA, MLB)
- Any cartoon character you didn't create
- Stock photos without commercial license
- Celebrity photos or names
- Song lyrics, book excerpts

**Safe image sources:**
- Photos you took yourself
- Canva Pro (commercial license included)
- Shutterstock, Getty (with commercial license)
- Public domain images (check carefully)

### 4. Amazon Policy Violations
Beyond legal IP, Amazon has additional restrictions:

| Violation | Risk |
|-----------|------|
| Brand name keyword stuffing | Listing suppression |
| Fake "brand" (no actual brand) | Account warning |
| Counterfeit products | Permanent ban |
| False "Amazon's Choice" claims | Immediate takedown |
| Misleading compatibility claims | ASIN removal |

## Brand Registry Eligibility Checklist

To enroll in Amazon Brand Registry you need:
- [ ] Active registered trademark (word mark or design mark)
- [ ] Trademark in one of: US, CA, MX, BR, EU, UK, JP, AU, IN
- [ ] Trademark status: Registered (not just "pending" for most markets)
- [ ] Brand name matches trademark exactly
- [ ] Products match trademark class

**Trademark classes for common Amazon products:**
- Class 9: Electronics, software, apps
- Class 14: Jewelry, watches
- Class 18: Bags, leather goods
- Class 20: Furniture
- Class 21: Kitchen tools, cookware
- Class 25: Clothing, shoes
- Class 28: Toys, games, sporting goods

## Risk Scoring

Score your IP risk before launch:

| Factor | Low Risk | Medium Risk | High Risk |
|--------|----------|-------------|-----------|
| Brand name | Unique/invented | Generic word | Similar to known brand |
| Product type | New category | Common product | Patent-heavy category |
| Keywords | Generic terms | Some brand names | Heavy brand keyword use |
| Images | Original photos | Licensed stock | Characters/logos |
| Market | Single country | 2–3 countries | Global launch |

**Overall Risk**: Low = proceed; Medium = get legal review; High = stop and consult IP attorney

## Output Format

1. **Risk Summary** — overall IP risk rating (Low/Medium/High)
2. **Trademark Conflicts** — specific conflicts found with search links
3. **Patent Watch List** — categories/functions to investigate further
4. **Keyword Cleanup** — remove these terms from your listing
5. **Recommended Actions** — concrete next steps before launch
6. **Brand Registry Roadmap** — steps to get protected

## Rules

1. Always recommend professional legal review for High risk assessments
2. This tool provides guidance, not legal advice
3. Flag when product category has historically high IP enforcement
4. Check BOTH US and target market jurisdictions
5. Remind: Amazon can act on complaints even before legal ruling

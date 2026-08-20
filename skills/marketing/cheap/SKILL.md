---
name: cheap
description: Find the cheapest meaningful visible price for a user-provided product name across major Chinese shopping platforms such as Taobao, Tmall, JD.com, Pinduoduo, Vipshop, and similar marketplaces. Use when the user asks where a product is cheapest, wants a quick cross-platform price check, wants the lowest current visible price, wants to compare the same product across Chinese e-commerce platforms, or asks questions like "哪个最便宜", "哪里买最便宜", "帮我比价", "全网找最低价", "哪个平台便宜", "哪里下单最划算", or "帮我找最低价".
install_source: official
install_method: download
skill_id: official_jFaRidz3
enabled_at: 1787231096821
version: 1.0.0
name_zh: 低价查找
---

# Cheap

Find the cheapest meaningful visible price for a product across Chinese e-commerce platforms.

Use this skill when the user provides a product name and wants the lowest current visible price, the cheapest platform, or a quick cross-platform price comparison.

This skill operates in two modes:
- **Mode 1: Price-accessible mode** — enough platform price evidence is accessible to support a meaningful comparison.
- **Mode 2: Price-limited mode** — platform access, product matching, or price visibility is too weak for a strong cheapest-price claim.

Read these references as needed:
- `references/product-matching.md` when deciding whether two listings are likely the same product
- `references/platform-playbook.md` when searching different Chinese shopping platforms
- `references/price-judgment.md` when deciding which price counts as the meaningful cheapest price
- `references/output-patterns.md` when preparing the final answer
- `references/failure-modes.md` when product matching, pricing, or platform access is weak
- `references/examples.md` when examples help calibrate the result format

## Workflow

1. Identify the product.
   - Accept a product name.
   - If the product is too broad or ambiguous, ask one short clarifying question for the most decision-relevant detail, such as brand, model, size, or key variant.

2. Check price accessibility.
   - Search across relevant Chinese platforms.
   - Decide which mode applies:
     - **Mode 1** if enough visible price evidence is accessible and comparable.
     - **Mode 2** if platform access, listing clarity, or price conditions are too weak for a strong cheapest-price claim.

3. If Mode 1, compare meaningful prices.
   - Prefer Taobao, Tmall, JD.com, Pinduoduo, and other clearly relevant platforms.
   - Use only currently visible price evidence.
   - Match comparable listings by brand, model, specs, quantity, version, and bundle contents.
   - Distinguish straightforward visible price from coupon-only, member-only, deposit/pre-sale, bundle-distorted, or variant-mismatched prices.

4. If Mode 2, do not fake precision.
   - State that the currently accessible evidence is too weak for a strong cheapest-price claim.
   - Explain whether the issue is platform access, weak product matching, or distorted price conditions.
   - Give only a limited conclusion when still useful.

5. Give the result.
   Cover:
   - cheapest platform or listing found when supportable
   - visible price evidence actually available
   - comparable alternatives when supportable
   - matching confidence
   - any caveats about variants, bundles, coupons, seller trust, or access limits

## Output

Use this structure unless the user asks for something else.

### Mode 1 output
Use when enough price evidence is accessible.

#### Cheapest Found
State the lowest meaningful visible price found and on which platform.

#### Comparable Options
List the main comparable prices found on other platforms.

#### Match Confidence
State whether the compared listings look like the same product:
- High
- Medium
- Low

#### Caveats
State any important risks, such as:
- unclear variant match
- bundle differences
- coupon or membership pricing
- deposit or pre-sale pricing
- seller quality concerns
- incomplete platform access

#### Final Advice
Give a direct buying suggestion in plain language.

### Mode 2 output
Use when accessible evidence is too weak for a strong lowest-price claim.

#### Current Best Signal
State the weakest still-usable price clue, if any.

#### Why No Strong Cheapest Claim
Explain whether the issue is:
- platform access limits
- weak listing comparability
- unclear price conditions
- incomplete platform coverage

#### What Remains Unverified
State what cannot yet be confirmed.

#### Final Advice
Give a cautious conclusion without pretending a definitive lowest price was found.

## Quality bar

Do:
- compare like-for-like listings
- say when the cheapest visible option may not be the best option
- distinguish real low price from misleading low price
- be explicit when matching confidence is weak

Do not:
- compare different variants as if they were the same item
- treat coupon-only or pre-sale prices as normal prices without warning
- claim full-market coverage when platform access is incomplete
- invent prices or listing details

## Limitation handling

If the product is too ambiguous:
- ask one short clarifying question

If platform access is incomplete:
- switch to Mode 2 unless a narrower Mode 1 comparison is still supportable
- say which platforms were actually checked
- avoid claiming a definitive all-platform lowest price
- do not present a partial platform scan as a full-market cheapest-price result

If listing comparability is weak:
- lower confidence
- explain what may not match cleanly

If the visible lowest number depends on unclear conditions:
- do not present it as the straightforward cheapest option without warning

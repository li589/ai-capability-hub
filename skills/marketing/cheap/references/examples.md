# Examples Reference

Reuse the logic, not the exact wording.

The first group below reflects **Mode 1: Price-accessible mode**. The last example reflects **Mode 2: Price-limited mode**.

## Example 1
Input: "帮我找 iPhone 15 128GB 哪里最便宜"

Good result shape:
- Cheapest Found: Pinduoduo, visible price XXXX
- Comparable Options: JD.com XXXX, Tmall XXXX
- Match Confidence: Medium
- Caveats: seller quality and variant verification matter
- Final Advice: choose the cheapest option only if the listing is clearly the same version and seller trust is acceptable

## Example 2
Input: "帮我比价：戴森吹风机 HD15"

Good result shape:
- Cheapest Found: Tmall official store or another platform if clearly lower
- Comparable Options: JD.com, Vipshop, Taobao
- Match Confidence: High
- Caveats: bundle contents may differ
- Final Advice: if price gap is small, prefer the more trustworthy official-style listing

## Example 3
Input: "盒马有机牛奶哪里最便宜"

Good result shape:
- If cross-platform comparability is weak, say so
- Ask one short clarification if needed
- Avoid fake precision when the product identity is not cleanly comparable across platforms

## Example 4
Input: "帮我找京东和拼多多上最便宜的小米 67W 充电器"

Good result shape:
- Cheapest Found: one platform with visible comparable price
- Comparable Options: the other platform plus any clearly comparable official-style listing
- Match Confidence: High or Medium depending on bundle/version clarity
- Caveats: watch for cable included vs charger-only differences
- Final Advice: if the price gap is small, prefer the cleaner same-spec listing

## Example 5
Input: "帮我找最便宜的 Dyson Airwrap"

Good result shape:
- If visible low prices vary wildly across platforms, lower match confidence
- Flag refurbished-like, accessory-missing, or suspiciously low listings if comparability is weak
- Avoid presenting the raw lowest number as the meaningful cheapest price

## Example 6: Mode 2 / price-limited case
Input: "帮我找最便宜的 Anker Soundcore Life Q30"

Good result shape:
- Current Best Signal: only partial platform price clues are accessible
- Why No Strong Cheapest Claim: some major platforms are blocked, weakly readable, or not clearly comparable
- What Remains Unverified: full cross-platform lowest comparable price
- Final Advice: treat the current result as partial rather than definitive

# Taobao Competitor Analyzer

Cross-platform shopping decision skill for Taobao users.

This skill checks the same or closest-matching product on:
- JD.com
- Pinduoduo
- Vipshop

Then it answers the question users actually care about:

`Should I keep buying this on Taobao, switch platforms, or wait?`

## What It Does

- Compares visible prices across major Chinese marketplaces
- Matches brand, model, spec, count, and packaging before comparing price
- Flags near-match risk instead of pretending similar items are identical
- Distinguishes list price from coupon price, subsidy price, member price, and group-buy price
- Weighs seller trust, shipping, and after-sales guarantees
- Returns a buying recommendation, not just raw search results

## Best Use Cases

- Compare a Taobao listing with JD / PDD / Vipshop
- Check whether a "cheaper" result is actually the same SKU
- Decide if it is worth switching platforms
- Do fast competitor research for consumer products
- Find the lowest visible comparable price with caveats

## Example Prompts

- `帮我查这个淘宝商品在京东、拼多多、唯品会有没有同款`
- `别只比价，告诉我哪个平台更值得买`
- `这个淘宝商品换到京东买值不值`
- `Compare this Taobao product with JD, PDD, and Vipshop and recommend where to buy`

## Output Style

The skill is optimized to return:
- recommended platform
- lowest visible comparable price
- whether the comparison is apples-to-apples
- major risks and caveats
- a direct buy / wait / avoid recommendation

## Positioning

This is not a generic shopping browser helper.

It is a focused purchase-decision skill for users who want:
- faster price comparison
- fewer fake "cheap" matches
- clearer marketplace tradeoff analysis

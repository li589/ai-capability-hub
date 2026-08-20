# Browser Workflow Guide

## Overview

This skill supports browser automation for JD.com shopping with clear safety boundaries.

## Supported Operations

| Operation | Login Required | Description |
|-----------|----------------|-------------|
| Search | No | Search products with filters |
| View Product | No | Read specs, price, reviews |
| Compare | No | Side-by-side comparison |
| Add to Cart | Yes | Add selected item |
| View Cart | Yes | Review cart contents |
| Apply Coupons | Yes | Check and apply discounts |
| Generate Order Preview | Yes | Calculate final price |
| Payment | **Never** | User only |

## Workflow Steps

### 1. Discovery (Public Pages)
```javascript
// Navigate to search
browser.navigate("https://search.jd.com/Search?keyword=...")

// Extract results
snapshot.extract({
  title: ".p-name",
  price: ".p-price .J_price",
  shop: ".p-shop",
  rating: ".p-commit"
})
```

### 2. Product Detail
```javascript
// Open product page
browser.navigate(productUrl)

// Extract details
snapshot.extract({
  title: ".sku-name",
  price: ".price",
  promotions: ".prom-words",
  specs: "#detail .Ptable",
  reviews: ".comment-item"
})
```

### 3. Cart Operations (Login Required)
```javascript
// Add to cart
browser.click("#InitCartUrl")

// View cart
browser.navigate("https://cart.jd.com/cart_index/")

// Extract cart info
snapshot.extract({
  items: ".item-list .item-item",
  subtotal: ".amount .sum",
  coupons: ".coupon-list"
})
```

### 4. Order Preview (Login Required)
```javascript
// Proceed to checkout
browser.click(".common-submit-btn")

// Extract order summary
snapshot.extract({
  address: ".address-list .selected",
  shipping: ".delivery-list .selected",
  items: ".goods-list .goods-item",
  coupons: ".coupon-item.selected",
  total: ".summary-price .price"
})
```

## Safety Rules

1. **Always announce** before browser actions
2. **Stop at payment** - never proceed to payment
3. **Ask before login** - get explicit consent
4. **Show evidence** - snapshot key information
5. **Handoff clearly** - tell user next manual steps

## Login Detection

```javascript
// Check if logged in
const isLoggedIn = await browser.evaluate(() => {
  return !!document.querySelector('.user-name') || 
         !!document.querySelector('.nickname')
})

if (!isLoggedIn) {
  // Prompt user to login
}
```

## Common Selectors

| Element | Selector |
|---------|----------|
| Search box | `#key` |
| Search button | `.button` |
| Product title | `.p-name a` |
| Price | `.p-price .J_price` |
| Shop name | `.p-shop .J_im_icon` |
| Add to cart | `#InitCartUrl` |
| Cart count | `#J_cart_num` |
| Coupon input | `.coupon-code-input` |
| Address | `.address-list .selected` |
| Submit order | `.common-submit-btn` |

## Error Handling

| Scenario | Action |
|----------|--------|
| CAPTCHA | Hand to user |
| Login required | Ask user first |
| Out of stock | Report and suggest alternatives |
| Price changed | Alert user before proceeding |
| Coupon invalid | Try alternatives or report |

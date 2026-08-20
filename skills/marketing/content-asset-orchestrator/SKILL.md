---
name: content-asset-orchestrator
description: Plan, organize, and audit ecommerce content assets across short video (TikTok/Douyin), Xiaohongshu posts, Amazon A+ content, Shopify PDP images, email banners, and Meta/Instagram creative. Use when content teams need a content production brief, asset gap audit, workflow calendar, or multi-channel content strategy without live DAM, analytics, or social API access.
install_source: official
install_method: download
skill_id: official_L3C0LAlv
enabled_at: 1787231065680
version: 1.0.0
name_zh: 内容资产编排器
---

# Content Asset Orchestrator

## Overview

Use this skill to turn rough content goals, channel priorities, and production constraints into an organized content operations brief. It applies a built-in content type framework, channel requirement matrix, and production workflow to generate an actionable asset plan.

This MVP is heuristic. It does **not** connect to live social accounts, DAM systems, analytics platforms, or content management tools. It relies on the user's provided content context, channel mix, and production resources.

## Trigger

Use this skill when the user wants to:
- plan a content production schedule across TikTok, Xiaohongshu, Amazon, Shopify, email, or Meta
- audit content assets for a product launch, campaign, or seasonal push
- identify content gaps across format types (short video, image, copy, UGC)
- build a content brief for a creator, photographer, or copywriter
- sequence content types across awareness, consideration, and conversion stages

### Example prompts

- "Help me plan content for our summer campaign across TikTok, Xiaohongshu, and Amazon A+"
- "Audit our current content assets for gaps before our product launch"
- "Create a content production brief for our DTC brand's new SKU"
- "What content should we produce this month for our Shopify and Meta channels?"

## Workflow

1. Capture the campaign or production window, target channels, and content goals.
2. Map content types to channels and identify required formats (video, image, copy, UGC).
3. Audit existing assets for completeness, quality, and channel fit.
4. Identify production gaps and assign owners or resource needs.
5. Return a markdown content operations brief with production calendar and asset brief.

## Inputs

The user can provide any mix of:
- campaign window: specific dates, seasonal push, or general monthly planning
- target channels: TikTok, Douyin, Xiaohongshu, Amazon A+, Shopify PDP, email, Meta, Instagram, WeChat
- content goal: awareness, traffic, conversion, UGC seeding, review collection, SEO
- product or SKU context: new launch, best seller, seasonal, clearance
- existing asset inventory: what formats already exist (video, images, copy, UGC)
- production resources: in-house team, agency, creator, photographer, copywriter
- budget for content production

## Outputs

Return a markdown brief with:
- content strategy summary (goal, channels, audience)
- channel requirement matrix (format, dimension, length, caption style)
- content type coverage map (what exists vs. what is needed)
- production gap analysis and asset priority list
- production calendar by week or content type
- brief for each content asset (video, image, copy, UGC) with key messages and format notes
- distribution and posting cadence recommendations

## Safety

- No live social accounts, analytics, DAM, or content management tool access.
- Content recommendations are directional; platform policies and creative quality determine actual performance.
- Do not claim guaranteed engagement or conversion lift from content assets.
- Brand voice and creative decisions remain with the content team.

## Best-fit Scenarios

- small-to-medium content teams managing 3-8 channels without a dedicated content director
- brands launching new products and needing a structured content production sequence
- operators transitioning from single-channel to multi-channel content operations

## Not Ideal For

- real-time content performance tracking, automated posting, or live social media management
- teams with enterprise-scale content operations requiring DAM or MAM integrations
- workflows that require automated approval routing or compliance review

## Acceptance Criteria

- Return markdown text.
- Include channel requirement matrix, gap analysis, and production calendar.
- Cover at least 3 channels with specific format requirements.
- Make resource assumptions explicit.
- Keep the brief practical for content teams and ecommerce operators.

---
name: tiktok-influencer-tracker
description: "TikTok creator/influencer management, sample tracking, and fulfillment analytics agent. Manage creator relationships, track sample shipments, analyze influencer performance, and optimize your TikTok Shop creator program. Triggers: tiktok influencer, creator management, tiktok creator, sample tracking, influencer outreach, tiktok affiliate, creator program, ugc management, influencer analytics, tiktok shop creator, creator collaboration, kol management"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/tiktok-influencer-tracker
install_source: official
install_method: download
skill_id: official_HEPa5QPQ
enabled_at: 1787231147259
version: 1.0.0
name_zh: TikTok 创作者与网红管理器
---

# TikTok Creator & Influencer Manager

Manage your TikTok creator program end-to-end — from outreach and collaboration to sample tracking, content performance, and affiliate commission analysis. Build and scale a creator network that drives consistent TikTok Shop revenue.

## Commands

```
creator add <username>            # add creator to management database
creator outreach <creator>        # generate outreach message for creator
creator profile <username>        # analyze creator profile and fit score
creator sample <creator> <product> # log sample shipment to creator
creator track                     # track all pending sample shipments
creator content <creator>         # log and analyze creator's content performance
creator commission <creator>      # calculate affiliate commission earned
creator rank                      # rank all creators by performance
creator report <period>           # full creator program performance report
creator recruit <niche>           # find creator recruitment criteria for a niche
```

## What Data to Provide

- **Creator username/handle** — TikTok username
- **Creator profile data** — follower count, engagement rate, niche
- **Sample shipment info** — product sent, date shipped, tracking number
- **Content performance** — views, likes, GMV driven per video
- **Commission data** — sales attributed to each creator

## Creator Management Framework

### Creator Tier Classification

**Mega influencers** (1M+ followers):
- Reach: Massive
- Cost: High ($1,000-10,000+ per post)
- ROI: Unpredictable, good for brand awareness
- Sample value: Free + commission (10-15%)
- Best for: Brand launches, viral moments

**Macro influencers** (100K-1M followers):
- Reach: Large
- Cost: $200-2,000 per post
- ROI: Moderate, trackable via affiliate
- Sample value: Free + 15-20% commission
- Best for: Product launches, key market segments

**Mid-tier creators** (10K-100K followers):
- Reach: Meaningful niche audiences
- Cost: $50-500 per post or free samples only
- ROI: Good, highly measurable
- Sample value: Free sample + 20-25% commission
- Best for: Most brands, consistent sales engine

**Micro influencers** (<10K followers):
- Reach: Small but highly engaged
- Cost: Free samples or $0-50
- ROI: Excellent per dollar
- Sample value: Product only (no fee)
- Best for: Product validation, review generation

**Recommendation**: Build 80% of program on mid-tier and micro creators (volume + ROI), 20% on macro for reach.

### Creator Fit Score

Rate each creator 1-5 on 4 dimensions:

1. **Niche alignment** — does their content match your product category?
2. **Audience match** — does their audience match your buyer profile?
3. **Engagement rate** — likes+comments / followers (benchmark: >3%)
4. **Content quality** — production value and authenticity

**Fit score formula:**
```
Total = Niche × 3 + Audience × 3 + Engagement × 2 + Quality × 2
Max score = 50

35+: Strong fit — prioritize outreach
25-34: Good fit — worth pursuing
15-24: Moderate fit — lower priority
<15: Poor fit — skip
```

**Engagement rate benchmarks:**
```
Nano (<10K):    >6% engagement is strong
Micro (10-50K): >4% engagement is strong
Mid (50-500K):  >2.5% engagement is strong
Macro (500K+):  >1.5% engagement is strong
```

### Outreach Message Templates

**Initial outreach (product gifting):**
```
Hi [Creator Name],

I love your content about [specific topic/video reference] —
your audience's reaction to [specific thing] was amazing.

I'm with [Brand], and we have a [product description] that I
think your audience would genuinely love.

Would you be interested in trying it? No strings attached —
we'd love to gift you one. If you like it and want to share
your honest review, we also have an affiliate program that
pays [X]% commission on all sales you drive.

Happy to send one your way. Interested?

[Your name]
[Brand]
```

**Affiliate program invitation:**
```
Hi [Creator Name],

Your TikTok content is exactly the type we love partnering with.

We'd like to invite you to our affiliate program for [Brand]:
• [X]% commission on every sale you drive
• Free products to review
• Exclusive discount code for your audience
• Performance bonuses for top creators

Here's how it works:
1. We send you our best-selling [product]
2. You create your authentic take
3. We track sales via your affiliate link
4. You earn [X]% on every purchase

Interested? Just reply and I'll send our collaboration brief.

[Your name]
```

### Sample Tracking System

Maintain a sample tracker:
```
Creator | Product | Sent Date | Expected Receive | Status | Follow-up | Content Posted | GMV
@user1  | Prod A  | Jan 5     | Jan 12           | ✓ Rcvd | Done      | Jan 20         | $450
@user2  | Prod B  | Jan 8     | Jan 15           | Shipped| Needed    | —              | $0
@user3  | Prod A  | Jan 10    | Jan 17           | Pending| —         | —              | —
```

**Follow-up timeline:**
- Day 0: Sample shipped, confirm tracking sent to creator
- Day +3: Check tracking, confirm delivered
- Day +5 post-delivery: First follow-up (how did you like it?)
- Day +10 post-delivery: Content reminder if not yet posted
- Day +14 post-delivery: Final follow-up, offer help or extension
- Day +21 post-delivery: Close out (content posted or write off)

### Content Performance Tracking

For each creator's content piece:
```
Creator   | Video Date | Views   | Likes  | Comments | GMV    | Conv%
@creator1 | Jan 20     | 45,000  | 2,300  | 180      | $890   | 2.0%
@creator2 | Jan 22     | 12,000  | 450    | 35       | $120   | 1.0%
@creator3 | Jan 25     | 280,000 | 18,000 | 1,200    | $5,400 | 1.9%
```

**Key performance formulas:**
```
GMV per view = Total GMV / Total views
Cost per sale = Sample cost / Units sold
ROAS = GMV / (Sample cost + any paid fee)
Creator ROI = (GMV - Cost) / Cost × 100
```

### Creator Commission Calculator

```
Example: Creator drives 50 sales at $30 each
Gross GMV:           $1,500
Commission rate:     20%
Creator earned:      $300
Your net:           $1,200
Product COGS (50×$8): $400
Profit from creator: $800

Creator ROI: ($800) / (sample $30 + commission $300) = 2.4x ROAS
```

### Scaling the Creator Program

**Funnel structure:**
```
Top of funnel:     100 creators contacted
↓
Agreed to try:      40 creators (40% acceptance)
↓
Sample sent:        35 creators
↓
Content posted:     20 creators (57% post rate)
↓
Sales generated:    15 creators (75% drive at least some GMV)
↓
Repeat creators:    8 creators (ongoing relationship)
```

**Monthly scaling cadence:**
- Week 1: Recruit 20-30 new creators
- Week 2: Ship samples, confirm receipt
- Week 3: Follow up, collect content
- Week 4: Analyze performance, tier creators for next month

## Workspace

Creates `~/creator-management/` containing:
- `database/` — creator profiles and status
- `samples/` — sample shipment tracking
- `content/` — content performance logs
- `outreach/` — message templates and history
- `reports/` — creator program performance reports

## Output Format

Every report outputs:
1. **Program Dashboard** — total GMV, active creators, ROAS summary
2. **Creator Leaderboard** — top 10 creators ranked by GMV and ROI
3. **Sample Pipeline** — status of all outstanding samples
4. **Content Calendar** — expected content from each creator
5. **Commission Report** — payouts owed to each creator
6. **Recruitment Targets** — criteria for next batch of creators to recruit
7. **Optimization Actions** — 3 specific changes to improve program performance

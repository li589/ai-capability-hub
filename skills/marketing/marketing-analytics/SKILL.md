---
name: marketing-analytics
description: Marketing analytics - UTM, attribution, CAC, ROAS, conversion tracking.
install_source: official
install_method: download
skill_id: official_fsJmlHBm
enabled_at: 1787231667958
version: 1.0.0
name_zh: 营销分析
---

# Marketing Analytics

## UTM Tracking Setup

### UTM Parameter Standartlari

```
https://example.com/landing?
  utm_source=google           # Trafik kaynagi (google, facebook, newsletter)
  &utm_medium=cpc             # Kanal tipi (cpc, email, social, organic)
  &utm_campaign=spring_2026   # Kampanya adi
  &utm_term=saas+analytics    # Arama terimi (paid search)
  &utm_content=hero_banner    # Reklam varyanti (A/B test)
```

### UTM Naming Convention

| Parameter | Format | Ornekler |
|-----------|--------|---------|
| source | lowercase, platform adi | google, facebook, linkedin, newsletter |
| medium | lowercase, kanal tipi | cpc, cpm, email, social, organic, referral |
| campaign | snake_case, tarih dahil | spring_sale_2026, product_launch_q1 |
| term | + ile ayrilmis | saas+analytics, project+management |
| content | snake_case, varyant | hero_banner, sidebar_cta, email_v2 |

### UTM Builder (TypeScript)

```typescript
interface UTMConfig {
  baseUrl: string;
  source: string;
  medium: string;
  campaign: string;
  term?: string;
  content?: string;
}

function buildUTMUrl(config: UTMConfig): string {
  const params = new URLSearchParams();
  params.set("utm_source", config.source.toLowerCase());
  params.set("utm_medium", config.medium.toLowerCase());
  params.set("utm_campaign", config.campaign.toLowerCase().replace(/\s+/g, "_"));
  if (config.term) params.set("utm_term", config.term.toLowerCase());
  if (config.content) params.set("utm_content", config.content.toLowerCase());

  const separator = config.baseUrl.includes("?") ? "&" : "?";
  return `${config.baseUrl}${separator}${params.toString()}`;
}

// UTM parametrelerini parse et ve kaydet
function captureUTM(): UTMParams | null {
  const params = new URLSearchParams(window.location.search);
  const utm: UTMParams = {
    source: params.get("utm_source") || undefined,
    medium: params.get("utm_medium") || undefined,
    campaign: params.get("utm_campaign") || undefined,
    term: params.get("utm_term") || undefined,
    content: params.get("utm_content") || undefined,
  };

  if (utm.source) {
    // First-touch ve last-touch ayri kaydet
    if (!localStorage.getItem("utm_first_touch")) {
      localStorage.setItem("utm_first_touch", JSON.stringify({ ...utm, timestamp: Date.now() }));
    }
    localStorage.setItem("utm_last_touch", JSON.stringify({ ...utm, timestamp: Date.now() }));
    return utm;
  }
  return null;
}
```

## Attribution Modeling

### Attribution Modelleri

| Model | Aciklama | Ne Zaman Kullan |
|-------|----------|----------------|
| First Touch | Ilk temas %100 kredi alir | Awareness kampanyalari |
| Last Touch | Son temas %100 kredi alir | Direct response kampanyalari |
| Linear | Tum temaslar esit kredi alir | Tum kanallari esit degerlendirme |
| Time Decay | Son temaslara daha cok kredi | Uzun satis dongusu |
| U-Shaped | Ilk ve son temas %40, orta %20 | Balanced B2B attribution |
| W-Shaped | Ilk, lead, opportunity %30, geri kalan %10 | Full-funnel B2B |
| Data-Driven | Algoritmik (Markov chain, Shapley) | Yeterli veri varsa (10K+ conversion) |

### Multi-Touch Attribution Query

```sql
-- U-Shaped Attribution
WITH touchpoints AS (
  SELECT
    conversion_id,
    user_id,
    channel,
    touch_timestamp,
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY touch_timestamp) AS touch_order,
    COUNT(*) OVER (PARTITION BY conversion_id) AS total_touches
  FROM marketing_touches
  WHERE conversion_id IS NOT NULL
),
attributed AS (
  SELECT
    conversion_id,
    channel,
    CASE
      WHEN total_touches = 1 THEN 1.0
      WHEN total_touches = 2 THEN 0.5
      WHEN touch_order = 1 THEN 0.4                            -- first touch
      WHEN touch_order = total_touches THEN 0.4                -- last touch
      ELSE 0.2 / (total_touches - 2)                           -- middle touches
    END AS attribution_weight
  FROM touchpoints
)
SELECT
  channel,
  ROUND(SUM(attribution_weight), 2) AS attributed_conversions,
  ROUND(SUM(attribution_weight * c.revenue), 2) AS attributed_revenue
FROM attributed a
JOIN conversions c ON a.conversion_id = c.id
GROUP BY channel
ORDER BY attributed_revenue DESC;
```

### Markov Chain Attribution

```typescript
interface TransitionMatrix {
  [fromState: string]: {
    [toState: string]: number;  // probability
  };
}

// Removal effect: Her kanalin conversion'a katki oranini hesapla
function calculateRemovalEffect(
  matrix: TransitionMatrix,
  channels: string[]
): Record<string, number> {
  const baseConversionRate = simulateConversions(matrix, channels);
  const effects: Record<string, number> = {};

  for (const channel of channels) {
    const withoutChannel = channels.filter(c => c !== channel);
    const reducedRate = simulateConversions(matrix, withoutChannel);
    effects[channel] = (baseConversionRate - reducedRate) / baseConversionRate;
  }

  // Normalize to sum to 1
  const total = Object.values(effects).reduce((a, b) => a + b, 0);
  for (const channel of channels) {
    effects[channel] = effects[channel] / total;
  }

  return effects;
}
```

## CAC (Customer Acquisition Cost)

### CAC Hesaplama

```typescript
interface CACMetrics {
  totalMarketingSpend: number;        // Toplam marketing harcamasi
  totalSalesSpend: number;            // Toplam sales harcamasi (maas dahil)
  newCustomers: number;               // Kazanilan musteri sayisi
  period: string;                     // "2026-Q1"
}

function calculateCAC(metrics: CACMetrics): {
  blendedCAC: number;
  paidCAC: number;
  organicCAC: number;
} {
  const totalSpend = metrics.totalMarketingSpend + metrics.totalSalesSpend;
  return {
    blendedCAC: totalSpend / metrics.newCustomers,
    paidCAC: metrics.totalMarketingSpend / (metrics.newCustomers * 0.6),  // %60 paid
    organicCAC: (metrics.totalSalesSpend * 0.3) / (metrics.newCustomers * 0.4),
  };
}
```

### CAC by Channel Query

```sql
SELECT
  channel,
  SUM(spend) AS total_spend,
  COUNT(DISTINCT conversion_user_id) AS new_customers,
  ROUND(SUM(spend) / NULLIF(COUNT(DISTINCT conversion_user_id), 0), 2) AS cac,
  ROUND(AVG(first_order_value), 2) AS avg_first_order
FROM (
  SELECT
    a.channel,
    a.spend,
    c.user_id AS conversion_user_id,
    c.revenue AS first_order_value
  FROM ad_spend a
  LEFT JOIN conversions c ON c.attributed_channel = a.channel
    AND c.conversion_date BETWEEN a.date AND a.date + INTERVAL '30 days'
  WHERE a.date >= CURRENT_DATE - INTERVAL '90 days'
) channel_data
GROUP BY channel
ORDER BY cac;
```

### CAC Benchmarks

| Industry | Median CAC | Iyi CAC | Target LTV:CAC |
|----------|-----------|---------|---------------|
| SaaS B2B (SMB) | $200-500 | < $200 | 3:1+ |
| SaaS B2B (Enterprise) | $5K-20K | < $5K | 5:1+ |
| SaaS B2C | $20-100 | < $30 | 3:1+ |
| E-commerce | $10-50 | < $15 | 3:1+ |
| Fintech | $100-500 | < $100 | 4:1+ |
| Marketplace | $50-200 | < $50 | 3:1+ |

## ROAS (Return on Ad Spend)

### ROAS Calculator

```typescript
function calculateROAS(
  revenue: number,
  adSpend: number
): { roas: number; roasPercentage: number; profitable: boolean } {
  const roas = revenue / adSpend;
  return {
    roas: Math.round(roas * 100) / 100,
    roasPercentage: Math.round(roas * 100),
    profitable: roas > 1,
  };
}

// Hedef ROAS hesapla (break-even icin)
function targetROAS(grossMargin: number): number {
  // Minimum ROAS = 1 / Gross Margin
  // %70 margin -> minimum 1.43 ROAS
  return Math.round((1 / grossMargin) * 100) / 100;
}
```

### ROAS Dashboard Query

```sql
SELECT
  campaign_name,
  channel,
  SUM(impressions) AS impressions,
  SUM(clicks) AS clicks,
  ROUND(100.0 * SUM(clicks) / NULLIF(SUM(impressions), 0), 2) AS ctr_pct,
  SUM(spend) AS spend,
  SUM(conversions) AS conversions,
  ROUND(SUM(spend) / NULLIF(SUM(conversions), 0), 2) AS cost_per_conversion,
  SUM(revenue) AS revenue,
  ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 2) AS roas,
  ROUND(SUM(revenue) - SUM(spend), 2) AS profit
FROM campaign_performance
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY campaign_name, channel
ORDER BY roas DESC;
```

### ROAS Benchmarks

| Platform | Ortalama ROAS | Iyi ROAS | Mukemmel ROAS |
|----------|-------------|---------|-------------|
| Google Search | 2:1 | 4:1 | 8:1+ |
| Google Display | 0.5:1 | 1.5:1 | 3:1+ |
| Facebook/Instagram | 1.5:1 | 3:1 | 6:1+ |
| LinkedIn | 1:1 | 2.5:1 | 5:1+ |
| TikTok | 1:1 | 2:1 | 4:1+ |
| Email Marketing | 10:1 | 30:1 | 40:1+ |

## Conversion Tracking

### Conversion Event Setup

```typescript
interface ConversionEvent {
  event_name: string;
  value: number;
  currency: string;
  conversion_type: "micro" | "macro";
  attribution_window_days: number;
}

const conversionEvents: ConversionEvent[] = [
  // Macro conversions (primary goals)
  { event_name: "purchase_completed", value: 0, currency: "USD", conversion_type: "macro", attribution_window_days: 30 },
  { event_name: "subscription_started", value: 0, currency: "USD", conversion_type: "macro", attribution_window_days: 30 },

  // Micro conversions (leading indicators)
  { event_name: "trial_started", value: 0, currency: "USD", conversion_type: "micro", attribution_window_days: 14 },
  { event_name: "demo_requested", value: 50, currency: "USD", conversion_type: "micro", attribution_window_days: 7 },
  { event_name: "email_subscribed", value: 5, currency: "USD", conversion_type: "micro", attribution_window_days: 7 },
];

// Server-side conversion tracking
async function trackConversion(
  event: ConversionEvent,
  userId: string,
  metadata: Record<string, unknown>
): Promise<void> {
  // 1. Internal analytics
  await analytics.track(event.event_name, {
    ...metadata,
    conversion_type: event.conversion_type,
    value: metadata.value || event.value,
  });

  // 2. Facebook Conversions API
  await sendFacebookConversion(event, userId, metadata);

  // 3. Google Ads offline conversion
  await sendGoogleOfflineConversion(event, userId, metadata);
}
```

### Conversion Funnel Query

```sql
-- Marketing funnel: Visit -> Lead -> MQL -> SQL -> Customer
SELECT
  'Visit' AS stage, COUNT(DISTINCT session_id) AS count, 100.0 AS pct
FROM sessions WHERE date >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT
  'Lead', COUNT(DISTINCT user_id),
  ROUND(100.0 * COUNT(DISTINCT user_id) /
    (SELECT COUNT(DISTINCT session_id) FROM sessions WHERE date >= CURRENT_DATE - INTERVAL '30 days'), 1)
FROM leads WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT
  'MQL', COUNT(DISTINCT user_id),
  ROUND(100.0 * COUNT(DISTINCT user_id) /
    (SELECT COUNT(DISTINCT user_id) FROM leads WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'), 1)
FROM leads WHERE status = 'mql' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT
  'SQL', COUNT(DISTINCT user_id),
  ROUND(100.0 * COUNT(DISTINCT user_id) /
    (SELECT COUNT(DISTINCT user_id) FROM leads WHERE status = 'mql' AND created_at >= CURRENT_DATE - INTERVAL '30 days'), 1)
FROM leads WHERE status = 'sql' AND created_at >= CURRENT_DATE - INTERVAL '30 days'
UNION ALL
SELECT
  'Customer', COUNT(DISTINCT user_id),
  ROUND(100.0 * COUNT(DISTINCT user_id) /
    (SELECT COUNT(DISTINCT user_id) FROM leads WHERE status = 'sql' AND created_at >= CURRENT_DATE - INTERVAL '30 days'), 1)
FROM conversions WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY
  CASE stage
    WHEN 'Visit' THEN 1 WHEN 'Lead' THEN 2 WHEN 'MQL' THEN 3
    WHEN 'SQL' THEN 4 WHEN 'Customer' THEN 5
  END;
```

## Landing Page Optimization

### Key Metrics

| Metrik | Formul | Iyi Deger |
|--------|--------|----------|
| Bounce Rate | single_page_sessions / total_sessions | < %40 |
| Conversion Rate | conversions / visitors | %3-5 (B2C), %2-3 (B2B) |
| Time on Page | avg(exit_time - entry_time) | > 60 saniye |
| Scroll Depth | avg(max_scroll_percentage) | > %60 |
| CTA Click Rate | cta_clicks / visitors | > %5 |
| Form Completion | form_submits / form_starts | > %30 |

### Landing Page A/B Test Template

```typescript
interface LandingPageTest {
  name: string;
  hypothesis: string;
  element: "headline" | "cta" | "hero_image" | "social_proof" | "pricing" | "layout";
  control: string;
  treatment: string;
  primary_metric: string;
  traffic_split: number;
  duration_days: number;
}

const tests: LandingPageTest[] = [
  {
    name: "headline_benefit_vs_feature",
    hypothesis: "Benefit-focused headline, feature-focused'a gore %15 daha yuksek conversion verir",
    element: "headline",
    control: "AI-Powered Analytics Dashboard",
    treatment: "Get Insights 10x Faster With AI",
    primary_metric: "cta_click_rate",
    traffic_split: 0.5,
    duration_days: 14,
  },
];
```

## Email Marketing Metrics

### KPI Dashboard

| Metrik | Formul | Iyi Deger | Aksiyonlar |
|--------|--------|----------|-----------|
| Open Rate | opens / delivered | %20-30 | Subject line A/B test |
| CTR | clicks / delivered | %2-5 | CTA ve icerik optimize |
| CTOR | clicks / opens | %10-15 | Icerik kalitesini olc |
| Unsubscribe Rate | unsubs / delivered | < %0.5 | Frekans ve segmentasyon |
| Bounce Rate | bounces / sent | < %2 | Liste temizligi |
| Conversion Rate | conversions / clicks | %1-5 | Landing page optimize |
| Revenue per Email | total_revenue / delivered | Varies | Segmentasyon iyilestir |

### Email Performance Query

```sql
SELECT
  campaign_name,
  sent_at::date AS send_date,
  COUNT(*) AS sent,
  SUM(CASE WHEN delivered THEN 1 ELSE 0 END) AS delivered,
  SUM(CASE WHEN opened THEN 1 ELSE 0 END) AS opens,
  ROUND(100.0 * SUM(CASE WHEN opened THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN delivered THEN 1 ELSE 0 END), 0), 1) AS open_rate,
  SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS clicks,
  ROUND(100.0 * SUM(CASE WHEN clicked THEN 1 ELSE 0 END) /
    NULLIF(SUM(CASE WHEN delivered THEN 1 ELSE 0 END), 0), 1) AS ctr,
  SUM(CASE WHEN converted THEN 1 ELSE 0 END) AS conversions,
  SUM(revenue) AS total_revenue,
  ROUND(SUM(revenue) / NULLIF(SUM(CASE WHEN delivered THEN 1 ELSE 0 END), 0), 2) AS revenue_per_email
FROM email_campaigns
WHERE sent_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY campaign_name, send_date
ORDER BY send_date DESC;
```

## Social Media Analytics

### Platform Metrics

| Platform | Key Metrics | Engagement Formula |
|----------|------------|-------------------|
| Twitter/X | Impressions, Engagement Rate, Link Clicks | (likes + retweets + replies) / impressions |
| LinkedIn | Impressions, CTR, Follower Growth | (likes + comments + shares + clicks) / impressions |
| Instagram | Reach, Saves, Shares | (likes + comments + saves + shares) / followers |
| TikTok | Views, Watch Time, Shares | (likes + comments + shares) / views |
| YouTube | Views, Watch Time, CTR | (likes + comments) / views |

### Social ROI Template

```typescript
interface SocialROI {
  platform: string;
  totalSpend: number;           // paid + organic (time cost)
  impressions: number;
  engagements: number;
  websiteTraffic: number;
  conversions: number;
  revenue: number;
}

function calculateSocialROI(data: SocialROI): {
  cpm: number;                  // Cost per 1000 impressions
  cpe: number;                  // Cost per engagement
  cpc: number;                  // Cost per click (to website)
  cpa: number;                  // Cost per acquisition
  roi: number;                  // Return on Investment %
} {
  return {
    cpm: (data.totalSpend / data.impressions) * 1000,
    cpe: data.totalSpend / data.engagements,
    cpc: data.totalSpend / data.websiteTraffic,
    cpa: data.totalSpend / data.conversions,
    roi: ((data.revenue - data.totalSpend) / data.totalSpend) * 100,
  };
}
```

## SEO Metrics

### Core SEO KPIs

| Metrik | Kaynak | Hedef |
|--------|--------|-------|
| Organic Traffic | Google Search Console / GA | +10% MoM |
| Keyword Rankings | Ahrefs / SEMrush | Top 10 icin hedef keyword |
| Click-Through Rate | Search Console | > %3 ortalama |
| Domain Authority | Ahrefs / Moz | Rakiplerden yuksek |
| Backlink Growth | Ahrefs | +5% MoM |
| Core Web Vitals | PageSpeed Insights | LCP < 2.5s, CLS < 0.1, INP < 200ms |
| Indexed Pages | Search Console | Sitemap'teki sayfa sayisina yakin |
| Organic Conversion Rate | GA | > %2 |

### Content Performance Scoring

```typescript
interface ContentScore {
  url: string;
  organic_traffic_30d: number;
  avg_position: number;
  ctr: number;
  conversions: number;
  backlinks: number;
  word_count: number;
  last_updated: string;
}

function scoreContent(content: ContentScore): {
  score: number;
  action: "keep" | "update" | "consolidate" | "remove";
} {
  let score = 0;

  // Traffic (0-30)
  if (content.organic_traffic_30d > 1000) score += 30;
  else if (content.organic_traffic_30d > 100) score += 20;
  else if (content.organic_traffic_30d > 10) score += 10;

  // Rankings (0-25)
  if (content.avg_position <= 3) score += 25;
  else if (content.avg_position <= 10) score += 15;
  else if (content.avg_position <= 20) score += 5;

  // Conversions (0-25)
  if (content.conversions > 10) score += 25;
  else if (content.conversions > 1) score += 15;
  else if (content.conversions > 0) score += 5;

  // Freshness (0-10)
  const daysSinceUpdate = (Date.now() - new Date(content.last_updated).getTime()) / 86400000;
  if (daysSinceUpdate < 90) score += 10;
  else if (daysSinceUpdate < 180) score += 5;

  // Backlinks (0-10)
  if (content.backlinks > 10) score += 10;
  else if (content.backlinks > 0) score += 5;

  let action: "keep" | "update" | "consolidate" | "remove";
  if (score >= 70) action = "keep";
  else if (score >= 40) action = "update";
  else if (score >= 20) action = "consolidate";
  else action = "remove";

  return { score, action };
}
```

## Marketing Funnel Optimization

### Funnel Stage Metrics

```
TOFU (Awareness)           MOFU (Consideration)        BOFU (Decision)
-------------------        ----------------------      ------------------
Impressions                Email subscribers            Demo requests
Website visitors           Content downloads            Trial signups
Social followers           Webinar attendees            Quote requests
Blog readers               Return visitors              Free trial users
                           Newsletter opens             Pricing page visits
```

### Channel Efficiency Matrix

```sql
SELECT
  channel,
  SUM(spend) AS spend,
  COUNT(DISTINCT visitor_id) AS visitors,
  COUNT(DISTINCT lead_id) AS leads,
  COUNT(DISTINCT customer_id) AS customers,
  ROUND(SUM(spend) / NULLIF(COUNT(DISTINCT visitor_id), 0), 2) AS cost_per_visit,
  ROUND(SUM(spend) / NULLIF(COUNT(DISTINCT lead_id), 0), 2) AS cost_per_lead,
  ROUND(SUM(spend) / NULLIF(COUNT(DISTINCT customer_id), 0), 2) AS cac,
  ROUND(100.0 * COUNT(DISTINCT lead_id) / NULLIF(COUNT(DISTINCT visitor_id), 0), 1) AS visit_to_lead_pct,
  ROUND(100.0 * COUNT(DISTINCT customer_id) / NULLIF(COUNT(DISTINCT lead_id), 0), 1) AS lead_to_customer_pct,
  SUM(customer_revenue) AS revenue,
  ROUND(SUM(customer_revenue) / NULLIF(SUM(spend), 0), 2) AS roas
FROM marketing_data
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY channel
ORDER BY roas DESC;
```

## Anti-Patterns

| Anti-Pattern | Dogru Yol |
|-------------|-----------|
| UTM'siz kampanya | Her kampanyada tutarli UTM kullan |
| Sadece last-touch attribution | Multi-touch modelleme yap |
| CAC'i toplam baz al | Kanal bazli CAC hesapla |
| ROAS'i revenue ile hesapla | Profit-based ROAS (POAS) kullan |
| Vanity metrics raporu (impressions) | Conversion-focused metriklere odaklan |
| Email herkese ayni icerik | Segmentasyon + kisisellesetirme |
| SEO sadece keyword | Technical SEO + Content + Backlink |
| Kanal silolari | Cross-channel attribution |

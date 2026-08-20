#!/usr/bin/env python3
import sys
from typing import Any, Dict, List, Union

CHANNEL_RULES = {
    'TikTok / Douyin': ['tiktok', 'douyin', 'short video'],
    'Xiaohongshu': ['xiaohongshu', 'rednote', 'xhs'],
    'Amazon A+': ['amazon a+', 'amazon a+ content'],
    'Shopify PDP': ['shopify', 'pdp', 'product page', 'storefront'],
    'Meta / Instagram': ['meta', 'facebook', 'instagram', 'fb', 'ig'],
    'Email': ['email', 'newsletter', 'klaviyo', 'mailchimp'],
    'WeChat': ['wechat', 'weixin'],
    'JD / Taobao': ['jd', 'taobao', '天猫'],
}

GOAL_RULES = {
    'Awareness': ['awareness', 'brand', 'reach', 'impression'],
    'Traffic': ['traffic', 'click', 'website', 'landing page'],
    'Conversion': ['conversion', 'sales', 'direct response', 'dra'],
    'UGC Seeding': ['ugc', 'user generated', 'creator', 'seeding'],
    'Review Collection': ['review', 'testimonial', 'rating'],
    'SEO': ['seo', 'search', 'blog', 'content'],
}

FORMAT_RULES = {
    'Short Video': ['video', 'tiktok', 'douyin', 'short form', 'reels', 'short video'],
    'Image / Carousel': ['image', 'photo', 'carousel', 'gallery', 'static'],
    'Copy / Caption': ['copy', 'caption', 'script', 'text', 'blog post'],
    'UGC / Creator': ['ugc', 'creator', 'influencer', 'user generated'],
    'A+ / Infographic': ['a+', 'infographic', 'comparison', 'chart'],
}

ContentInput = Union[str, Dict[str, Any]]


def _score_rules(text: str, rules: Dict[str, List[str]]) -> Dict[str, int]:
    return {name: sum(1 for kw in kws if kw in text) for name, kws in rules.items()}


def _join(items: List[str]) -> str:
    return ', '.join(items) if items else 'Not specified'


class ContentAssetOrchestrator:
    def __init__(self, user_input: ContentInput):
        self.raw = user_input
        self.text = self._normalize_input(user_input)
        self.lower = self.text.lower()
        self.channels = self._detect_channels()
        self.goals = self._detect_goals()
        self.formats = self._detect_formats()
        self.existing_assets = self._detect_existing()

    def _normalize_input(self, user_input: ContentInput) -> str:
        if isinstance(user_input, dict):
            chunks: List[str] = []
            for key in ['window', 'channels', 'goals', 'product', 'existing', 'resources', 'notes']:
                value = user_input.get(key)
                if not value:
                    continue
                if isinstance(value, list):
                    value = ', '.join(str(v) for v in value)
                chunks.append(f'{key}: {value}')
            return ' | '.join(chunks)
        return str(user_input or '').strip()

    def _detect_channels(self) -> List[str]:
        matched = [name for name, kws in CHANNEL_RULES.items() if any(kw in self.lower for kw in kws)]
        return matched or ['TikTok / Douyin', 'Xiaohongshu', 'Shopify PDP']

    def _detect_goals(self) -> List[str]:
        matched = [name for name, kws in GOAL_RULES.items() if any(kw in self.lower for kw in kws)]
        return matched or ['Conversion']

    def _detect_formats(self) -> List[str]:
        matched = [name for name, kws in FORMAT_RULES.items() if any(kw in self.lower for kw in kws)]
        return matched or ['Short Video', 'Image / Carousel', 'Copy / Caption']

    def _detect_existing(self) -> List[str]:
        existing = []
        if any(kw in self.lower for kw in ['已有', 'existing', 'already have', 'current']):
            existing = ['Assets noted as partial — assume most formats need refresh or supplementation.']
        return existing

    def _channel_matrix(self) -> List[str]:
        lines = ['| Channel | Primary Format | Aspect Ratio / Spec | Copy Style | Cadence |']
        lines.append('|---|---|---|---|---|')
        specs = {
            'TikTok / Douyin': ('9:16 Short Video', '9:16, 1080×1920', 'Conversational, hook-first, 3–5s to value', '3–7x/week'),
            'Xiaohongshu': ('Image or 9:16 Video', '3:4 or 9:16, 1080×1350', 'Lifestyle, personal, specific use-case', '3–5x/week'),
            'Amazon A+': ('A+ Infographic + Image', '1200×600 (module)', 'Feature-benefit, comparison', 'Set once, refresh quarterly'),
            'Shopify PDP': ('Hero Image + Gallery', '1200×1200 (square)', 'Benefit-led, SEO-friendly', 'Set per SKU, refresh with new launches'),
            'Meta / Instagram': ('Feed Image or Reels', '1:1 or 4:5', 'Brand voice, varied hooks', '1–2x/day'),
            'Email': ('Banner + Copy', '600×200 (banner)', 'Direct, benefit-first, CTA-clear', '1–2x/week'),
            'WeChat': ('Image + Mini Program', '2:3 or 9:16', 'Formal, relationship-first', '2–4x/week'),
            'JD / Taobao': ('Main Image + Video', '800×800 or 9:16', 'Feature-dense, comparison', 'Set per SKU'),
        }
        for ch in self.channels:
            row = specs.get(ch, ('TBD', 'TBD', 'TBD', 'TBD'))
            lines.append(f'| {ch} | {row[0]} | {row[1]} | {row[2]} | {row[3]} |')
        return lines

    def _gap_analysis(self) -> List[str]:
        gaps = []
        if 'Short Video' in self.formats and 'TikTok / Douyin' in self.channels:
            gaps.append('TikTok short video: need 3–5 video concepts with hook, body, and CTA per concept.')
        if 'Xiaohongshu' in self.channels:
            gaps.append('Xiaohongshu: need 3–5 posts with lifestyle narrative, product mention, and hashtag strategy.')
        if 'Amazon A+' in self.channels:
            gaps.append('Amazon A+: need infographic modules, comparison chart, and brand story section.')
        if 'UGC / Creator' in self.formats or 'UGC Seeding' in self.goals:
            gaps.append('UGC: brief for 2–3 creators with talking points, format requirements, and disclosure guidelines.')
        if 'Email' in self.channels:
            gaps.append('Email: banner image brief + subject line variants + CTA copy.')
        if not gaps:
            gaps.append('No critical gaps identified from input; proceed with asset production list.')
        return gaps

    def _priority_list(self) -> List[str]:
        priorities = []
        if 'Conversion' in self.goals:
            priorities.append('1. Hero content (video or image) for the highest-traffic SKU or campaign.')
            priorities.append('2. A+ or PDP upgrade if Amazon or Shopify is in scope.')
        if 'UGC Seeding' in self.goals:
            priorities.append('1. Creator brief and content guidelines before production begins.')
        if 'Awareness' in self.goals:
            priorities.insert(0, '1. TikTok/Xiaohongshu content pipeline for top-of-funnel reach.')
        priorities.append('N. Refresh existing assets that are older than 3 months or underperforming.')
        return priorities

    def _production_brief(self) -> List[Dict[str, str]]:
        briefs = []
        for ch in self.channels[:3]:
            brief = {'channel': ch, 'asset_type': 'TBD', 'key_message': 'TBD', 'format_notes': 'TBD'}
            if ch == 'TikTok / Douyin':
                brief['asset_type'] = 'Short Video (3–5 variants)'
                brief['key_message'] = 'Hook in first 3 seconds; product benefit or transformation moment.'
                brief['format_notes'] = '9:16, 1080×1920, no watermark, subtitle file recommended.'
            elif ch == 'Xiaohongshu':
                brief['asset_type'] = 'Image Post or Short Video'
                brief['key_message'] = 'Real-use scenario, personal experience, specific result or tip.'
                brief['format_notes'] = '3:4 image or 9:16 video; first image is the hook.'
            elif ch == 'Amazon A+':
                brief['asset_type'] = 'A+ Infographic Modules'
                brief['key_message'] = 'Feature, benefit, and proof point for each module.'
                brief['format_notes'] = '1200×600 per module; brand story + comparison grid recommended.'
            elif ch == 'Shopify PDP':
                brief['asset_type'] = 'Hero Image + Gallery'
                brief['key_message'] = 'Primary benefit above the fold; lifestyle + spec images below.'
                brief['format_notes'] = '1200×1200 minimum; WebP format recommended.'
            briefs.append(brief)
        return briefs

    def render(self) -> str:
        lines: List[str] = []
        lines.append('# Content Asset Orchestrator Brief')
        lines.append('')
        lines.append(f'**Campaign window:** {self._campaign_window()}')
        lines.append(f'**Channels:** {_join(self.channels)}')
        lines.append(f'**Content goals:** {_join(self.goals)}')
        lines.append(f'**Format priorities:** {_join(self.formats)}')
        lines.append('**Method note:** This is a heuristic content planning brief. No live social, DAM, or analytics platform was accessed.')
        lines.append('')
        lines.append('## Content Strategy Summary')
        lines.append(f'- Goal: drive {", ".join(self.goals).lower()} across {", ".join(self.channels[:3])}.')
        lines.append('- Lead with high-impact visual content; support with targeted copy and UGC seeding.')
        lines.append('- Build a content pipeline that can run 3–5 weeks before major campaign activation.')
        lines.append('')
        lines.append('## Channel Requirement Matrix')
        for row in self._channel_matrix():
            lines.append(row)
        lines.append('')
        lines.append('## Content Type Coverage Map')
        lines.append('| Format | In Scope | Existing? | Gap? | Priority |')
        lines.append('|---|---|---|---|---|')
        for fmt in self.formats:
            in_scope = '✅' if fmt in self.formats else '❌'
            gap = '⚠️ Gap identified' if any(g.lower().startswith(fmt.lower().split()[0]) for g in self._gap_analysis()) else '✅ OK'
            pri = '🔴 High' if fmt in ['Short Video', 'Image / Carousel'] else '🟡 Medium'
            lines.append(f'| {fmt} | {in_scope} | Partial assumed | {gap} | {pri} |')
        lines.append('')
        lines.append('## Production Gap Analysis')
        for gap in self._gap_analysis():
            lines.append(f'- {gap}')
        lines.append('')
        lines.append('## Asset Priority List')
        for item in self._priority_list():
            lines.append(f'- {item}')
        lines.append('')
        lines.append('## Production Briefs')
        for brief in self._production_brief():
            lines.append(f'### {brief["channel"]}')
            lines.append(f'- **Asset type:** {brief["asset_type"]}')
            lines.append(f'- **Key message:** {brief["key_message"]}')
            lines.append(f'- **Format notes:** {brief["format_notes"]}')
            lines.append('')
        lines.append('## Distribution & Posting Cadence')
        lines.append('- TikTok: post 3–7x/week; go live with creator at least 1x/week during campaign window.')
        lines.append('- Xiaohongshu: post 3–5x/week; seed with creator UGC 2 weeks before conversion push.')
        lines.append('- Amazon A+: load 1 week before campaign launch; refresh every 3 months.')
        lines.append('- Email: send 1–2x/week to engaged segment; pause for 1 week pre/post major campaign.')
        return '\n'.join(lines)

    def _campaign_window(self) -> str:
        if any(kw in self.lower for kw in ['monthly', 'this month', 'q1', 'q2', 'q3', 'q4']):
            return 'This quarter'
        if any(kw in self.lower for kw in ['launch', 'new product', 'new sku']):
            return 'Launch window (T-4 weeks pre-launch)'
        return 'General planning window'


def handle(user_input: ContentInput) -> str:
    return ContentAssetOrchestrator(user_input).render()


if __name__ == '__main__':
    payload = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    print(handle(payload))

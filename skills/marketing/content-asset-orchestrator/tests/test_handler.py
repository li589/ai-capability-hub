#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from handler import ContentAssetOrchestrator, handle


def test_channel_detection_tiktok_xiaohongshu():
    orchestrator = ContentAssetOrchestrator('Plan content for TikTok and Xiaohongshu summer campaign')
    assert 'TikTok / Douyin' in orchestrator.channels
    assert 'Xiaohongshu' in orchestrator.channels


def test_channel_detection_amazon_email():
    orchestrator = ContentAssetOrchestrator('Amazon A+ content and email newsletter planning')
    assert 'Amazon A+' in orchestrator.channels
    assert 'Email' in orchestrator.channels


def test_goal_detection_awareness():
    orchestrator = ContentAssetOrchestrator('Awareness campaign content for new brand launch')
    assert 'Awareness' in orchestrator.goals


def test_format_detection_video():
    orchestrator = ContentAssetOrchestrator('Short video content for TikTok and Douyin')
    assert 'Short Video' in orchestrator.formats


def test_render_contains_sections():
    output = handle('Help me plan content for our summer campaign across TikTok, Xiaohongshu, and Amazon A+')
    assert output.startswith('# Content Asset Orchestrator Brief')
    assert '## Channel Requirement Matrix' in output
    assert '## Production Gap Analysis' in output
    assert '## Production Briefs' in output


def test_dict_input_supported():
    output = handle({
        'window': 'Q2',
        'channels': ['TikTok / Douyin', 'Xiaohongshu', 'Shopify PDP'],
        'goals': ['Conversion', 'UGC Seeding'],
        'product': 'skincare brand launch'
    })
    assert '# Content Asset Orchestrator Brief' in output
    assert 'TikTok' in output or 'TikTok' in output


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
    print('All tests passed.')

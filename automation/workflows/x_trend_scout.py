#!/usr/bin/env python3
"""
X/Twitter Trend Scout
Extrahiert virale Patterns, Hooks und Angles aus X Content
Integriert mit Strategy-State für adaptive Shorts-Erstellung
"""
from __future__ import annotations

import json
import hashlib
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from automation.utils.files import ensure_dir, timestamp_id, write_json, write_text

ROOT = Path(__file__).resolve().parents[2]
DELIVERABLES_DIR = ROOT / "content_factory" / "deliverables" / "x_trends"
NUGGETS_DIR = ROOT / "ai-vault" / "nuggets"


@dataclass
class XTrendItem:
    """Ein X/Twitter Trend-Item mit viralen Signalen"""
    tweet_id: str
    author: str
    content: str
    created_at: str
    likes: int
    retweets: int
    replies: int
    views: int
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    viral_score: float = 0.0
    hook_pattern: str = ""
    angle_type: str = ""  # contrarian, educational, story, newsjacking, etc.


@dataclass
class TrendAnalysis:
    """Aggregierte Trend-Analyse für Content-Strategie"""
    timestamp: str
    top_hooks: List[str] = field(default_factory=list)
    trending_angles: List[str] = field(default_factory=list)
    hot_topics: List[str] = field(default_factory=list)
    viral_patterns: List[str] = field(default_factory=list)
    sentiment_indicators: Dict[str, float] = field(default_factory=dict)
    recommended_urgency: str = "medium"  # low, medium, high


@dataclass
class XScoutConfig:
    """Konfiguration für X Trend Scout"""
    run_id: str
    bearer_token: str = ""  # X API Bearer Token
    search_queries: List[str] = field(default_factory=list)
    min_engagement_threshold: int = 100
    max_results_per_query: int = 50
    lookback_hours: int = 24
    target_niche: str = "AI Automation"  # DE AI Automation
    auto_save_nuggets: bool = True


def _calc_viral_score(likes: int, retweets: int, replies: int, views: int) -> float:
    """Berechnet viralen Score basierend auf Engagement"""
    if views == 0:
        return 0.0

    # Engagement-Rate gewichten
    engagement_rate = (likes + retweets * 2 + replies * 3) / views

    # Absolute Zahlen skalieren
    volume_factor = min(views / 10000, 10)  # Cap bei 100k views

    return round(engagement_rate * volume_factor * 100, 2)


def _extract_hooks(content: str) -> List[str]:
    """Extrahiert potentielle Hooks aus Content"""
    hooks = []

    # Pattern 1: Zahlen-basiert ("3 Dinge...", "Top 5...")
    number_pattern = r'^(\d+)\s+(\w+.*?)(?:\n|$)'
    if match := re.search(number_pattern, content, re.IGNORECASE):
        hooks.append(f"{match.group(1)} {match.group(2)}")

    # Pattern 2: Fragen ("Wusstest du...?", "Warum...?")
    if content.strip().endswith('?') and len(content) < 100:
        hooks.append(content.strip()[:80])

    # Pattern 3: Contrarian ("Die meisten..., aber...", "X ist falsch...")
    contrarian_starters = ["die meisten", "fast alle", "alle reden über", "stop", "nicht", "nie", "kein"]
    first_sentence = content.split('.')[0].lower()
    if any(s in first_sentence for s in contrarian_starters):
        hooks.append(content.split('.')[0][:80])

    # Pattern 4: Story-Start ("Ich habe...", "Letztes Jahr...")
    story_starters = ["ich habe", "letztes", "vor", "damals", "gestern", "heute"]
    if any(s in first_sentence for s in story_starters):
        hooks.append(content.split('.')[0][:80])

    return hooks


def _classify_angle(content: str, engagement: dict) -> str:
    """Klassifiziert den Angle-Type basierend auf Content und Engagement"""
    content_lower = content.lower()

    # Contrarian: Hohe Reply-Rate + negative Wörter
    reply_ratio = engagement.get('replies', 0) / max(engagement.get('likes', 1), 1)
    if reply_ratio > 0.2 or any(w in content_lower for w in ['falsch', 'mythos', 'lüge', 'nicht', 'nie']):
        return "contrarian"

    # Educational: Anleitungen, Schritt-für-Schritt
    if any(w in content_lower for w in ['so geht', 'anleitung', 'tutorial', 'guide', 'schritt', 'how to']):
        return "educational"

    # Story: Persönliche Erfahrung
    if any(w in content_lower for w in ['ich habe', 'meine', 'mir ist', 'erlebt', 'geschichte']):
        return "story"

    # Newsjacking: Aktuelles, Zeitbezug
    if any(w in content_lower for w in ['gerade', 'aktuell', 'neu', 'update', 'breaking']):
        return "newsjacking"

    # Authority: Expertise, Erfahrung
    if any(w in content_lower for w in ['jahre', 'erfahrung', 'experte', 'gelernt', 'festgestellt']):
        return "authority"

    return "general"


def _extract_hashtags(content: str) -> List[str]:
    """Extrahiert Hashtags aus Content"""
    return re.findall(r'#(\w+)', content)


def _extract_mentions(content: str) -> List[str]:
    """Extrahiert Mentions aus Content"""
    return re.findall(r'@(\w+)', content)


def _extract_urls(content: str) -> List[str]:
    """Extrahiert URLs aus Content"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, content)


def parse_x_export_json(export_path: Path) -> List[XTrendItem]:
    """
    Parst X/Twitter Daten-Export (tweets.js oder x.json)
    Unterstützt offizielle X Export-Formate
    """
    items = []

    if not export_path.exists():
        return items

    # Versuche tweets.js (Standard X Export)
    if export_path.suffix == '.js' or 'tweets' in export_path.name.lower():
        content = export_path.read_text(encoding='utf-8')
        # Entferne JavaScript-Wrapper
        content = re.sub(r'^\s*window\.YTD\.tweets\.part\d+\s*=\s*', '', content)
        content = content.strip().rstrip(';')

        try:
            tweets = json.loads(content)
        except json.JSONDecodeError:
            return items
    else:
        # JSON direkt
        try:
            tweets = json.loads(export_path.read_text(encoding='utf-8'))
            if isinstance(tweets, dict):
                tweets = tweets.get('tweets', tweets.get('data', []))
        except json.JSONDecodeError:
            return items

    for tweet in tweets:
        if not isinstance(tweet, dict):
            continue

        # Handle verschiedene X Export-Formate
        tweet_data = tweet.get('tweet', tweet)

        tweet_id = str(tweet_data.get('id') or tweet_data.get('id_str', ''))
        content = tweet_data.get('full_text') or tweet_data.get('text', '')
        created_at = tweet_data.get('created_at', '')

        # Engagement-Zahlen
        favorite_count = int(tweet_data.get('favorite_count', 0))
        retweet_count = int(tweet_data.get('retweet_count', 0))
        reply_count = int(tweet_data.get('reply_count', 0))

        # Views nicht immer verfügbar in Export
        views = int(tweet_data.get('views', tweet_data.get('view_count', favorite_count * 10)))

        author = tweet_data.get('user', {}).get('screen_name', 'unknown')

        # Extrahiere Metadaten
        hashtags = _extract_hashtags(content)
        mentions = _extract_mentions(content)
        urls = _extract_urls(content)

        # Berechne Viralität
        viral_score = _calc_viral_score(favorite_count, retweet_count, reply_count, views)

        # Klassifiziere Angle
        engagement = {'likes': favorite_count, 'retweets': retweet_count, 'replies': reply_count}
        angle_type = _classify_angle(content, engagement)

        # Extrahiere Hooks
        hooks = _extract_hooks(content)
        hook_pattern = hooks[0] if hooks else ""

        items.append(XTrendItem(
            tweet_id=tweet_id,
            author=author,
            content=content,
            created_at=created_at,
            likes=favorite_count,
            retweets=retweet_count,
            replies=reply_count,
            views=views,
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
            viral_score=viral_score,
            hook_pattern=hook_pattern,
            angle_type=angle_type,
        ))

    return items


def fetch_x_trends_api(config: XScoutConfig) -> List[XTrendItem]:
    """
    Fetcht Trends über X API v2 (falls Bearer Token verfügbar)
    Fallback zu Export-Parsing wenn kein Token
    """
    if not config.bearer_token:
        return []

    items = []

    headers = {
        "Authorization": f"Bearer {config.bearer_token}",
        "Content-Type": "application/json",
    }

    for query in config.search_queries:
        try:
            # Recent Search Endpoint
            encoded_query = urllib.parse.quote(f"{query} lang:de -is:retweet")
            url = (
                f"https://api.twitter.com/2/tweets/search/recent"
                f"?query={encoded_query}"
                f"&max_results={min(config.max_results_per_query, 100)}"
                f"&tweet.fields=created_at,public_metrics,entities,author_id"
            )

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            tweets = data.get('data', [])
            for tweet in tweets:
                metrics = tweet.get('public_metrics', {})

                items.append(XTrendItem(
                    tweet_id=tweet.get('id', ''),
                    author=tweet.get('author_id', 'unknown'),
                    content=tweet.get('text', ''),
                    created_at=tweet.get('created_at', ''),
                    likes=metrics.get('like_count', 0),
                    retweets=metrics.get('retweet_count', 0),
                    replies=metrics.get('reply_count', 0),
                    views=metrics.get('impression_count', 0),
                    hashtags=[h.get('tag') for h in tweet.get('entities', {}).get('hashtags', [])],
                    viral_score=_calc_viral_score(
                        metrics.get('like_count', 0),
                        metrics.get('retweet_count', 0),
                        metrics.get('reply_count', 0),
                        metrics.get('impression_count', 1),
                    ),
                    angle_type=_classify_angle(tweet.get('text', ''), metrics),
                ))

        except Exception as e:
            print(f"[X Scout] API Error for query '{query}': {e}")
            continue

    return items


def analyze_trends(items: List[XTrendItem]) -> TrendAnalysis:
    """Analysiert Trends und generiert Content-Empfehlungen"""
    if not items:
        return TrendAnalysis(timestamp=datetime.now().isoformat())

    # Sortiere nach Viralität
    sorted_items = sorted(items, key=lambda x: x.viral_score, reverse=True)
    top_items = sorted_items[:20]

    # Sammle Top Hooks
    all_hooks = []
    for item in top_items:
        if item.hook_pattern:
            all_hooks.append(item.hook_pattern)
    top_hooks = list(dict.fromkeys(all_hooks))[:10]  # Dedupe, max 10

    # Trending Angles
    angle_counts = {}
    for item in top_items:
        angle_counts[item.angle_type] = angle_counts.get(item.angle_type, 0) + 1
    trending_angles = sorted(angle_counts.keys(), key=lambda a: angle_counts[a], reverse=True)[:5]

    # Hot Topics (Hashtags)
    hashtag_counts = {}
    for item in top_items:
        for tag in item.hashtags:
            hashtag_counts[tag.lower()] = hashtag_counts.get(tag.lower(), 0) + 1
    hot_topics = [f"#{t}" for t in sorted(hashtag_counts.keys(), key=lambda x: hashtag_counts[x], reverse=True)[:10]]

    # Virale Patterns
    patterns = []
    for item in top_items[:10]:
        if item.viral_score > 50:
            patterns.append({
                'hook': item.hook_pattern[:50] if item.hook_pattern else item.content[:50],
                'angle': item.angle_type,
                'score': item.viral_score,
            })

    # Sentiment-Indikatoren
    high_performing = [i for i in items if i.viral_score > 30]
    avg_engagement = sum(i.likes + i.retweets for i in high_performing) / len(high_performing) if high_performing else 0

    sentiment = {
        'avg_engagement_rate': round(avg_engagement, 2),
        'high_performing_count': len(high_performing),
        'total_analyzed': len(items),
        'top_viral_score': top_items[0].viral_score if top_items else 0,
    }

    # Urgency-Bestimmung
    if len(high_performing) > 10 and top_items[0].viral_score > 100:
        urgency = "high"
    elif len(high_performing) > 5:
        urgency = "medium"
    else:
        urgency = "low"

    return TrendAnalysis(
        timestamp=datetime.now().isoformat(),
        top_hooks=top_hooks,
        trending_angles=trending_angles,
        hot_topics=hot_topics,
        viral_patterns=[p['hook'] for p in patterns],
        sentiment_indicators=sentiment,
        recommended_urgency=urgency,
    )


def convert_to_nuggets(items: List[XTrendItem], analysis: TrendAnalysis) -> List[Dict[str, Any]]:
    """Konvertiert Top Trends zu Gold Nuggets Format"""
    nuggets = []

    for item in items[:15]:  # Top 15
        if item.viral_score < 20:  # Mindest-Schwelle
            continue

        nugget = {
            "nugget_id": f"x_trend_{item.tweet_id[:12]}",
            "source": "x_twitter",
            "asset_type": _map_angle_to_asset_type(item.angle_type),
            "content": item.hook_pattern if item.hook_pattern else item.content[:100],
            "full_context": item.content,
            "viral_signals": {
                "score": item.viral_score,
                "likes": item.likes,
                "retweets": item.retweets,
                "views": item.views,
            },
            "meta": {
                "author": item.author,
                "created_at": item.created_at,
                "hashtags": item.hashtags,
                "angle_type": item.angle_type,
            },
            "ranking": {
                "impact": min(item.viral_score / 10, 10),
                "novelty": 7 if item.angle_type == "newsjacking" else 5,
                "ease": 8 if item.angle_type in ["contrarian", "story"] else 6,
                "time_relevance": 9 if item.angle_type == "newsjacking" else 7,
            }
        }
        nuggets.append(nugget)

    # Füge Meta-Nuggets für Patterns hinzu
    for hook in analysis.top_hooks[:5]:
        stable_id = hashlib.sha1(hook.encode("utf-8")).hexdigest()[:12]
        nuggets.append({
            "nugget_id": f"x_pattern_{stable_id}",
            "source": "x_analysis",
            "asset_type": "hook",
            "content": hook,
            "full_context": f"Viral hook pattern from X trends. Urgency: {analysis.recommended_urgency}",
            "meta": {"pattern_type": "hook", "urgency": analysis.recommended_urgency},
            "ranking": {"impact": 9, "novelty": 6, "ease": 9, "time_relevance": 8},
        })

    return nuggets


def _map_angle_to_asset_type(angle: str) -> str:
    """Mappt X Angle zu Nugget Asset Type"""
    mapping = {
        "contrarian": "angle",
        "educational": "process",
        "story": "story",
        "newsjacking": "angle",
        "authority": "metric",
        "general": "hook",
    }
    return mapping.get(angle, "hook")


def save_nuggets(nuggets: List[Dict[str, Any]], run_id: str) -> Path:
    """Speichert Nuggets im ai-vault/nuggets/"""
    ensure_dir(NUGGETS_DIR)

    output_file = NUGGETS_DIR / f"x_trends_{run_id}.json"
    write_json(output_file, {"nuggets": nuggets, "count": len(nuggets), "run_id": run_id})

    return output_file


def run_x_scout(
    export_path: Path | None = None,
    bearer_token: str = "",
    search_queries: List[str] | None = None,
    run_id: str | None = None,
) -> Dict[str, Any]:
    """
    Hauptfunktion für X Trend Scout

    Args:
        export_path: Pfad zu X Export (tweets.js oder JSON)
        bearer_token: X API Bearer Token (optional)
        search_queries: Liste von Suchqueries für API
        run_id: Optional run_id

    Returns:
        Dictionary mit Analysis, Nuggets, und Datei-Referenzen
    """
    resolved_run_id = run_id or timestamp_id()
    ensure_dir(DELIVERABLES_DIR / resolved_run_id)

    # Default Queries für AI Automation Nische (DE)
    default_queries = [
        "KI Automation",
        "AI Tools Deutsch",
        "ChatGPT Tipps",
        "KI Business",
        "Automation Workflow",
    ]
    queries = search_queries or default_queries

    config = XScoutConfig(
        run_id=resolved_run_id,
        bearer_token=bearer_token,
        search_queries=queries,
    )

    items = []

    # 1. Versuche Export-Parsing
    if export_path and export_path.exists():
        print(f"[X Scout] Parsing export: {export_path}")
        items.extend(parse_x_export_json(export_path))

    # 2. Versuche API (falls Token vorhanden)
    if bearer_token:
        print(f"[X Scout] Fetching from API...")
        items.extend(fetch_x_trends_api(config))

    if not items:
        return {
            "run_id": resolved_run_id,
            "status": "no_data",
            "message": "No X data available. Provide export file or bearer token.",
        }

    # Analyse
    analysis = analyze_trends(items)

    # Convert zu Nuggets
    nuggets = convert_to_nuggets(items, analysis)

    # Speichern
    nuggets_file = save_nuggets(nuggets, resolved_run_id)
    analysis_file = DELIVERABLES_DIR / resolved_run_id / "trend_analysis.json"
    write_json(analysis_file, analysis.__dict__)

    # Markdown Report
    report_lines = [
        f"# X Trend Scout Report: {resolved_run_id}",
        "",
        f"**Zeit:** {analysis.timestamp}",
        f"**Urgency:** {analysis.recommended_urgency}",
        f"**Items Analyzed:** {len(items)}",
        f"**Nuggets Extracted:** {len(nuggets)}",
        "",
        "## 🔥 Top Hooks",
        "",
    ]
    for i, hook in enumerate(analysis.top_hooks[:10], 1):
        report_lines.append(f"{i}. {hook}")

    report_lines.extend(["", "## 📐 Trending Angles", ""])
    for angle in analysis.trending_angles:
        report_lines.append(f"- {angle}")

    report_lines.extend(["", "## 🏷️ Hot Topics", ""])
    for topic in analysis.hot_topics[:10]:
        report_lines.append(f"- {topic}")

    report_lines.extend(["", "## 📊 Sentiment Indicators", ""])
    for key, value in analysis.sentiment_indicators.items():
        report_lines.append(f"- {key}: {value}")

    report_lines.extend(["", "## 💡 Viral Patterns", ""])
    for pattern in analysis.viral_patterns[:10]:
        report_lines.append(f"- {pattern}")

    report_file = DELIVERABLES_DIR / resolved_run_id / "trend_report.md"
    write_text(report_file, "\n".join(report_lines))

    return {
        "run_id": resolved_run_id,
        "status": "success",
        "items_analyzed": len(items),
        "nuggets_extracted": len(nuggets),
        "nuggets_file": str(nuggets_file),
        "analysis_file": str(analysis_file),
        "report_file": str(report_file),
        "urgency": analysis.recommended_urgency,
        "top_hooks": analysis.top_hooks[:5],
        "trending_angles": analysis.trending_angles,
    }


if __name__ == "__main__":
    import sys

    # CLI Usage
    export_file = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    result = run_x_scout(export_path=export_file)
    print(json.dumps(result, indent=2, ensure_ascii=False))

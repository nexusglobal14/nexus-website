#!/usr/bin/env python3
"""
Nexus Pakistan - static page builder.

Run this AFTER your script has refreshed latest_news.json and
"Google trends Daily/latest_trends.csv":

    python build_static.py

It writes index.html with the headlines and trends already inside the HTML,
so search engines see real content without running JavaScript. It also
rewrites sitemap.xml with today's date. Browsers then refresh the lists
live with the small script in the page.
"""
import csv, html, json, os, re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://web.nexusglobalit.org"
PKT = timezone(timedelta(hours=5))
esc = lambda s: html.escape(s, quote=True)
is_rtl = lambda s: bool(re.search(r"[\u0600-\u06FF]", s))

def load_news(limit=10):
    with open(os.path.join(ROOT, "latest_news.json"), encoding="utf-8") as f:
        items = json.load(f)
    out = []
    for it in items:
        title, link = (it.get("title") or "").strip(), (it.get("link") or "").strip()
        if not title or not link.startswith(("http://", "https://")):
            continue
        dt = None
        try:
            dt = parsedate_to_datetime(it.get("pubDate") or "").astimezone(PKT)
        except Exception:
            pass
        host = urlparse(link).netloc.replace("www.", "")
        source = "BBC Urdu" if "bbc." in host and "/urdu/" in link else host
        out.append(dict(title=title, link=link, dt=dt, source=source))
    out.sort(key=lambda x: x["dt"] or datetime(1970, 1, 1, tzinfo=PKT), reverse=True)
    return out[:limit]

def load_trends(limit=10):
    path = os.path.join(ROOT, "Google trends Daily", "latest_trends.csv")
    out = []
    with open(path, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            topic = (row.get("Trends") or "").strip()
            if not topic:
                continue
            link = (row.get("Explore link") or "").strip()
            if not link.startswith("http"):
                link = "https://trends.google.com/trends/explore?q=" + topic.replace(" ", "%20") + "&geo=PK"
            out.append(dict(topic=topic, volume=(row.get("Search volume") or "").strip(), link=link))
            if len(out) >= limit:
                break
    return out

def news_html(items):
    parts = []
    for n in items:
        when = n["dt"].strftime("%d %b %Y, %I:%M %p PKT") if n["dt"] else "Recent update"
        lang = ' lang="ur" dir="rtl"' if is_rtl(n["title"]) else ""
        parts.append(f'<div class="news-item"><a href="{esc(n["link"])}" target="_blank" rel="noopener noreferrer" class="news-title"{lang}>{esc(n["title"])}</a>'
                     f'<span class="news-time">{esc(when)} &middot; Source: {esc(n["source"])}</span></div>')
    return "\n".join(parts)

def trends_html(items):
    parts = []
    for i, t in enumerate(items, 1):
        vol = f' <span class="news-time">({esc(t["volume"])} searches)</span>' if t["volume"] else ""
        lang = ' lang="ur" dir="auto"' if is_rtl(t["topic"]) else ""
        parts.append(f'<div class="news-item"><span class="rank">#{i}</span><a href="{esc(t["link"])}" target="_blank" rel="noopener noreferrer" class="trend-link"{lang}>{esc(t["topic"])}</a>{vol}</div>')
    return "\n".join(parts)

HEADER = '''<header class="site"><a class="logo" href="/">NEXUS <span>PAKISTAN</span></a>
<nav aria-label="Main"><a href="/">Home</a><a href="/about/">About</a><a href="https://calc.nexusglobalit.org/">Calculators</a><a href="https://tools.nexusglobalit.org/">Tools</a><a href="/contact/">Contact</a></nav></header>'''
FOOTER = '''<footer class="site"><a href="/">Home</a><a href="/about/">About</a><a href="/privacy-policy/">Privacy Policy</a><a href="/contact/">Contact</a><a href="https://www.nexusglobalit.org/">Nexus Global</a>
<p style="margin-top:8px">&copy; 2026 Nexus Global Information Technology</p></footer>'''

def build_index():
    news, trends = load_news(), load_trends()
    now = datetime.now(PKT)
    updated = now.strftime("%d %B %Y, %I:%M %p PKT")
    ld = [
        {"@context": "https://schema.org", "@type": "WebSite", "name": "Nexus Pakistan", "url": BASE + "/",
         "publisher": {"@type": "Organization", "name": "Nexus Global Information Technology", "url": "https://www.nexusglobalit.org/"}},
        {"@context": "https://schema.org", "@type": "ItemList", "name": "Top Google Trends in Pakistan",
         "itemListElement": [{"@type": "ListItem", "position": i, "name": t["topic"], "url": t["link"]} for i, t in enumerate(trends, 1)]},
    ]
    desc = "Daily Pakistan dashboard: latest Urdu news headlines from BBC Urdu, today's top Google Trends in Pakistan and live USD and EUR to PKR rates."
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pakistan News Headlines, Google Trends & USD to PKR Rate Today | Nexus Pakistan</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{BASE}/">
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:site_name" content="Nexus Pakistan"><meta property="og:title" content="Pakistan News Headlines, Google Trends &amp; USD to PKR Rate Today"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{BASE}/"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body>
<div class="container">
{HEADER}
<section class="intro"><h1>Pakistan Today: News Headlines, Google Trends and PKR Rates</h1>
<p>Latest Urdu headlines, what Pakistan is searching for on Google right now, and live exchange rates, all in one place. Last updated: <time datetime="{now.isoformat()}">{updated}</time>.</p></section>
<main>
<div class="widget"><h2><span>Top Headlines</span><span class="status-badge" id="news-status">Updated {now.strftime("%d %b")}</span></h2>
<div id="news-container">
{news_html(news)}
</div>
<a class="cta" href="https://calc.nexusglobalit.org/">Free calculators: mortgage, SIP, BMI, age and more</a>
</div>
</main>
<aside>
<div class="widget"><h2><span>Live Rates</span><span class="status-badge">API</span></h2>
<div class="ticker-bar"><div class="ticker-item">USD / PKR<span class="ticker-val" id="usd-pkr">Loading...</span></div><div class="ticker-item">EUR / PKR<span class="ticker-val" id="eur-pkr">Loading...</span></div></div>
<p class="news-time" style="margin-top:8px">Rates load live in your browser from open.er-api.com. They are indicative mid-market rates and may differ from bank or open-market rates.</p></div>
<div class="widget"><h2><span>Top 10 Google Trends in Pakistan</span></h2>
<div id="trends-container">
{trends_html(trends)}
</div></div>
</aside>
<section class="about" id="about">
<h2>About this page</h2>
<p>Nexus Pakistan is a simple daily dashboard that brings together three things people in Pakistan check often: the latest news headlines, the topics trending on Google Search in Pakistan, and the US dollar and euro exchange rates against the Pakistani rupee.</p>
<h2>Where the information comes from</h2>
<ul><li><strong>Headlines</strong> come from the public RSS feed of BBC Urdu. We show the headline and link to the original article, which opens on the BBC website. We do not copy article text.</li>
<li><strong>Trends</strong> are the daily trending searches for Pakistan from Google Trends. Each item links to its Google Trends page. Search volume is shown as Google reports it, for example 50K+.</li>
<li><strong>Exchange rates</strong> are fetched live in your browser from the open.er-api.com service.</li></ul>
<h2>How often it updates</h2>
<p>Headlines and trends are refreshed regularly and the page is rebuilt each time. The time of the last update is shown at the top of the page. Exchange rates refresh every minute while the page is open.</p>
<h2>Limits and disclaimer</h2>
<p>Headlines are the work of their original publishers and Nexus Pakistan is not responsible for their content. Trending topics only show what people are searching for, not whether something is true. Exchange rates are indicative and should not be used for financial decisions without checking with your bank or exchange company.</p>
<p>See also our free <a href="https://calc.nexusglobalit.org/">online calculators</a> and <a href="https://tools.nexusglobalit.org/">browser tools</a>.</p>
</section>
{FOOTER}
</div>
<noscript><p style="text-align:center;color:#94a3b8;margin-top:10px">Live exchange rates need JavaScript. Headlines and trends above were saved at the last update.</p></noscript>
<script>
(function(){{
function el(t,c,x){{var e=document.createElement(t);if(c)e.className=c;if(x!==undefined)e.textContent=x;return e;}}
function safe(u){{return /^https?:\\/\\//i.test(u);}}
function hasUrdu(s){{return /[\\u0600-\\u06FF]/.test(s);}}
var clock=document.getElementById('clock');
async function rates(){{try{{var r=await fetch('https://open.er-api.com/v6/latest/USD');var d=await r.json();
if(d&&d.rates&&d.rates.PKR){{document.getElementById('usd-pkr').textContent='Rs '+d.rates.PKR.toFixed(2);
document.getElementById('eur-pkr').textContent='Rs '+(d.rates.PKR/d.rates.EUR).toFixed(2);}}}}catch(e){{document.getElementById('usd-pkr').textContent='Unavailable';document.getElementById('eur-pkr').textContent='Unavailable';}}}}
async function news(){{try{{var r=await fetch('/latest_news.json?v='+Date.now());if(!r.ok)return;var items=await r.json();if(!items||!items.length)return;
items.sort(function(a,b){{return (Date.parse(b.pubDate)||0)-(Date.parse(a.pubDate)||0);}});
var box=document.getElementById('news-container');var frag=document.createDocumentFragment();
items.slice(0,10).forEach(function(it){{if(!it.title||!safe(it.link||''))return;var d=el('div','news-item');var a=el('a','news-title',it.title);a.href=it.link;a.target='_blank';a.rel='noopener noreferrer';
if(hasUrdu(it.title)){{a.lang='ur';a.dir='rtl';}}var t=Date.parse(it.pubDate);
d.appendChild(a);d.appendChild(el('span','news-time',(t?new Date(t).toLocaleString([], {{dateStyle:'medium',timeStyle:'short'}}):'Recent update')+' \\u00b7 Source: BBC Urdu'));frag.appendChild(d);}});
if(frag.childNodes.length){{box.textContent='';box.appendChild(frag);}}}}catch(e){{}}}}
rates();news();setInterval(rates,60000);setInterval(news,300000);
}})();
</script>
</body>
</html>'''
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    return now


def page(slug, title, desc, h1, body):
    url = f"{BASE}/{slug}/"
    s = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Nexus Pakistan</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<div class="container">
{HEADER}
<main class="page" style="grid-column:1/-1"><h1>{h1}</h1>
{body}
</main>
{FOOTER}
</div>
</body>
</html>'''
    os.makedirs(os.path.join(ROOT, slug), exist_ok=True)
    with open(os.path.join(ROOT, slug, "index.html"), "w", encoding="utf-8") as f:
        f.write(s)

def build_pages():
    page("about", "About", "About Nexus Pakistan, a daily dashboard of Pakistan news headlines, Google Trends and PKR exchange rates from Nexus Global Information Technology.", "About Nexus Pakistan",
'''<p>Nexus Pakistan is a small project of <a href="https://www.nexusglobalit.org/">Nexus Global Information Technology</a>. It gives you one quick page to see the latest Urdu headlines, what Pakistan is searching for on Google today and the current USD and EUR rates in rupees.</p>
<h2>What we do</h2>
<p>We collect public headline feeds and daily trend lists, rebuild the page whenever they change, and link every item back to its original source. We do not republish article text.</p>
<h2>What we do not do</h2>
<p>We are not a newsroom. We do not write or verify the news that appears here, so please read the original publisher for the full story. Exchange rates are indicative only.</p>
<h2>More from Nexus Global</h2>
<ul><li><a href="https://calc.nexusglobalit.org/">Free online calculators</a> for finance, health and everyday math.</li>
<li><a href="https://tools.nexusglobalit.org/">Free browser tools</a> such as an image compressor, JSON formatter and QR code generator.</li></ul>
<p>Questions or corrections? Use the <a href="/contact/">contact page</a>.</p>''')
    page("contact", "Contact", "Contact the Nexus Pakistan team with feedback, corrections or removal requests.", "Contact Us",
'''<p>Send feedback, report a problem or ask us to remove a link. We read every message.</p>
<form action="https://formspree.io/f/xbgorkgb" method="POST">
<label for="name">Your name</label><input id="name" name="name" type="text" required>
<label for="email">Your email</label><input id="email" name="email" type="email" required>
<label for="message">Message</label><textarea id="message" name="message" rows="5" required></textarea>
<button type="submit">Send message</button></form>
<p style="margin-top:12px;font-size:.85rem">Messages are delivered through Formspree. We use your email only to reply.</p>''')
    page("privacy-policy", "Privacy Policy", "How Nexus Pakistan handles data: no accounts, no tracking cookies, and third-party services used on the page.", "Privacy Policy",
'''<p style="font-size:.85rem">Last updated: November 15, 2026</p>
<h2>What we collect</h2>
<p>We do not ask you to create an account and we do not set advertising or tracking cookies. Our hosting provider may keep standard server logs, such as IP address, browser type and pages requested, for security and operations.</p>
<h2>Third-party services</h2>
<p>To show live exchange rates, your browser contacts open.er-api.com directly, which means that service can see your IP address. Links on this page lead to other websites, including BBC Urdu and Google Trends, which have their own privacy policies.</p>
<h2>Contact form</h2>
<p>If you submit the contact form, your name, email address and message are sent to Formspree and delivered to us. We use them only to reply.</p>
<h2>Contact</h2>
<p>Questions about this policy? Use the <a href="/contact/">contact page</a>.</p>''')

def write_sitemap(now):
    d = now.strftime("%Y-%m-%d")
    urls = [("/", d), ("/about/", "2026-11-15"), ("/contact/", "2026-11-15"), ("/privacy-policy/", "2026-11-15")]
    body = "".join(f"  <url>\n    <loc>{BASE}{u}</loc>\n    <lastmod>{m}</lastmod>\n  </url>\n" for u, m in urls)
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n")

if __name__ == "__main__":
    n = build_index()
    build_pages()
    write_sitemap(n)
    print("index.html and sitemap.xml written at", n.isoformat())

#!/usr/bin/env python3
"""PersianPulse static site builder (stdlib only).
Usage: python3 _src/build.py --out _site [--through YYYY-MM-DD]
Reads _src/data/pieces.json. Publishes pieces dated on or before the cutoff
(default: most recent Saturday on/before yesterday, Pacific time)."""
import argparse, json, shutil, html, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
SRC = Path(__file__).parent
E_ = html.escape

def cutoff_default():
    y = (dt.datetime.now(ZoneInfo("America/Los_Angeles")) - dt.timedelta(days=1)).date()
    return y - dt.timedelta(days=(y.weekday() - 5) % 7)

CSS = """
@font-face{font-family:Lora;src:url(/assets/fonts/Lora-Variable.ttf);font-weight:400 700;font-display:swap}
@font-face{font-family:Inter;src:url(/assets/fonts/Inter-Regular.otf);font-weight:400;font-display:swap}
@font-face{font-family:Inter;src:url(/assets/fonts/Inter-SemiBold.otf);font-weight:600;font-display:swap}
@font-face{font-family:Vazirmatn;src:url(/assets/fonts/Vazirmatn-Regular.ttf);font-weight:400;font-display:swap}
@font-face{font-family:Vazirmatn;src:url(/assets/fonts/Vazirmatn-Bold.ttf);font-weight:700;font-display:swap}
:root{--crimson:#C42B2F;--dark:#8D1E21;--gold:#C9A24B;--sage:#9DB59A;--sagel:#E8EEE3;--paper:#F8F4EC;--ink:#1F1A1C;--muted:#5B5655;--line:#E4DCCB}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 Inter,system-ui,sans-serif}
h1,h2,h3{font-family:Lora,Georgia,serif;line-height:1.2;margin:0 0 .5em}
h1{font-size:clamp(2rem,5vw,3rem)}h2{font-size:1.6rem}h3{font-size:1.2rem}
a{color:var(--dark)}a:hover{color:var(--crimson)}
.wrap{max-width:1060px;margin:0 auto;padding:0 20px}
header.top{border-bottom:1px solid var(--line);background:var(--paper);position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font:700 1.25rem Lora,serif}
.brand img{width:40px;height:40px}
nav{display:flex;gap:4px 18px;flex-wrap:wrap;margin-left:auto;font-size:.95rem}
nav a{text-decoration:none;color:var(--muted);padding:4px 0;border-bottom:2px solid transparent}
nav a.langsw{color:var(--dark);font-weight:600}nav a:hover,nav a.on{color:var(--crimson);border-color:var(--crimson)}
.hero{padding:56px 0 40px;background:linear-gradient(180deg,var(--sagel),var(--paper))}
.hero p{max-width:620px;color:var(--muted);font-size:1.15rem}
.fa{font-family:Vazirmatn,Inter,sans-serif;direction:rtl;font-style:normal}
.btn{display:inline-block;background:var(--crimson);color:#fff;text-decoration:none;padding:10px 20px;border-radius:999px;font-weight:600;font-size:.95rem;border:0;cursor:pointer}
.btn:hover{background:var(--dark);color:#fff}.btn.alt{background:#fff;color:var(--dark);border:1.5px solid var(--crimson)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:22px;margin:28px 0 56px}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;text-decoration:none;color:var(--ink);display:block;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 24px rgba(31,26,28,.12)}
.card img{width:100%;aspect-ratio:4/5;object-fit:cover;display:block;background:var(--sagel)}
.card div{padding:12px 16px 16px}.card small{color:var(--muted)}
.card h3{font-size:1.05rem;margin:.2em 0 0}
.tag{display:inline-block;background:var(--sagel);color:#46603f;border-radius:999px;padding:2px 12px;font-size:.8rem;font-weight:600}
main{padding:36px 0 64px;min-height:60vh}
.piece{display:grid;grid-template-columns:minmax(0,520px) minmax(0,1fr);gap:40px;align-items:start}
@media(max-width:820px){.piece{grid-template-columns:1fr}}
.piece img.main{width:100%;height:auto;border-radius:12px;border:1px solid var(--line);display:block}
.tabs{display:flex;gap:8px;margin:0 0 18px}
.tabs button{font:600 .95rem Inter,sans-serif;padding:8px 20px;border-radius:999px;border:1.5px solid var(--line);background:#fff;cursor:pointer;color:var(--muted)}
.tabs button[aria-selected=true]{background:var(--crimson);border-color:var(--crimson);color:#fff}
[hidden]{display:none!important}.hero{margin-top:-36px}body.fa{font-family:Vazirmatn,Inter,sans-serif}body.fa h1,body.fa h2,body.fa h3,body.fa .brand{font-family:Vazirmatn,Lora,serif;font-weight:700}body.fa nav{margin-left:0;margin-right:auto}body.fa .box ul{padding:0 1.2em 0 0}body.fa .card div{text-align:right}
.box{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:16px 0}
.box h3{font-size:1rem;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:.4em}
.box ul{margin:0;padding-left:1.2em}.box.fa ul{padding:0 1.2em 0 0}
.row{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
.note{background:var(--sagel);border-radius:10px;padding:10px 16px;font-size:.92rem;color:#3d5237}
footer{border-top:1px solid var(--line);background:#fff;padding:32px 0;color:var(--muted);font-size:.92rem}
footer .wrap{display:flex;flex-wrap:wrap;gap:12px 32px;justify-content:space-between}
.prose{max-width:720px}.prose li{margin:.3em 0}
.empty{background:#fff;border:1px dashed var(--gold);border-radius:12px;padding:24px;color:var(--muted)}
"""
JS = """document.querySelectorAll('.tabs').forEach(function(t){var bs=t.querySelectorAll('button');bs.forEach(function(b){b.addEventListener('click',function(){bs.forEach(function(x){x.setAttribute('aria-selected',x===b)});document.querySelectorAll('.lang').forEach(function(l){l.hidden=l.dataset.l!==b.dataset.l});})})});
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){var t=document.getElementById(b.dataset.copy).innerText;if(navigator.clipboard){navigator.clipboard.writeText(t);b.textContent='Copied'}})});"""
UI = {
 "en": {"nav":[("/","Home"),("/archive/","Archive"),("/topics/","Topics"),("/words/","Words to Know"),("/sources/","Sources and method"),("/about/","About")],
        "foot":"Educational content, not medical advice. For adults 18+.","follow":"Follow","other":"فارسی","dl":"Download high resolution","cap":"Caption","src":"Sources","alt":"Image description (ALT text)","back":"← Archive","latest":"Latest","browse":"Browse the archive"},
 "fa": {"nav":[("/","خانه"),("/archive/","آرشیو"),("/topics/","موضوع‌ها"),("/words/","واژه‌های مهم"),("/sources/","منبع‌ها و روش"),("/about/","درباره")],
        "foot":"محتوای آموزشی است و توصیه پزشکی نیست. برای بزرگسالان ۱۸ سال به بالا.","follow":"ما را دنبال کنید","other":"English","dl":"دریافت با کیفیت بالا","cap":"کپشن","src":"منبع‌ها","alt":"متن جایگزین تصویر","back":"آرشیو ←","latest":"تازه‌ترین‌ها","browse":"مشاهده آرشیو"},
}
def pre(l): return "/fa" if l == "fa" else ""

def page(title, body, path, site, desc=None, og=None, lang="en"):
    """path is the language-neutral path, e.g. /archive/ or /p/slug/."""
    u = UI[lang]; P = pre(lang)
    desc = desc or (site["tagline_fa"] if lang == "fa" else site["tagline"])
    nav = "".join(f'<a href="{P}{x}"{" class=on" if (x==path or (x!="/" and path.startswith(x))) else ""}>{n}</a>' for x, n in u["nav"])
    ol = "en" if lang == "fa" else "fa"
    ogimg = f'<meta property="og:image" content="{site["url"]}{og or "/assets/og.png"}">'
    sitename = site["name"]
    return f"""<!doctype html><html lang="{lang}"{' dir="rtl"' if lang=="fa" else ''}><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E_(title)}</title><meta name="description" content="{E_(desc)}">
<link rel="alternate" hreflang="{ol}" href="{site['url']}{pre(ol)}{path}"><link rel="alternate" hreflang="{lang}" href="{site['url']}{P}{path}">
<meta property="og:title" content="{E_(title)}"><meta property="og:description" content="{E_(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{site['url']}{P}{path}">{ogimg}<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css"></head><body class="{lang}">
<header class="top"><div class="wrap"><a class="brand" href="{P}/"><img src="/assets/logo.svg" alt="">{E_(sitename)}</a><nav>{nav}<a class="langsw" href="{pre(ol)}{path}" hreflang="{ol}" lang="{ol}">{u['other']}</a></nav></div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap"><div><strong>{E_(sitename)}</strong><br>{u['foot']}</div>
<div>{u['follow']} <span dir="ltr">{E_(site['handle'])}</span><br><a href="https://www.instagram.com/pomandpulse/">Instagram</a> · <a href="https://www.threads.net/@pomandpulse">Threads</a> · <a href="https://x.com/pomandpulse">X</a></div></div></footer>
<script src="/assets/site.js"></script></body></html>"""

FA_MONTHS = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن","ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]
def fadig(x): return str(x).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
def fmt(d, l="en"):
    x = dt.date.fromisoformat(d)
    return f"{fadig(x.day)} {FA_MONTHS[x.month-1]} {fadig(x.year)}" if l == "fa" else x.strftime("%b %-d, %Y")
def slug(s): return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-")
def T(p, k, l): return p[k + "_fa"] if l == "fa" else p[k]

def card(p, l):
    return f'<a class="card" href="{pre(l)}/p/{p["slug"]}/"><img src="/img/{p["id"]}_{l}_t.jpg" alt="{E_(T(p,"alt",l)[:140])}" loading="lazy"><div><span class="tag">{E_(T(p,"topic",l))}</span><h3>{E_(T(p,"title",l))}</h3><small>{fmt(p["date"],l)}</small></div></a>'

def piece_page(p, site, l):
    u = UI[l]; fa = l == "fa"
    src = "".join(f'<li><a href="{E_(x["u"])}">{E_(x["t"])}</a></li>' for x in p["sources"])
    note = f'<p class="note">{E_(T(p,"note",l))}</p>' if p.get("note") else ""
    body = f"""<p><a href="{pre(l)}/archive/">{u['back']}</a> · <span class="tag">{E_(T(p,'topic',l))}</span> · {fmt(p['date'],l)}</p>
<div class="piece"><div><img class="main" src="/img/{p['id']}_{l}.jpg" width="1280" height="1600" alt="{E_(T(p,'alt',l))}"></div><div>
<h1>{E_(T(p,'title',l))}</h1>
<div class="row"><a class="btn" href="/dl/{p['id']}_{l}_hi.jpg" download>{u['dl']} · JPG</a><a class="btn alt" href="/dl/{p['id']}_{l}_hi.pdf" download>PDF</a></div>
<div class="box"><h3>{u['cap']}</h3><p>{E_(T(p,'caption',l))}</p></div>
<div class="box"><h3>{u['src']}</h3><ul>{src}</ul></div>
<details class="box"><summary>{u['alt']}</summary><p>{E_(T(p,'alt',l))}</p></details>{note}</div></div>"""
    return page(f'{T(p,"title",l)} | {site["name"]}', body, f'/p/{p["slug"]}/', site, T(p,"caption",l), f'/img/{p["id"]}_en.jpg', l)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="_site"); ap.add_argument("--through")
    a = ap.parse_args()
    cut = dt.date.fromisoformat(a.through) if a.through else cutoff_default()
    data = json.loads((SRC / "data/pieces.json").read_text(encoding="utf-8"))
    site = data["site"]
    ps = sorted([p for p in data["pieces"] if dt.date.fromisoformat(p["date"]) <= cut], key=lambda p: p["date"], reverse=True)
    out = Path(a.out)
    if out.exists(): shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    shutil.copytree(SRC / "assets", out / "assets", dirs_exist_ok=True)
    (out / "assets/site.css").write_text(CSS); (out / "assets/site.js").write_text(JS)
    shutil.copy(out / "assets/logo.svg", out / "assets/favicon.svg")
    for sub in ("img", "dl"): (out / sub).mkdir()
    for p in ps:
        for f in list(SRC.glob(f"img/{p['id']}_*")) + list(SRC.glob(f"dl/{p['id']}_*")):
            shutil.copy(f, out / f.relative_to(SRC))
    def w(path, html_, l="en"):
        full = pre(l) + path
        f = out / "404.html" if path == "/404.html" else out / full.strip("/") / "index.html"
        f.parent.mkdir(parents=True, exist_ok=True); f.write_text(html_, encoding="utf-8")
    srcs = {}
    for p in ps:
        for x in p["sources"]: srcs.setdefault(x["u"], x["t"])
    for l in ("en", "fa"):
        fa = l == "fa"; u = UI[l]; N = site["name"]
        for p in ps: w(f'/p/{p["slug"]}/', piece_page(p, site, l), l)
        grid = "".join(card(p, l) for p in ps)
        latest = "".join(card(p, l) for p in ps[:6])
        intro = ("پست‌های گرم، کنجکاوانه و مبتنی بر شواهد درباره غذا و سلامت، به فارسی و <span lang=\"en\" dir=\"ltr\">English</span>." if fa else
                 'Warm, curious, evidence-first posts about food and health, in English and <a class="fa" href="/fa/" lang="fa">فارسی</a>.')
        tagl = site["tagline_fa"] if fa else site["tagline"]
        home = f"""</div><section class="hero"><div class="wrap"><h1>{N}</h1><p style="font:600 1.3rem Lora,serif;color:var(--dark)">{E_(tagl)}</p><p>{intro}</p><a class="btn" href="{pre(l)}/archive/">{u['browse']}</a></div></section><div class="wrap"><h2>{u['latest']}</h2><div class="grid">{latest}</div>"""
        w("/", page(f'{N} | {tagl}', home, "/", site, None, None, l), l)
        w("/archive/", page(f'{"آرشیو" if fa else "Archive"} | {N}', f'<h1>{"آرشیو" if fa else "Archive"}</h1><div class="grid">{grid}</div>', "/archive/", site, None, None, l), l)
        topics = {}
        for p in ps: topics.setdefault(T(p, "topic", l), []).append(p)
        tb = f'<h1>{"موضوع‌ها" if fa else "Topics"}</h1>' + "".join(f'<h2 id="{slug(t)}">{E_(t)}</h2><div class="grid">{"".join(card(p,l) for p in v)}</div>' for t, v in sorted(topics.items()))
        w("/topics/", page(f'{"موضوع‌ها" if fa else "Topics"} | {N}', tb, "/topics/", site, None, None, l), l)
        ws = data["words"]
        if fa:
            wb = '<h1>واژه‌های مهم</h1><p class="prose">فرهنگ‌واژه‌ای رو به رشد از اصطلاح‌های غذا و سلامت، از مجموعه «واژه‌های مهم» ما.</p>' + ("".join(f'<div class="box"><h3>{E_(x.get("term_fa",x["term"]))}</h3><p>{E_(x.get("def_fa",x["def"]))}</p></div>' for x in ws) or '<div class="empty">نخستین واژه‌ها پس از آغاز این مجموعه اینجا اضافه می‌شوند.</div>')
        else:
            wb = '<h1>Words to Know</h1><p class="prose">A growing glossary of food and health terms, in English and <span class="fa">فارسی</span>, drawn from our Words to Know series.</p>' + ("".join(f'<div class="box"><h3>{E_(x["term"])}</h3><p>{E_(x["def"])}</p></div>' for x in ws) or '<div class="empty">The first Words to Know entries will appear here once the series starts.</div>')
        w("/words/", page(f'{"واژه‌های مهم" if fa else "Words to Know"} | {N}', wb, "/words/", site, None, None, l), l)
        sl = "".join(f'<li><a href="{E_(k)}">{E_(v)}</a></li>' for k, v in srcs.items())
        if fa:
            sb = f"""<h1>منبع‌ها و روش</h1><div class="prose"><h2>روش کار ما</h2><ul>
<li>نخست منبع‌های اصلی: سازمان‌های رسمی سلامت، پژوهش‌های داوری‌شده و برگه‌های اطلاعات رسمی.</li>
<li>هرگز عدد از خود نمی‌سازیم. هر عددی روی تصاویر به منبعی پیوند دارد.</li>
<li>زبان محتاط: یافته‌ها «ممکن است» یا «نشان می‌دهند»، کمتر چیزی را «ثابت می‌کنند».</li>
<li>هر تصویر منبع‌ها و اعتبار عکس را نام می‌برد.</li>
<li>محتوای آموزشی است و توصیه پزشکی نیست. درباره وضعیت خودتان با یک متخصص سلامت مشورت کنید.</li></ul>
<h2>منبع‌های به‌کاررفته تاکنون</h2><ul>{sl}</ul></div>"""
        else:
            sb = f"""<h1>Sources and method</h1><div class="prose"><h2>How we work</h2><ul>
<li>Primary sources first: government health agencies, peer-reviewed research and official fact sheets.</li>
<li>We never invent numbers. Every figure on a graphic is traceable to a linked source.</li>
<li>Cautious wording: findings "may" or "suggest", they rarely "prove".</li>
<li>Every graphic names its sources and photo credits.</li>
<li>Educational content, not medical advice. Talk to a health professional about your own situation.</li></ul>
<h2>Sources used so far</h2><ul>{sl}</ul></div>"""
        w("/sources/", page(f'{"منبع‌ها و روش" if fa else "Sources and method"} | {N}', sb, "/sources/", site, None, None, l), l)
        if fa:
            ab = f"""<h1>درباره</h1><div class="prose"><p>{N} یک برند غذا، تغذیه و سلامت به فارسی و انگلیسی برای بزرگسالان ۱۸ سال به بالاست. ما با لحنی گرم و کنجکاو توضیح می‌دهیم شواهد درباره غذاهای روزمره چه می‌گویند، و هر پست منبع دارد.</p>
<p>ما را در اینستاگرام، تردز و ایکس با نام <strong dir="ltr">{E_(site['handle'])}</strong> پیدا کنید.</p><p class="note">محتوای آموزشی است و توصیه پزشکی نیست.</p></div>"""
        else:
            ab = f"""<h1>About</h1><div class="prose"><p>{N} is a food, nutrition and health brand in English and <span class="fa">فارسی</span> for adults 18+. We explain what the evidence says about everyday food in a warm, curious way, with sources on every post.</p>
<p>Find us on Instagram, Threads and X as <strong>{E_(site['handle'])}</strong>.</p><p class="note">Educational content, not medical advice.</p></div>"""
        w("/about/", page(f'{"درباره" if fa else "About"} | {N}', ab, "/about/", site, None, None, l), l)
    w("/404.html", page(f'Page not found | {site["name"]}', '<h1>Page not found</h1><p>That page does not exist. <a href="/">Back to the home page</a> · <a href="/fa/" class="fa">خانه</a>.</p>', "/404", site))
    base = site["url"]
    urls = [pre(l) + x for l in ("en", "fa") for x in ["/", "/archive/", "/topics/", "/words/", "/sources/", "/about/"] + [f'/p/{p["slug"]}/' for p in ps]]
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{base}{x}</loc></url>" for x in urls) + "</urlset>")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")
    (out / ".nojekyll").write_text("")
    print(f"built {len(ps)} piece(s) through {cut} -> {out}")
if __name__ == "__main__": main()

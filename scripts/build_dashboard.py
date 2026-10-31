"""Generates dashboard/imdb_dashboard.html from data/imdb_top_1000.csv."""
import json
import os

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(BASE, 'data', 'imdb_top_1000.csv')
OUT  = os.path.join(BASE, 'dashboard', 'imdb_dashboard.html')

df = pd.read_csv(CSV)

# ── cleaning ─────────────────────────────────────────────────────────────────
# Known data-entry error in the Kaggle file: Apollo 13 has its certificate in the year column
df.loc[df['Series_Title'].eq('Apollo 13') & df['Released_Year'].eq('PG'), 'Released_Year'] = '1995'

df['year']    = pd.to_numeric(df['Released_Year'], errors='coerce').astype('Int64')
df['runtime'] = pd.to_numeric(df['Runtime'].str.replace('min', '').str.strip(), errors='coerce')
df['gross']   = pd.to_numeric(df['Gross'].str.replace(',', ''), errors='coerce')
df['genres']  = df['Genre'].fillna('').str.split(', ')
# The CSV ships 67x98 thumbnails; keep the base image URL so the page can request any width
df['poster']  = df['Poster_Link'].str.replace(r'\._V1_.*\.jpg$', '', regex=True)

def num(x, nd=None):
    if pd.isna(x):
        return None
    return round(float(x), nd) if nd is not None else int(x)

movies = []
for _, r in df.iterrows():
    movies.append({
        't':  r['Series_Title'],
        'y':  num(r['year']),
        'g':  [g for g in r['genres'] if g],
        'r':  float(r['IMDB_Rating']),
        'm':  num(r['Meta_score']),
        'v':  int(r['No_of_Votes']),
        'rt': num(r['runtime']),
        'gr': num(r['gross']),
        'd':  r['Director'],
        's':  [r[c] for c in ['Star1', 'Star2', 'Star3', 'Star4'] if pd.notna(r[c])],
        'c':  r['Certificate'] if pd.notna(r['Certificate']) else None,
        'p':  r['poster'],
        'o':  r['Overview'],
    })

data_json = json.dumps({'movies': movies}, ensure_ascii=False).replace('</', '<\\/')

# ── HTML template ─────────────────────────────────────────────────────────────
HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMDb Top 1000 · Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>
  // apply the saved theme before first paint
  try { if(localStorage.getItem("imdb-theme") === "dark") document.documentElement.dataset.theme = "dark"; } catch(e) {}
</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}

:root{
  color-scheme:light;
  --page:#E6E6EA; --panel:#FFFFFF; --card:#F4F4F6; --card-2:#EBEBEF;
  --line:#EDEDF0; --line-2:#DCDCE2;
  --text:#17171B; --muted:#6B6B75; --subtle:#A3A3AD;
  --accent:#E5322D; --accent-2:#D02A25; --accent-soft:rgba(229,50,45,.09); --on-accent:#FFFFFF;
  /* diverging pair for correlations */
  --pos:#0E9AA7; --neg:#E07B39;
  --neutral:#2A2A31;
  --dot:rgba(23,23,27,.22);
  --hover:rgba(23,23,27,.035);
  --tip-bg:#FFFFFF;
  --shadow:0 1px 2px rgba(20,20,30,.04),0 12px 32px -18px rgba(20,20,30,.18);
  --font:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;
  --r-lg:22px; --r-md:16px; --r-sm:10px;
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0D0E12; --panel:#16171C; --card:#1E1F26; --card-2:#25262E;
  --line:#272830; --line-2:#33343D;
  --text:#ECECEF; --muted:#8D8E99; --subtle:#5F606B;
  --accent:#FF5A52; --accent-2:#FF8A84; --accent-soft:rgba(255,90,82,.14); --on-accent:#FFFFFF;
  --pos:#35C2CB; --neg:#F0965A;
  --neutral:#B9BAC4;
  --dot:rgba(236,236,239,.22);
  --hover:rgba(255,255,255,.04);
  --tip-bg:#25262E;
  --shadow:none;
}

html{scroll-behavior:smooth}
body{
  background:var(--page);
  color:var(--text);
  font-family:var(--font);
  font-size:14px;
  font-feature-settings:'tnum' 1;
  -webkit-font-smoothing:antialiased;
  min-height:100vh;
}
button,input,select{font-family:inherit;color:inherit}
svg.i{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
svg.star{width:12px;height:12px;fill:var(--accent);stroke:none;flex-shrink:0}

/* ── SHELL ───────────────────────────────────────────────────── */
.shell{
  display:grid;
  grid-template-columns:200px minmax(0,1fr) 280px;
  gap:14px;
  padding:14px;
  max-width:1600px;
  margin:0 auto;
  min-height:100vh;
}
.side,.main,.rail{background:var(--panel);border-radius:var(--r-lg);min-width:0;box-shadow:var(--shadow)}

/* sidebar */
.side{display:flex;flex-direction:column;padding:18px 14px;position:sticky;top:14px;height:calc(100vh - 28px)}
.brand{display:flex;align-items:center;gap:10px;padding:4px 8px 20px}
.brand-mark{
  width:30px;height:30px;border-radius:8px;display:grid;place-items:center;
  background:var(--card-2);border:1px solid var(--line-2);color:var(--accent);
}
.brand-mark svg{width:14px;height:14px}
.brand b{display:block;font-size:.88rem;font-weight:600;letter-spacing:-.01em;line-height:1.2}
.brand small{display:block;font-size:.68rem;color:var(--subtle);line-height:1.3}
.nav-label{font-size:.7rem;color:var(--subtle);padding:14px 10px 8px}
.nav-item{
  display:flex;align-items:center;gap:12px;width:100%;
  padding:10px 10px;border-radius:var(--r-sm);border:none;background:none;cursor:pointer;
  font-size:.86rem;font-weight:500;color:var(--muted);text-align:left;position:relative;
  transition:color .15s,background .15s;
}
.nav-item:hover{color:var(--text);background:var(--hover)}
.nav-item.active{color:var(--text)}
.nav-item.active svg{color:var(--accent)}
.nav-item.active::after{content:'';position:absolute;right:4px;top:12px;bottom:12px;width:3px;border-radius:3px;background:var(--accent)}
.side-foot{margin-top:auto;padding:12px 10px 4px;font-size:.7rem;line-height:1.55;color:var(--subtle)}

/* main */
.main{padding:16px 18px 24px}
.topbar{display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.search{
  display:flex;align-items:center;gap:10px;flex:1;min-width:220px;max-width:420px;
  padding:10px 14px;border-radius:12px;background:var(--card);color:var(--muted);
  border:1px solid transparent;
}
.search:focus-within{border-color:var(--line-2);color:var(--text)}
.search input{border:none;outline:none;background:none;font-size:.84rem;width:100%;color:var(--text)}
.search input::placeholder{color:var(--subtle)}
.active-filters{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.fchip{
  display:inline-flex;align-items:center;gap:7px;padding:7px 8px 7px 12px;border-radius:99px;
  background:var(--accent-soft);color:var(--accent-2);font-size:.76rem;font-weight:600;border:none;cursor:pointer;
}
.fchip svg{width:13px;height:13px}
.fchip:hover{background:rgba(255,138,61,.22)}
.count{margin-left:auto;font-size:.76rem;color:var(--muted)}
.count b{color:var(--text);font-weight:600}

.view{display:none}
.view.active{display:block}

/* hero */
.hero{
  position:relative;min-height:220px;border-radius:var(--r-lg);overflow:hidden;background:#16171C;color:#fff;
  isolation:isolate;display:flex;flex-direction:column;justify-content:space-between;gap:16px;
  padding:22px 190px 14px 24px;
}
.hero-bg{
  position:absolute;inset:-30px;background-size:cover;background-position:center 30%;
  filter:blur(30px) saturate(.9) brightness(.35);transform:scale(1.1);z-index:-2;
}
.hero::before{
  content:'';position:absolute;inset:0;z-index:-1;
  background:linear-gradient(90deg,rgba(22,23,28,.96) 0%,rgba(22,23,28,.7) 60%,rgba(22,23,28,.4) 100%);
}
.hero-poster{
  position:absolute;right:22px;top:20px;bottom:20px;aspect-ratio:2/3;border-radius:12px;
  background-size:cover;background-position:center;box-shadow:0 14px 30px -12px rgba(0,0,0,.7);
}
.hero-body{min-width:0}
.pill{
  display:inline-flex;align-items:center;gap:6px;padding:6px 11px;border-radius:99px;
  background:rgba(255,255,255,.95);color:#121216;font-size:.76rem;font-weight:700;
}
.pill small{font-weight:600;color:#6B6B75;font-size:.66rem}
.hero-rank{margin-left:8px;font-size:.74rem;color:rgba(255,255,255,.65);font-weight:500}
.hero-title{
  font-size:1.75rem;font-weight:700;line-height:1.15;letter-spacing:-.02em;margin:12px 0 8px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}
.hero-over{font-size:.8rem;line-height:1.5;color:rgba(255,255,255,.72);max-width:520px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.hero-bar{
  margin-left:-12px;
  display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding:12px 16px;border-radius:14px;
  background:rgba(30,31,38,.6);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,.06);
}
.hero-stat{font-size:.7rem;color:rgba(255,255,255,.55)}
.hero-stat b{display:block;font-size:.88rem;color:#fff;font-weight:600;margin-top:1px}
.hero-nav{margin-left:auto;display:flex;gap:6px}
.round{
  width:34px;height:34px;border-radius:10px;border:1px solid rgba(255,255,255,.12);
  background:rgba(255,255,255,.06);display:grid;place-items:center;cursor:pointer;color:#fff;
}
.round:hover{background:rgba(255,255,255,.14)}
.round svg{width:16px;height:16px}
.dots{display:flex;justify-content:center;gap:6px;margin:12px 0 4px}
.dots button{width:8px;height:4px;border-radius:4px;border:none;background:var(--line-2);cursor:pointer;transition:all .25s}
.dots button.on{width:26px;background:var(--accent)}

/* rows of cards */
.section-head{display:flex;align-items:baseline;gap:12px;margin:22px 0 12px}
.section-title{font-size:1.08rem;font-weight:600;letter-spacing:-.01em;white-space:nowrap}
.section-sub{font-size:.76rem;color:var(--muted)}
.ghost{
  margin-left:auto;padding:6px 12px;border-radius:99px;border:1px solid var(--line-2);background:none;
  font-size:.72rem;color:var(--accent-2);cursor:pointer;white-space:nowrap;
}
.ghost:hover{background:var(--accent-soft);border-color:transparent}
.row{
  display:grid;grid-auto-flow:column;grid-auto-columns:minmax(132px,1fr);gap:10px;
  overflow-x:auto;padding-bottom:6px;scroll-snap-type:x mandatory;scrollbar-width:thin;
}
.card{
  position:relative;aspect-ratio:2/3;border-radius:var(--r-md);overflow:hidden;background:#1E1F26;color:#fff;
  scroll-snap-align:start;cursor:default;
}
.card img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transition:transform .5s}
.card:hover img{transform:scale(1.05)}
.card::after{content:'';position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,0) 35%,rgba(10,10,14,.92) 100%)}
.card .pill{position:absolute;top:10px;left:10px;z-index:1;padding:5px 9px;font-size:.72rem}
.card-body{position:absolute;left:12px;right:12px;bottom:12px;z-index:1}
.card-title{font-size:.8rem;font-weight:600;line-height:1.25;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-meta{font-size:.7rem;color:rgba(255,255,255,.65);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-meter{display:flex;align-items:center;gap:8px;margin-top:9px;font-size:.64rem;color:rgba(255,255,255,.6)}
.card-meter span{flex:1;height:3px;border-radius:3px;background:rgba(255,255,255,.18);overflow:hidden}
.card-meter i{display:block;height:100%;background:rgba(255,255,255,.8)}

.list-row{display:grid;grid-template-columns:20px minmax(0,1fr) auto;gap:10px;align-items:center;padding:8px 0;font-size:.8rem}
.list-row + .list-row{border-top:1px solid var(--line)}
.list-row .pos{font-size:.72rem;color:var(--subtle);text-align:right}
.list-row b{display:block;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.list-row small{display:block;font-size:.7rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.list-row .val{text-align:right;font-weight:600;white-space:nowrap}
.list-row .val small{font-weight:400}

/* panels inside main */
.panels{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.box{background:var(--card);border-radius:var(--r-md);padding:18px 18px 16px;min-width:0}
.box.wide{grid-column:1 / -1}
.box-head{margin-bottom:14px}
.box-title{font-size:.98rem;font-weight:600}
.box-sub{font-size:.74rem;color:var(--muted);margin-top:4px;line-height:1.45}
.chart-box{position:relative;height:230px}
.chart-box.tall{height:270px}

.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:12px}
.kpi{background:var(--card);border-radius:var(--r-md);padding:16px 16px 14px;min-width:0}
.kpi-label{font-size:.72rem;color:var(--muted)}
.kpi-val{font-size:1.55rem;font-weight:700;letter-spacing:-.02em;margin-top:6px}
.kpi-cap{font-size:.7rem;color:var(--subtle);margin-top:3px}
.kpi-bar{height:4px;border-radius:4px;background:var(--line-2);margin-top:10px;overflow:hidden}
.kpi-bar i{display:block;height:100%;background:var(--accent);border-radius:4px}

.rank-row{
  display:grid;grid-template-columns:100px minmax(0,1fr) 40px 36px;gap:12px;align-items:center;
  width:100%;padding:7px 8px;margin:0 -8px;border-radius:9px;border:none;background:none;cursor:pointer;
  font-size:.8rem;text-align:left;width:calc(100% + 16px);
}
.rank-row:hover{background:var(--hover)}
.rank-row.sel{background:var(--accent-soft)}
.rank-row .name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rank-row .bar{height:6px;border-radius:6px;background:var(--line-2);overflow:hidden}
.rank-row .bar i{display:block;height:100%;border-radius:6px;background:var(--neutral)}
.rank-row.sel .bar i{background:var(--accent)}
.rank-row .v{font-weight:600;text-align:right}
.rank-row .n{color:var(--muted);text-align:right;font-size:.74rem}

.corr-row{display:grid;grid-template-columns:96px minmax(0,1fr) 46px;gap:12px;align-items:center;padding:9px 0;font-size:.8rem}
.corr-row + .corr-row{border-top:1px solid var(--line)}
.corr-row small{display:block;font-size:.68rem;color:var(--subtle)}
.corr-track{position:relative;height:8px;background:var(--card-2);border-radius:8px}
.corr-track::before{content:'';position:absolute;left:50%;top:-4px;bottom:-4px;width:1px;background:var(--line-2)}
.corr-track i{position:absolute;top:0;bottom:0;border-radius:8px}
.corr-row .v{font-weight:600;text-align:right}
.corr-scale{display:grid;grid-template-columns:96px minmax(0,1fr) 46px;gap:12px;font-size:.66rem;color:var(--subtle);margin-top:4px}
.corr-scale div{display:flex;justify-content:space-between}

/* table */
.table-scroll{overflow-x:auto}
table{width:100%;border-collapse:separate;border-spacing:0 6px;font-size:.8rem}
th{
  text-align:left;padding:4px 10px;font-size:.72rem;font-weight:500;color:var(--muted);
  white-space:nowrap;user-select:none;
}
th[data-col]{cursor:pointer}
th[data-col]:hover{color:var(--text)}
th .arrow{display:inline-block;margin-left:4px;font-size:.6rem;color:var(--accent)}
th.sort-asc .arrow::after{content:'▲'}
th.sort-desc .arrow::after{content:'▼'}
td{padding:8px 10px;background:var(--card);white-space:nowrap;vertical-align:middle}
td:first-child{border-radius:12px 0 0 12px}
td:last-child{border-radius:0 12px 12px 0}
tbody tr:hover td{background:var(--card-2)}
.r{text-align:right}
.film{display:flex;align-items:center;gap:12px;max-width:250px}
.film img{width:34px;height:50px;border-radius:7px;object-fit:cover;background:var(--card-2);flex-shrink:0}
.film > div{min-width:0}
.film b{display:block;font-weight:600;overflow:hidden;text-overflow:ellipsis}
.film span{display:block;font-size:.72rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis}
.tag{display:inline-block;font-size:.66rem;padding:2px 7px;border-radius:99px;border:1px solid var(--line-2);color:var(--muted);margin-right:4px}
.score{display:inline-flex;align-items:center;gap:5px;font-weight:600}
.meta-badge{display:inline-block;min-width:32px;text-align:center;padding:3px 7px;border-radius:7px;font-weight:600;font-size:.74rem}
.dash{color:var(--subtle)}
.table-foot{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-top:10px;font-size:.76rem;color:var(--muted)}
.select{
  padding:6px 26px 6px 10px;border:1px solid var(--line-2);border-radius:9px;background:var(--card);
  font-size:.78rem;cursor:pointer;outline:none;appearance:none;-webkit-appearance:none;color:var(--text);
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%238D8E99' stroke-width='2.4'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 9px center;
}
.pager{display:flex;align-items:center;gap:8px}
.pager .cur{min-width:30px;padding:5px 8px;border-radius:8px;background:var(--card);text-align:center;color:var(--text);font-weight:600}
.pager .round{width:30px;height:30px;border-color:var(--line-2);background:none;color:var(--text)}
.pager .round:hover{background:var(--hover)}
.pager .round:disabled{opacity:.35;cursor:default}
.empty{text-align:center;padding:32px 10px;color:var(--subtle);font-size:.8rem}

/* right rail */
.rail{padding:18px 16px 20px;display:flex;flex-direction:column;gap:24px;align-self:start;position:relative;z-index:5}
.rail-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.rail-title{font-size:.98rem;font-weight:600}
.link{border:none;background:none;cursor:pointer;font-size:.74rem;color:var(--accent-2)}
.link:hover{text-decoration:underline}
.dd{position:relative}
.dd-btn{
  display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;
  padding:10px 12px;border-radius:12px;border:1px solid var(--line-2);background:var(--panel);
  font-size:.84rem;font-weight:500;cursor:pointer;text-align:left;
}
.dd-btn:hover,.dd-btn[aria-expanded="true"]{border-color:var(--subtle)}
.dd-btn.on{border-color:var(--accent);color:var(--accent-2)}
.dd-btn svg{width:16px;height:16px;color:var(--muted);transition:transform .15s}
.dd-btn[aria-expanded="true"] svg{transform:rotate(180deg)}
.dd-menu{
  position:absolute;left:0;right:0;top:calc(100% + 6px);z-index:20;
  max-height:300px;overflow-y:auto;padding:6px;border-radius:12px;
  background:var(--panel);border:1px solid var(--line-2);
  box-shadow:0 16px 40px -12px rgba(0,0,0,.28);
}
.dd-opt{
  display:grid;grid-template-columns:minmax(0,1fr) auto 16px;gap:10px;align-items:center;width:100%;
  padding:8px 10px;border:none;border-radius:8px;background:none;cursor:pointer;font-size:.82rem;text-align:left;
}
.dd-opt:hover,.dd-opt:focus-visible{background:var(--hover);outline:none}
.dd-opt.on{color:var(--accent-2);font-weight:600}
.dd-opt small{font-size:.72rem;color:var(--muted);font-weight:400}
.dd-opt svg{width:14px;height:14px;visibility:hidden}
.dd-opt.on svg{visibility:visible}
.dd-opt:disabled{color:var(--subtle);cursor:default;background:none}

.dec-bars{display:flex;align-items:flex-end;gap:5px;height:84px}
.dec-bars button{
  flex:1;border:none;cursor:pointer;border-radius:6px 6px 3px 3px;background:var(--line-2);min-height:4px;
  transition:background .15s;position:relative;
}
.dec-bars button:hover{background:var(--subtle)}
.dec-bars button.on{background:var(--accent)}
.dec-labels{display:flex;gap:5px;margin-top:7px}
.dec-labels span{flex:1;text-align:center;font-size:.6rem;color:var(--subtle)}
.dec-labels span.on{color:var(--accent-2);font-weight:600}

.person{display:grid;grid-template-columns:36px minmax(0,1fr) auto;gap:11px;align-items:center;padding:7px 0}
.avatar{
  width:36px;height:36px;border-radius:50%;display:grid;place-items:center;font-size:.72rem;font-weight:600;
  background:var(--card-2);color:var(--muted);
}
.person b{display:block;font-size:.8rem;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.person small{display:block;font-size:.7rem;color:var(--muted)}
.person .score{font-size:.8rem}

.mini-kpis{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.mini{background:var(--card);border-radius:12px;padding:11px 12px}
.mini span{display:block;font-size:.66rem;color:var(--muted)}
.mini b{display:block;font-size:1.05rem;font-weight:700;margin-top:3px}

::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--line-2);border-radius:8px}

.theme-btn{
  width:34px;height:34px;border-radius:10px;border:1px solid var(--line-2);background:var(--panel);
  display:grid;place-items:center;cursor:pointer;color:var(--muted);flex-shrink:0;
}
.theme-btn:hover{color:var(--text)}
.theme-btn svg{width:16px;height:16px}
.theme-btn .moon{display:none}
:root[data-theme="dark"] .theme-btn .sun{display:none}
:root[data-theme="dark"] .theme-btn .moon{display:block}

@media(max-width:1280px){
  .shell{grid-template-columns:200px minmax(0,1fr)}
  .rail{grid-column:2;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px 28px}
}
@media(max-width:860px){
  .shell{grid-template-columns:minmax(0,1fr);padding:10px;gap:10px}
  .side{position:static;height:auto;flex-direction:row;align-items:center;padding:8px 10px;gap:2px}
  .brand{padding:0 6px 0 0}
  .brand > div:last-child,.nav-label,.side-foot{display:none}
  .nav-item{width:auto;padding:9px 10px;gap:7px;white-space:nowrap;font-size:.82rem}
  .nav-item svg{width:16px;height:16px}
  .nav-item.active::after{left:10px;right:10px;top:auto;bottom:2px;width:auto;height:2px}
  .rail{grid-column:1;grid-template-columns:minmax(0,1fr)}
  .main{padding:14px 12px 18px}
  .hero{padding:20px 20px 12px}
  .hero-poster{display:none}
  .hero-title{font-size:1.5rem}
  .hero-bar{margin:0 -8px;gap:12px}
  .hero-nav{display:none}
  .section-head{flex-wrap:wrap;row-gap:4px}
  .panels,.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .panels .box{grid-column:1 / -1}
  .search{max-width:none;flex-basis:100%}
  .rank-row{grid-template-columns:84px minmax(0,1fr) 36px 30px;gap:8px}
}
</style>
</head>
<body>

<div class="shell">

  <!-- ═══════════════════ SIDEBAR ═══════════════════ -->
  <aside class="side">
    <div class="brand">
      <div class="brand-mark">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z"/></svg>
      </div>
      <div><b>Top 1000</b><small>IMDb film analysis</small></div>
    </div>
    <div class="nav-label">Menu</div>
    <button class="nav-item active" data-view="home">
      <svg class="i" viewBox="0 0 24 24"><path d="M4 11l8-7 8 7v8a1 1 0 0 1-1 1h-4v-6H9v6H5a1 1 0 0 1-1-1z"/></svg>Home
    </button>
    <button class="nav-item" data-view="insights">
      <svg class="i" viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>Insights
    </button>
    <button class="nav-item" data-view="titles">
      <svg class="i" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4"/></svg>All titles
    </button>
    <div class="side-foot">
      Source: IMDb Dataset of Top 1000 Movies and TV Shows (Kaggle).<br>
      Box office is unadjusted USD and missing for ~17% of titles.
    </div>
  </aside>

  <!-- ═══════════════════ MAIN ═══════════════════ -->
  <main class="main">
    <div class="topbar">
      <label class="search">
        <svg class="i" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/></svg>
        <input id="search" type="text" placeholder="Search title, director or cast…">
      </label>
      <div class="active-filters" id="active-filters"></div>
      <span class="count">Showing <b id="sub-count">—</b> of <b id="sub-total">—</b></span>
      <button class="theme-btn" onclick="toggleTheme()" aria-label="Toggle light/dark theme" title="Toggle theme">
        <svg class="i sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg class="i moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>
      </button>
    </div>

    <!-- HOME -->
    <section class="view active" id="view-home">
      <div class="hero" id="hero">
        <div class="hero-bg" id="hero-bg"></div>
        <div class="hero-poster" id="hero-poster"></div>
        <div class="hero-body">
          <span class="pill"><svg class="star" viewBox="0 0 24 24"><path d="M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z"/></svg><span id="hero-rating"></span><small>/10 IMDb</small></span>
          <span class="hero-rank" id="hero-rank"></span>
          <div class="hero-title" id="hero-title"></div>
          <div class="hero-over" id="hero-over"></div>
        </div>
        <div class="hero-bar" id="hero-bar"></div>
      </div>
      <div class="dots" id="dots"></div>

      <div class="section-head">
        <span class="section-title">Highest rated</span>
        <span class="section-sub">Ranks 6–15, after the spotlight</span>
        <button class="ghost" onclick="goTo('titles')">Explore all</button>
      </div>
      <div class="row" id="row-top"></div>

      <div class="panels" style="margin-top:22px">
        <div class="box">
          <div class="box-head">
            <div class="box-title">Titles by decade</div>
            <div class="box-sub" id="decade-insight"></div>
          </div>
          <div class="chart-box"><canvas id="decadeChart"></canvas></div>
        </div>
        <div class="box">
          <div class="box-head">
            <div class="box-title">Critics vs. audience</div>
            <div class="box-sub" id="scatter-insight"></div>
          </div>
          <div class="chart-box"><canvas id="scatterChart"></canvas></div>
        </div>
        <div class="box">
          <div class="box-head">
            <div class="box-title">Hidden gems</div>
            <div class="box-sub">Rated 8.0+ with fewer than 100K votes</div>
          </div>
          <div id="list-gems"></div>
        </div>
        <div class="box">
          <div class="box-head">
            <div class="box-title">Box office giants</div>
            <div class="box-sub">Highest unadjusted gross</div>
          </div>
          <div id="list-gross"></div>
        </div>
      </div>
    </section>

    <!-- INSIGHTS -->
    <section class="view" id="view-insights">
      <div class="panels">
        <div class="box wide">
          <div class="box-head">
            <div class="box-title">What moves the rating?</div>
            <div class="box-sub">Pearson correlation with IMDb rating</div>
          </div>
          <div id="corr-list"></div>
          <div class="corr-scale"><span></span><div><span>−1</span><span>0</span><span>+1</span></div><span></span></div>
        </div>
        <div class="box wide">
          <div class="box-head">
            <div class="box-title">Best-rated genres</div>
            <div class="box-sub" id="genre-insight"></div>
          </div>
          <div id="genre-list"></div>
        </div>
      </div>
    </section>

    <!-- TITLES -->
    <section class="view" id="view-titles">
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th data-col="t">Title<span class="arrow"></span></th>
              <th data-col="y">Year<span class="arrow"></span></th>
              <th>Genre</th>
              <th data-col="r" class="r">IMDb<span class="arrow"></span></th>
              <th data-col="m" class="r">Metascore<span class="arrow"></span></th>
              <th data-col="v" class="r">Votes<span class="arrow"></span></th>
              <th data-col="rt" class="r">Runtime<span class="arrow"></span></th>
              <th data-col="gr" class="r">Gross<span class="arrow"></span></th>
            </tr>
          </thead>
          <tbody id="table-body"></tbody>
        </table>
      </div>
      <div class="table-foot">
        <label style="display:flex;align-items:center;gap:8px">Show
          <select class="select" id="page-size"><option>10</option><option selected>25</option><option>50</option></select>
        </label>
        <div class="pager">
          <button class="round" id="prev" aria-label="Previous page"><svg class="i" viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg></button>
          <span class="cur" id="page-cur">1</span><span>/</span><span id="page-total">1</span>
          <button class="round" id="next" aria-label="Next page"><svg class="i" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>
        </div>
      </div>
    </section>
  </main>

  <!-- ═══════════════════ RIGHT RAIL ═══════════════════ -->
  <aside class="rail">
    <div>
      <div class="rail-head"><span class="rail-title">At a glance</span></div>
      <div class="mini-kpis">
        <div class="mini"><span>Avg. rating</span><b id="m-rating">—</b></div>
        <div class="mini"><span>Avg. Metascore</span><b id="m-meta">—</b></div>
        <div class="mini"><span>Median votes</span><b id="m-votes">—</b></div>
        <div class="mini"><span>Box office</span><b id="m-gross">—</b></div>
      </div>
    </div>

    <div>
      <div class="rail-head">
        <span class="rail-title">Genres</span>
        <button class="link" id="genre-clear" onclick="setFilter('genre','')" hidden>Clear</button>
      </div>
      <div class="dd" id="genre-dd">
        <button class="dd-btn" id="genre-btn" aria-haspopup="listbox" aria-expanded="false">
          <span id="genre-label">All genres</span>
          <svg class="i" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <div class="dd-menu" id="genre-menu" role="listbox" hidden></div>
      </div>
    </div>

    <div>
      <div class="rail-head">
        <span class="rail-title">Decades</span>
        <button class="link" id="decade-clear" onclick="setFilter('decade','')" hidden>Clear</button>
      </div>
      <div class="dec-bars" id="dec-bars"></div>
      <div class="dec-labels" id="dec-labels"></div>
    </div>

    <div>
      <div class="rail-head">
        <span class="rail-title">Top directors</span>
        <span class="section-sub" id="dir-insight"></span>
      </div>
      <div id="dir-list"></div>
    </div>
  </aside>

</div>

<script>
const MOVIES = %DATA_JSON%.movies;

// computed style is live, so v() always returns the current theme's token
var css = getComputedStyle(document.documentElement);
function v(name){ return css.getPropertyValue(name).trim(); }
function isDark(){ return document.documentElement.dataset.theme === "dark"; }
var FONT = {family:"Inter", size:11};
Chart.defaults.locale = "en-US";
var STAR = "<svg class='star' viewBox='0 0 24 24'><path d='M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8 6.6 19.7l1.1-6.1L3.2 9.4l6.1-.8z'/></svg>";
var X_ICON = "<svg class='i' viewBox='0 0 24 24'><path d='M18 6L6 18M6 6l12 12'/></svg>";

function fmt(n, d){ return n.toLocaleString("en-US",{minimumFractionDigits:d||0, maximumFractionDigits:d||0}); }
function compact(n){
  if(n >= 1e9) return "$"+fmt(n/1e9,1)+"B";
  if(n >= 1e6) return "$"+fmt(n/1e6,1)+"M";
  return "$"+fmt(n/1e3,0)+"K";
}
function compactVotes(n){ return n >= 1e6 ? fmt(n/1e6,2)+"M" : fmt(n/1e3,0)+"K"; }
function mean(a){ return a.length ? a.reduce(function(s,x){return s+x;},0)/a.length : NaN; }
function median(a){
  if(!a.length) return NaN;
  var s = a.slice().sort(function(x,y){return x-y;}), m = Math.floor(s.length/2);
  return s.length%2 ? s[m] : (s[m-1]+s[m])/2;
}
function pearson(pairs){
  var n = pairs.length; if(n < 3) return NaN;
  var mx = mean(pairs.map(function(p){return p[0];})), my = mean(pairs.map(function(p){return p[1];}));
  var sxy=0, sxx=0, syy=0;
  pairs.forEach(function(p){ var dx=p[0]-mx, dy=p[1]-my; sxy+=dx*dy; sxx+=dx*dx; syy+=dy*dy; });
  return sxy/Math.sqrt(sxx*syy);
}
function esc(s){ return String(s).replace(/[&<>"']/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
function decadeOf(m){ return m.y === null ? null : Math.floor(m.y/10)*10; }
function img(m, w){ return m.p+"._V1_QL75_UX"+w+"_.jpg"; }
function byRating(a,b){ return b.r-a.r || b.v-a.v; }

// ── filters ──────────────────────────────────────────────────────────────────
var state = {genre:"", decade:"", q:""};
var GENRES  = [...new Set(MOVIES.flatMap(function(m){return m.g;}))]
  .sort(function(a,b){ return countGenre(b)-countGenre(a); });
function countGenre(g){ return MOVIES.filter(function(m){return m.g.indexOf(g)>=0;}).length; }
var DECADES = [...new Set(MOVIES.map(decadeOf).filter(function(d){return d!==null;}))].sort();
document.getElementById("sub-total").textContent = fmt(MOVIES.length);

function setFilter(key, val){
  state[key] = String(val);
  render();
}
function byGenre(m){ return !state.genre || m.g.indexOf(state.genre) >= 0; }
function byDecade(m){ return !state.decade || String(decadeOf(m)) === state.decade; }
function bySearch(m){
  var q = state.q; if(!q) return true;
  return m.t.toLowerCase().includes(q) || m.d.toLowerCase().includes(q) ||
    m.s.some(function(s){ return s.toLowerCase().includes(q); });
}

document.getElementById("search").addEventListener("input", function(e){
  state.q = e.target.value.toLowerCase().trim();
  if(state.q && currentView === "home") goTo("titles");
  render();
});

// ── views ────────────────────────────────────────────────────────────────────
var currentView = "home";
function goTo(view){
  currentView = view;
  document.querySelectorAll(".nav-item").forEach(function(t){ t.classList.toggle("active", t.dataset.view===view); });
  document.querySelectorAll(".view").forEach(function(s){ s.classList.toggle("active", s.id==="view-"+view); });
  history.replaceState(null,"","#"+view);
  if(view === "home"){ decadeChart.resize(); scatterChart.resize(); }
}
document.querySelectorAll(".nav-item").forEach(function(t){ t.addEventListener("click", function(){ goTo(t.dataset.view); }); });

// ── charts ───────────────────────────────────────────────────────────────────
var tooltipStyle = {
  borderWidth:1, padding:10, cornerRadius:10,
  titleFont:{family:"Inter", size:10, weight:"500"}, bodyFont:{family:"Inter", size:12},
  displayColors:false
};
var gridOpts = {};

var decadeChart = new Chart(document.getElementById("decadeChart"),{
  type:"bar",
  data:{labels:DECADES.map(function(d){return "'"+String(d).slice(2);}), datasets:[{data:[], backgroundColor:[], borderRadius:6, maxBarThickness:30, avg:[]}]},
  options:{
    responsive:true, maintainAspectRatio:false,
    onClick:function(e, els){
      if(!els.length) return;
      var d = String(DECADES[els[0].index]);
      setFilter("decade", state.decade === d ? "" : d);
    },
    onHover:function(e, els){ e.native.target.style.cursor = els.length ? "pointer" : "default"; },
    plugins:{
      legend:{display:false},
      tooltip:Object.assign({}, tooltipStyle, {callbacks:{
        title:function(i){ return DECADES[i[0].dataIndex]+"s"; },
        label:function(c){
          var a = c.dataset.avg[c.dataIndex];
          return [fmt(c.raw)+" titles", isNaN(a) ? "" : "Avg. rating "+fmt(a,2)];
        }
      }})
    },
    scales:{
      x:{grid:{display:false}, border:{display:false}, ticks:{font:FONT, maxRotation:0, autoSkip:false}},
      y:{grid:gridOpts, border:{display:false, dash:[3,3]}, ticks:{font:FONT, maxTicksLimit:5, precision:0}}
    }
  }
});

var scatterChart = new Chart(document.getElementById("scatterChart"),{
  type:"scatter",
  data:{datasets:[{data:[], pointRadius:3.5, pointHoverRadius:6, borderWidth:0}]},
  options:{
    responsive:true, maintainAspectRatio:false,
    plugins:{
      legend:{display:false},
      tooltip:Object.assign({}, tooltipStyle, {callbacks:{
        title:function(i){ var m = i[0].raw.m; return m.t+(m.y?" ("+m.y+")":""); },
        label:function(c){ return "IMDb "+fmt(c.raw.y,1)+"  ·  Metascore "+c.raw.x; }
      }})
    },
    scales:{
      x:{min:25, max:100, grid:gridOpts, border:{display:false, dash:[3,3]}, ticks:{font:FONT},
         title:{display:true, text:"Metascore", font:FONT}},
      y:{min:7.5, max:9.5, grid:gridOpts, border:{display:false, dash:[3,3]},
         ticks:{font:FONT, stepSize:.5, callback:function(x){ return fmt(x,1); }},
         title:{display:true, text:"IMDb rating", font:FONT}}
    }
  }
});

function applyChartTheme(){
  var muted = v("--muted");
  gridOpts.color = v("--line");
  [decadeChart, scatterChart].forEach(function(ch){
    Object.assign(ch.options.plugins.tooltip, {
      backgroundColor:v("--tip-bg"), titleColor:muted, bodyColor:v("--text"), borderColor:v("--line-2")
    });
    Object.values(ch.options.scales).forEach(function(s){
      s.ticks.color = muted;
      if(s.title) s.title.color = muted;
    });
  });
  var dots = scatterChart.data.datasets[0];
  dots.backgroundColor = v("--dot");
  dots.pointHoverBackgroundColor = v("--accent");
}
applyChartTheme();

function toggleTheme(){
  var dark = !isDark();
  if(dark) document.documentElement.dataset.theme = "dark";
  else delete document.documentElement.dataset.theme;
  try { localStorage.setItem("imdb-theme", dark ? "dark" : "light"); } catch(e) {}
  applyChartTheme();
  render();
}

// ── render ───────────────────────────────────────────────────────────────────
function render(){
  var rows = MOVIES.filter(function(m){ return byGenre(m) && byDecade(m); });
  document.getElementById("sub-count").textContent = fmt(rows.length);

  renderActiveFilters();
  renderGenreChips();
  renderDecadeBars();
  renderKpis(rows);
  renderDirectors(rows);
  renderHero(rows);
  renderRows(rows);
  renderDecadeChart();
  renderScatter(rows);
  renderGenres();
  renderCorr(rows);
  applyTable();
}

function renderActiveFilters(){
  var html = "";
  if(state.genre)  html += "<button class='fchip' onclick=\"setFilter('genre','')\">"+esc(state.genre)+X_ICON+"</button>";
  if(state.decade) html += "<button class='fchip' onclick=\"setFilter('decade','')\">"+state.decade+"s"+X_ICON+"</button>";
  document.getElementById("active-filters").innerHTML = html;
  document.getElementById("genre-clear").hidden = !state.genre;
  document.getElementById("decade-clear").hidden = !state.decade;
}

// ── genre dropdown ───────────────────────────────────────────────────────────
var ddBtn = document.getElementById("genre-btn"), ddMenu = document.getElementById("genre-menu");
function openGenreMenu(open){
  ddMenu.hidden = !open;
  ddBtn.setAttribute("aria-expanded", open);
  if(open){ var cur = ddMenu.querySelector(".dd-opt.on") || ddMenu.querySelector(".dd-opt"); if(cur) cur.focus(); }
}
ddBtn.addEventListener("click", function(){ openGenreMenu(ddMenu.hidden); });
document.addEventListener("click", function(e){ if(!document.getElementById("genre-dd").contains(e.target)) openGenreMenu(false); });
document.addEventListener("keydown", function(e){
  if(ddMenu.hidden) return;
  if(e.key === "Escape"){ openGenreMenu(false); ddBtn.focus(); }
  if(e.key === "ArrowDown" || e.key === "ArrowUp"){
    var opts = [...ddMenu.querySelectorAll(".dd-opt:not(:disabled)")], i = opts.indexOf(document.activeElement);
    opts[(i + (e.key === "ArrowDown" ? 1 : -1) + opts.length) % opts.length].focus();
    e.preventDefault();
  }
});

function renderGenreChips(){
  // counts respect the decade filter so the menu shows what each choice would return
  var base = MOVIES.filter(byDecade);
  var CHECK = "<svg class='i' viewBox='0 0 24 24'><path d='M5 12l5 5 9-10'/></svg>";
  var opts = [{g:"", label:"All genres", n:base.length}].concat(GENRES.map(function(g){
    return {g:g, label:g, n:base.filter(function(m){return m.g.indexOf(g)>=0;}).length};
  }));
  ddMenu.innerHTML = opts.map(function(o){
    return "<button class='dd-opt"+(o.g===state.genre?" on":"")+"' role='option' aria-selected='"+(o.g===state.genre)+"' data-g='"+esc(o.g)+"'"
      +(o.n || o.g===state.genre ? "" : " disabled")+">"
      +"<span>"+esc(o.label)+"</span><small>"+fmt(o.n)+"</small>"+CHECK+"</button>";
  }).join("");
  ddMenu.querySelectorAll(".dd-opt").forEach(function(b){
    b.addEventListener("click", function(){ openGenreMenu(false); setFilter("genre", b.dataset.g); });
  });
  document.getElementById("genre-label").textContent = state.genre || "All genres";
  ddBtn.classList.toggle("on", !!state.genre);
}

function renderDecadeBars(){
  var base = MOVIES.filter(byGenre);
  var counts = DECADES.map(function(d){ return base.filter(function(m){return decadeOf(m)===d;}).length; });
  var max = Math.max.apply(null, counts.concat([1]));
  var bars = document.getElementById("dec-bars");
  bars.innerHTML = DECADES.map(function(d,i){
    return "<button class='"+(String(d)===state.decade?"on":"")+"' data-d='"+d+"' style='height:"+Math.max(5, counts[i]/max*100)+"%' title='"+d+"s: "+counts[i]+" titles'></button>";
  }).join("");
  bars.querySelectorAll("button").forEach(function(b){
    b.addEventListener("click", function(){ setFilter("decade", state.decade===b.dataset.d ? "" : b.dataset.d); });
  });
  document.getElementById("dec-labels").innerHTML = DECADES.map(function(d){
    return "<span class='"+(String(d)===state.decade?"on":"")+"'>'"+String(d).slice(2)+"</span>";
  }).join("");
}

function renderKpis(rows){
  var metas = rows.filter(function(m){return m.m!==null;}).map(function(m){return m.m;});
  var gross = rows.filter(function(m){return m.gr!==null;});
  document.getElementById("m-rating").textContent = rows.length ? fmt(mean(rows.map(function(m){return m.r;})),2) : "—";
  document.getElementById("m-meta").textContent   = metas.length ? fmt(mean(metas),1) : "—";
  document.getElementById("m-votes").textContent  = rows.length ? compactVotes(median(rows.map(function(m){return m.v;}))) : "—";
  document.getElementById("m-gross").textContent  = gross.length ? compact(gross.reduce(function(s,m){return s+m.gr;},0)) : "—";
}

function renderDirectors(rows){
  var minN = rows.length >= 500 ? 5 : 2;
  var by = {};
  rows.forEach(function(m){ (by[m.d] = by[m.d] || []).push(m.r); });
  var list = Object.keys(by).map(function(d){ return {d:d, n:by[d].length, avg:mean(by[d])}; })
    .filter(function(s){return s.n >= minN;})
    .sort(function(a,b){ return b.avg-a.avg || b.n-a.n; }).slice(0,6);
  document.getElementById("dir-insight").textContent = "min. "+minN+" films";
  document.getElementById("dir-list").innerHTML = list.length ? list.map(function(s,i){
    var ini = s.d.split(" ").map(function(w){return w[0];}).join("").slice(0,2);
    return "<div class='person'><span class='avatar'>"+esc(ini)+"</span>"
      +"<div style='min-width:0'><b>"+esc(s.d)+"</b><small>"+s.n+" films in selection</small></div>"
      +"<span class='score'>"+STAR+fmt(s.avg,2)+"</span></div>";
  }).join("") : "<div class='empty'>No director reaches the minimum</div>";
}

// ── hero carousel ────────────────────────────────────────────────────────────
var heroList = [], heroIdx = 0;
function renderHero(rows){
  heroList = rows.slice().sort(byRating).slice(0,5);
  heroIdx = 0;
  showHero();
}
function stepHero(d){ heroIdx = (heroIdx + d + heroList.length) % heroList.length; showHero(); }
function showHero(){
  var hero = document.getElementById("hero");
  if(!heroList.length){
    hero.style.visibility = "hidden"; document.getElementById("dots").innerHTML = ""; return;
  }
  hero.style.visibility = "";
  var m = heroList[heroIdx];
  document.getElementById("hero-bg").style.backgroundImage = "url('"+img(m,300)+"')";
  document.getElementById("hero-poster").style.backgroundImage = "url('"+img(m,500)+"')";
  document.getElementById("hero-rating").textContent = fmt(m.r,1);
  document.getElementById("hero-rank").textContent = "#"+(heroIdx+1)+" in selection";
  document.getElementById("hero-title").textContent = m.t;
  // warm the cache for the next slide so the swap doesn't flash empty
  var next = heroList[(heroIdx+1) % heroList.length];
  [300,500].forEach(function(w){ new Image().src = img(next,w); });
  document.getElementById("hero-over").textContent = m.o;
  var stats = [
    ["Year", m.y || "—"],
    ["Genre", m.g.join(", ")],
    ["Director", m.d],
    ["Metascore", m.m !== null ? m.m : "—"],
    ["Votes", compactVotes(m.v)],
    ["Gross", m.gr !== null ? compact(m.gr) : "—"]
  ];
  document.getElementById("hero-bar").innerHTML = stats.map(function(s){
    return "<div class='hero-stat'>"+s[0]+"<b>"+esc(s[1])+"</b></div>";
  }).join("")
    +"<div class='hero-nav'><button class='round' onclick='stepHero(-1)' aria-label='Previous'><svg class='i' viewBox='0 0 24 24'><path d='M15 6l-6 6 6 6'/></svg></button>"
    +"<button class='round' onclick='stepHero(1)' aria-label='Next'><svg class='i' viewBox='0 0 24 24'><path d='M9 6l6 6-6 6'/></svg></button></div>";
  document.getElementById("dots").innerHTML = heroList.map(function(_,i){
    return "<button class='"+(i===heroIdx?"on":"")+"' onclick='heroIdx="+i+";showHero()' aria-label='Show title "+(i+1)+"'></button>";
  }).join("");
}

// ── poster rows ──────────────────────────────────────────────────────────────
function card(m, badge){
  var meter = m.m !== null
    ? "<div class='card-meter'>Meta<span><i style='width:"+m.m+"%'></i></span>"+m.m+"</div>"
    : "<div class='card-meter'>No Metascore</div>";
  return "<div class='card' title='"+esc(m.t)+"'>"
    +"<img loading='lazy' src='"+img(m,300)+"' alt='' onerror=\"this.style.display='none'\">"
    +"<span class='pill'>"+badge+"</span>"
    +"<div class='card-body'><div class='card-title'>"+esc(m.t)+"</div>"
    +"<div class='card-meta'>"+esc(m.g.slice(0,2).join(", "))+(m.y ? " · "+m.y : "")+"</div>"+meter+"</div></div>";
}
function fillRow(id, list, badgeFn, emptyMsg){
  document.getElementById(id).innerHTML = list.length
    ? list.map(function(m){ return card(m, badgeFn(m)); }).join("")
    : "<div class='empty'>"+emptyMsg+"</div>";
}
function fillList(id, list, valFn, emptyMsg){
  document.getElementById(id).innerHTML = list.length ? list.map(function(m,i){
    return "<div class='list-row'><span class='pos'>"+(i+1)+"</span>"
      +"<div style='min-width:0'><b title='"+esc(m.t)+"'>"+esc(m.t)+"</b><small>"+(m.y||"")+" · "+esc(m.d)+"</small></div>"
      +"<span class='val'>"+valFn(m)+"</span></div>";
  }).join("") : "<div class='empty'>"+emptyMsg+"</div>";
}
function renderRows(rows){
  fillRow("row-top", rows.slice().sort(byRating).slice(5,15), function(m){ return STAR+fmt(m.r,1); }, "No titles in this selection");
  fillList("list-gems", rows.filter(function(m){return m.r >= 8 && m.v < 100000;}).sort(byRating).slice(0,6),
    function(m){ return "<span class='score'>"+STAR+fmt(m.r,1)+"</span><small>"+compactVotes(m.v)+" votes</small>"; },
    "No hidden gems in this selection");
  fillList("list-gross", rows.filter(function(m){return m.gr !== null;}).sort(function(a,b){return b.gr-a.gr;}).slice(0,6),
    function(m){ return compact(m.gr)+"<small>"+STAR.replace("class='star'","class='star' style='width:10px;height:10px'")+" "+fmt(m.r,1)+"</small>"; },
    "No box-office data in this selection");
}

// ── insights ─────────────────────────────────────────────────────────────────
function renderDecadeChart(){
  var base = MOVIES.filter(byGenre);
  var groups = DECADES.map(function(d){ return base.filter(function(m){return decadeOf(m)===d;}); });
  var ds = decadeChart.data.datasets[0];
  ds.data = groups.map(function(a){return a.length;});
  ds.avg  = groups.map(function(a){return mean(a.map(function(m){return m.r;}));});
  ds.backgroundColor = DECADES.map(function(d){
    if(!state.decade) return v("--neutral");
    return String(d)===state.decade ? v("--accent") : v("--line-2");
  });
  decadeChart.update();

  var peak = ds.data.indexOf(Math.max.apply(null, ds.data));
  var recent = ds.data.slice(-3).reduce(function(s,x){return s+x;},0);
  document.getElementById("decade-insight").textContent = base.length
    ? "The "+DECADES[peak]+"s lead with "+fmt(ds.data[peak])+" titles; "+fmt(recent/base.length*100)+"% are from 2000 onwards · click a bar to filter"
    : "No titles for this selection";
}

function renderScatter(rows){
  var pts = rows.filter(function(m){return m.m!==null;}).map(function(m){ return {x:m.m, y:m.r, m:m}; });
  scatterChart.data.datasets[0].data = pts;
  scatterChart.update();
  var r = pearson(pts.map(function(p){return [p.x,p.y];}));
  var verdict = Math.abs(r) < 0.2 ? "critics and audiences barely agree"
              : Math.abs(r) < 0.5 ? "critics and audiences only partially agree"
              : "critics and audiences largely agree";
  document.getElementById("scatter-insight").textContent = isNaN(r)
    ? "Not enough titles with a Metascore"
    : "r = "+fmt(r,2)+" across "+fmt(pts.length)+" titles — "+verdict+(pts.length < 30 ? " (small sample)" : "");
}

function renderGenres(){
  var base = MOVIES.filter(byDecade);
  var minN = state.decade ? 5 : 20;
  var stats = GENRES.map(function(g){
    var a = base.filter(function(m){return m.g.indexOf(g)>=0;});
    return {g:g, n:a.length, avg:mean(a.map(function(m){return m.r;}))};
  }).filter(function(s){return s.n >= minN;}).sort(function(a,b){return b.avg-a.avg;}).slice(0,10);

  var spread = stats.length > 1 ? stats[0].avg - stats[stats.length-1].avg : 0;
  document.getElementById("genre-insight").textContent =
    (stats.length > 1 ? "Top 10 sit within "+fmt(spread,2)+" points of each other — genre alone explains little · " : "")
    +"min. "+minN+" titles"+(state.decade ? " in the "+state.decade+"s" : "")+" · click to filter";
  var lo = 7.6, hi = 8.4;
  var el = document.getElementById("genre-list");
  el.innerHTML = stats.length ? stats.map(function(s){
    var w = Math.max(4, Math.min(100, (s.avg-lo)/(hi-lo)*100));
    return "<button class='rank-row"+(s.g===state.genre?" sel":"")+"' data-g='"+esc(s.g)+"'>"
      +"<span class='name'>"+esc(s.g)+"</span>"
      +"<span class='bar'><i style='width:"+w+"%'></i></span>"
      +"<span class='v'>"+fmt(s.avg,2)+"</span>"
      +"<span class='n'>"+s.n+"</span></button>";
  }).join("") : "<div class='empty'>No genre reaches the minimum sample</div>";
  el.querySelectorAll(".rank-row").forEach(function(b){
    b.addEventListener("click", function(){ setFilter("genre", state.genre===b.dataset.g ? "" : b.dataset.g); });
  });
}

function renderCorr(rows){
  var vars = [
    {k:"v",  label:"Votes"},
    {k:"m",  label:"Metascore"},
    {k:"rt", label:"Runtime"},
    {k:"gr", label:"Box office"},
    {k:"y",  label:"Release year"}
  ];
  document.getElementById("corr-list").innerHTML = vars.map(function(x){
    var pairs = rows.filter(function(m){return m[x.k]!==null;}).map(function(m){return [m[x.k], m.r];});
    var r = pearson(pairs);
    var bar = "";
    if(!isNaN(r)){
      bar = "<i style='"+(r>=0 ? "left:50%" : "right:50%")+";width:"+(Math.abs(r)*50)+"%;background:"+(r>=0 ? v("--pos") : v("--neg"))+"'></i>";
    }
    return "<div class='corr-row'><span>"+x.label+"<small>n = "+fmt(pairs.length)+"</small></span>"
      +"<span class='corr-track'>"+bar+"</span>"
      +"<span class='v'>"+(isNaN(r) ? "—" : (r>0?"+":r<0?"−":"")+fmt(Math.abs(r),2))+"</span></div>";
  }).join("");
}

// ── table ────────────────────────────────────────────────────────────────────
var filtered = [], sortCol = "r", sortDir = -1, currentPage = 1;

document.getElementById("page-size").addEventListener("change", function(){ currentPage=1; renderTable(); });
document.getElementById("prev").addEventListener("click", function(){ currentPage--; renderTable(); });
document.getElementById("next").addEventListener("click", function(){ currentPage++; renderTable(); });
document.querySelectorAll("th[data-col]").forEach(function(th){
  th.addEventListener("click", function(){
    var col = th.dataset.col;
    if(sortCol === col) sortDir *= -1;
    else { sortCol = col; sortDir = col === "t" ? 1 : -1; }
    document.querySelectorAll("th[data-col]").forEach(function(h){
      h.classList.remove("sort-asc","sort-desc");
      if(h.dataset.col === sortCol) h.classList.add(sortDir===1 ? "sort-asc" : "sort-desc");
    });
    applySort(); renderTable();
  });
});

function applyTable(){
  filtered = MOVIES.filter(function(m){ return byGenre(m) && byDecade(m) && bySearch(m); });
  applySort();
  currentPage = 1;
  renderTable();
}

function applySort(){
  filtered.sort(function(a,b){
    var av = a[sortCol], bv = b[sortCol];
    if(av === null && bv === null) return 0;
    if(av === null) return 1;   // missing values always last
    if(bv === null) return -1;
    if(typeof av === "string") return av.localeCompare(bv)*sortDir;
    return (av-bv)*sortDir || (b.v-a.v);
  });
}

function metaBadge(x){
  if(x === null) return "<span class='dash'>—</span>";
  var c = isDark()
    ? (x >= 80 ? ["rgba(31,175,85,.16)","#5FD68B"] : x >= 60 ? ["rgba(255,176,61,.16)","#FFC46B"] : ["rgba(240,100,127,.16)","#F58CA0"])
    : (x >= 80 ? ["#E3F4EA","#17803F"] : x >= 60 ? ["#FDF3DC","#9A6A00"] : ["#FDECEF","#B4233F"]);
  return "<span class='meta-badge' style='background:"+c[0]+";color:"+c[1]+"'>"+x+"</span>";
}

function renderTable(){
  var size = +document.getElementById("page-size").value;
  var total = filtered.length;
  var pages = Math.max(1, Math.ceil(total/size));
  currentPage = Math.min(Math.max(1,currentPage), pages);
  var page = filtered.slice((currentPage-1)*size, currentPage*size);

  document.getElementById("table-body").innerHTML = page.length ? page.map(function(m){
    return "<tr>"
      +"<td><div class='film'><img loading='lazy' src='"+img(m,100)+"' alt='' onerror=\"this.style.visibility='hidden'\"><div><b title='"+esc(m.t)+"'>"+esc(m.t)+"</b><span>"+esc(m.d)+" · "+esc(m.s.slice(0,2).join(", "))+"</span></div></div></td>"
      +"<td>"+(m.y||"<span class='dash'>—</span>")+"</td>"
      +"<td>"+m.g.slice(0,2).map(function(g){return "<span class='tag'>"+esc(g)+"</span>";}).join("")
        +(m.g.length > 2 ? "<span class='tag' title='"+esc(m.g.slice(2).join(", "))+"'>+"+(m.g.length-2)+"</span>" : "")+"</td>"
      +"<td class='r'><span class='score'>"+STAR+fmt(m.r,1)+"</span></td>"
      +"<td class='r'>"+metaBadge(m.m)+"</td>"
      +"<td class='r' title='"+fmt(m.v)+" votes'>"+compactVotes(m.v)+"</td>"
      +"<td class='r'>"+(m.rt ? m.rt+" min" : "<span class='dash'>—</span>")+"</td>"
      +"<td class='r'>"+(m.gr !== null ? compact(m.gr) : "<span class='dash'>—</span>")+"</td>"
      +"</tr>";
  }).join("") : "<tr><td colspan='8' class='empty'>No titles match</td></tr>";

  document.getElementById("page-cur").textContent = currentPage;
  document.getElementById("page-total").textContent = pages;
  document.getElementById("prev").disabled = currentPage===1;
  document.getElementById("next").disabled = currentPage===pages;
}

document.querySelector("th[data-col='r']").classList.add("sort-desc");
render();
var startView = location.hash.slice(1);
if(["insights","titles"].indexOf(startView) >= 0) goTo(startView);
</script>
</body>
</html>'''

html_out = HTML.replace('%DATA_JSON%', data_json)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html_out)

print("Dashboard written to:", OUT)
print("Size:", round(os.path.getsize(OUT) / 1024, 1), "KB")
print("Titles:", len(movies))

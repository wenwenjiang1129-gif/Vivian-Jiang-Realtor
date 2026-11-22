#!/usr/bin/env python3
"""Build a monthly market report page from a JSON data file.

usage: make_report.py data.json out.html [--mode repo|artifact] [--draft]
"""
import json, sys, math, argparse, os
from html import escape as E

ap = argparse.ArgumentParser()
ap.add_argument('data'); ap.add_argument('out')
ap.add_argument('--mode', default='repo'); ap.add_argument('--archive', default=''); ap.add_argument('--draft', action='store_true')
a = ap.parse_args()
D = json.load(open(a.data))
G, L = D['gvr'], D['liv']
SITE = 'https://www.vivianjiang.ca'


def T(en, zh, tag='span', style=''):
    st = f' style="{style}"' if style else ''
    return f'<{tag}{st} data-zh="{E(zh, quote=True)}">{E(en)}</{tag}>'


def money_class(v):
    return ''


# ---------------------------------------------------------------- gauge (static svg)
COL = ['#6F8CA3', '#D2BD86', '#B96A4F']
MAX = 30.0


def zone(v):
    return 0 if v < 12 else (1 if v <= 20 else 2)


ZN = [("Buyers’ market", "买方市场"), ("Balanced", "供需平衡"), ("Sellers’ market", "卖方市场")]


def pt(r, v):
    th = math.pi * (1 - min(max(v, 0), MAX) / MAX)
    return 200 + r * math.cos(th), 200 - r * math.sin(th)


def arc(v0, v1, ro, ri):
    a_, b_, c_, d_ = pt(ro, v0), pt(ro, v1), pt(ri, v1), pt(ri, v0)
    return (f'M{a_[0]:.2f} {a_[1]:.2f} A{ro} {ro} 0 0 1 {b_[0]:.2f} {b_[1]:.2f} '
            f'L{c_[0]:.2f} {c_[1]:.2f} A{ri} {ri} 0 0 0 {d_[0]:.2f} {d_[1]:.2f} Z')


def gauge_svg(v):
    z = zone(v)
    p = [f'<svg viewBox="0 0 400 272" role="img" aria-label="Sales-to-active listings ratio gauge: {v:.1f}%, {ZN[z][0]}" style="display:block;width:100%;height:auto">']
    for i, (v0, v1) in enumerate([(0, 12), (12, 20), (20, MAX)]):
        p.append(f'<path d="{arc(v0, v1, 160, 108)}" fill="{COL[i]}" stroke="#FBF9F5" stroke-width="3"/>')
    for val, lab in [(0, '0%'), (12, '12%'), (20, '20%'), (MAX, '30%+')]:
        x, y = pt(178, val)
        y += 16 if val in (0, MAX) else 4
        p.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" font-size="12" fill="#6A6258" font-family="\'Hanken Grotesk\', sans-serif">{lab}</text>')
    tx, ty = pt(118, v)
    p.append(f'<line x1="200" y1="200" x2="{tx:.2f}" y2="{ty:.2f}" stroke="#1C1A17" stroke-width="3.5" stroke-linecap="round"/>')
    p.append('<circle cx="200" cy="200" r="9" fill="#1C1A17"/>')
    p.append(f'<text x="200" y="246" text-anchor="middle" font-size="40" fill="#1C1A17" font-family="\'Cormorant Garamond\', Georgia, serif" font-weight="500">{v:.1f}%</text>')
    zc = '#8A6A3E' if z == 1 else COL[z]
    p.append(f'<text x="200" y="266" text-anchor="middle" font-size="14" font-weight="600" fill="{zc}" font-family="\'Hanken Grotesk\', sans-serif" data-zh="{ZN[z][1]}">{ZN[z][0]}</text>')
    p.append('</svg>')
    return ''.join(p)


def type_bar(label_en, label_zh, v):
    z = zone(v)
    segs = ''.join(f'<div style="height:10px;background:{COL[k]};width:{w / MAX * 100:.4f}%"></div>' for k, w in enumerate([12, 8, 10]))
    left = min(max(v, 0), MAX) / MAX * 100
    return (f'<div><div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;font-size:15px;padding-bottom:8px">'
            f'<span style="font-weight:600" data-zh="{E(label_zh)}">{E(label_en)}</span>'
            f'<span style="color:#4A443B;font-variant-numeric:tabular-nums"><strong>{v:.1f}%</strong> · <span data-zh="{ZN[z][1]}">{ZN[z][0]}</span></span></div>'
            f'<div style="position:relative;height:10px;display:flex;gap:2px">{segs}'
            f'<div style="position:absolute;top:-4px;width:18px;height:18px;margin-left:-9px;border-radius:50%;background:#1C1A17;border:3px solid #FBF9F5;box-sizing:border-box;left:{left:.2f}%"></div></div></div>')


# ---------------------------------------------------------------- building blocks
EYE = "font-family:'Hanken Grotesk',sans-serif;font-weight:600;font-size:13px;letter-spacing:0.22em;color:#8A6A3E"
H2 = "margin:0;font-family:'Cormorant Garamond',Georgia,serif;font-weight:400;font-size:clamp(36px,4.6vw,60px);line-height:1.02;letter-spacing:-0.01em"
CARD = "flex:1 1 240px;min-width:0;box-sizing:border-box;background:#FBF9F5;border:1px solid #D9D0C2;padding:26px;display:flex;flex-direction:column;gap:6px"
BIG = "font-family:'Cormorant Garamond',Georgia,serif;font-weight:500;font-size:44px;line-height:1.05;font-variant-numeric:tabular-nums"
SUB = "font-size:14px;color:#6A6258"
WRAP = "max-width:1200px;margin:0 auto;box-sizing:border-box;padding:{p};display:flex;flex-direction:column;gap:{g}px"
TH = "text-align:{al};padding:12px 14px;font-size:12px;letter-spacing:0.14em;text-transform:uppercase;color:#6A6258;background:#EAE3D7;border-bottom:1px solid #D9D0C2;font-weight:600;white-space:nowrap"
TD = "text-align:{al};padding:12px 14px;border-bottom:1px solid #E6DECF;font-variant-numeric:tabular-nums;white-space:nowrap"


def section(inner, bg='#F5F1EA', pad='72px 24px', gap=36, sid=''):
    i = f' id="{sid}"' if sid else ''
    return f'<section{i} style="background:{bg}"><div style="{WRAP.format(p=pad, g=gap)}">{inner}</div></section>'


def head(eyebrow, h2=None, intro=None):
    s = f'<div style="display:flex;flex-direction:column;gap:16px;max-width:720px"><div style="{EYE}">{eyebrow}</div>'
    if h2:
        s += f'<h2 style="{H2}">{h2}</h2>'
    if intro:
        s += f'<p style="margin:0;color:#4A443B">{intro}</p>'
    return s + '</div>'


def card(label, value, subs):
    s = f'<div style="{CARD}"><div style="{EYE}">{label}</div><div style="{BIG}">{value}</div>'
    for x in subs:
        s += f'<div style="{SUB}">{x}</div>'
    return s + '</div>'


def table(headers, rows, first_w=''):
    h = ''.join(f'<th style="{TH.format(al="left" if i == 0 else "right")}">{c}</th>' for i, c in enumerate(headers))
    b = ''
    for r in rows:
        tds = ''.join(f'<td style="{TD.format(al="left" if i == 0 else "right")}{";font-weight:600" if (i == 0 or (len(r) and r[0].startswith("<strong"))) else ""}">{c}</td>' for i, c in enumerate(r))
        b += f'<tr>{tds}</tr>'
    return (f'<div style="overflow-x:auto;background:#FBF9F5;border:1px solid #D9D0C2"><table style="border-collapse:collapse;width:100%;font-size:15px;min-width:520px">'
            f'<thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')


def n(x):
    return f'{x:,}'


def dash(x):
    return x if x else '—'


month_en, month_zh = D['month_en'], D['month_zh']
prev_en, prev_zh = D['prev_en'], D['prev_zh']

parts = []

# --- hero
parts.append(section(
    f'<div style="display:flex;flex-direction:column;gap:18px;max-width:760px">'
    f'<div style="{EYE}">{T("MONTHLY MARKET REPORT", "月度市场报告")}</div>'
    f'<h1 style="margin:0;font-family:\'Cormorant Garamond\',Georgia,serif;font-weight:400;font-size:clamp(44px,6vw,84px);line-height:1;letter-spacing:-0.01em">'
    f'{T("Metro Vancouver, " + month_en, "大温哥华，" + month_zh)}</h1>'
    f'<p style="margin:0;color:#4A443B;font-size:19px">{T("Home sales, prices and rents across Metro Vancouver and its main areas, drawn from the Greater Vancouver REALTORS® and liv.rent.", "大温哥华及主要地区的房屋成交、价格与租金概况，数据来自大温哥华地产商会（GVR）和 liv.rent。")}</p>'
    f'</div>', pad='72px 24px 40px', gap=0))

# --- at a glance
glance = head(T('THE MONTH AT A GLANCE', '本月概览'), T('What happened in ' + month_en.split()[0], '本月发生了什么'))
cards = ''.join([
    card(T('HOME SALES', '房屋成交'), G['sales'], [
        T(f"{G['sales_yoy']} vs. {prev_en}", f"较 {prev_zh}{'下降' if G['sales_yoy'].startswith('−') else '上升'} {G['sales_yoy'][1:]}"),
        T(f"{G['sales_vs_10yr']} the 10-year seasonal average", f"比十年季节性平均{'低' if 'below' in G['sales_vs_10yr'] else '高'} {G['sales_vs_10yr'].split()[0]}")]),
    card(T('NEW LISTINGS', '新增房源'), G['new'], [
        T(f"{G['new_yoy']} vs. {prev_en}", f"较 {prev_zh}{'下降' if G['new_yoy'].startswith('−') else '上升'} {G['new_yoy'][1:]}"),
        T(f"{G['new_vs_10yr']} the 10-year seasonal average", f"比十年季节性平均{'低' if 'below' in G['new_vs_10yr'] else '高'} {G['new_vs_10yr'].split()[0]}")]),
    card(T('ACTIVE LISTINGS', '在售房源'), G['active'], [
        T(f"{G['active_yoy']} vs. {prev_en}", f"较 {prev_zh}{'下降' if G['active_yoy'].startswith('−') else '上升'} {G['active_yoy'][1:]}"),
        T(f"{G['active_vs_10yr']} the 10-year seasonal average", f"比十年季节性平均{'低' if 'below' in G['active_vs_10yr'] else '高'} {G['active_vs_10yr'].split()[0]}")]),
    card(T('BENCHMARK PRICE', '基准价格'), G['composite_price'], [
        T(f"{G['composite_yoy']} vs. {prev_en} · {G['composite_mom']} vs. last month", f"较 {prev_zh} {G['composite_yoy']} · 较上月 {G['composite_mom']}"),
        T('MLS® HPI composite, all residential', 'MLS® HPI 综合指数（所有住宅）')]),
])
glance += f'<div style="display:flex;flex-wrap:wrap;gap:24px">{cards}</div>'
parts.append(section(glance, pad='40px 24px 72px'))

# --- gauge
s = G['sal']
bars = ''.join([type_bar('Detached', '独立屋', s['detached']), type_bar('Attached', '联排及半独立住宅', s['attached']), type_bar('Apartments', '公寓', s['apartment'])])
legend = ''.join(
    f'<span style="display:inline-flex;align-items:center;gap:8px"><span style="display:inline-block;width:12px;height:12px;background:{COL[i]}"></span>'
    f'<span data-zh="{zh}">{en}</span><span>·</span><span data-zh="{ZN[i][1]}">{ZN[i][0]}</span></span>'
    for i, (en, zh) in enumerate([('Below 12%', '低于 12%'), ('12–20%', '12–20%'), ('Above 20%', '高于 20%')]))
intro_g = (f"{month_en.split()[0]}’s sales-to-active listings ratio was {s['overall']:.1f}%, in the lower half of the balanced range. "
           f"Detached homes, at {s['detached']:.1f}%, were just under the 12% level usually linked to downward price pressure, "
           f"while attached homes were the firmest at {s['attached']:.1f}%.")
intro_gz = (f"{month_zh.split(' 年 ')[1]}销售与在售房源比率为 {s['overall']:.1f}%，处于供需平衡区间的偏低一侧。"
            f"独立屋为 {s['detached']:.1f}%，略低于通常对应价格下行压力的 12%；联排及半独立住宅最为坚挺，为 {s['attached']:.1f}%。")
X = D.get('text', {})
if 'gauge_intro' in X:
    intro_g, intro_gz = X['gauge_intro']
gauge_panel = (
    f'<div style="background:#FBF9F5;border:1px solid #D9D0C2;padding:36px 32px;display:flex;flex-wrap:wrap;gap:36px 64px;align-items:center">'
    f'<div style="flex:1 1 320px;min-width:0;max-width:460px;display:flex;flex-direction:column;gap:14px">'
    f'<p style="margin:0;color:#4A443B">{T(intro_g, intro_gz)}</p>'
    f'<p style="margin:0;color:#4A443B">{T("When the ratio stays below 12%, prices tend to face downward pressure; above 20%, upward pressure. In between, the market is balanced.", "比率持续低于 12% 时，价格往往面临下行压力；高于 20% 时则面临上行压力；介于两者之间则供需平衡。")}</p>'
    f'<div style="font-size:13px;color:#6A6258">{T("Ratios as published in the Greater Vancouver REALTORS® monthly news release; thresholds are the ones commonly cited by the board. This is a snapshot, not a forecast.", "比率取自大温哥华地产商会（GVR）的月度新闻稿；门槛为该会常用的参考值。此为当月快照，并非预测。")}</div>'
    f'</div>'
    f'<div style="flex:1 1 340px;min-width:0;display:flex;flex-direction:column;gap:28px">'
    f'<div style="display:flex;flex-direction:column;align-items:center;gap:6px"><div style="font-weight:600;font-size:14px">{T("All residential types combined", "所有住宅类型合计")}</div>'
    f'<div style="width:100%;max-width:400px">{gauge_svg(s["overall"])}</div></div>'
    f'<div style="display:flex;flex-direction:column;gap:18px">{bars}</div>'
    f'<div style="display:flex;flex-wrap:wrap;gap:8px 22px;font-size:13px;color:#4A443B">{legend}</div>'
    f'</div></div>')
parts.append(section(head(T('MARKET BALANCE', '市场供需'), T('How balanced is the market?', '市场供需是否平衡？')) + gauge_panel, bg='#EAE3D7'))

# --- prices by type
rows = []
for en, zh, price, yoy, mom, dec in G['types']:
    rows.append([T(en, zh), price, yoy, mom, dec])
sbt = G['sales_by_type']
sbt_en = (f"Sales by type vs. {prev_en}: detached {sbt['detached'][0]} ({sbt['detached'][1]}), attached {sbt['attached'][0]} ({sbt['attached'][1]}), "
          f"apartments {sbt['apartment'][0]} ({sbt['apartment'][1]}).")
sbt_zh = (f"各类物业成交量（较 {prev_zh}）：独立屋 {sbt['detached'][0]}（{sbt['detached'][1]}），联排及半独立住宅 {sbt['attached'][0]}（{sbt['attached'][1]}），"
          f"公寓 {sbt['apartment'][0]}（{sbt['apartment'][1]}）。")
prices = (head(T('PRICES', '价格'), T('Benchmark prices by property type', '各类物业基准价格')) +
          table([T('Property type', '物业类型'), T('Benchmark price', '基准价格'), T('1-year change', '一年变化'), T('1-month change', '一个月变化'), T('10-year change', '十年变化')], rows) +
          f'<div style="font-size:15px;color:#4A443B">{T(sbt_en, sbt_zh)}</div>')
parts.append(section(prices))

# --- areas
price_rows = [[T(en, zh), dash(c), dash(d_), dash(t_), dash(ap_)] for en, zh, c, d_, t_, ap_ in G['price_areas']]
areas = (head(T('BY AREA', '分区概况'), T('Benchmark prices by area', '各区基准价格'),
              T('Benchmark prices are reported for the board’s sub-areas. A dash means the board shows no figure.',
                '基准价格按地产商会的子区统计。“—”表示地产商会未提供数据。')) +
         f'<div style="display:flex;flex-direction:column;gap:12px"><div style="font-weight:600">{T("MLS® HPI benchmark price by area, " + month_en, "各区 MLS® HPI 基准价格，" + month_zh)}</div>' +
         table([T('Area', '地区'), T('All residential', '所有住宅'), T('Detached', '独立屋'), T('Townhouse', '联排'), T('Apartment', '公寓')], price_rows) + '</div>')
parts.append(section(areas, bg='#EAE3D7'))

# --- rentals
lv = L
metro = card(T('METRO VANCOUVER · 1-BED', '大温哥华 · 一居室'), lv['metro_1bed'], [
    T(f"{lv['metro_1bed_yoy']} vs. {prev_en} ({lv['metro_1bed_yoy_amt']})", f"较 {prev_zh} {lv['metro_1bed_yoy']}（{lv['metro_1bed_yoy_amt']}）"),
    T(f"{lv['metro_1bed_mom']} vs. last month · unfurnished", f"较上月 {lv['metro_1bed_mom']} · 不带家具"),
    T(f"Furnished: {lv['metro_1bed_furn']} ({lv['metro_1bed_furn_mom']} vs. last month)", f"带家具：{lv['metro_1bed_furn']}（较上月 {lv['metro_1bed_furn_mom']}）")])
van1 = card(T('VANCOUVER · 1-BED', '温哥华 · 一居室'), lv['van_1bed'], [
    T(f"{lv['van_1bed_yoy']} vs. {prev_en}", f"较 {prev_zh} {lv['van_1bed_yoy']}"), T('Unfurnished', '不带家具')])
van2 = card(T('VANCOUVER · 2-BED', '温哥华 · 两居室'), lv['van_2bed'], [
    T(f"{lv['van_2bed_yoy']} vs. {prev_en} ({lv['van_2bed_prev']})", f"较 {prev_zh} {lv['van_2bed_yoy']}（{lv['van_2bed_prev']}）"), T('Unfurnished', '不带家具')])
psf = card(T('RENT PER SQ. FT.', '每平方英尺租金'), lv['psf_metro'], [
    T('Metro Vancouver average', '大温哥华平均'),
    T(f"Vancouver {lv['psf_van']} · North Vancouver {lv['psf_nv']} · West Vancouver {lv['psf_wv']}", f"温哥华 {lv['psf_van']} · 北温哥华 {lv['psf_nv']} · 西温哥华 {lv['psf_wv']}")])
t3 = lv['top3']
top_en = f"Among the Canadian cities liv.rent tracks, {t3[0][0]} ({t3[0][1]}), {t3[1][0]} ({t3[1][1]}) and {t3[2][0]} ({t3[2][1]}) have the highest one-bedroom asking rents."
top_zh = f"在 liv.rent 追踪的加拿大城市中，一居室挂牌租金最高的是西温哥华（{t3[0][1]}）、北温哥华（{t3[1][1]}）和温哥华（{t3[2][1]}）。"
yr = lv['yoy_range']
yoy_en = f"Year over year, one-bedroom asking rents fell in all nine cities in the report, from {yr[0]} in Vancouver to {yr[1]} in Richmond."
yoy_zh = f"与去年同期相比，报告所列九个城市的一居室挂牌租金全部下降，从温哥华的 {yr[0]} 到列治文的 {yr[1]}。"
mm = lv['mom']
mom_en = (f"Month over month, one-bedroom asking rents rose in West Vancouver ({mm['up'][0][1]}) and Coquitlam ({mm['up'][1][1]}) "
          f"and fell in Richmond ({mm['down'][0][1]}) and Burnaby ({mm['down'][1][1]}).")
mom_zh = (f"与上月相比，西温哥华（{mm['up'][0][1]}）和高贵林（{mm['up'][1][1]}）的一居室挂牌租金上升，"
          f"列治文（{mm['down'][0][1]}）和本拿比（{mm['down'][1][1]}）下降。")
hd = lv['hoods']
hood_en = (f"In Vancouver, the highest one-bedroom asking rent was in {hd['high'][0]} ({hd['high'][1]}) and the lowest in {hd['low'][0]} ({hd['low'][1]}). "
           f"Kitsilano was {hd['kits']} and Downtown {hd['downtown']}.")
hood_zh = (f"在温哥华，一居室挂牌租金最高的是 {hd['high'][0]}（{hd['high'][1]}），最低的是 {hd['low'][0]}（{hd['low'][1]}）；"
           f"基斯兰奴为 {hd['kits']}，市中心为 {hd['downtown']}。")
LI = "padding:14px 0;border-top:1px solid #D9D0C2;color:#4A443B"
if 'rent_notes' in X:
    _notes = X['rent_notes']
else:
    _notes = [(top_en, top_zh), (yoy_en, yoy_zh), (mom_en, mom_zh), (hood_en, hood_zh)]
notes_list = ''.join(f'<div style="{LI}">{T(e, z)}</div>' for e, z in _notes)
rent_note = T('These are asking rents from listings on liv.rent and other sites. They differ from what current tenants pay and from CMHC figures. Luxury listings over $5,000 a month, rooms and shared accommodation are excluded.',
              '以上为 liv.rent 及其他网站上的挂牌租金，与现有租客实际支付的租金以及 CMHC 的数据不同。每月租金超过 5,000 加元的豪华房源、单间出租和合租均不在统计之内。')
rentals = (head(T('RENTALS', '租金'), T('Asking rents, from liv.rent', '租金概况（来源：liv.rent）')) +
           f'<div style="display:flex;flex-wrap:wrap;gap:24px">{metro}{van1}{van2}{psf}</div>' +
           (f'<div style="display:flex;flex-direction:column;border-bottom:1px solid #D9D0C2">{notes_list}</div>' if notes_list else '') +
           (f'<div style="display:flex;flex-direction:column;gap:12px"><div style="font-weight:600">{T("Average unfurnished asking rent by city, " + month_en, "各城市不带家具平均挂牌租金，" + month_zh)}</div>' +
            table([T('City', '城市'), T('1-bed', '一居室'), T('2-bed', '两居室'), T('3-bed', '三居室'), T('1-bed, year over year', '一居室同比')],
                  [[T(e, z), a, b, c, y] for e, z, a, b, c, y in lv['cities']]) +
            f'<div style="font-size:13px;color:#6A6258">{T("Year-over-year change is for unfurnished one-bedrooms, compared with October last year.", "同比变化为不带家具一居室，与去年 10 月相比。")}</div></div>') +
           f'<div style="font-size:13px;color:#6A6258">{rent_note}</div>')
parts.append(section(rentals))

# --- our take (draft copy)
mon = month_en.split()[0]
take = [
    (f"{mon} was quiet on both sides. Sales fell {G['sales_yoy'][1:]} from a year ago and new listings fell {G['new_yoy'][1:]}, so buyers and sellers both held back. "
     f"Active listings are {G['active_yoy'][1:]} below last {mon} but still {G['active_vs_10yr'].split()[0]} above the 10-year seasonal average, so buyers have more choice than in a typical {mon}.",
     f"{month_zh.split(' 年 ')[1]}买卖双方都比较观望。成交量较去年同期下降 {G['sales_yoy'][1:]}，新增房源下降 {G['new_yoy'][1:]}。"
     f"在售房源较去年 10 月减少 {G['active_yoy'][1:]}，但仍比十年季节性平均高 {G['active_vs_10yr'].split()[0]}，因此买家的选择比往年同期更多。"),
    (f"With a sales-to-active ratio of {s['overall']:.1f}%, the market sits at the lower end of balanced. Detached homes are just under the 12% mark, where conditions favour buyers most; attached homes are the firmest at {s['attached']:.1f}%.",
     f"销售与在售房源比率为 {s['overall']:.1f}%，市场处于供需平衡的偏低一侧。独立屋略低于 12%，是对买家最有利的类别；联排及半独立住宅最为坚挺，为 {s['attached']:.1f}%。"),
    (f"Benchmark prices are {G['composite_yoy'][1:]} lower than a year ago, with detached homes down {G['types'][1][3][1:]}, attached homes down {G['types'][2][3][1:]} and apartments down {G['types'][3][3][1:]}. "
     f"On the rental side, one-bedroom asking rents across Metro Vancouver are down {lv['metro_1bed_yoy'][1:]} from a year ago, while Vancouver two-bedrooms are up {lv['van_2bed_yoy'][1:]}.",
     f"基准价格较去年同期下降 {G['composite_yoy'][1:]}，其中独立屋下降 {G['types'][1][3][1:]}，联排及半独立住宅下降 {G['types'][2][3][1:]}，公寓下降 {G['types'][3][3][1:]}。"
     f"租金方面，大温哥华一居室挂牌租金较去年同期下降 {lv['metro_1bed_yoy'][1:]}，而温哥华两居室上涨 {lv['van_2bed_yoy'][1:]}。"),
    ("If you’re thinking of buying or selling, send us your address or the area you’re watching and we’ll walk you through what this means for your own situation.",
     "如果您正考虑买房或卖房，欢迎把地址或您关注的区域发给我们，我们会为您分析这些数据对您个人情况的意义。"),
]
if 'take' in X:
    take = [tuple(t) for t in X['take']]
if os.environ.get('DUMP_TEXT'):
    json.dump({'gauge_intro': [intro_g, intro_gz], 'rent_notes': [list(t) for t in _notes], 'take': [list(t) for t in take]}, open(os.environ['DUMP_TEXT'], 'w'), ensure_ascii=False, indent=2)
take_html = ''.join(f'<p style="margin:0;color:#4A443B;font-size:18px">{T(e, z)}</p>' for e, z in take)
parts.append(section(head(T('OUR TAKE', '我们的看法'), T('What this means', '这意味着什么')) +
                     f'<div style="display:flex;flex-direction:column;gap:18px;max-width:760px">{take_html}</div>', bg='#EAE3D7'))

# --- sources
SRC = "color:inherit;text-underline-offset:4px"
sources = (head(T('SOURCES AND NOTES', '资料来源与说明')) +
           f'<div style="display:flex;flex-direction:column;gap:12px;color:#4A443B">'
           f'<div>{T("Greater Vancouver REALTORS®, news release “" + G["release_title"] + ",” " + G["release_date"] + ".", "大温哥华地产商会（GVR）新闻稿《" + G["release_title"] + "》，" + G["release_date"] + "。")} '
           f'<a href="{G["release_url"]}" target="_blank" rel="noopener" style="{SRC}">{T("Read the release", "查看新闻稿")}</a></div>'
           f'<div>{T("liv.rent, " + L["report_title"] + ".", "liv.rent，2026 年 10 月大温哥华租金报告。")} '
           f'<a href="{L["report_url"]}" target="_blank" rel="noopener" style="{SRC}">{T("Read the report", "查看报告")}</a></div>'
           f'<div style="font-size:14px;color:#6A6258">{T("Benchmark prices are MLS® Home Price Index (HPI) figures. Information is drawn from the sources above, believed reliable but not guaranteed, and may be revised. This report is general information, not advice.", "基准价格为 MLS® 房价指数（HPI）数据。信息来自上述资料，相信可靠但不作保证，且可能被修订。本报告仅为一般信息，不构成建议。")}</div>'
           f'</div>')
parts.append(section(sources, pad='56px 24px'))


# --- earlier reports
archive_html = ''
if a.archive:
    prior = [r for r in json.load(open(a.archive)) if r['month'] != D['month']]
    prior.sort(key=lambda r: r['month'], reverse=True)
    if prior:
        links = ''.join(f'<a href="{SITE if a.mode != "dc" else ""}/market-report-{r["month"]}.html" style="color:inherit;text-underline-offset:4px;padding:14px 0;border-top:1px solid #D9D0C2;display:block">{T(r["month_en"], r["month_zh"])}</a>' for r in prior)
        archive_html = section(head(T('EARLIER REPORTS', '往期报告')) + f'<div style="display:flex;flex-direction:column;max-width:420px;border-bottom:1px solid #D9D0C2">{links}</div>', pad='56px 24px')

# --- subscribe
INP = "font:inherit;font-size:16px;padding:12px 14px;border:1px solid #BDB2A0;background:#FFFFFF;color:#1C1A17;border-radius:0;width:100%;box-sizing:border-box"
subscribe = (f'<section id="subscribe" style="background:#FBF9F5"><div style="max-width:1200px;margin:0 auto;box-sizing:border-box;padding:64px 24px;display:flex;flex-wrap:wrap;gap:32px 64px;align-items:flex-start">'
    f'<div style="flex:1 1 320px;min-width:0;max-width:520px;display:flex;flex-direction:column;gap:14px">'
    f'<div style="{EYE}">{T("GET THE NEXT REPORT", "订阅下期报告")}</div>'
    f'<div style="font-family:\'Cormorant Garamond\',Georgia,serif;font-weight:400;font-size:clamp(30px,3.4vw,42px);line-height:1.1">{T("Get this report by email each month", "每月通过电子邮件收到本报告")}</div>'
    f'<p style="margin:0;color:#4A443B">{T("A short note with the new report once a month, usually in the middle of the month. No spam, and you can unsubscribe at any time.", "每月一封简短邮件，附上最新报告，通常在月中发送。不发垃圾邮件，随时可以退订。")}</p></div>'
    f'<form id="sub-form" style="flex:1 1 340px;min-width:0;max-width:520px;display:flex;flex-direction:column;gap:14px">'
    f'<label style="display:flex;flex-direction:column;gap:6px"><span style="font-weight:600;font-size:13px;letter-spacing:0.08em;color:#4A443B">{T("Name (optional)", "姓名（选填）")}</span><input name="name" type="text" autocomplete="name" style="{INP}"></label>'
    f'<label style="display:flex;flex-direction:column;gap:6px"><span style="font-weight:600;font-size:13px;letter-spacing:0.08em;color:#4A443B">{T("Email address", "电子邮件")}</span><input name="email" type="email" required autocomplete="email" style="{INP}"></label>'
    f'<input type="text" name="_honey" tabindex="-1" autocomplete="off" style="position:absolute;left:-9999px;opacity:0;height:0;width:0">'
    f'<label style="display:flex;gap:10px;align-items:flex-start;font-size:14px;color:#4A443B"><input name="consent" type="checkbox" required style="margin-top:4px;flex:none"><span>{T("Yes, I’d like to receive Vivian Jiang’s monthly market report by email. I understand I can unsubscribe at any time.", "是的，我愿意通过电子邮件接收 Vivian Jiang 的月度市场报告，并了解可随时退订。")}</span></label>'
    f'<button type="submit" style="background:#1C1A17;color:#F5F1EA;border:0;font:inherit;font-weight:600;padding:14px 26px;min-height:44px;cursor:pointer;align-self:flex-start">{T("Subscribe", "订阅")}</button>'
    f'<div id="sub-msg" role="status" style="font-size:15px;font-weight:600;display:none"></div>'
    f'<div style="font-size:13px;color:#6A6258">{T("Sent by Vivian Jiang Personal Real Estate Corporation, Royal Pacific Realty Corp., 1200 West 73rd Avenue, Vancouver, BC. Questions: vivianjiang@royalpacific.com.", "发送方：Vivian Jiang Personal Real Estate Corporation，Royal Pacific Realty Corp.，1200 West 73rd Avenue, Vancouver, BC。如有疑问：vivianjiang@royalpacific.com。")}</div>'
    f'</form></div></section>')

SUBJS = r"""
(function () {
var f = document.getElementById('sub-form'); if (!f) return;
var msg = document.getElementById('sub-msg'), btn = f.querySelector('button');
var M = {
  ok: ['Thank you. You’re on the list for the next report.', '谢谢，您已加入下期报告的订阅名单。'],
  bad: ['Sorry, that could not be sent. Please email vivianjiang@royalpacific.com and we’ll add you.', '抱歉，提交失败。请发邮件至 vivianjiang@royalpacific.com，我们会为您添加。']
};
function say(k, ok) { msg.style.display = 'block'; msg.style.color = ok ? '#2F6B3F' : '#9B2C2C'; msg.setAttribute('data-zh', M[k][1]); msg.textContent = (document.documentElement.lang === 'zh-CN') ? M[k][1] : M[k][0]; msg.__en = M[k][0]; }
f.addEventListener('submit', function (e) {
  e.preventDefault();
  if (f.elements._honey.value) return;
  var d = { name: f.elements.name.value || '(no name)', email: f.elements.email.value, consent: 'Agreed to receive the monthly market report by email', _subject: 'Market report subscription: ' + f.elements.email.value, _template: 'table', _captcha: 'false', _cc: 'wenwenjiang1129@gmail.com', page: location.href };
  btn.disabled = true;
  fetch('https://formsubmit.co/ajax/vivianjiang@royalpacific.com', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(d) })
    .then(function (r) { return r.json(); })
    .then(function (j) { if (j && (j.success === true || j.success === 'true')) { f.reset(); say('ok', true); btn.style.display = 'none'; } else { throw 0; } })
    .catch(function () { say('bad', false); btn.disabled = false; });
});
})();
"""

# --- cta
cta = (f'<section style="background:#1C1A17;color:#F5F1EA"><div style="max-width:1200px;margin:0 auto;box-sizing:border-box;padding:64px 24px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px 48px">'
       f'<div style="min-width:0;max-width:560px"><div style="font-family:\'Cormorant Garamond\',Georgia,serif;font-weight:400;font-size:36px;line-height:1.1">{T("Questions about your area?", "想了解您所在的区域？")}</div>'
       f'<div style="color:#CFC6B8;padding-top:10px">Vivian Jiang Personal Real Estate Corporation<br>Royal Pacific Realty Corp. · 1200 West 73rd Avenue, Vancouver<br>vivianjiang@royalpacific.com</div></div>'
       f'<a href="tel:7783899947" style="background:#C8A97A;color:#1C1A17;text-decoration:none;font-weight:600;padding:14px 26px;min-height:44px;box-sizing:border-box;display:inline-flex;align-items:center">{T("Call 778-389-9947", "致电 778-389-9947")}</a>'
       f'</div></section>')

if a.mode == 'dc':
    H_HOME, H_LIST, H_MKT = 'Main.dc.html', 'AllListings.dc.html', 'Main.dc.html#market'
    H_NB = 'Neighbourhoods.dc.html'
else:
    H_HOME, H_LIST, H_MKT = SITE + '/', SITE + '/listings.html', SITE + '/index.html#market'
    H_NB = SITE + '/neighbourhoods.html'
header = (f'<header style="background:#1C1A17;color:#F5F1EA"><div style="max-width:1200px;margin:0 auto;box-sizing:border-box;padding:22px 24px;display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:14px 32px">'
          f'<a href="{H_HOME}" style="font-family:\'Cormorant Garamond\',Georgia,serif;font-weight:500;font-size:22px;letter-spacing:0.02em;text-decoration:none;color:inherit">Vivian Jiang <span style="font-weight:400;font-size:12px;letter-spacing:0.2em;color:#CFC6B8">PREC</span></a>'
          f'<nav style="display:flex;flex-wrap:wrap;align-items:center;gap:8px 28px;font-weight:500;font-size:15px">'
          f'<a href="{H_HOME}" style="color:inherit">{T("Home", "首页")}</a>'
          f'<a href="{H_LIST}" style="color:inherit">{T("All current listings", "全部在售房源")}</a>'
          f'<a href="{H_NB}" style="color:inherit">{T("Neighbourhoods", "社区")}</a>'
          f'<a href="{H_MKT}" style="color:inherit">{T("Market", "市场")}</a>'
          f'<a href="#" data-lang-toggle style="color:inherit">普通话</a>'
          f'<a href="tel:7783899947" style="color:inherit">778-389-9947</a></nav></div></header>')

banner = ''
if a.draft:
    banner = ('<div style="background:#F3E3B5;color:#4A3A12;padding:12px 24px;font-size:14px;text-align:center">'
              'Draft for review. The “Our take” section is written for Vivian to edit; every figure comes from the sources listed at the bottom.</div>')

SCRIPT = r'''<script>
(function () {
var KEY = 'vj-lang';
function get() { try { return localStorage.getItem(KEY) === 'zh' ? 'zh' : 'en'; } catch (e) { return 'en'; } }
function set(l) { try { localStorage.setItem(KEY, l); } catch (e) {} }
var nodes = [].slice.call(document.querySelectorAll('[data-zh]'));
nodes.forEach(function (n) { n.__en = n.textContent; });
var cur = 'en';
function apply(l) {
  nodes.forEach(function (n) { n.textContent = l === 'zh' ? n.getAttribute('data-zh') : n.__en; });
  document.documentElement.lang = l === 'zh' ? 'zh-CN' : 'en';
  var tg = document.querySelectorAll('[data-lang-toggle]');
  for (var i = 0; i < tg.length; i++) tg[i].textContent = l === 'zh' ? 'English' : '普通话';
}
function sync() { var l = get(); if (l !== cur) { cur = l; apply(l); } }
var tgs = document.querySelectorAll('[data-lang-toggle]');
for (var i = 0; i < tgs.length; i++) tgs[i].addEventListener('click', function (e) { e.preventDefault(); set(get() === 'zh' ? 'en' : 'zh'); sync(); });
window.addEventListener('storage', sync);
setInterval(sync, 700);
sync();
})();
</script>'''
SCRIPT = SCRIPT.replace('</script>', SUBJS + '</script>')

title = f'Metro Vancouver Market Report, {month_en}'
css = ("body{margin:0;font-variant-numeric:lining-nums;background:#F5F1EA}"
       "a:hover{color:#8A6A3E}"
       "table{font-family:inherit}")
fonts = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Hanken+Grotesk:wght@400;500;600&display=swap">'
body = (f'<div style="background:#F5F1EA;color:#1C1A17;font-family:\'Hanken Grotesk\',system-ui,sans-serif;font-size:17px;line-height:1.6">'
        f'{banner}{header}{"".join(parts)}{archive_html}{subscribe}{cta}</div>{SCRIPT}')

if a.mode == 'dc':
    js = SCRIPT.replace('<script>', '', 1).rsplit('</script>', 1)[0]
    body_dc = (f'<div style="background:#F5F1EA;color:#1C1A17;font-family:\'Hanken Grotesk\',system-ui,sans-serif;font-size:17px;line-height:1.6">'
               f'{header}{"".join(parts)}{archive_html}{subscribe}{cta}</div>')
    out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>Market Report</title>\n<script src="./support.js"></script>\n</head>\n<body>\n<x-dc>\n<helmet>\n'
           f'{fonts}\n<style>{css}</style>\n</helmet>\n{body_dc}\n</x-dc>\n'
           '<script type="text/x-dc" data-dc-script data-props=\'{"$preview":{"width":1360,"height":6000}}\'>\nclass Component extends DCLogic {\ncomponentDidMount() {\ntry {\n' + js + '\n} catch (e) {}\n\n}\nrenderVals() {\nreturn {};\n}\n}\n</script>\n</body>\n</html>\n')
elif a.mode == 'artifact':
    out = (f'<title>{E(title)}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n{fonts}\n<style>:root{{color-scheme:light}}{css}</style>\n{body}\n')
else:
    out = (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
           f'<title>{E(title)}</title>\n<meta name="description" content="Monthly Metro Vancouver home sales, prices and rents for {E(month_en)}, from the Greater Vancouver REALTORS® and liv.rent.">\n'
           f'{fonts}\n<style>{css}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n')
open(a.out, 'w').write(out)
print('wrote', a.out, len(out))

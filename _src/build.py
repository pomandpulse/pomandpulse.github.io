#!/usr/bin/env python3
"""PersianPulse static site builder (stdlib only).
Usage: python3 _src/build.py --out _site [--through YYYY-MM-DD]
Reads _src/data/pieces.json. Publishes pieces dated on or before the cutoff
(default: most recent Saturday on/before yesterday, Pacific time)."""
import argparse, json, shutil, html, hashlib, datetime as dt
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
:root{--crimson:#C42B2F;--dark:#8D1E21;--gold:#C9A24B;--sage:#9DB59A;--sagel:#E8EEE3;--paper:#F8F4EC;--ink:#1F1A1C;--muted:#5B5655;--line:#E4DCCB;--r:18px;--pat:url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%2780%27%20height%3D%2780%27%20viewBox%3D%270%200%2080%2080%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27%23C9A24B%27%20stroke-opacity%3D%27.30%27%20stroke-width%3D%271.1%27%20stroke-linejoin%3D%27round%27%3E%3Cpolygon%20points%3D%2740.00%2C16.00%2047.03%2C23.03%2056.97%2C23.03%2056.97%2C32.97%2064.00%2C40.00%2056.97%2C47.03%2056.97%2C56.97%2047.03%2C56.97%2040.00%2C64.00%2032.97%2C56.97%2023.03%2C56.97%2023.03%2C47.03%2016.00%2C40.00%2023.03%2C32.97%2023.03%2C23.03%2032.97%2C23.03%27%2F%3E%3Cpolygon%20points%3D%2740.00%2C30.00%2042.93%2C32.93%2047.07%2C32.93%2047.07%2C37.07%2050.00%2C40.00%2047.07%2C42.93%2047.07%2C47.07%2042.93%2C47.07%2040.00%2C50.00%2037.07%2C47.07%2032.93%2C47.07%2032.93%2C42.93%2030.00%2C40.00%2032.93%2C37.07%2032.93%2C32.93%2037.07%2C32.93%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-24.00%207.03%2C-16.97%2016.97%2C-16.97%2016.97%2C-7.03%2024.00%2C0.00%2016.97%2C7.03%2016.97%2C16.97%207.03%2C16.97%200.00%2C24.00%20-7.03%2C16.97%20-16.97%2C16.97%20-16.97%2C7.03%20-24.00%2C0.00%20-16.97%2C-7.03%20-16.97%2C-16.97%20-7.03%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-10.00%202.93%2C-7.07%207.07%2C-7.07%207.07%2C-2.93%2010.00%2C0.00%207.07%2C2.93%207.07%2C7.07%202.93%2C7.07%200.00%2C10.00%20-2.93%2C7.07%20-7.07%2C7.07%20-7.07%2C2.93%20-10.00%2C0.00%20-7.07%2C-2.93%20-7.07%2C-7.07%20-2.93%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-24.00%2087.03%2C-16.97%2096.97%2C-16.97%2096.97%2C-7.03%20104.00%2C0.00%2096.97%2C7.03%2096.97%2C16.97%2087.03%2C16.97%2080.00%2C24.00%2072.97%2C16.97%2063.03%2C16.97%2063.03%2C7.03%2056.00%2C0.00%2063.03%2C-7.03%2063.03%2C-16.97%2072.97%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-10.00%2082.93%2C-7.07%2087.07%2C-7.07%2087.07%2C-2.93%2090.00%2C0.00%2087.07%2C2.93%2087.07%2C7.07%2082.93%2C7.07%2080.00%2C10.00%2077.07%2C7.07%2072.93%2C7.07%2072.93%2C2.93%2070.00%2C0.00%2072.93%2C-2.93%2072.93%2C-7.07%2077.07%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%270.00%2C56.00%207.03%2C63.03%2016.97%2C63.03%2016.97%2C72.97%2024.00%2C80.00%2016.97%2C87.03%2016.97%2C96.97%207.03%2C96.97%200.00%2C104.00%20-7.03%2C96.97%20-16.97%2C96.97%20-16.97%2C87.03%20-24.00%2C80.00%20-16.97%2C72.97%20-16.97%2C63.03%20-7.03%2C63.03%27%2F%3E%3Cpolygon%20points%3D%270.00%2C70.00%202.93%2C72.93%207.07%2C72.93%207.07%2C77.07%2010.00%2C80.00%207.07%2C82.93%207.07%2C87.07%202.93%2C87.07%200.00%2C90.00%20-2.93%2C87.07%20-7.07%2C87.07%20-7.07%2C82.93%20-10.00%2C80.00%20-7.07%2C77.07%20-7.07%2C72.93%20-2.93%2C72.93%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C56.00%2087.03%2C63.03%2096.97%2C63.03%2096.97%2C72.97%20104.00%2C80.00%2096.97%2C87.03%2096.97%2C96.97%2087.03%2C96.97%2080.00%2C104.00%2072.97%2C96.97%2063.03%2C96.97%2063.03%2C87.03%2056.00%2C80.00%2063.03%2C72.97%2063.03%2C63.03%2072.97%2C63.03%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C70.00%2082.93%2C72.93%2087.07%2C72.93%2087.07%2C77.07%2090.00%2C80.00%2087.07%2C82.93%2087.07%2C87.07%2082.93%2C87.07%2080.00%2C90.00%2077.07%2C87.07%2072.93%2C87.07%2072.93%2C82.93%2070.00%2C80.00%2072.93%2C77.07%2072.93%2C72.93%2077.07%2C72.93%27%2F%3E%3Cpath%20d%3D%27M40%200%20L52%2012%20L40%2024%20L28%2012Z%20M40%2056%20L52%2068%20L40%2080%20L28%2068Z%20M0%2040%20L12%2052%20L0%2064%20M0%2040%20L12%2028%20L0%2016%20M80%2040%20L68%2052%20L80%2064%20M80%2040%20L68%2028%20L80%2016%27%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");--pat-b:url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%2780%27%20height%3D%2780%27%20viewBox%3D%270%200%2080%2080%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27%23C9A24B%27%20stroke-opacity%3D%27.13%27%20stroke-width%3D%271.1%27%20stroke-linejoin%3D%27round%27%3E%3Cpolygon%20points%3D%2740.00%2C16.00%2047.03%2C23.03%2056.97%2C23.03%2056.97%2C32.97%2064.00%2C40.00%2056.97%2C47.03%2056.97%2C56.97%2047.03%2C56.97%2040.00%2C64.00%2032.97%2C56.97%2023.03%2C56.97%2023.03%2C47.03%2016.00%2C40.00%2023.03%2C32.97%2023.03%2C23.03%2032.97%2C23.03%27%2F%3E%3Cpolygon%20points%3D%2740.00%2C30.00%2042.93%2C32.93%2047.07%2C32.93%2047.07%2C37.07%2050.00%2C40.00%2047.07%2C42.93%2047.07%2C47.07%2042.93%2C47.07%2040.00%2C50.00%2037.07%2C47.07%2032.93%2C47.07%2032.93%2C42.93%2030.00%2C40.00%2032.93%2C37.07%2032.93%2C32.93%2037.07%2C32.93%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-24.00%207.03%2C-16.97%2016.97%2C-16.97%2016.97%2C-7.03%2024.00%2C0.00%2016.97%2C7.03%2016.97%2C16.97%207.03%2C16.97%200.00%2C24.00%20-7.03%2C16.97%20-16.97%2C16.97%20-16.97%2C7.03%20-24.00%2C0.00%20-16.97%2C-7.03%20-16.97%2C-16.97%20-7.03%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-10.00%202.93%2C-7.07%207.07%2C-7.07%207.07%2C-2.93%2010.00%2C0.00%207.07%2C2.93%207.07%2C7.07%202.93%2C7.07%200.00%2C10.00%20-2.93%2C7.07%20-7.07%2C7.07%20-7.07%2C2.93%20-10.00%2C0.00%20-7.07%2C-2.93%20-7.07%2C-7.07%20-2.93%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-24.00%2087.03%2C-16.97%2096.97%2C-16.97%2096.97%2C-7.03%20104.00%2C0.00%2096.97%2C7.03%2096.97%2C16.97%2087.03%2C16.97%2080.00%2C24.00%2072.97%2C16.97%2063.03%2C16.97%2063.03%2C7.03%2056.00%2C0.00%2063.03%2C-7.03%2063.03%2C-16.97%2072.97%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-10.00%2082.93%2C-7.07%2087.07%2C-7.07%2087.07%2C-2.93%2090.00%2C0.00%2087.07%2C2.93%2087.07%2C7.07%2082.93%2C7.07%2080.00%2C10.00%2077.07%2C7.07%2072.93%2C7.07%2072.93%2C2.93%2070.00%2C0.00%2072.93%2C-2.93%2072.93%2C-7.07%2077.07%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%270.00%2C56.00%207.03%2C63.03%2016.97%2C63.03%2016.97%2C72.97%2024.00%2C80.00%2016.97%2C87.03%2016.97%2C96.97%207.03%2C96.97%200.00%2C104.00%20-7.03%2C96.97%20-16.97%2C96.97%20-16.97%2C87.03%20-24.00%2C80.00%20-16.97%2C72.97%20-16.97%2C63.03%20-7.03%2C63.03%27%2F%3E%3Cpolygon%20points%3D%270.00%2C70.00%202.93%2C72.93%207.07%2C72.93%207.07%2C77.07%2010.00%2C80.00%207.07%2C82.93%207.07%2C87.07%202.93%2C87.07%200.00%2C90.00%20-2.93%2C87.07%20-7.07%2C87.07%20-7.07%2C82.93%20-10.00%2C80.00%20-7.07%2C77.07%20-7.07%2C72.93%20-2.93%2C72.93%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C56.00%2087.03%2C63.03%2096.97%2C63.03%2096.97%2C72.97%20104.00%2C80.00%2096.97%2C87.03%2096.97%2C96.97%2087.03%2C96.97%2080.00%2C104.00%2072.97%2C96.97%2063.03%2C96.97%2063.03%2C87.03%2056.00%2C80.00%2063.03%2C72.97%2063.03%2C63.03%2072.97%2C63.03%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C70.00%2082.93%2C72.93%2087.07%2C72.93%2087.07%2C77.07%2090.00%2C80.00%2087.07%2C82.93%2087.07%2C87.07%2082.93%2C87.07%2080.00%2C90.00%2077.07%2C87.07%2072.93%2C87.07%2072.93%2C82.93%2070.00%2C80.00%2072.93%2C77.07%2072.93%2C72.93%2077.07%2C72.93%27%2F%3E%3Cpath%20d%3D%27M40%200%20L52%2012%20L40%2024%20L28%2012Z%20M40%2056%20L52%2068%20L40%2080%20L28%2068Z%20M0%2040%20L12%2052%20L0%2064%20M0%2040%20L12%2028%20L0%2016%20M80%2040%20L68%2052%20L80%2064%20M80%2040%20L68%2028%20L80%2016%27%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");--pat-w:url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%2780%27%20height%3D%2780%27%20viewBox%3D%270%200%2080%2080%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27%23FFFFFF%27%20stroke-opacity%3D%27.14%27%20stroke-width%3D%271.1%27%20stroke-linejoin%3D%27round%27%3E%3Cpolygon%20points%3D%2740.00%2C16.00%2047.03%2C23.03%2056.97%2C23.03%2056.97%2C32.97%2064.00%2C40.00%2056.97%2C47.03%2056.97%2C56.97%2047.03%2C56.97%2040.00%2C64.00%2032.97%2C56.97%2023.03%2C56.97%2023.03%2C47.03%2016.00%2C40.00%2023.03%2C32.97%2023.03%2C23.03%2032.97%2C23.03%27%2F%3E%3Cpolygon%20points%3D%2740.00%2C30.00%2042.93%2C32.93%2047.07%2C32.93%2047.07%2C37.07%2050.00%2C40.00%2047.07%2C42.93%2047.07%2C47.07%2042.93%2C47.07%2040.00%2C50.00%2037.07%2C47.07%2032.93%2C47.07%2032.93%2C42.93%2030.00%2C40.00%2032.93%2C37.07%2032.93%2C32.93%2037.07%2C32.93%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-24.00%207.03%2C-16.97%2016.97%2C-16.97%2016.97%2C-7.03%2024.00%2C0.00%2016.97%2C7.03%2016.97%2C16.97%207.03%2C16.97%200.00%2C24.00%20-7.03%2C16.97%20-16.97%2C16.97%20-16.97%2C7.03%20-24.00%2C0.00%20-16.97%2C-7.03%20-16.97%2C-16.97%20-7.03%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-10.00%202.93%2C-7.07%207.07%2C-7.07%207.07%2C-2.93%2010.00%2C0.00%207.07%2C2.93%207.07%2C7.07%202.93%2C7.07%200.00%2C10.00%20-2.93%2C7.07%20-7.07%2C7.07%20-7.07%2C2.93%20-10.00%2C0.00%20-7.07%2C-2.93%20-7.07%2C-7.07%20-2.93%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-24.00%2087.03%2C-16.97%2096.97%2C-16.97%2096.97%2C-7.03%20104.00%2C0.00%2096.97%2C7.03%2096.97%2C16.97%2087.03%2C16.97%2080.00%2C24.00%2072.97%2C16.97%2063.03%2C16.97%2063.03%2C7.03%2056.00%2C0.00%2063.03%2C-7.03%2063.03%2C-16.97%2072.97%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-10.00%2082.93%2C-7.07%2087.07%2C-7.07%2087.07%2C-2.93%2090.00%2C0.00%2087.07%2C2.93%2087.07%2C7.07%2082.93%2C7.07%2080.00%2C10.00%2077.07%2C7.07%2072.93%2C7.07%2072.93%2C2.93%2070.00%2C0.00%2072.93%2C-2.93%2072.93%2C-7.07%2077.07%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%270.00%2C56.00%207.03%2C63.03%2016.97%2C63.03%2016.97%2C72.97%2024.00%2C80.00%2016.97%2C87.03%2016.97%2C96.97%207.03%2C96.97%200.00%2C104.00%20-7.03%2C96.97%20-16.97%2C96.97%20-16.97%2C87.03%20-24.00%2C80.00%20-16.97%2C72.97%20-16.97%2C63.03%20-7.03%2C63.03%27%2F%3E%3Cpolygon%20points%3D%270.00%2C70.00%202.93%2C72.93%207.07%2C72.93%207.07%2C77.07%2010.00%2C80.00%207.07%2C82.93%207.07%2C87.07%202.93%2C87.07%200.00%2C90.00%20-2.93%2C87.07%20-7.07%2C87.07%20-7.07%2C82.93%20-10.00%2C80.00%20-7.07%2C77.07%20-7.07%2C72.93%20-2.93%2C72.93%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C56.00%2087.03%2C63.03%2096.97%2C63.03%2096.97%2C72.97%20104.00%2C80.00%2096.97%2C87.03%2096.97%2C96.97%2087.03%2C96.97%2080.00%2C104.00%2072.97%2C96.97%2063.03%2C96.97%2063.03%2C87.03%2056.00%2C80.00%2063.03%2C72.97%2063.03%2C63.03%2072.97%2C63.03%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C70.00%2082.93%2C72.93%2087.07%2C72.93%2087.07%2C77.07%2090.00%2C80.00%2087.07%2C82.93%2087.07%2C87.07%2082.93%2C87.07%2080.00%2C90.00%2077.07%2C87.07%2072.93%2C87.07%2072.93%2C82.93%2070.00%2C80.00%2072.93%2C77.07%2072.93%2C72.93%2077.07%2C72.93%27%2F%3E%3Cpath%20d%3D%27M40%200%20L52%2012%20L40%2024%20L28%2012Z%20M40%2056%20L52%2068%20L40%2080%20L28%2068Z%20M0%2040%20L12%2052%20L0%2064%20M0%2040%20L12%2028%20L0%2016%20M80%2040%20L68%2052%20L80%2064%20M80%2040%20L68%2028%20L80%2016%27%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");--pat-g:url("data:image/svg+xml,%3Csvg%20xmlns%3D%27http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%27%20width%3D%2780%27%20height%3D%2780%27%20viewBox%3D%270%200%2080%2080%27%3E%3Cg%20fill%3D%27none%27%20stroke%3D%27%23C9A24B%27%20stroke-opacity%3D%27.16%27%20stroke-width%3D%271.1%27%20stroke-linejoin%3D%27round%27%3E%3Cpolygon%20points%3D%2740.00%2C16.00%2047.03%2C23.03%2056.97%2C23.03%2056.97%2C32.97%2064.00%2C40.00%2056.97%2C47.03%2056.97%2C56.97%2047.03%2C56.97%2040.00%2C64.00%2032.97%2C56.97%2023.03%2C56.97%2023.03%2C47.03%2016.00%2C40.00%2023.03%2C32.97%2023.03%2C23.03%2032.97%2C23.03%27%2F%3E%3Cpolygon%20points%3D%2740.00%2C30.00%2042.93%2C32.93%2047.07%2C32.93%2047.07%2C37.07%2050.00%2C40.00%2047.07%2C42.93%2047.07%2C47.07%2042.93%2C47.07%2040.00%2C50.00%2037.07%2C47.07%2032.93%2C47.07%2032.93%2C42.93%2030.00%2C40.00%2032.93%2C37.07%2032.93%2C32.93%2037.07%2C32.93%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-24.00%207.03%2C-16.97%2016.97%2C-16.97%2016.97%2C-7.03%2024.00%2C0.00%2016.97%2C7.03%2016.97%2C16.97%207.03%2C16.97%200.00%2C24.00%20-7.03%2C16.97%20-16.97%2C16.97%20-16.97%2C7.03%20-24.00%2C0.00%20-16.97%2C-7.03%20-16.97%2C-16.97%20-7.03%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%270.00%2C-10.00%202.93%2C-7.07%207.07%2C-7.07%207.07%2C-2.93%2010.00%2C0.00%207.07%2C2.93%207.07%2C7.07%202.93%2C7.07%200.00%2C10.00%20-2.93%2C7.07%20-7.07%2C7.07%20-7.07%2C2.93%20-10.00%2C0.00%20-7.07%2C-2.93%20-7.07%2C-7.07%20-2.93%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-24.00%2087.03%2C-16.97%2096.97%2C-16.97%2096.97%2C-7.03%20104.00%2C0.00%2096.97%2C7.03%2096.97%2C16.97%2087.03%2C16.97%2080.00%2C24.00%2072.97%2C16.97%2063.03%2C16.97%2063.03%2C7.03%2056.00%2C0.00%2063.03%2C-7.03%2063.03%2C-16.97%2072.97%2C-16.97%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C-10.00%2082.93%2C-7.07%2087.07%2C-7.07%2087.07%2C-2.93%2090.00%2C0.00%2087.07%2C2.93%2087.07%2C7.07%2082.93%2C7.07%2080.00%2C10.00%2077.07%2C7.07%2072.93%2C7.07%2072.93%2C2.93%2070.00%2C0.00%2072.93%2C-2.93%2072.93%2C-7.07%2077.07%2C-7.07%27%2F%3E%3Cpolygon%20points%3D%270.00%2C56.00%207.03%2C63.03%2016.97%2C63.03%2016.97%2C72.97%2024.00%2C80.00%2016.97%2C87.03%2016.97%2C96.97%207.03%2C96.97%200.00%2C104.00%20-7.03%2C96.97%20-16.97%2C96.97%20-16.97%2C87.03%20-24.00%2C80.00%20-16.97%2C72.97%20-16.97%2C63.03%20-7.03%2C63.03%27%2F%3E%3Cpolygon%20points%3D%270.00%2C70.00%202.93%2C72.93%207.07%2C72.93%207.07%2C77.07%2010.00%2C80.00%207.07%2C82.93%207.07%2C87.07%202.93%2C87.07%200.00%2C90.00%20-2.93%2C87.07%20-7.07%2C87.07%20-7.07%2C82.93%20-10.00%2C80.00%20-7.07%2C77.07%20-7.07%2C72.93%20-2.93%2C72.93%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C56.00%2087.03%2C63.03%2096.97%2C63.03%2096.97%2C72.97%20104.00%2C80.00%2096.97%2C87.03%2096.97%2C96.97%2087.03%2C96.97%2080.00%2C104.00%2072.97%2C96.97%2063.03%2C96.97%2063.03%2C87.03%2056.00%2C80.00%2063.03%2C72.97%2063.03%2C63.03%2072.97%2C63.03%27%2F%3E%3Cpolygon%20points%3D%2780.00%2C70.00%2082.93%2C72.93%2087.07%2C72.93%2087.07%2C77.07%2090.00%2C80.00%2087.07%2C82.93%2087.07%2C87.07%2082.93%2C87.07%2080.00%2C90.00%2077.07%2C87.07%2072.93%2C87.07%2072.93%2C82.93%2070.00%2C80.00%2072.93%2C77.07%2072.93%2C72.93%2077.07%2C72.93%27%2F%3E%3Cpath%20d%3D%27M40%200%20L52%2012%20L40%2024%20L28%2012Z%20M40%2056%20L52%2068%20L40%2080%20L28%2068Z%20M0%2040%20L12%2052%20L0%2064%20M0%2040%20L12%2028%20L0%2016%20M80%2040%20L68%2052%20L80%2064%20M80%2040%20L68%2028%20L80%2016%27%2F%3E%3C%2Fg%3E%3C%2Fsvg%3E");}
*{box-sizing:border-box}html{scroll-behavior:smooth}[hidden]{display:none!important}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 Inter,system-ui,sans-serif}
body.fa{font-family:Vazirmatn,Inter,sans-serif}
h1,h2,h3{font-family:Lora,Georgia,serif;line-height:1.15;margin:0 0 .5em}
body.fa h1,body.fa h2,body.fa h3,body.fa .brand{font-family:Vazirmatn,Lora,serif;font-weight:700;line-height:1.4}
h1{font-size:clamp(2.1rem,5vw,3.4rem)}h2{font-size:clamp(1.5rem,3vw,2.1rem)}h3{font-size:1.15rem}
a{color:var(--dark)}a:hover{color:var(--crimson)}
.wrap{max-width:1120px;margin:0 auto;padding:0 22px}
.fa{font-family:Vazirmatn,Inter,sans-serif;direction:rtl;font-style:normal}
header.top{background:rgba(248,244,236,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;align-items:center;gap:18px;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--ink);font:700 1.3rem Lora,serif}
.brand img{width:42px;height:42px}
nav{display:flex;gap:4px 20px;flex-wrap:wrap;margin-left:auto;font-size:.95rem;align-items:center}
body.fa nav{margin-left:0;margin-right:auto}
nav a{text-decoration:none;color:var(--muted);padding:4px 0;border-bottom:2px solid transparent}
nav a:hover,nav a.on{color:var(--crimson);border-color:var(--crimson)}
nav a.langsw{background:var(--crimson);color:#fff;border:0;border-radius:999px;padding:5px 16px;font-weight:600}
nav a.langsw:hover{background:var(--dark);color:#fff}
.btn{display:inline-flex;align-items:center;gap:8px;background:var(--crimson);color:#fff;text-decoration:none;padding:12px 24px;border-radius:999px;font-weight:600;font-size:.95rem;border:2px solid var(--crimson);cursor:pointer;font-family:inherit;transition:transform .15s,background .15s}
.btn:hover{background:var(--dark);border-color:var(--dark);color:#fff;transform:translateY(-2px)}
.btn.alt{background:transparent;color:var(--dark)}.btn.alt:hover{background:var(--crimson);color:#fff}
.btn.gold{background:var(--gold);border-color:var(--gold);color:var(--ink)}.btn.gold:hover{background:#fff;border-color:#fff;color:var(--dark)}
.tag{display:inline-block;background:var(--sagel);color:#46603f;border-radius:999px;padding:3px 13px;font-size:.8rem;font-weight:600}
.eyebrow{display:inline-flex;gap:10px;align-items:center;font-size:.8rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--dark);margin-bottom:18px}
.eyebrow:before{content:"";width:34px;height:2px;background:var(--gold)}
body.fa .eyebrow{letter-spacing:0;text-transform:none;font-size:.95rem}
/* hero */
.hero{position:relative;overflow:hidden;margin-top:-56px;padding:72px 0 120px;background:
 radial-gradient(circle at 85% 20%,rgba(196,43,47,.13),transparent 45%),
 radial-gradient(circle at 5% 90%,rgba(157,181,154,.45),transparent 45%),rgba(248,244,236,.9)}
.hero:before{content:"";position:absolute;inset:0;background:var(--pat);background-size:96px 96px;-webkit-mask-image:radial-gradient(ellipse at 85% 30%,#000 0,transparent 62%);mask-image:radial-gradient(ellipse at 85% 30%,#000 0,transparent 62%);opacity:.8}
.hero .wrap{position:relative;z-index:1;display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center}
.hero h1 em{font-style:normal;color:var(--crimson);background:linear-gradient(transparent 68%,rgba(201,162,75,.45) 68%)}
.hero .lead{font-size:1.2rem;color:var(--muted);max-width:540px;margin:0 0 28px}
.hero .cta{display:flex;gap:12px;flex-wrap:wrap}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin-top:30px}
.chips span{background:#fff;border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:.85rem;color:var(--muted)}
.feature{position:relative;display:block;text-decoration:none;justify-self:center;width:min(100%,400px)}
.feature:before{content:"";position:absolute;inset:18px -18px -18px 18px;background:var(--gold);border-radius:var(--r);opacity:.85}
body.fa .feature:before{inset:18px 18px -18px -18px}
.feature img{position:relative;width:100%;height:auto;display:block;border-radius:var(--r);box-shadow:0 24px 50px rgba(31,26,28,.28);transform:rotate(-2deg);transition:transform .25s}
.feature:hover img{transform:rotate(0) scale(1.02)}
.feature .badge{position:absolute;z-index:2;top:-14px;left:-10px;background:var(--crimson);color:#fff;border-radius:999px;padding:6px 16px;font-size:.8rem;font-weight:600;box-shadow:0 6px 16px rgba(196,43,47,.4)}
body.fa .feature .badge{left:auto;right:-10px}
.pulse{position:absolute;left:0;right:0;bottom:40px;z-index:0;width:100%;height:60px;pointer-events:none}
.pulse path{fill:none;stroke:var(--crimson);stroke-width:2.5;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:1600;stroke-dashoffset:1600;animation:draw 3.2s ease-out .3s forwards;opacity:.55}
@keyframes draw{to{stroke-dashoffset:0}}
@media(prefers-reduced-motion:reduce){.pulse path{animation:none;stroke-dashoffset:0}.feature img,.btn,.card{transition:none}}
/* sections */
section.s{padding:64px 0}
.sh{display:flex;justify-content:space-between;align-items:end;gap:20px;flex-wrap:wrap;margin-bottom:28px}
.sh h2{margin:0}.sh a{font-weight:600;text-decoration:none}
.pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:22px;margin-top:-46px;position:relative;z-index:2}
.pillar{background:#fff;border:1px solid var(--line);border-radius:var(--r);padding:26px;box-shadow:0 10px 30px rgba(31,26,28,.07)}
.pillar .ic{width:48px;height:48px;border-radius:14px;background:var(--sagel);display:grid;place-items:center;margin-bottom:14px}
.pillar:nth-child(2) .ic{background:#F6E3E1}.pillar:nth-child(3) .ic{background:#F4EBD3}
.pillar svg{width:26px;height:26px;stroke:var(--dark);fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.pillar h3{margin-bottom:.3em}.pillar p{margin:0;color:var(--muted);font-size:.95rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:26px}
.card{background:#fff;border:1px solid var(--line);border-radius:var(--r);overflow:hidden;text-decoration:none;color:var(--ink);display:block;transition:transform .2s,box-shadow .2s;position:relative}
.card:after{content:"";position:absolute;left:0;right:0;bottom:0;height:4px;background:linear-gradient(90deg,var(--crimson),var(--gold));transform:scaleX(0);transform-origin:left;transition:transform .3s}
.card:hover{transform:translateY(-5px);box-shadow:0 16px 34px rgba(31,26,28,.16)}.card:hover:after{transform:scaleX(1)}
.card img{width:100%;aspect-ratio:4/5;object-fit:cover;display:block;background:var(--sagel)}
.card div{padding:14px 18px 20px}.card small{color:var(--muted)}
.card h3{font-size:1.05rem;margin:.5em 0 .2em}
.band{background:var(--dark);color:var(--paper);position:relative;overflow:hidden}
.band:before{content:"";position:absolute;inset:0;background:var(--pat-w) 0 0/96px 96px,radial-gradient(circle at 90% 0,rgba(201,162,75,.35),transparent 50%),radial-gradient(circle at 0 100%,rgba(196,43,47,.7),transparent 55%)}
.band .wrap{position:relative;display:grid;grid-template-columns:1.2fr .8fr;gap:40px;align-items:center}
.band h2{color:#fff}.band p{color:#F1D9D9;max-width:520px}
.band .terms{display:flex;gap:10px;flex-wrap:wrap}.band .terms span{border:1.5px solid rgba(255,255,255,.35);border-radius:999px;padding:8px 18px;font-family:Lora,serif;font-size:1.05rem}
body.fa .band .terms span{font-family:Vazirmatn,sans-serif}
.follow{display:flex;gap:12px;flex-wrap:wrap}
.chipbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:28px}
.chipbar a{background:#fff;border:1.5px solid var(--line);border-radius:999px;padding:6px 16px;text-decoration:none;font-size:.9rem;color:var(--muted)}.chipbar a:hover{border-color:var(--crimson);color:var(--crimson)}
main{padding:40px 0 70px;min-height:55vh}
.pagehead{margin-bottom:30px;padding-bottom:22px;border-bottom:2px solid var(--line);position:relative}
.pagehead:after{content:"";position:absolute;left:0;bottom:-2px;width:90px;height:2px;background:var(--crimson)}
body.fa .pagehead:after{left:auto;right:0}
.pagehead p{color:var(--muted);margin:0;max-width:620px}
/* piece */
.piece{display:grid;grid-template-columns:minmax(0,520px) minmax(0,1fr);gap:48px;align-items:start}
.piece .pic{position:sticky;top:90px}
@media(max-width:860px){.piece{grid-template-columns:1fr}.piece .pic{position:static}.hero .wrap,.band .wrap{grid-template-columns:1fr}.hero{padding:48px 0 120px}.feature{margin-top:14px}}
.piece img.main{width:100%;height:auto;border-radius:var(--r);box-shadow:0 20px 44px rgba(31,26,28,.22);display:block}
.meta{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px;color:var(--muted);font-size:.9rem}
.meta a{text-decoration:none;font-weight:600}
.row{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 22px}
.box{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 22px;margin:16px 0}
.box.cap{border-inline-start:5px solid var(--crimson)}
.box h3{font-size:.8rem;font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.5em}
body.fa .box h3{letter-spacing:0;font-size:.95rem;text-transform:none;font-family:Vazirmatn,sans-serif}
.box p{margin:0}.box ul{margin:0;padding-inline-start:1.2em}
.box summary{cursor:pointer;font-weight:600}
.note{background:var(--sagel);border-radius:12px;padding:12px 18px;font-size:.92rem;color:#3d5237}
.prose{max-width:720px}.prose li{margin:.4em 0}
.empty{background:#fff;border:2px dashed var(--gold);border-radius:var(--r);padding:30px;color:var(--muted)}
footer{background:var(--ink) var(--pat-g);background-size:80px 80px;color:#CFC7BF;padding:44px 0;font-size:.92rem;border-top:4px solid var(--crimson)}
footer a{color:#F1D9A8}footer strong{color:#fff;font:700 1.2rem Lora,serif}
footer .wrap{display:flex;flex-wrap:wrap;gap:16px 40px;justify-content:space-between}

/* ---- polish layer ---- */
:root{--sh1:0 1px 2px rgba(31,26,28,.04),0 6px 18px rgba(31,26,28,.06);--sh2:0 2px 4px rgba(31,26,28,.05),0 18px 40px rgba(31,26,28,.14);--ease:cubic-bezier(.2,.7,.2,1)}
h1,h2{letter-spacing:-.018em}body.fa h1,body.fa h2,body.fa h3{letter-spacing:0}
header.top{background:rgba(248,244,236,.94) var(--pat-b);background-size:auto,80px 80px}
.btn{height:48px;padding:0 26px;border-radius:999px;font-size:.95rem;justify-content:center;transition:transform .25s var(--ease),background .2s,color .2s,box-shadow .25s var(--ease)}
.btn:hover{box-shadow:0 8px 20px rgba(196,43,47,.28)}.btn.alt:hover{box-shadow:0 8px 20px rgba(196,43,47,.2)}.btn.gold:hover{box-shadow:0 8px 20px rgba(0,0,0,.25)}
.btn:active{transform:translateY(0)}
nav a.langsw{height:34px;display:inline-flex;align-items:center;padding:0 16px}
section.s{padding:92px 0}
.hero{padding:76px 0 132px;background:radial-gradient(circle at 85% 20%,rgba(196,43,47,.11),transparent 48%),radial-gradient(circle at 0 65%,rgba(157,181,154,.34),transparent 42%),linear-gradient(180deg,rgba(248,244,236,.2) 78%,var(--paper))}
.hero h1{font-size:clamp(2.4rem,5.4vw,4rem);margin-bottom:.35em}
.trust{display:flex;flex-wrap:wrap;gap:6px 0;margin:0 0 22px;font-size:.9rem;font-weight:600;color:var(--dark)}
.trust span{display:inline-flex;align-items:center}.trust span+span:before{content:"";width:5px;height:5px;background:var(--gold);transform:rotate(45deg);margin:0 14px}
.hero .lead{margin-bottom:30px}
.langpick{display:flex;align-items:center;gap:12px;margin-top:34px;padding-top:24px;border-top:1px solid var(--line);font-size:.88rem;color:var(--muted);max-width:540px}
.langpick a{display:inline-flex;align-items:center;height:34px;padding:0 16px;border:1.5px solid var(--line);border-radius:999px;text-decoration:none;color:var(--ink);background:#fff;font-weight:600;transition:border-color .2s,color .2s,transform .25s var(--ease)}
.langpick a:hover{border-color:var(--crimson);color:var(--crimson);transform:translateY(-2px)}
.langpick a.cur{background:var(--ink);color:#fff;border-color:var(--ink)}
.feature:before{transition:transform .35s var(--ease)}
.feature img{box-shadow:var(--sh2);transition:transform .35s var(--ease),box-shadow .35s var(--ease)}
.feature:hover img{transform:rotate(0) translateY(-8px) scale(1.015);box-shadow:0 4px 8px rgba(31,26,28,.08),0 32px 60px rgba(31,26,28,.26)}
.feature:hover:before{transform:translate(8px,8px)}body.fa .feature:hover:before{transform:translate(-8px,8px)}
.pulse{bottom:58px;opacity:1;-webkit-mask-image:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent);mask-image:linear-gradient(90deg,transparent,#000 18%,#000 82%,transparent)}
.pulse path{stroke-width:2;opacity:.4}
.pillars{margin-top:-58px;gap:24px}
.pillar,.card,.box,.wide{border-radius:var(--r);box-shadow:var(--sh1)}
.pillar{padding:30px;transition:transform .3s var(--ease),box-shadow .3s var(--ease)}
.pillar:hover{transform:translateY(-4px);box-shadow:var(--sh2)}
.pillar .ic{margin-bottom:18px}
.card:hover{box-shadow:var(--sh2)}
.card div{padding:16px 20px 22px}
.sh{margin-bottom:34px}
.sh h2{margin:0}
.wide{display:grid;grid-template-columns:minmax(0,300px) 1fr;gap:0;background:#fff;border:1px solid var(--line);overflow:hidden;transition:box-shadow .3s var(--ease),transform .3s var(--ease)}
.wide:hover{box-shadow:var(--sh2);transform:translateY(-4px)}
.wide>a img{width:100%;height:100%;object-fit:cover;display:block;aspect-ratio:4/5}
.wide .wb{padding:34px 38px;display:flex;flex-direction:column;align-items:flex-start;justify-content:center;gap:4px}
.wide h3{font-size:1.7rem;margin:.4em 0 .3em}
.wide p{color:var(--muted);margin:0 0 20px;max-width:560px}
.wide .row{margin:0}
.more{margin-top:26px;text-align:center;color:var(--muted);font-size:.95rem}
@media(max-width:700px){.wide{grid-template-columns:1fr}.wide .wb{padding:24px}.wide>a img{aspect-ratio:4/3;object-position:top}}
.band .terms a.chip{display:inline-flex;align-items:center;gap:8px;border:1.5px solid rgba(255,255,255,.4);border-radius:999px;padding:9px 20px;font-family:Lora,serif;font-size:1.05rem;color:#fff;text-decoration:none;transition:background .2s,color .2s,transform .25s var(--ease),border-color .2s}
body.fa .band .terms a.chip{font-family:Vazirmatn,sans-serif}
.band .terms a.chip:hover{background:var(--gold);border-color:var(--gold);color:var(--ink);transform:translateY(-3px)}
.band .terms a.chip:after{content:"→";opacity:0;margin-inline-start:-6px;width:0;transition:all .2s}.band .terms a.chip:hover:after{opacity:1;width:auto;margin-inline-start:0}
body.fa .band .terms a.chip:after{content:"←"}
.band .terms{gap:12px}
.band{border-top:0}
.band:after{content:"";position:absolute;left:0;right:0;top:0;height:3px;background:linear-gradient(90deg,var(--gold),var(--crimson),var(--gold))}
.hello{background:linear-gradient(180deg,var(--paper),var(--sagel))}
.chipbar a{transition:all .2s}.chipbar a:hover{background:var(--crimson);color:#fff}
main{padding:56px 0 90px}main:has(.hello){padding-bottom:0}
/* footer */
footer{background:var(--ink) var(--pat-g);background-size:80px 80px;border-top:0;padding:0;position:relative;color:#CFC7BF}
footer:before{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--crimson),var(--gold),var(--crimson))}
footer .fgrid{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;padding-top:56px;padding-bottom:44px}
@media(max-width:760px){footer .fgrid{grid-template-columns:1fr;gap:30px;padding-top:40px;padding-bottom:30px}}
footer .fb{display:flex;align-items:center;gap:12px;margin-bottom:12px}footer .fb img{width:40px;height:40px}
footer .fb strong{font:700 1.35rem Lora,serif;color:#fff}body.fa footer .fb strong{font-family:Vazirmatn,serif}
footer h4{margin:0 0 14px;font:600 .75rem Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)}body.fa footer h4{letter-spacing:0;font-size:.9rem;font-family:Vazirmatn,sans-serif}
footer ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
footer a{color:#E9E1D8;text-decoration:none;transition:color .2s}footer a:hover{color:var(--gold)}
footer p{margin:0;max-width:340px;color:#B9B0A8}
footer .fbar{border-top:1px solid rgba(255,255,255,.12);padding:20px 0;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:.85rem;color:#B9B0A8;background:rgba(0,0,0,.18)}
footer .fbar .wrap{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;width:100%}
footer .fbar{display:block;padding:0}footer .fbar .wrap{padding-top:18px;padding-bottom:18px}
body.fa .hero h1{font-size:clamp(2.1rem,4.4vw,3.3rem)}.hero h1 em{white-space:nowrap}body.fa footer li[dir=ltr]{text-align:right}
.follow .btn{min-width:132px}@media(max-width:480px){.follow{display:grid;grid-template-columns:repeat(3,minmax(0,1fr))}.follow .btn{min-width:0;padding:0 6px;gap:6px;font-size:.88rem}}
.btn.soc svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.btn.soc{color:#fff;border:0}.btn.th svg{width:21px;height:21px}
.btn.ig{background:linear-gradient(45deg,#F9A24B 0%,#E1306C 50%,#833AB4 100%)}
.btn.th{background:#1b1b1b}.btn.xx{background:#000}
.btn.soc:hover{color:#fff;border-color:transparent;filter:brightness(1.1);box-shadow:0 8px 20px rgba(0,0,0,.28)}
.btn.ig:hover{background:linear-gradient(45deg,#F9A24B 0%,#E1306C 50%,#833AB4 100%)}.btn.th:hover{background:#1b1b1b}.btn.xx:hover{background:#000}
.btn.xx svg{width:22px;height:22px}.vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
/* motion */
.js .reveal{opacity:0;transform:translateY(18px);transition:opacity .7s var(--ease),transform .7s var(--ease)}
.js .reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.js .reveal{opacity:1;transform:none;transition:none}.btn,.card,.pillar,.wide,.langpick a,.chip{transition:none}}
@media(max-width:860px){section.s{padding:64px 0}.hero{padding:44px 0 120px}.pillars{margin-top:-64px}}
"""
JS = """document.documentElement.classList.add('js');if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.12});document.querySelectorAll('.reveal').forEach(function(x){io.observe(x)})}else{document.querySelectorAll('.reveal').forEach(function(x){x.classList.add('in')})}
document.querySelectorAll('.tabs').forEach(function(t){var bs=t.querySelectorAll('button');bs.forEach(function(b){b.addEventListener('click',function(){bs.forEach(function(x){x.setAttribute('aria-selected',x===b)});document.querySelectorAll('.lang').forEach(function(l){l.hidden=l.dataset.l!==b.dataset.l});})})});
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){var t=document.getElementById(b.dataset.copy).innerText;if(navigator.clipboard){navigator.clipboard.writeText(t);b.textContent='Copied'}})});"""
UI = {
 "en": {"nav":[("/","Home"),("/archive/","Archive"),("/topics/","Topics"),("/words/","Words to Know"),("/sources/","Sources and method"),("/about/","About")],
        "foot":"Educational content, not medical advice. For adults 18+.","follow":"Follow","explore":"Explore","read":"Read the post","readother":"فارسی","other":"فارسی","dl":"Download high resolution","cap":"Caption","src":"Sources","alt":"Image description (ALT text)","back":"← Archive","latest":"Latest posts","browse":"Browse the archive","all":"View all","eyebrow":"Food · Health · Evidence","follow_btn":"Follow us","latest_badge":"Latest",
        "pil":[("Evidence first","Primary sources and cautious wording. We say what research may suggest, not what it proves."),("Two languages","Every post in English and فارسی, written for each language, not just translated."),("Sources on every post","Each graphic names its sources and photo credits so you can check for yourself.")],
        "wtk_h":"Words to Know","wtk_p":"Short, plain-language explainers of the food and health terms you keep hearing, in English and Farsi.","wtk_btn":"Explore the glossary","fol_h":"Come say hello","fol_p":"New posts every day on Instagram, Threads and X."},
 "fa": {"nav":[("/","خانه"),("/archive/","آرشیو"),("/topics/","موضوع‌ها"),("/words/","واژه‌های مهم"),("/sources/","منبع‌ها و روش"),("/about/","درباره")],
        "foot":"محتوای آموزشی است و توصیه پزشکی نیست. برای بزرگسالان ۱۸ سال به بالا.","follow":"ما را دنبال کنید","explore":"بخش‌ها","read":"خواندن پست","readother":"English","other":"English","dl":"دریافت با کیفیت بالا","cap":"کپشن","src":"منبع‌ها","alt":"متن جایگزین تصویر","back":"آرشیو ←","latest":"تازه‌ترین پست‌ها","browse":"مشاهده آرشیو","all":"همه پست‌ها","eyebrow":"غذا · سلامت · شواهد","follow_btn":"ما را دنبال کنید","latest_badge":"تازه",
        "pil":[("اول شواهد","منبع‌های اصلی و زبانی محتاط. می‌گوییم پژوهش‌ها چه چیزی را نشان می‌دهند، نه اینکه چه چیزی را ثابت می‌کنند."),("دو زبان","هر پست به فارسی و انگلیسی، برای هر زبان نوشته شده و فقط ترجمه نیست."),("منبع در هر پست","هر تصویر منبع‌ها و اعتبار عکس را نام می‌برد تا خودتان بررسی کنید.")],
        "wtk_h":"واژه‌های مهم","wtk_p":"توضیح‌های کوتاه و ساده از اصطلاح‌های غذا و سلامت که مدام می‌شنوید، به فارسی و انگلیسی.","wtk_btn":"دیدن واژه‌نامه","fol_h":"به ما سر بزنید","fol_p":"هر روز پست تازه در اینستاگرام، تردز و ایکس."},
}
VER = hashlib.md5((CSS + JS).encode()).hexdigest()[:8]
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
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/site.css?v={VER}"></head><body class="{lang}">
<header class="top"><div class="wrap"><a class="brand" href="{P}/"><img src="/assets/logo.svg" alt="">{E_(sitename)}</a><nav>{nav}<a class="langsw" href="{pre(ol)}{path}" hreflang="{ol}" lang="{ol}">{u['other']}</a></nav></div></header>
<main><div class="wrap">{body}</div></main>
<footer><div class="wrap fgrid"><div><div class="fb"><img src="/assets/logo.svg" alt=""><strong>{E_(sitename)}</strong></div><p>{E_(site['tagline_fa'] if lang=='fa' else site['tagline'])}</p></div>
<div><h4>{u['explore']}</h4><ul>{''.join(f'<li><a href="{P}{x}">{n}</a></li>' for x, n in u['nav'][1:])}</ul></div>
<div><h4>{u['follow']}</h4><ul><li><a href="https://www.instagram.com/pomandpulse/">Instagram</a></li><li><a href="https://www.threads.net/@pomandpulse">Threads</a></li><li><a href="https://x.com/pomandpulse">X</a></li><li dir="ltr" style="color:#B9B0A8">{E_(site['handle'])}</li></ul></div></div>
<div class="fbar"><div class="wrap"><span>{u['foot']}</span><span dir="ltr">© {E_(sitename)}</span></div></div></footer>
<script src="/assets/site.js?v={VER}"></script></body></html>"""

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
    body = f"""<div class="meta"><a href="{pre(l)}/archive/">{u['back']}</a><span class="tag">{E_(T(p,'topic',l))}</span><span>{fmt(p['date'],l)}</span></div>
<div class="piece"><div class="pic"><img class="main" src="/img/{p['id']}_{l}.jpg" width="1280" height="1600" alt="{E_(T(p,'alt',l))}"></div><div>
<h1>{E_(T(p,'title',l))}</h1>
<div class="row"><a class="btn" href="/dl/{p['id']}_{l}_hi.jpg" download>{u['dl']} · JPG</a><a class="btn alt" href="/dl/{p['id']}_{l}_hi.pdf" download>PDF</a></div>
<div class="box cap"><h3>{u['cap']}</h3><p id="cap">{E_(T(p,'caption',l))}</p><p style="margin-top:12px"><button class="btn alt" style="padding:6px 16px" data-copy="cap">{"کپی" if l=="fa" else "Copy caption"}</button></p></div>
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
        feat = ps[0] if ps else None
        icons = ['<svg viewBox="0 0 24 24"><path d="M4 12h4l2-6 4 12 2-6h4"/></svg>', '<svg viewBox="0 0 24 24"><path d="M4 5h9v7H8l-3 3v-3H4zM15 10h5v7h-1v3l-3-3h-4v-3"/></svg>', '<svg viewBox="0 0 24 24"><path d="M6 3h9l3 3v15H6zM9 11h6M9 15h6M9 7h3"/></svg>']
        pil = "".join(f'<div class="pillar reveal"><div class="ic">{icons[i]}</div><h3>{E_(t)}</h3><p>{E_(d)}</p></div>' for i, (t, d) in enumerate(u["pil"]))
        tagl = site["tagline_fa"] if fa else site["tagline"]
        h1 = ("غذا و سلامت، <em>با شواهد</em>" if fa else "Food and health, explained <em>with evidence</em>")
        lead = ("پست‌های گرم، کنجکاوانه و مبتنی بر شواهد درباره غذا و سلامت، به فارسی و انگلیسی." if fa else 'Warm, curious posts about what we eat and what the research says, in English and فارسی.')
        trust = ("<span>منبع‌های اصلی</span><span>زبان محتاط</span><span>بزرگسالان ۱۸+</span>" if fa else "<span>Primary sources</span><span>Cautious language</span><span>Adults 18+</span>")
        pick = ('<span>خواندن به</span><a class="cur" href="/fa/" lang="fa">فارسی</a><a href="/" lang="en">English</a>' if fa else '<span>Read in</span><a class="cur" href="/" lang="en">English</a><a href="/fa/" lang="fa">فارسی</a>')
        pulse = '<svg class="pulse" viewBox="0 0 1200 60" preserveAspectRatio="none"><path d="M0 34 H430 L455 34 L475 8 L505 56 L530 22 L545 34 H1200"/></svg>'
        ft = f'<a class="feature" href="{pre(l)}/p/{feat["slug"]}/"><span class="badge">{u["latest_badge"]}</span><img src="/img/{feat["id"]}_{l}.jpg" width="1280" height="1600" alt="{E_(T(feat,"alt",l))}"></a>' if feat else ""
        socials = '<a class="btn soc ig" href="https://www.instagram.com/pomandpulse/"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".8" fill="currentColor"/></svg>Instagram</a><a class="btn soc th" href="https://www.threads.net/@pomandpulse"><svg viewBox="0 0 24 24"><path d="M17.5 11.2c-.4-3.4-2.4-5.2-5.6-5.2-3.2 0-5.4 2.3-5.4 6s2.2 6 5.6 6c2.8 0 4.6-1.5 4.6-3.6 0-2.3-2-3.3-4.4-3.3-1.6 0-2.8.8-2.8 2 0 1 .9 1.7 2.1 1.7 1.8 0 2.8-1.2 2.8-3.4"/></svg>Threads</a><a class="btn soc xx" href="https://x.com/pomandpulse"><svg viewBox="0 0 24 24"><path d="M5 4l14 16M19 4L5 20"/></svg><span class="vh">X</span></a>'
        words = ["Glycemic index","Fiber","Probiotic","Antioxidant","Sodium"] if not fa else ["شاخص گلایسمی","فیبر","پروبیوتیک","آنتی‌اکسیدان","سدیم"]
        if len(ps) == 1:
            q = ps[0]
            cap = " ".join(w_ for w_ in T(q, "caption", l).split() if not w_.startswith("#")); tt = T(q, "title", l)
            if cap.startswith(tt): cap = cap[len(tt):].strip()
            lat = f'<div class="wide reveal"><a href="{pre(l)}/p/{q["slug"]}/"><img src="/img/{q["id"]}_{l}_t.jpg" alt="{E_(T(q,"alt",l)[:140])}"></a><div class="wb"><span class="tag">{E_(T(q,"topic",l))}</span><h3>{E_(T(q,"title",l))}</h3><p>{E_(cap)}</p><div class="row"><a class="btn" href="{pre(l)}/p/{q["slug"]}/">{u["read"]}</a><a class="btn alt" href="{pre("en" if fa else "fa")}/p/{q["slug"]}/" lang="{"en" if fa else "fa"}">{u["readother"]}</a></div></div></div><p class="more">{"پست‌های بیشتر به‌زودی؛ در شبکه‌های اجتماعی ما را دنبال کنید." if fa else "More posts arrive daily. Follow along on social."}</p>'
        else:
            lat = '<div class="grid">' + "".join(card(q, l).replace('class="card"', 'class="card reveal"') for q in ps[:3]) + '</div>'
        home = f"""</div><section class="hero"><div class="wrap"><div><div class="eyebrow">{u['eyebrow']}</div><h1>{h1}</h1><div class="trust">{trust}</div><p class="lead">{lead}</p><div class="cta"><a class="btn" href="{pre(l)}/archive/">{u['browse']}</a><a class="btn alt" href="https://www.instagram.com/pomandpulse/">{u['follow_btn']}</a></div><div class="langpick">{pick}</div></div>{ft}</div>{pulse}</section>
<div class="wrap"><div class="pillars">{pil}</div></div>
<section class="s"><div class="wrap"><div class="sh reveal"><h2>{u['latest']}</h2><a href="{pre(l)}/archive/">{u['all']} →</a></div>{lat}</div></section>
<section class="band s"><div class="wrap"><div class="reveal"><h2>{u['wtk_h']}</h2><p>{u['wtk_p']}</p><a class="btn gold" href="{pre(l)}/words/">{u['wtk_btn']}</a></div><div class="terms reveal">{''.join(f'<a class="chip" href="{pre(l)}/words/">{E_(x)}</a>' for x in words)}</div></div></section>
<section class="s hello"><div class="wrap reveal" style="text-align:center"><h2>{u['fol_h']}</h2><p style="color:var(--muted);margin:0 0 26px">{u['fol_p']}</p><div class="follow" style="justify-content:center">{socials}</div></div></section><div class="wrap">"""
        w("/", page(f'{N} | {tagl}', home, "/", site, None, None, l), l)
        w("/archive/", page(f'{"آرشیو" if fa else "Archive"} | {N}', f'<div class="pagehead"><h1>{"آرشیو" if fa else "Archive"}</h1><p>{"همه پست‌ها، تازه‌ترین در بالا." if fa else "Every post, newest first."}</p></div><div class="grid">{grid}</div>', "/archive/", site, None, None, l), l)
        topics = {}
        for p in ps: topics.setdefault(T(p, "topic", l), []).append(p)
        tb = f'<div class="pagehead"><h1>{"موضوع‌ها" if fa else "Topics"}</h1></div><div class="chipbar">' + "".join(f'<a href="#{slug(t)}">{E_(t)}</a>' for t in sorted(topics)) + '</div>' + "".join(f'<h2 id="{slug(t)}" style="margin-top:36px">{E_(t)}</h2><div class="grid">{"".join(card(p,l) for p in v)}</div>' for t, v in sorted(topics.items()))
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

"""
CANOBURO ANALİZ - Streamlit App (ULTIMATE UI V4.2)
Force-reload on JSON change and manual refresh button.
"""

import streamlit as st
import json
import math
import os
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="CANOBURO ANALİZ", layout="wide")

# --- Styles ---
st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 1rem; }
    
    /* Card Style for Metrics */
    .stat-card {
        background: #1a1a2e;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 8px;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #fff;
        line-height: 1.1;
    }
    .stat-label {
        font-size: 0.73rem;
        color: #999;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Section Headers */
    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        margin: 1.8rem 0 1rem 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #4CAF50;
        display: flex;
        align-items: center;
    }
    
    /* Team Header Box */
    .team-banner {
        padding: 0.8rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        font-size: 1.4rem;
        font-weight: bold;
        background: #16213e;
        border: 1px solid #333;
    }

    /* Coupon Card */
    .coupon-card { 
        background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
        border: 2px solid #4CAF50; border-radius: 15px; padding: 25px; margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    
    .info-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        height: 100%;
    }
    .info-title { font-size: 0.8rem; color: #999; text-transform: uppercase; margin-bottom: 5px; }
    .info-content { font-size: 0.95rem; color: #fff; font-weight: 500; }

    [data-testid="stSidebar"] { min-width: 350px; max-width: 350px; }
</style>
""", unsafe_allow_html=True)

# --- Helpers ---
def metric_card(label, value, target=st):
    card_html = f"""
    <div class="stat-card">
        <div class="stat-label">{label}</div>
        <div class="stat-value">{value}</div>
    </div>
    """
    target.markdown(card_html, unsafe_allow_html=True)

def content_card(label, content, icon, target=st):
    target.markdown(f"""
    <div class="info-card">
        <div class="info-title">{icon} {label}</div>
        <div class="info-content">{content}</div>
    </div>
    """, unsafe_allow_html=True)

# --- Load Data with File-Watch ---
def get_file_mtime(filepath):
    try:
        return os.path.getmtime(filepath)
    except: return 0

@st.cache_data
def load_data(mtime):
    if os.path.exists("nba_data.json"):
        with open("nba_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# Sidebar Refresh Logic
if st.sidebar.button("🔄 Verileri Yenile (Cache Temizle)"):
    st.cache_data.clear()
    st.rerun()

data_file = "nba_data.json"
mtime = get_file_mtime(data_file)
data = load_data(mtime)

st.sidebar.title("🏀 CANOBURO ANALİZ")
if data:
    st.sidebar.caption(f"🔄 Güncelleme: {data['last_updated'][:16]}")
    unique_dates = sorted(list(set(g['api_date'] for g in data['games'])))
    selected_date = st.sidebar.selectbox("📅 Tarih Seçin", unique_dates, index=len(unique_dates)-1 if unique_dates else 0)
    date_games = [g for g in data['games'] if g['api_date'] == selected_date]
    if not date_games:
        st.sidebar.warning("Bu tarihte maç bulunamadı.")
        st.stop()
    game_labels = [f"⚔️ {g['visitor']['name']} @ {g['home']['name']}" for g in date_games]
    selected_game_label = st.sidebar.radio("🔥 Maç Seçimi", game_labels, key="match_select")
    game = date_games[game_labels.index(selected_game_label)]
else:
    st.error("Veri dosyası bulunamadı. Lütfen prefetch scriptini çalıştırın.")
    st.stop()

# --- Main Page ---
home, visitor = game['home'], game['visitor']
h2h_logs, h2h_stats = game.get('h2h_logs', []), game.get('h2h_stats', {})

st.title(f"{visitor['name']} @ {home['name']}")
st.caption(f"📅 {game['api_date']} | 🏟️ {home['name']} Home | Status: {game['game_time']}")

# =============================================================================
# TEMEL İSTATİSTİKLER (8 Specific Cards)
# =============================================================================
st.markdown('<div class="section-title">📊 Temel İstatistikler (Son 10 Maç)</div>', unsafe_allow_html=True)
v_col, h_col = st.columns(2)

def display_basic_stats(col, team, color_emoji):
    s = team['stats']
    with col:
        st.markdown(f'<div class="team-banner">{color_emoji} {team["name"]}</div>', unsafe_allow_html=True)
        # MS Row (4 Cards)
        c1, c2, c3, c4 = st.columns(4)
        metric_card("MS ORT", s.get('pts_avg', 0), c1)
        metric_card("MS MIN", s.get('pts_min', 0), c2)
        metric_card("MS MAX", s.get('pts_max', 0), c3)
        metric_card("MS GAL", f"{s.get('wins', 0)}/10", c4)
        
        # 1Y Row (4 Cards)
        c1, c2, c3, c4 = st.columns(4)
        metric_card("1Y ORT", s.get('pts_1h_avg', 0), c1)
        metric_card("1Y MIN", s.get('pts_1h_min', 0), c2)
        metric_card("1Y MAX", s.get('pts_1h_max', 0), c3)
        metric_card("IY GAL", f"{s.get('wins_1h', 0)}/10", c4)

display_basic_stats(v_col, visitor, "🔵")
display_basic_stats(h_col, home, "🟢")

# =============================================================================
# QUARTER ANALYSIS (Differential Focused)
# =============================================================================
st.markdown('<div class="section-title">📈 Çeyrek Analizi (Averaj & Verimlilik)</div>', unsafe_allow_html=True)
v_q_col, h_q_col = st.columns(2)

def display_quarters(col, team):
    s = team['stats']
    with col:
        st.markdown(f"**{team['name']}**")
        c1, c2, c3, c4 = st.columns(4)
        
        diffs = {}
        for q in ['q1','q2','q3','q4']:
            scored = s.get(q, 0)
            allowed = s.get(f'opp_{q}', 0)
            diff = round(scored - allowed, 1)
            diffs[q] = diff
            
            with (c1 if q=='q1' else c2 if q=='q2' else c3 if q=='q3' else c4):
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">{q.upper()}</div>
                    <div style="font-size: 1.3rem; color: #fff; font-weight:bold;">{scored}</div>
                    <div style="font-size: 0.85rem; color: #999;">{allowed} Y</div>
                    <div style="font-size: 0.75rem; color: {'#4CAF50' if diff >= 0 else '#F44336'}; margin-top:2px; font-weight:bold;">
                        ({'+' if diff >= 0 else ''}{diff})
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if any(v != 0 for v in diffs.values()):
            best_q = max(diffs, key=diffs.get).upper()
            worst_q = min(diffs, key=diffs.get).upper()
            st.markdown(f"🌟 En Verimli: **{best_q}** ({'+' if diffs[best_q.lower()] > 0 else ''}{diffs[best_q.lower()]}) | ⚠️ En Zayıf: **{worst_q}** ({diffs[worst_q.lower()]})")

display_quarters(v_q_col, visitor)
display_quarters(h_q_col, home)

# =============================================================================
# LEADERS & INJURIES (Modern UI)
# =============================================================================
st.markdown('<div class="section-title">🌟 Oyuncu Performansı ve Sakatlıklar</div>', unsafe_allow_html=True)
v_l_col, h_l_col = st.columns(2)

def display_modern_info(col, team):
    with col:
        st.markdown(f"**{team['name']} Bilgi Merkezi**")
        l = team['leaders']
        
        def format_top2(key):
            players = l.get(key, [])
            if not players: return "Veri Yok"
            p1 = f"<b>{players[0]['name']}</b> ({players[0]['val']})"
            p2 = f"<br><b>{players[1]['name']}</b> ({players[1]['val']})" if len(players) > 1 else ""
            return f"{p1}{p2}"

        # 2x2 Grid of cards
        row1 = st.columns(2)
        content_card("Sayı Liderleri", format_top2('pts'), "🏀", row1[0])
        content_card("Ribaund Liderleri", format_top2('reb'), "🔄", row1[1])
        
        row2 = st.columns(2)
        content_card("Asist Liderleri", format_top2('ast'), "🎯", row2[0])
        
        inj = team.get('injuries', [])
        inj_html = "<br>".join([f"• {i['player']} ({i['status'][:15]})" for i in inj[:3]]) if inj else "Sakatlık Yok"
        content_card("Sakatlık Raporu", inj_html, "🏥", row2[1])

display_modern_info(v_l_col, visitor)
display_modern_info(h_l_col, home)

# =============================================================================
# H2H ANALYSIS
# =============================================================================
st.markdown('<div class="section-title">⚔️ H2H: Karşılıklı Maçlar (Bu Sezon)</div>', unsafe_allow_html=True)
if h2h_logs:
    col1, col2, col3 = st.columns(3)
    metric_card("MAÇ SAYISI", len(h2h_logs), col1)
    metric_card(f"{visitor['name'][:15]} H2H", h2h_stats.get('visitor_avg', 0), col2)
    metric_card(f"{home['name'][:15]} H2H", h2h_stats.get('home_avg', 0), col3)
    
    h2h_df = pd.DataFrame([{
        'Tarih': l['date'],
        f'{visitor["name"]}': l['t2_pts'],
        f'{home["name"]}': l['t1_pts'],
        f'{visitor["name"]} 1Y': l['t2_1h'],
        f'{home["name"]} 1Y': l['t1_1h']
    } for l in h2h_logs])
    st.dataframe(h2h_df, use_container_width=True, hide_index=True)
else:
    st.info("Bu sezon aralarında maç oynanmamış.")

# =============================================================================
# COUPON SECTION
# =============================================================================
st.markdown('<div class="section-title">🎫 Algoritmik Kupon Önerileri</div>', unsafe_allow_html=True)
h_avg, v_avg = home['stats'].get('pts_avg', 0), visitor['stats'].get('pts_avg', 0)
h_h2h, v_h2h = h2h_stats.get('home_avg', 0), h2h_stats.get('visitor_avg', 0)
h_cons = min(h_avg, h_h2h) if h_h2h > 0 else h_avg
v_cons = min(v_avg, v_h2h) if v_h2h > 0 else v_avg
h_base, v_base = math.floor(h_cons), math.floor(v_cons)
h_marg, v_marg = h_base - home['stats'].get('pts_min', 0), v_base - visitor['stats'].get('pts_min', 0)

if h_marg <= v_marg: t_pick, t_base, t_marg = home, h_base, h_marg
else: t_pick, t_base, t_marg = visitor, v_base, v_marg

if t_marg < 10: s_label = "Çok Stabil"
elif t_marg <= 20: s_label = "Ortalama"
else: s_label = "Çok Stabil Değil"

total_base = math.floor(min(h_avg + v_avg, h_h2h + v_h2h if h_h2h > 0 else 999))

st.markdown(f"""
<div class="coupon-card">
    <div style="display:flex; justify-content:space-around; align-items:center; text-align:center; flex-wrap:wrap;">
        <div style="flex:1; min-width:250px;">
            <p style="color:#999; margin-bottom:5px;">🎯 TAKIM TOPLAM ÜST</p>
            <h2 style="color:#4CAF50; margin-bottom:0;">{t_pick['name']}</h2>
            <h1 style="color:#fff; margin-top:5px;">{t_base - 0.5} ÜST</h1>
            <p style="font-size:0.8rem; color:#888; margin-bottom:0;">Stabilite Marjı: {t_marg}</p>
            <p style="font-size:0.75rem; color:#4CAF50; font-weight:bold; margin-top:0;">({s_label})</p>
        </div>
        <div style="width:2px; height:80px; background:#444; margin:0 20px;"></div>
        <div style="flex:1; min-width:250px;">
            <p style="color:#999; margin-bottom:5px;">🏟️ MAÇ SONU TOPLAM ÜST</p>
            <h1 style="color:#fff; margin-bottom:5px;">{total_base - 1.5} ÜST</h1>
            <h2 style="color:#81C784; margin-top:0;">{total_base - 2.5} ÜST (Banko)</h2>
            <p style="font-size:0.8rem; color:#888;">Barem: {total_base}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# GAME LOGS
# =============================================================================
st.markdown('<div class="section-title">📚 Son 10 Maç Geçmişi</div>', unsafe_allow_html=True)
v_l, h_l = st.columns(2)
def show_log(col, team):
    with col:
        st.write(f"**{team['name']}**")
        if team['last10_logs']:
            df = pd.DataFrame(team['last10_logs'])[['date', 'matchup', 'wl', 'pts', 'opp_pts', 'pts_1h', 'opp_pts_1h']].copy()
            df.columns = ['Tarih', 'Maç', 'G/M', 'Sayı', 'Rakip', '1Y', '1Y Rakip']
            st.dataframe(df, use_container_width=True, hide_index=True)
show_log(v_l, visitor)
show_log(h_l, home)

st.divider()
st.caption("CANOBURO ANALİZ © 2026 | NBA Verileri: swar/nba_api")

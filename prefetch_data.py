"""
CANOBURO ANALİZ - Prefetch Script (ELITE VERSION)
Expanded cache window and additional stat metrics for UI cards.
"""

import json
import math
import time
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
from nba_api.stats.static import teams
from nba_api.stats.endpoints import scoreboardv2, leaguegamefinder, teamplayerdashboard
import pandas as pd

# --- Config ---
SEASON_YEAR = "2025-26"
ISTANBUL_TZ = pytz.timezone('Europe/Istanbul')
OUTPUT_FILE = "nba_data.json"
QUARTER_CACHE = {} 

def safe_api_call(endpoint_func, **kwargs):
    for attempt in range(3):
        try:
            res = endpoint_func(**kwargs)
            time.sleep(0.4)
            return res
        except Exception as e:
            time.sleep((attempt+1)*2)
    return None

def get_team_map():
    all_teams = teams.get_teams()
    return {t['id']: t['full_name'] for t in all_teams}

TEAM_MAP = get_team_map()

# --- Bulk Scoreboard Fetch ---
def build_quarter_cache(days=120):
    """Expanded to 120 days to cover almost all teams' last 10 games."""
    print(f"[Prefetch] Building quarter cache for last {days} days...")
    today = datetime.now(ISTANBUL_TZ).date()
    for i in range(days + 1):
        d = today - timedelta(days=i)
        print(f"  Fetching {d}...", end="\r")
        board = safe_api_call(scoreboardv2.ScoreboardV2, game_date=d.strftime('%Y-%m-%d'))
        if not board: continue
        lines = board.line_score.get_data_frame()
        if lines.empty: continue
        
        for _, row in lines.iterrows():
            game_id = row['GAME_ID']
            team_id = int(row['TEAM_ID'])
            if game_id not in QUARTER_CACHE: QUARTER_CACHE[game_id] = {}
            
            def safe_get(key):
                val = row.get(key, 0)
                return int(val) if pd.notna(val) else 0
                
            q1, q2, q3, q4 = safe_get('PTS_QTR1'), safe_get('PTS_QTR2'), safe_get('PTS_QTR3'), safe_get('PTS_QTR4')
            QUARTER_CACHE[game_id][team_id] = {
                'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4,
                'pts_1h': q1 + q2
            }
    print(f"\n[Prefetch] Quarter cache built: {len(QUARTER_CACHE)} games.")

def get_schedule(date_obj):
    board = safe_api_call(scoreboardv2.ScoreboardV2, game_date=date_obj.strftime('%Y-%m-%d'))
    if not board: return []
    header = board.game_header.get_data_frame()
    if header.empty: return []
    
    games = []
    for _, row in header.iterrows():
        games.append({
            'game_id': row['GAME_ID'],
            'home_id': int(row['HOME_TEAM_ID']),
            'visitor_id': int(row['VISITOR_TEAM_ID']),
            'home_name': TEAM_MAP.get(row['HOME_TEAM_ID'], "Unknown"),
            'visitor_name': TEAM_MAP.get(row['VISITOR_TEAM_ID'], "Unknown"),
            'home_abbr': row.get('HOME_TEAM_ABBREVIATION', ''),
            'visitor_abbr': row.get('VISITOR_TEAM_ABBREVIATION', ''),
            'game_time': row.get('GAME_STATUS_TEXT', ''),
            'api_date': date_obj.strftime('%Y-%m-%d')
        })
    return games

def get_team_l10(team_id):
    obj = safe_api_call(leaguegamefinder.LeagueGameFinder, team_id_nullable=team_id, season_nullable=SEASON_YEAR)
    if not obj: return []
    df = obj.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    df = df.sort_values("GAME_DATE", ascending=False).head(10)
    
    logs = []
    for _, row in df.iterrows():
        gid = row['GAME_ID']
        qs = QUARTER_CACHE.get(gid, {})
        team_q = qs.get(team_id, {})
        
        # Robust opponent lookup
        opp_q = {}
        for k, v in qs.items():
            if k != team_id:
                opp_q = v
                break
        
        pts = int(row['PTS'])
        pm = row['PLUS_MINUS'] if pd.notna(row['PLUS_MINUS']) else 0
        opp_pts = int(pts - pm)
        
        logs.append({
            'game_id': gid, 'date': row['GAME_DATE'].strftime('%Y-%m-%d'),
            'matchup': row['MATCHUP'], 'is_home': 'vs.' in row['MATCHUP'], 'wl': row['WL'].strip(),
            'pts': pts, 'opp_pts': opp_pts,
            'pts_1h': team_q.get('pts_1h', 0), 'opp_pts_1h': opp_q.get('pts_1h', 0),
            'q1': team_q.get('q1', 0), 'q2': team_q.get('q2', 0), 'q3': team_q.get('q3', 0), 'q4': team_q.get('q4', 0),
            'opp_q1': opp_q.get('q1', 0), 'opp_q2': opp_q.get('q2', 0), 'opp_q3': opp_q.get('q3', 0), 'opp_q4': opp_q.get('q4', 0)
        })
    return logs

# (Rest of the helper functions remain similar but stats computation is updated)

def compute_stats(logs):
    if not logs: return {}
    pts = [g['pts'] for g in logs]
    pts1h = [g['pts_1h'] for g in logs if g['pts_1h'] > 0]
    
    def q_avg(key):
        vals = [g[key] for g in logs if g[key] > 0]
        return round(sum(vals)/len(vals), 1) if vals else 0

    return {
        'games_count': len(logs), 
        'pts_avg': round(sum(pts)/len(pts), 1),
        'pts_max': max(pts) if pts else 0,
        'pts_min': min(pts) if pts else 0,
        'pts_1h_avg': round(sum(pts1h)/len(pts1h), 1) if pts1h else 0,
        'pts_1h_max': max(pts1h) if pts1h else 0,
        'pts_1h_min': min(pts1h) if pts1h else 0,
        'wins': sum(1 for g in logs if g['wl'] == 'W'),
        'wins_1h': sum(1 for g in logs if g['pts_1h'] > g['opp_pts_1h'] and g['pts_1h'] > 0),
        'q1': q_avg('q1'), 'q2': q_avg('q2'), 'q3': q_avg('q3'), 'q4': q_avg('q4'),
        'opp_q1': q_avg('opp_q1'), 'opp_q2': q_avg('opp_q2'), 'opp_q3': q_avg('opp_q3'), 'opp_q4': q_avg('opp_q4'),
    }

# Keep original get_h2h, get_leaders, get_injuries
def get_h2h(t1_id, t2_id):
    obj = safe_api_call(leaguegamefinder.LeagueGameFinder, team_id_nullable=t1_id, vs_team_id_nullable=t2_id, season_nullable=SEASON_YEAR)
    if not obj: return []
    df = obj.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    logs = []
    for _, row in df.iterrows():
        gid = row['GAME_ID']
        qs = QUARTER_CACHE.get(gid, {})
        t1_q, t2_q = qs.get(t1_id, {}), qs.get(t2_id, {})
        logs.append({
            'date': row['GAME_DATE'].strftime('%Y-%m-%d'),
            't1_pts': int(row['PTS']), 't2_pts': int(row['PTS'] - (row['PLUS_MINUS'] if pd.notna(row['PLUS_MINUS']) else 0)),
            't1_1h': t1_q.get('pts_1h', 0), 't2_1h': t2_q.get('pts_1h', 0)
        })
    return logs

def get_leaders(team_id):
    obj = safe_api_call(teamplayerdashboard.TeamPlayerDashboard, team_id=team_id, season=SEASON_YEAR, per_mode_detailed='PerGame')
    if not obj: return {'pts':[], 'reb':[], 'ast':[]}
    df = obj.get_data_frames()[1]
    def top2(col):
        top = df.sort_values(col, ascending=False).head(2)
        return [{'name': r['PLAYER_NAME'], 'val': round(r[col], 1)} for _, r in top.iterrows()]
    return {'pts': top2('PTS'), 'reb': top2('REB'), 'ast': top2('AST')}

def get_injuries(team_name):
    try:
        url = "https://www.cbssports.com/nba/injuries/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        search = team_name.split(' ')[0].lower()
        for table in soup.find_all('div', class_='TableBaseWrapper'):
            header = table.find('span', class_='TeamName')
            if header and search in header.text.lower():
                inj = []
                for row in table.find_all('tr', class_='TableBase-bodyTr'):
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        p_tag = cols[0].find('span', class_='CellPlayerName--long')
                        p = p_tag.text.strip() if p_tag else cols[0].text.strip()
                        inj.append({'player': p, 'status': cols[-1].text.strip()})
                return inj
        return []
    except: return []

def main():
    now = datetime.now(ISTANBUL_TZ)
    print(f"[Prefetch] Start: {now.isoformat()}")
    build_quarter_cache(120) 
    dates = [now.date() - timedelta(days=1), now.date(), now.date() + timedelta(days=1)]
    raw = []
    for d in dates: raw.extend(get_schedule(d))
    seen = set()
    uniq = [g for g in raw if not (g['game_id'] in seen or seen.add(g['game_id']))]
    enriched = []
    for i, g in enumerate(uniq):
        print(f"  [{i+1}/{len(uniq)}] {g['visitor_name']} @ {g['home_name']}")
        h_id, v_id = g['home_id'], g['visitor_id']
        h_l10, v_l10 = get_team_l10(h_id), get_team_l10(v_id)
        h2h = get_h2h(h_id, v_id)
        h_stats, v_stats = compute_stats(h_l10), compute_stats(v_l10)
        h2h_avg = {'home_avg': round(sum(x['t1_pts'] for x in h2h)/len(h2h), 1), 'visitor_avg': round(sum(x['t2_pts'] for x in h2h)/len(h2h), 1)} if h2h else {}
        enriched.append({
            'game_id': g['game_id'], 'api_date': g['api_date'], 'game_time': g['game_time'],
            'home': {'id': h_id, 'name': g['home_name'], 'last10_logs': h_l10, 'stats': h_stats, 'leaders': get_leaders(h_id), 'injuries': get_injuries(g['home_name'])},
            'visitor': {'id': v_id, 'name': g['visitor_name'], 'last10_logs': v_l10, 'stats': v_stats, 'leaders': get_leaders(v_id), 'injuries': get_injuries(g['visitor_name'])},
            'h2h_logs': h2h, 'h2h_stats': h2h_avg
        })
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump({'last_updated': now.isoformat(), 'games': enriched}, f, ensure_ascii=False, indent=2)
    print(f"[Prefetch] Saved {len(enriched)} games.")

if __name__ == "__main__": main()

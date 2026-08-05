import json, os, sys
from datetime import datetime, timedelta
import requests

CLIENT_ID = os.environ['STRAVA_CLIENT_ID']
CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['STRAVA_REFRESH_TOKEN']

resp = requests.post('https://www.strava.com/oauth/token', data={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'refresh_token',
    'refresh_token': REFRESH_TOKEN,
})
if not resp.ok:
    print(f"Token refresh failed: {resp.status_code} {resp.text}", file=sys.stderr)
    sys.exit(1)
access_token = resp.json()['access_token']
print("Token refreshed")

type_map = {
    'Run': 'ラン', 'VirtualRun': 'ラン', 'TrailRun': 'ラン',
    'Treadmill': 'トレッドミル',
    'Ride': 'ロードサイクリング',
    'VirtualRide': '仮想サイクリング',
    'MountainBikeRide': 'マウンテンバイク',
    'Swim': 'プールスイム',
    'Walk': 'ウォーク',
    'Workout': '筋力トレーニング',
    'WeightTraining': '筋力トレーニング',
}

days = 152
after = int((datetime.now() - timedelta(days=days)).timestamp())

activities = []
page = 1
headers = {'Authorization': f'Bearer {access_token}'}
while True:
    r = requests.get(
        'https://www.strava.com/api/v3/athlete/activities',
        headers=headers,
        params={'after': after, 'per_page': 100, 'page': page},
    )
    if not r.ok:
        print(f"Fetch failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    batch = r.json()
    if not batch:
        break
    activities.extend(batch)
    if len(batch) < 100:
        break
    page += 1

print(f"Fetched {len(activities)} activities")

out = []
for a in activities:
    jp_type = type_map.get(a.get('type'), a.get('type') or 'その他')
    date = (a.get('start_date_local') or '')[:10]
    time_min = round((a.get('moving_time') or 0) / 60, 2)
    if not date or time_min <= 0:
        continue
    avg_hr = a.get('average_heartrate')
    max_hr = a.get('max_heartrate')
    np_val = a.get('weighted_average_watts')
    out.append({
        'type': jp_type, 'date': date,
        'dist': round((a.get('distance') or 0) / 1000, 3),
        'time': time_min,
        'avgHR': int(avg_hr) if avg_hr else None,
        'maxHR': int(max_hr) if max_hr else None,
        'np': int(np_val) if np_val else None,
        'tss': 0, 'p20': None,
        'name': a.get('name', ''),
    })

out.sort(key=lambda x: x['date'], reverse=True)
if out:
    print(f"Date range: {out[-1]['date']} to {out[0]['date']}")

with open('strava_activities.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"Saved {len(out)} activities")

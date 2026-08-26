import json, os, sys
from datetime import datetime, timedelta
from garminconnect import Garmin

email = os.environ.get('GARMIN_EMAIL')
password = os.environ.get('GARMIN_PASSWORD')

if not email or not password:
    print("GARMIN_EMAIL and GARMIN_PASSWORD must be set before running this script.", file=sys.stderr)
    print("Example:", file=sys.stderr)
    print("  set GARMIN_EMAIL=your_email@example.com", file=sys.stderr)
    print("  set GARMIN_PASSWORD=your_password", file=sys.stderr)
    print("  python fetch_garmin.py", file=sys.stderr)
    sys.exit(1)

try:
    client = Garmin(email, password)
    client.login()
    print("Login OK")
except Exception as e:
    print(f"Login failed: {e}", file=sys.stderr)
    sys.exit(1)

# Use tomorrow as end to catch JST activities (UTC+9 offset)
end = datetime.today() + timedelta(days=2)
start = end - timedelta(days=152)

print(f"Fetching {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

try:
    activities = client.get_activities_by_date(
        start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d')
    )
    print(f"Fetched {len(activities)} activities")
except Exception as e:
    print(f"Fetch failed: {e}", file=sys.stderr)
    sys.exit(1)

# Also get the 20 most recent to ensure latest are included
try:
    recent = client.get_activities(0, 20)
    print(f"Also fetched {len(recent)} recent activities")
    # Merge: add recent activities not already in the list
    existing_ids = {a.get('activityId') for a in activities}
    for a in recent:
        if a.get('activityId') not in existing_ids:
            activities.append(a)
            existing_ids.add(a.get('activityId'))
    print(f"Total after merge: {len(activities)} activities")
except Exception as e:
    print(f"Recent fetch warning: {e}")

type_map = {
    'running': '\u30e9\u30f3',
    'trail_running': '\u30e9\u30f3',
    'treadmill_running': '\u30c8\u30ec\u30c3\u30c9\u30df\u30eb',
    'cycling': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'road_biking': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'indoor_cycling': '\u5c4b\u5185\u30d0\u30a4\u30af',
    'virtual_ride': '\u4eee\u60f3\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'mountain_biking': '\u30de\u30a6\u30f3\u30c6\u30f3\u30d0\u30a4\u30af',
    'swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'open_water_swimming': '\u5c4b\u5916\u30b9\u30a4\u30e0',
    'lap_swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'walking': '\u30a6\u30a9\u30fc\u30af',
    'strength_training': '\u7b4b\u529b\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0',
    'multi_sport': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
    'triathlon': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
    'indoor_rowing': '\u30ed\u30fc\u30a4\u30f3\u30b0',
    'yoga': '\u30e8\u30ac',
    'jump_rope': '\u306a\u308f\u3068\u3073',
    'fitness_equipment': '\u30d5\u30a3\u30c3\u30c8\u30cd\u30b9',
}

out = []
for a in activities:
    atype = a.get('activityType', {}).get('typeKey', 'other')
    jp_type = type_map.get(atype, atype)
    dist_m = a.get('distance', 0) or 0
    duration_s = a.get('duration', 0) or 0
    avg_hr = a.get('averageHR', None)
    max_hr = a.get('maxHR', None)
    tss = a.get('trainingStressScore', 0) or 0
    np_val = a.get('normPower', None)
    start_local = (a.get('startTimeLocal', '') or '')[:10]
    if not start_local:
        continue
    out.append({
        'type': jp_type,
        'date': start_local,
        'dist': round(dist_m / 1000, 3),
        'time': round(duration_s / 60, 2),
        'avgHR': int(avg_hr) if avg_hr else None,
        'maxHR': int(max_hr) if max_hr else None,
        'np': int(np_val) if np_val else None,
        'tss': float(tss),
        'p20': None,
        'name': a.get('activityName', '')
    })

# Sort by date descending
out.sort(key=lambda x: x['date'], reverse=True)

if out:
    print(f"Date range: {out[-1]['date']} to {out[0]['date']}")

with open('activities.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"Saved {len(out)} activities to activities.json")

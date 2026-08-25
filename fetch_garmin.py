import json, os, sys
from datetime import datetime, timedelta
from garminconnect import Garmin

email = os.environ['GARMIN_EMAIL']
password = os.environ['GARMIN_PASSWORD']

try:
    client = Garmin(email, password)
    client.login()
    print("Login OK")
except Exception as e:
    print(f"Login failed: {e}", file=sys.stderr)
    sys.exit(1)

# Step 1: Get the 100 most recent activities first (most reliable for latest data)
all_activities = []
try:
    recent = client.get_activities(0, 100)
    all_activities.extend(recent)
    if recent:
        latest = recent[0].get('startTimeLocal', '')[:10]
        print(f"Recent 100: latest date = {latest}")
    else:
        print("Recent 100: empty")
except Exception as e:
    print(f"Recent fetch warning: {e}")

# Step 2: Get historical data by date range
end = datetime.today() + timedelta(days=1)
start = end - timedelta(days=152)
print(f"Fetching date range {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")

try:
    dated = client.get_activities_by_date(
        start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d')
    )
    print(f"Date range fetch: {len(dated)} activities")
    all_activities.extend(dated)
except Exception as e:
    print(f"Date range fetch warning: {e}")

# Merge by activityId (deduplicate)
seen_ids = set()
unique = []
for a in all_activities:
    aid = a.get('activityId')
    if aid and aid not in seen_ids:
        seen_ids.add(aid)
        unique.append(a)
    elif not aid:
        unique.append(a)

print(f"Total unique: {len(unique)} activities")

type_map = {
    'running': '\u30e9\u30f3',
    'trail_running': '\u30e9\u30f3',
    'treadmill_running': '\u30c8\u30ec\u30c3\u30c9\u30df\u30eb',
    'cycling': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'road_biking': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'indoor_cycling': '\u5c4b\u5185\u30d0\u30a4\u30af',
    'virtual_ride': '\u4ed3\u60f3\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'mountain_biking': '\u30de\u30a6\u30f3\u30c6\u30f3\u30d0\u30a4\u30af',
    'swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'open_water_swimming': '\u5c4b\u5916\u30b9\u30a4\u30e0',
    'lap_swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'walking': '\u30a6\u30a9\u30fc\u30af',
    'strength_training': '\u7b4b\u529b\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0',
    'multi_sport': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
    'triathlon': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
    'jump_rope': '\u306a\u308f\u3068\u3073',
    'yoga': '\u30e8\u30ac',
    'fitness_equipment': '\u30d5\u30a3\u30c3\u30c8\u30cd\u30b9',
    'elliptical': '\u30a8\u30ea\u30d7\u30c6\u30a3\u30ab\u30eb',
}

out = []
for a in unique:
    atype = a.get('activityType', {}).get('typeKey', 'other')
    jp_type = type_map.get(atype, atype)
    dist_m = a.get('distance', 0) or 0
    duration_s = a.get('duration', 0) or 0
    avg_hr = a.get('averageHR', None)
    max_hr = a.get('maxHR', None)
    tss = a.get('trainingStressScore', 0) or 0
    np_val = a.get('normPower', None)
    date = (a.get('startTimeLocal', '') or '')[:10]
    if not date:
        continue
    out.append({
        'type': jp_type, 'date': date,
        'dist': round(dist_m / 1000, 3),
        'time': round(duration_s / 60, 2),
        'avgHR': int(avg_hr) if avg_hr else None,
        'maxHR': int(max_hr) if max_hr else None,
        'np': int(np_val) if np_val else None,
        'tss': float(tss), 'p20': None,
        'name': a.get('activityName', '')
    })

out.sort(key=lambda x: x['date'], reverse=True)
if out:
    print(f"Date range in output: {out[-1]['date']} to {out[0]['date']}")

with open('activities.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"Saved {len(out)} activities")

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

end = datetime.today()
start = end - timedelta(days=150)

try:
    activities = client.get_activities_by_date(
        start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d')
    )
    print(f"Fetched {len(activities)} activities")
except Exception as e:
    print(f"Fetch failed: {e}", file=sys.stderr)
    sys.exit(1)

type_map = {
    'running': '\u30e9\u30f3',
    'treadmill_running': '\u30c8\u30ec\u30c3\u30c9\u30df\u30eb',
    'cycling': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'road_biking': '\u30ed\u30fc\u30c9\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'indoor_cycling': '\u5c4b\u5185\u30d0\u30a4\u30af',
    'virtual_ride': '\u4ed3\u60f3\u30b5\u30a4\u30af\u30ea\u30f3\u30b0',
    'swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'open_water_swimming': '\u5c4b\u5916\u30b9\u30a4\u30e0',
    'lap_swimming': '\u30d7\u30fc\u30eb\u30b9\u30a4\u30e0',
    'walking': '\u30a6\u30a9\u30fc\u30af',
    'strength_training': '\u7b4b\u529b\u30c8\u30ec\u30fc\u30cb\u30f3\u30b0',
    'multi_sport': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
    'triathlon': '\u30de\u30eb\u30c1\u30b9\u30dd\u30fc\u30c4',
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
    out.append({
        'type': jp_type,
        'date': (a.get('startTimeLocal', '') or '')[:10],
        'dist': round(dist_m / 1000, 3),
        'time': round(duration_s / 60, 2),
        'avgHR': int(avg_hr) if avg_hr else None,
        'maxHR': int(max_hr) if max_hr else None,
        'np': int(np_val) if np_val else None,
        'tss': float(tss),
        'p20': None,
        'name': a.get('activityName', '')
    })

with open('activities.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"Saved {len(out)} activities")

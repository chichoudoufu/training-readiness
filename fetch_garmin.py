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

all_activities = []
seen_ids = set()

def add_activities(acts, label):
    added = 0
    for a in (acts or []):
        aid = a.get('activityId')
        key = aid if aid else str(a.get('startTimeLocal','')) + a.get('activityName','')
        if key not in seen_ids:
            seen_ids.add(key)
            all_activities.append(a)
            added += 1
    if added:
        dates = [a.get('startTimeLocal','')[:10] for a in acts if a.get('startTimeLocal')]
        dates = [d for d in dates if d]
        if dates:
            print(f"{label}: {added} new, latest={max(dates)}")
    return added

# 1. Most recent 200 activities (catches latest regardless of date indexing)
try:
    recent = client.get_activities(0, 200)
    add_activities(recent, "Recent 200")
except Exception as e:
    print(f"Recent fetch warning: {e}")

# 2. Try get_last_activity for the absolute latest
try:
    last = client.get_last_activity()
    if last:
        add_activities([last], "Last activity")
        print(f"  Last activity date: {last.get('startTimeLocal','')[:10]}")
except Exception as e:
    print(f"Last activity warning: {e}")

# 3. Get activities for specific recent dates
today = datetime.today()
for days_back in range(5):
    target = today - timedelta(days=days_back)
    date_str = target.strftime('%Y-%m-%d')
    try:
        day_acts = client.get_activities_fordate(date_str)
        added = add_activities(day_acts, f"Date {date_str}")
    except Exception as e:
        pass

# 4. Historical date range fetch
end = today + timedelta(days=1)
start = end - timedelta(days=152)
try:
    dated = client.get_activities_by_date(
        start.strftime('%Y-%m-%d'),
        end.strftime('%Y-%m-%d')
    )
    added = add_activities(dated, f"Date range {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
except Exception as e:
    print(f"Date range fetch warning: {e}")

print(f"Total unique activities: {len(all_activities)}")

type_map = {
    'running': '\u30e9\u30f3', 'trail_running': '\u30e9\u30f3',
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
}

out = []
for a in all_activities:
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
    print(f"Output date range: {out[-1]['date']} to {out[0]['date']}")

with open('activities.json', 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"Saved {len(out)} activities")

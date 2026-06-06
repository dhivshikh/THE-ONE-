import urllib.request
import json

try:
    req = urllib.request.Request('http://localhost:8000/api/v1/timetable/cleanup-fake-electives', method='POST')
    with urllib.request.urlopen(req) as response:
        print('Cleanup Response:', response.read().decode())
except Exception as e:
    print('Cleanup Error:', e)

try:
    req2 = urllib.request.Request('http://localhost:8000/api/v1/timetable/elective-audit')
    with urllib.request.urlopen(req2) as response:
        data = json.loads(response.read().decode())
        print('Audit Summary:', data.get('summary'))
        print('Fake entries remaining:', len(data.get('fake_elective_entries', [])))
        for k, v in data.get('elective_groups', {}).items():
            print(f"Basket {k}: Sync OK={v.get('theory_sync_ok')} / Lab Sync OK={v.get('lab_sync_ok')}")
except Exception as e:
    print('Audit Error:', e)

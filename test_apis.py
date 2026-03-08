import requests

BASE = 'http://localhost:8000/api'
tests = [
    ('/predict/TCS', 'Prediction'),
    ('/recommendation/RELIANCE', 'Recommendation'),
    ('/backtest/INFY', 'Backtest'),
]
for ep, name in tests:
    try:
        r = requests.get(BASE + ep, timeout=20)
        d = r.json()
        if r.status_code == 200:
            print('[OK]', name, '200')
        else:
            print('[FAIL]', name, r.status_code, str(r.text)[:120])
    except Exception as e:
        print('[ERR]', name, str(e)[:80])

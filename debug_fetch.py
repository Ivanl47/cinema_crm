from app import create_app
import json

app = create_app('development')
with app.test_client() as c:
    resp = c.get('/bookings/sessions')
    print('sessions', resp.status_code)
    try:
        print(json.dumps(resp.get_json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print('sessions parse error', e)

    resp2 = c.get('/bookings/halls')
    print('\nhalls', resp2.status_code)
    try:
        print(json.dumps(resp2.get_json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print('halls parse error', e)

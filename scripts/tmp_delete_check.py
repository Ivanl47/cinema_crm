import urllib.request, json, sys
base='http://127.0.0.1:5000'

def get(url):
    try:
        r=urllib.request.urlopen(url, timeout=5)
        return r.getcode(), json.loads(r.read().decode())
    except Exception as e:
        print('GET ERR', url, e)
        return None, None

code, users = get(base+'/users')
print('ALL USERS code', code)
print(json.dumps(users, indent=2, ensure_ascii=False))
# find admin
admin_id=None
if users and 'users' in users:
    for u in users['users']:
        if u.get('username','').lower() in ('root','admin'):
            admin_id=u['id']; break
# find target non-admin user
target_id=None
if users and 'users' in users:
    for u in users['users']:
        if u['id']!=admin_id:
            target_id=u['id']; break
print('admin_id', admin_id, 'target_id', target_id)
if not admin_id or not target_id:
    print('no suitable users'); sys.exit(0)
# attempt DELETE with JSON body
req = urllib.request.Request(f"{base}/users/{target_id}", data=json.dumps({'acting_user_id': admin_id}).encode(), headers={'Content-Type':'application/json'})
req.get_method = lambda : 'DELETE'
try:
    r = urllib.request.urlopen(req, timeout=5)
    print('DELETE resp', r.getcode(), r.read().decode())
except Exception as e:
    print('DELETE ERR', e)

code2, users2 = get(base+'/users')
print('AFTER', code2)
print(json.dumps(users2, indent=2, ensure_ascii=False))

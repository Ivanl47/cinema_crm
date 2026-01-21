import runpy


def load_create_app():
    # execute app.py in its own namespace and return create_app
    try:
        import sys, os
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
        g = runpy.run_path('app.py', run_name='__main__')
        return g.get('create_app') or g.get('create_app')
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


def fetch_and_save(app, path, outname):
    with app.test_client() as client:
        resp = client.get(path)
        print(path, '=>', resp.status_code)
        if resp.status_code == 200:
            with open(outname, 'wb') as f:
                f.write(resp.data)
            print('Saved', outname)
        else:
            print('Response:', resp.get_data(as_text=True))


if __name__ == '__main__':
    create_app = load_create_app()
    app = create_app()
    # adjust acting_user_id and dates as needed
    start = '2026-01-01'
    end = '2026-01-21'
    admin = 3

    fetch_and_save(app, f'/reports/sold_tickets?acting_user_id={admin}&start_date={start}&end_date={end}', 'sold_tickets.csv')
    fetch_and_save(app, f'/reports/revenue_per_session?acting_user_id={admin}&start_date={start}&end_date={end}', 'revenue_per_session.csv')
    fetch_and_save(app, f'/reports/occupancy_by_day?acting_user_id={admin}&start_date={start}&end_date={end}', 'occupancy_by_day.csv')

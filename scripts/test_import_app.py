import traceback
try:
    import app
    print('import succeeded')
except Exception:
    traceback.print_exc()

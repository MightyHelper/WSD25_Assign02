from app.main import create_app
app = create_app()
print('\n'.join(sorted([r.path for r in app.routes])))
print('---')
for r in app.routes:
    try:
        print(r.path, r.methods)
    except Exception:
        pass


import sys
from app import create_app
from precondition.load_sample import load_sample


def main(argv=None):
    argv = argv or sys.argv[1:]
    force = '--force' in argv or '-f' in argv
    app = create_app()
    with app.app_context():
        created = load_sample(force=force)
        print('Seeded:', created)


if __name__ == '__main__':
    main()

if __name__ == '__main__':
    import sys

    import pytest
    from coverage import Coverage
    cov = Coverage(source=['pytableaux'])
    cov.erase()
    cov.start()
    exitcode = pytest.main()
    cov.stop()
    cov.save()
    if exitcode == 0:
        cov.html_report()
    sys.exit(exitcode)
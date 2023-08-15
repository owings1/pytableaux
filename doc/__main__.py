if __name__ == '__main__':
    import os.path
    import subprocess
    import sys
    sys.exit(subprocess.run(sys.argv[1:],
        executable='make',
        cwd=os.path.abspath(os.path.dirname(__file__)),
        stderr=sys.stderr,
        stdout=sys.stdout,
        stdin=sys.stdin).returncode)
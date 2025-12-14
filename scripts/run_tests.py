import subprocess
import sys

cmd = [sys.executable, '-m', 'pytest', '-q', '-r', 'a']
print('Running:', ' '.join(cmd))
proc = subprocess.run(cmd, capture_output=True, text=True)
print('RETURN CODE:', proc.returncode)
print('\n=== STDOUT ===\n')
print(proc.stdout)
print('\n=== STDERR ===\n')
print(proc.stderr)
sys.exit(proc.returncode)


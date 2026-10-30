"""Run a release helper with bounded BLAS threads and CPython's WMI fallback.

The host WMI service can stall platform.machine() during SciPy import after
memory pressure. This changes only this process; no service or system settings.
Usage: Python313 run_local.py path/to/helper.py [helper arguments...]
"""
import os
import platform
import runpy
import sys


def unavailable_wmi(*args, **kwargs):
    raise OSError('Host WMI unavailable; use CPython platform fallback')


def main():
    if len(sys.argv)<2:
        raise SystemExit('Usage: run_local.py helper.py [arguments...]')
    os.environ['OPENBLAS_NUM_THREADS']='1'
    os.environ['OMP_NUM_THREADS']='1'
    if hasattr(platform,'_wmi_query'):
        platform._wmi_query=unavailable_wmi
    target=sys.argv.pop(1)
    sys.argv[0]=target
    runpy.run_path(target,run_name='__main__')


if __name__=='__main__':main()

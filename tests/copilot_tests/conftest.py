import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for p in (HERE, HERE.parent.parent):          # the fakes beside the tests, and the repository root for `copilot`
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

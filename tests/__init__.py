import sys
from pathlib import Path

# Resolve the parent directory path
parent_dir = str(Path(__file__).resolve().parent.parent)

# Inject it at the beginning of sys.path
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
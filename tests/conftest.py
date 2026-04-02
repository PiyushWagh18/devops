import sys
import os

# Add the project root to sys.path so `from app import ...` works
# when pytest is run from any directory (including GitHub Actions runner).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# environment_check.py
import sys
import pygame
import numpy as np
import sklearn
import filterpy

print(f"Python:     {sys.version}")
print(f"Pygame:     {pygame.__version__}")
print(f"NumPy:      {np.__version__}")
print(f"Scikit:     {sklearn.__version__}")
print(f"FilterPy:   {filterpy.__version__}")
print("✅ Environment ready.")
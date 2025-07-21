import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils import calculate_debt_service_coverage_ratio


def test_dscr():
    assert calculate_debt_service_coverage_ratio(12000, 10000) == 1.2

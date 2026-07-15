#!/usr/bin/env python3
"""
Tests for search company details from Unified State Registry for Legal Companies.
"""
# MIT License
#
# Copyright (c) 2026 Vladislav Shubnikov
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
from typing import List

from company_usrlc_scanner.companies_scanner import collect_tpn_from_web


def load_test_short_input() -> List[List[str]]:
    """Load fixed test input"""
    out = [
        ["company 00", "7802931180"],
        ["company 01", "7447256358"],
        ["company 02", "780519211821"],
        ["company 03", "780529453700"],
        ["company 04", "561404718520"],
        ["company 05", "246219420752"],
        ["company 06", "230802249406"],
        ["company 07", "663403958607"],
        ["company 08 not found", "9909726766"],
        ["company 09", "550611166608"],
        ["company 10", "7816515991"],
        ["company 11", "0264060612"],
        ["company 12", "7817332133"],
        ["company 13", "7606089955"],
        ["company 14", "7627054512"],
        ["company 15", "6670327210"],
        ["company 16", "7807238565"],
        ["company 17", "7811205259"],
        ["company 18", "7735010706"],
        ["company 19", "7327080600"],
        ["company 20", "3123315768"],
        ["company 21", "4703174618"],
        ["company 22", "6025025671"],
        ["company 23", "7804368083"],
        ["company 24", "5047120398"],
        ["company 25", "7707206150"],
        ["company 26", "4025442914"],
        ["company 27", "5031078380"],
        ["company 28", "7708336515"],
        ["company 29", "7805367935"],
        ["company 30", "7106521581"],
        ["company 31", "6686056069"],
        ["company 32", "6671025854"],
        ["company 33", "4253029657"],
        ["company 34", "3528081420"],
        ["company 35", "1646043280"],
        ["company 36", "7203105308"],
        ["company 37", "7807021918"],
        ["company 38", "7825343611"],
        ["company 39", "7721691830"],
        ["company 40", "7447256358"],
    ]
    return out


def test_short_input() -> None:
    """Test with predefined data : 41 companies"""
    arr_input = load_test_short_input()
    num_results_per_table = 100
    t_start = time.perf_counter()

    collect_tpn_from_web(arr_input, num_results_per_table)

    elapsed = time.perf_counter() - t_start
    # maximum possible processing time for single company
    max_processing_time_seconds = 1.7
    assert elapsed < len(arr_input) * max_processing_time_seconds

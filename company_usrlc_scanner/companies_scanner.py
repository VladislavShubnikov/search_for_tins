#!/usr/bin/env python3
"""
Search company details from Unified State Registry for Legal Companies.

The goal of this script is to find details about legal companies from
State Registry for Legal Companies website. This script allows you to receive
hundreds-thousands result for the list of taxpayer numbers. Unlike search this
information "by hand", this script performs this search in automatic mode.
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

import argparse
import csv
import ctypes
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Define Windows API flags, required for sleep on/off functionality
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


def prevent_sleep():
    """
    Keeps the system awake and the screen turned on continuously.
    This code is optional. In most cases script will perform
    all actions shortly, so you need not prevent windows sleeping.
    """
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


def allow_sleep():
    """Restores default Windows sleep and screen timeout behavior."""
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


@dataclass
class CompanyNumbers:
    """ Digital values for company details"""
    ## individual taxpayer number ("INN" in russian)
    tpn: str = ''
    ## Company registration number ("OGRN" in russian)
    state_reg_number: str = ''
    ## Date of company registration
    date_state_reg_number: str = ''
    ## Code for registration reason ("KPP" in russian)
    kpp: str = ''


@dataclass
class Company:
    """ Single company detail. tpn and short_name is input """
    ## numbers data for company. please see @CompanyNumbers
    numbers: CompanyNumbers = field(default_factory=CompanyNumbers)
    ## short name of th company
    short_name: str = ''
    ## Has company active registration (or closed)
    active_status: bool = True
    ## Closure date (for closed companies only)
    date_closed: str = ''
    ## Registration region of the company
    region: str = ''
    ## Optional text details. In most cases,
    # it can be the name of the official company head
    company_details: str = ''


class WebWorm:
    """ Web crawler. This class performs
    automatic company data extraction from series of web requests
    Each request for each company in input list.
    """
    def __init__(self):
        options = webdriver.ChromeOptions()
        # Here option "--headless" can be added via "add_argument".
        # This means that during script run you will not
        # see results of web search on the screen.
        # This option can slightly speed up the search,
        # but you will not be able to see the "progress"
        options.add_argument("--disable-gpu")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def close(self):
        """
        @brief Close web interface
        """
        self.driver.quit()

    def get_tax_payer_info(self, url: str, personal_tax_number: str) -> str:
        """
        @brief Get taxpayer info
        @param[in] url website of company info search service
        @param[in] personal_tax_number Taxpayer individual number
        @return text result of company data search (can be parsed later)
        """
        out = ''
        try:
            self.driver.get(url)

            # wait 5 seconds to wait while search element in web page
            time_out = 4.0
            wait = WebDriverWait(self.driver, time_out)

            text_field = wait.until(
                ec.presence_of_element_located((By.ID, "query"))
            )

            text_field.send_keys(personal_tax_number)

            button = wait.until(
                ec.presence_of_element_located((By.ID, "btnSearch"))
            )
            button.click()

            # Pause briefly to wait site search completion (seconds)
            time_out = 0.7
            time.sleep(time_out)

            div_result = wait.until(
                ec.presence_of_element_located((By.CLASS_NAME, "res-text"))
            )

            # Pause for next call to avoid website anti dds blocker
            time_out = 0.2
            time.sleep(time_out)

            if div_result is not None:
                out = div_result.text

        except TimeoutException:
            print('Exception timeout')

        except NoSuchElementException:
            print("The locator used could not find the element.")

        except StaleElementReferenceException:
            print("The DOM refreshed and the element is no longer valid.")

        except Exception as e:
            print(f'!!! Exception = {e}')

        return out

    def get_company_info(self, personal_tax_number: str, short_name: str = '') -> Company:
        """
        @bried Get structure company details
        @param[in] personal_tax_number Individual company taxpayer number
        @param[in] short_name Short name of the company
        @return Company detailed description
        """
        company = Company()

        # input data
        company.numbers.tpn = personal_tax_number
        company.short_name = short_name

        url = 'https://egrul.nalog.ru/index.html'

        status_text = self.get_tax_payer_info(url, personal_tax_number)

        pattern = r'Дата прекращения деятельности:\s*(\d{2}\.\d{2}\.\d{4})'
        match = re.search(pattern, status_text)
        if match:
            company.active_status = False

            date_str = match.group(1)
            company.date_closed = date_str
            company.region = 'НЕТ'
            company.numbers.state_reg_number = '0'
            company.numbers.date_state_reg_number = '01.01.1900'
            company.numbers.kpp = '0'
            company.company_details = 'НЕТ'

        else:
            company.active_status = True

            pattern_large = \
                (r'([\s\S]*), ОГРН: (\d+), Дата присвоения ОГРН: (\d{2}.\d{2}.\d{4}), '
                 r'ИНН: (\d+), КПП: (\d+), \s*([\S\s]*)')
            pattern_large_no_details = \
                (r'([\s\S]*), ОГРН: (\d+), Дата присвоения ОГРН: (\d{2}.\d{2}.\d{4}), '
                 r'ИНН: (\d+), КПП: (\d+)')
            pattern_small = \
                r'ОГРНИП: ([\d]+), ИНН: ([\d]+), Дата присвоения ОГРНИП: (\d{2}.\d{2}.\d{4})'

            match_large = re.search(pattern_large, status_text)
            match_large_no_details = re.search(pattern_large_no_details, status_text)
            match_small = re.search(pattern_small, status_text)
            if match_large:
                company.region = match_large.group(1)
                company.numbers.state_reg_number = match_large.group(2)
                company.numbers.date_state_reg_number = match_large.group(3)
                company.numbers.kpp = match_large.group(5)
                company.company_details = match_large.group(6)
            elif match_large_no_details:
                company.region = match_large_no_details.group(1)
                company.numbers.state_reg_number = match_large_no_details.group(2)
                company.numbers.date_state_reg_number = match_large_no_details.group(3)
                company.numbers.kpp = match_large_no_details.group(5)
                company.company_details = 'НЕТ'
            elif match_small:
                company.region = 'НЕТ'
                company.numbers.state_reg_number = match_small.group(1)
                company.numbers.date_state_reg_number = match_small.group(3)
                company.numbers.kpp = '0'
                company.company_details = 'НЕТ'
            else:
                company.active_status = False
                company.region = 'НЕНАЙДЕН'
                company.numbers.state_reg_number = '0'
                company.numbers.date_state_reg_number = '01.01.1900'
                company.numbers.kpp = '0'
                company.company_details = 'НЕНАЙДЕН'

        return company


def print_company(company: Company) -> None:
    """
    @bried Print info about company
    This method is just for debugging purposes.
    @param company: Company detailed description
    """
    print('--------------------')
    print(f'ИНН: {company.numbers.tpn}')
    print(f'ИмяСокр: {company.short_name}')
    status: str = "АКТИВЕН" if company.active_status else "ЗАКРЫТ"
    print(f'Статус: {status}')
    print(f'ДатаЗакрытия: {company.date_closed}')
    print(f'Регион: {company.region}')
    print(f'ОГРН: {company.numbers.state_reg_number}')
    print(f'ОГРН ДатаРег: {company.numbers.date_state_reg_number}')
    print(f'КПП: {company.numbers.kpp}')
    print(f'Детали: {company.company_details}')


def get_csv_out_name(index_out: int) -> Path:
    """
    @brief Get temp csv output file name
    Collected results are placed into series of
    csv files to do not overload system with too much
    data: collect first N companies, save them, collect
    next N companies, save them again, etc.

    @param[in] index_out Index of temporary csv output file
    @return Path to output file
    """
    script_dir = Path(__file__).parent.parent.resolve()
    name_out = f'out_{index_out:04d}.csv'
    file_path = script_dir / "data" / name_out
    return file_path


def collect_tpn_from_web(arr_input: List[List[str]], num_results: int) -> int:
    """
    @bried Create companies info, collecting data from web requests

    In the success, a lot of temporary CSV files will be created in the
    data/out folder. All of them will be merged into the single CSV table later.

    @param[in] arr_input List of companies info. Each row has number and short name
    @param[in] num_results Number of companies in the single CSV result table
    @return number of companies collected
    """

    data_out : dict = {
        'short_name': [],
        'tpn': [],
        'active_status': [],
        'date_closed': [],
        'region': [],
        'state_reg_number': [],
        'date_state_reg_number': [],
        'kpp': [],
        'company_details': [],
    }

    # Custom headers for created table
    headers_rename = {
        'short_name': 'КороткоеИмя',
        'tpn': 'ИНН',
        'active_status': 'Статус',
        'date_closed': 'ДатаЗакрытия',
        'region': 'Регион',
        'state_reg_number': 'ОГРН',
        'date_state_reg_number': 'ДатаОГРН',
        'kpp': 'КПП',
        'company_details': 'Детали'
    }

    index_out = 0

    web_worm = WebWorm()

    for index, pair in enumerate(arr_input):

        # print progress each 16 scans
        if index % 16 == 0:
            print('.', end='')

        if index % num_results == 0:

            if index > 0:
                df = pd.DataFrame(data_out)

                # rename columns
                df = df.rename(columns=headers_rename)

                file_path = get_csv_out_name(index_out)
                index_out += 1

                df.to_csv(file_path, index=False)

            # prepare dictionary to save later into csv
            data_out = {
                'short_name': [],
                'tpn': [],
                'active_status': [],
                'date_closed': [],
                'region': [],
                'state_reg_number': [],
                'date_state_reg_number': [],
                'kpp': [],
                'company_details': [],
            }

        #                                    number, name
        company = web_worm.get_company_info(pair[1], pair[0])
        data_out['short_name'].append(company.short_name)
        data_out['tpn'].append(company.numbers.tpn)
        status = "АКТИВЕН" if company.active_status else "ЗАКРЫТ"
        data_out['active_status'].append(status)
        data_out['date_closed'].append(company.date_closed)
        data_out['region'].append(company.region)
        data_out['state_reg_number'].append(company.numbers.state_reg_number)
        data_out['date_state_reg_number'].append(company.numbers.date_state_reg_number)
        data_out['kpp'].append(company.numbers.kpp)
        data_out['company_details'].append(company.company_details)
    # for all input companies

    # close web interface
    web_worm.close()

    # last output data save
    df = pd.DataFrame(data_out)

    # rename columns
    df = df.rename(columns=headers_rename)

    file_path = get_csv_out_name(index_out)
    index_out += 1

    df.to_csv(file_path, index=False)

    print(' ')
    print('collect_tpn_from_web finished')
    return len(arr_input)


def merge_output(in_short_file_name: str) -> None:
    """
    @brief Merge output csv files
    Merge all collected temporary CSV files with companies info
    into the single output file
    @param[in] in_short_file_name Input file name (be copied for output file)
    """
    input_tables = []
    for i in range (0, 2048):
        file_name_short = f'out_{i:04d}.csv'
        script_dir = Path(__file__).parent.parent.resolve()
        file_path = script_dir / "data" / file_name_short
        if not os.path.exists(file_path):
            break
        table = pd.read_csv(file_path)
        input_tables.append(table)
    # for all files
    out = pd.concat(input_tables, ignore_index=True)

    col_name_taxpayer_index = out.columns[5]
    col_name_kpp = out.columns[7]
    out[col_name_taxpayer_index] = out[col_name_taxpayer_index].astype(int)
    out[col_name_kpp] = out[col_name_kpp].astype(int)

    script_dir = Path(__file__).parent.parent.resolve()
    file_path_out = script_dir / "data" / "out" / in_short_file_name
    out.to_csv(file_path_out, index=False)

    # remove input files
    num_tables = len(input_tables)
    for i in range (0, num_tables):
        file_name_short = f'out_{i:04d}.csv'
        script_dir = Path(__file__).parent.parent.resolve()
        file_path = script_dir / "data" / file_name_short
        if os.path.exists(file_path):
            os.remove(file_path)
    # all files

    print(f'Please, see file {file_path_out}')


def load_input(short_name: str) -> List[List[str]]:
    """
    @brief Load original companies csv file with name + tpn
    Read input CSV file in the form like:
    company01, tpn01
    company02, tpn02
    ...
    @param[in] short_name Input CSV file name
    @return List of list with format elem[0]: name, elem[1]: tpn
    """
    script_dir = Path(__file__).parent.parent.resolve()
    file_path = script_dir / "data" / "in" / short_name
    out = []

    if not os.path.exists(file_path):
        print(f'File {file_path} not exists')
        return []

    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        csv_reader = csv.reader(file, delimiter=',')
        max_rows = 128 * 1000
        cur_row = 0
        for row in csv_reader:
            text_name: str = row[0]
            text_number: str = row[1]
            arr = [text_name, text_number]
            out.append(arr)
            cur_row += 1
            if cur_row == max_rows:
                break
    # with
    return out


def main() -> None:
    """ Main function: run web worm """
    parser = argparse.ArgumentParser(
        description=
        "Scan companies csv file and find company "
        "details by their taxpayer number"
    )
    parser.add_argument(
        "filename",
        type=str,
        help="Short file name of input csv file, it should be in data/in folder"
    )
    args = parser.parse_args()
    file_name = args.filename

    arr_input = load_input(file_name)

    if len(arr_input) == 0:
        return

    prevent_sleep()
    num_results_per_table = 100
    t_start = time.perf_counter()

    num_companies = collect_tpn_from_web(arr_input, num_results_per_table)

    elapsed = time.perf_counter() - t_start
    print(f'{num_companies} companies downloaded sequentially in {elapsed} seconds.')

    allow_sleep()

    merge_output(file_name)

if __name__ == '__main__':
    main()

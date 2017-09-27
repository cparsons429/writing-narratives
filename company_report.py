from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import csv
import datetime
import numpy as np


class Company(object):
    def __init__(self, ticker, dates, closes):
        self.ticker = ticker
        self.dates = dates
        self.closes = closes
        self.trends = []
        self.events = []

    def generate_overall_trend(self, thresholds=None):
        self.trends.append(Trend(self.dates[0], self.dates[len(self.dates) - 1], self, thresholds))

    def generate_significant_weeks(self, threshold):
        i = 0
        while i < len(self.closes) - 5:
            if self.closes[i] != 0:
                change = (self.closes[i + 5] - self.closes[i]) / self.closes[i]
            else:
                raise ValueError('The company was worth $0 on ' + int_to_english_datetime(self.dates[i]))

            if abs(change) > threshold:
                self.events.append(Event(self.dates[i], self.dates[i + 5], change, change > 0))
                i += 5
            else:
                i += 1

    def get_abs_correlation_with(self, company):
        copy_company_dates = list(company.dates)
        shared_dates = []
        self_abs_changes = []
        company_abs_changes = []

        for date in self.dates:
            try:
                shared_dates.append(copy_company_dates.pop(copy_company_dates.index(date)))
            except ValueError:
                pass

        for i in range(len(shared_dates) - 1):
            self_cur_value = self.closes[self.dates.index(shared_dates[i])]
            self_next_value = self.closes[self.dates.index(shared_dates[i + 1])]
            if self_cur_value != 0:
                self_abs_changes.append(abs(self_next_value - self_cur_value) / self_cur_value)
            else:
                raise ValueError('This company was worth $0 on ' +
                                 int_to_english_datetime(self.dates.index(shared_dates[i])))

            company_cur_value = company.closes[company.dates.index(shared_dates[i])]
            company_next_value = company.closes[company.dates.index(shared_dates[i + 1])]
            if company_cur_value != 0:
                company_abs_changes.append(abs(company_next_value - company_cur_value) / company_cur_value)
            else:
                raise ValueError('The comparison company was worth $0 on ' +
                                 int_to_english_datetime(company.dates.index(shared_dates[i])))

        return np.corrcoef(self_abs_changes, company_abs_changes)[0, 1]


class Trend(object):
    def __init__(self, start_date_int, end_date_int, company, thresholds=None):
        self.start_date_int = start_date_int
        self.end_date_int = end_date_int

        start_date_val = company.closes[company.dates.index(start_date_int)]
        end_date_val = company.closes[company.dates.index(end_date_int)]

        if start_date_val != 0:
            self.change = (end_date_val - start_date_val) / start_date_val
        else:
            raise ValueError('The company was worth $0 on ' + int_to_english_datetime(start_date_int))

        self.significance_level = None

        if thresholds is not None:
            for i in range(len(thresholds)):
                if self.change < thresholds[i]:
                    self.significance_level = i
                    break
            if self.significance_level is None:
                self.significance_level = len(thresholds)


class Event(object):
    def __init__(self, start_date_int, end_date_int, change, is_good, link=None):
        self.english_date = int_to_english_datetime(start_date_int)
        self.start_date_int = start_date_int
        self.end_date_int = end_date_int
        self.change = change
        self.is_good = is_good
        self.link = link


def datetime_to_int(date_string):
    date = [int(x) for x in date_string.split('-')]
    return (datetime.datetime(date[0], date[1], date[2]) - datetime.datetime(1970, 1, 1)).days


def int_to_english_datetime(date_int):
    return (datetime.datetime(1970, 1, 1) + datetime.timedelta(date_int)).strftime('%B %d, %Y')


def get_kpis(subject_ticker, similar_tickers, data_dir):
    subject_company = get_kpi(subject_ticker, data_dir)
    similar_companies = []

    for similar_ticker in similar_tickers:
        similar_company = get_kpi(similar_ticker, data_dir)
        similar_companies.append(similar_company)

    return subject_company, similar_companies


def get_kpi(company_ticker, data_dir):
    company_path = os.path.join(data_dir, company_ticker) + '.csv'

    raw_file = open(company_path, 'r')
    raw_csv = csv.reader(raw_file)

    headers = raw_file.next()
    headers = headers.split(',')

    date_col = headers.index('Date')
    close_col = headers.index('Close')

    dates = []
    closes = []

    for day in raw_csv:
        dates.append(datetime_to_int(day[date_col]))
        closes.append(float(day[close_col]))

    raw_file.close()

    return Company(company_ticker, dates, closes)


def generate_report(subject_ticker, data_dir):
    similar_tickers = [os.path.splitext(similar_ticker)[0] for similar_ticker in os.listdir(data_dir)]
    similar_tickers.pop(similar_tickers.index(subject_ticker))

    subject_company, similar_companies = get_kpis(subject_ticker, similar_tickers, data_dir)

    report = 'Over the past year, ' + subject_ticker + ' has '

    annual_trend_thresholds = [-0.1, 0, 0.1]
    subject_company.generate_overall_trend(annual_trend_thresholds)
    subject_trend = subject_company.trends[0]

    if subject_trend.significance_level == 0:
        report += 'crashed this year, losing ' + str(abs(subject_trend.change) * 100) + '% of market value. '
    elif subject_trend.significance_level == 1:
        report += 'had a poor year, losing ' + str(abs(subject_trend.change) * 100) + '% of market value. '
    elif subject_trend.significance_level == 2:
        report += 'moderately improved in market value, growing ' + str(abs(subject_trend.change) * 100) + '%. '
    elif subject_trend.significance_level == 3:
        report += 'had a strong year, growing ' + str(abs(subject_trend.change) * 100) + '%. '
    else:
        raise ValueError('Error in calculating the significance level of the company\'s annual stock trend.')

    report += 'Among its key competitors of '

    abs_correlations = []
    for similar_company in similar_companies:
        abs_correlations.append(subject_company.get_abs_correlation_with(similar_company))

    competitor_indices = []
    for i in range(3):
        index = abs_correlations.index(max(abs_correlations))
        abs_correlations.pop(index)
        competitor_indices.append(index)

    report += similar_tickers[competitor_indices[0]] + ', '
    report += similar_tickers[competitor_indices[1]] + ', and '
    report += similar_tickers[competitor_indices[2]] + ', ' + subject_ticker + ' has been performing '

    competitor_changes = []
    for competitor_index in competitor_indices:
        similar_companies[competitor_index].generate_overall_trend(annual_trend_thresholds)
        competitor_changes.append(similar_companies[competitor_index].trends[0].change)
    competitor_changes.sort()

    if subject_trend.change <= competitor_changes[0]:
        report += 'poorly, sitting at the bottom of the pack.\n\n'
    elif subject_trend.change < competitor_changes[2]:
        report += 'okay, sitting at the middle of the pack.\n\n'
    else:
        report += 'excellently, outperforming all others!\n\n'

    subject_company.generate_significant_weeks(threshold=0.15)
    for event in subject_company.events:
        report += subject_ticker + ' had a '
        if event.is_good:
            report += 'great week starting ' + event.english_date + ', when its stock rose ' + str(event.change * 100) \
                      + '%!\n\n'
        else:
            report += 'poor week starting ' + event.english_date + ', when its stock fell ' + str(abs(event.change)
                                                                                                  * 100) + '%.\n\n'

    return report


my_subject_ticker = 'FIT'
my_data_dir = os.path.join(os.path.dirname(__file__), 'market_report_datasets')

print(generate_report(my_subject_ticker, my_data_dir))

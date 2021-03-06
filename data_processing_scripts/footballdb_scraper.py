import requests
from bs4 import BeautifulSoup
import imp
import os


CWD = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_PATH = CWD + '/../data/{0}_{1}.csv'

class FootballdbScraper(object):

    def __init__(self, city_team='seattle-seahawks'):
        self.city_team = city_team
        self.url = 'http://www.footballdb.com/teams/nfl/{0}/results/{1}'

    def download_year(self, year, file_path=None):
        if file_path is None:
            file_path = DOWNLOAD_PATH.format(self.city_team, year)

        url = self.url.format(self.city_team, year)
        r = requests.get(url)
        soup = BeautifulSoup(r.text)
        headers = soup.findAll('tr', {'class': 'header'})[0]
        table = soup.findAll('tr')
        self._write_csv(table, headers, file_path)

    def download_years(self, years):
        for year in years:
            self.download_year(year)

    def _write_csv(self, table, headers, file_path):
        unwanted = set(['@ ', ', ', 'OT', '\n'])
        quotes = '"{0}"'
        with open(file_path, 'w') as f:
            headers = [quotes.format(header) for header in headers.strings]
            f.write(','.join(headers))
            f.write('\n')
            for row in table:
                if row.attrs.values()[0][0] != 'header':
                    data = []
                    for i, s in enumerate(row.strings):
                        quotes = '"{0}"'
                        if i == 0:
                            data.append(quotes.format(s.split(' ')[0]))
                        else:
                            if s not in unwanted:
                                data.append(quotes.format(s))
                    if len(data) < len(headers):
                        for i in range(len(headers) - len(data)):
                            data.append('')
                    f.write(','.join(data))
                    f.write('\n')

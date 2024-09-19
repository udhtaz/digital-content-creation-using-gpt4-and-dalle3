import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta

import logging
logging.basicConfig(level = logging.INFO)


class HolidayEvents:


    base_url = "https://www.timeanddate.com/holidays/"
    
    def __init__(self, country, year):
        self.country = country
        self.year = year

    def fetch_all_events(self):
        session = requests.Session()
        date_format = '%d %b %Y'
        alternate_format = '%b %d %Y'
        all_events = []
        
        logging.info("========== fetching holiday events ==========")
        url = f"{self.base_url}{self.country.lower()}/{self.year}"
        res = session.get(url)
        
        bs = BeautifulSoup(res.text, 'html.parser')
        event_table = bs.find('table', {"class": "table--holidaycountry"})
        event_details = event_table.find_all('tr')
        for event_detail in event_details[1:]:
            event_info_tags = event_detail.find_all("td")
            event_info = [tag.text.strip().replace("'", "").lower() for tag in event_info_tags]
            # event_info = [tag.text.strip().lower() for tag in event_info_tags]
            event_date = event_detail.find("th")
            if any(event_info):
                if event_date:
                    event_date = f"{event_date.text.strip()} {self.year}"
                    try:
                        event_date = datetime.strptime(event_date, date_format)
                    except Exception as err:
                        logging.info(f"Error formatting date. {err} - retrying with alternate format")
                        event_date = datetime.strptime(event_date, alternate_format)

                    day_date = event_date.strftime("%F")
                    event_location = self.country.lower()
                    event_month = event_date.strftime("%B")
                    event_week = event_date.strftime('%Y-%W')

                    extra_info = [day_date, event_location, event_month, 'static', f'www.timeanddate.com/holidays/{self.country.lower()}', event_week]
                    event_info.insert(0, event_date)
                    event_info.extend(extra_info)

                    all_events.append(event_info)
        
        col_headings = [tag.text.strip().lower() for tag in event_details[0].find_all("th")]
        col_headings = [heading if heading else "day" for heading in col_headings]
        extra_headings = ['eventday', 'location', 'month', 'static_or_dynamic','source', 'week']
        col_headings.extend(extra_headings)
        
        df = pd.DataFrame(all_events, columns = col_headings)
        rename_cols = {'name': 'event', 'type': 'category'}
        df.rename(columns=rename_cols, inplace = True)
        try:
            df.drop('details', axis=1, inplace=True)
        except Exception:
            pass
        
        return df

    def filter_events(self, start=False, num_days = 7):
        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d")
        else:
            start_date = datetime.today()

        end_date = start_date + timedelta(days=num_days)
        df = self.fetch_all_events()
        event_df = df[(df['date']>=start_date) & (df['date']<end_date)]
        event_df['date'] = event_df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
        event_df.reset_index(drop=True, inplace=True)
        return event_df
    
    
    
    
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

logging.basicConfig(level=logging.INFO,format='%(asctime)s- %(levelname)s- %(message)s')
logger=logging.getLogger(__name__)

class HolidayScraper:
    def __init__(self,cache_file="holidays_cache.json"):
        load_dotenv(override=True)
        self.api_token=os.getenv('APIFY_API_TOKEN')
        if self.api_token:
            logger.info(f"Loaded Apify token starting with: {self.api_token[:10]}...")
        if not self.api_token:
            raise ValueError("Apify API token must be set in the .env file.")
        
        self.client=ApifyClient(self.api_token)
        self.cache_file=cache_file
        
    def get_holidays(self,country_code="US",year=None) -> list:
        if year is None:
            year=datetime.now().year
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file,'r') as f:
                    cache_data=json.load(f)
                cache_key=f"{country_code}_{year}"
                if cache_key in cache_data:
                    logger.info(f"Using cached holidays for {country_code} in {year}.")
                    return cache_data[cache_key]
            except Exception as e:
                logger.warning(f"Error reading cache file: {e}. Proceeding to fetch from API.")
                        
        logger.info(f"Cache miss.Calling Apify to fetch holidays for {country_code} in {year}.")
        # Apify call using the official cheerio-scraper and a public holiday API
        run_input = {
            "startUrls": [{"url": f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"}],
            "pageFunction": """async function pageFunction(context) { 
                const data = JSON.parse(context.body); 
                data.forEach(holiday => {
                    context.pushData({ date: holiday.date });
                });
            }"""
        }
        try:
            run=self.client.actor("apify/cheerio-scraper").call(run_input=run_input)

            holidays=[]
            for item in self.client.dataset(run['defaultDatasetId']).iterate_items():
                if "date" in item:
                    holidays.append(item["date"])
            logger.info(f"Sucessfully scraped {len(holidays)} holidays for {country_code} in {year}.")
            self._save_to_cache(country_code,year,holidays)
            
            return holidays
        except Exception as e:
            logger.error(f"Apify scraping failed: {e}")
            # Fallback: if the scraper fails or actor doesn't exist, return a hardcoded failsafe list so our system doesn't break
            logger.warning("Returning fallback default holidays.")
            return [f"{year}-01-01", f"{year}-12-25"]
        
    
    
    def _save_to_cache(self, country, year, holidays):
        """Helper function to save results to a JSON file."""
        cache_data = {}
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                cache_data = json.load(f)
                
        cache_key = f"{country}_{year}"
        cache_data[cache_key] = holidays
        
        with open(self.cache_file, "w") as f:
            json.dump(cache_data, f, indent=4)
        logger.info(f"Saved holidays to cache file: {self.cache_file}")



if __name__=="__main__":
    scraper = HolidayScraper()
    dates = scraper.get_holidays(country_code="US", year=2026)
    print("\n--- Fetched Holidays ---")
    print(dates)
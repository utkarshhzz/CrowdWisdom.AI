import logging
from datetime import datetime
import pytz
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from holiday_scraper import HolidayScraper

logger=logging.getLogger(__name__)

def check_if_good_time_to_call(timezone_str:str,country_code:str='US',override_time:datetime=None) -> bool:
    """
    Hermes Skill: Checks if it is a legally and logically acceptable time to call a debtor.
    
    Args:
        timezone_str: The IANA timezone string of the debtor (e.g., 'America/New_York').
        country_code: The 2-letter country code for holiday checking (e.g., 'US').
        override_time: Used for unit testing to pretend it's a different day/time.
        
    Returns:
        True if it is safe to call, False otherwise.
    """
    
    if timezone_str == "DEMO":
        logger.info("DEMO MODE ENABLED: Bypassing all safety checks and returning True.")
        return True
    
    try:
        # checking what time it is currently in debtors specific city
        tz=pytz.timezone(timezone_str)
        # use override time if testing
        local_time=override_time if override_time else datetime.now(tz)
        local_date_str=local_time.strftime("%Y-%m-%d")
        logger.info(f"Checking schedule for timezone: {timezone_str}. Local time is: {local_time}")
        
        
        # chekcing if weekend or not
        if local_time.weekday() >=5:
            logger.info("Result: FALSE,it is the weekend")
            return False
        
        # checking if it is within business hours so for 9-5 we check if hour is before 9 or after 18 ie 6pm
        if local_time.hour < 9 or local_time.hour >=18:
            logger.info(f"Result: FALSE,Outside business hours (Current hours: {local_time.hour})")
            return False
          
        # checking if public holiday or not
        scraper=HolidayScraper()
        holidays=scraper.get_holidays(country_code=country_code,year=local_time.year)
        
        if local_date_str in holidays:
            logger.info(f"Result: FALSE,Today {local_date_str} is a public holiday in {country_code}")
            return False
        
        logger.info("Result: TRUE,it is a valid business time to call")
        return True
    
    except pytz.UnknownTimeZoneError:
        logger.error(f"Invalid timezone provided: {timezone_str}")
        return False
    
    except Exception as e:
        logger.error(f"Error in schedule checking: {e}")
        return False
    
    
if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format='%(levelname)s: %(message)s')
    print("\n--- Running Unit Tests for Scheduling Skill ---")

    test_tz="America/New_York"
    
    # Test 1: A normal Wednesday at 2:00 PM (14:00) -> Should be TRUE
    good_time = datetime(2026, 4, 15, 14, 0, 0, tzinfo=pytz.timezone(test_tz))
    print(f"\nTest 1 (Wed 2 PM): {'PASS' if check_if_good_time_to_call(test_tz, override_time=good_time) else 'FAIL'}")

    # Test 2: Saturday at 2:00 PM -> Should be FALSE
    weekend_time = datetime(2026, 4, 18, 14, 0, 0, tzinfo=pytz.timezone(test_tz))
    print(f"\nTest 2 (Saturday): {'PASS' if not check_if_good_time_to_call(test_tz, override_time=weekend_time) else 'FAIL'}")

    # Test 3: Wednesday at 8:00 AM (Too early) -> Should be FALSE
    early_time = datetime(2026, 4, 15, 8, 0, 0, tzinfo=pytz.timezone(test_tz))
    print(f"\nTest 3 (8 AM): {'PASS' if not check_if_good_time_to_call(test_tz, override_time=early_time) else 'FAIL'}")

    # Test 4: Christmas Day (Holiday) at 2:00 PM -> Should be FALSE
    holiday_time = datetime(2026, 12, 25, 14, 0, 0, tzinfo=pytz.timezone(test_tz))
    print(f"\nTest 4 (Christmas): {'PASS' if not check_if_good_time_to_call(test_tz, override_time=holiday_time) else 'FAIL'}")
    
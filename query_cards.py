import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime

def retrieve_cards_from_query(query, sort, market, end_dt=None):
	base_url = "https://back.130point.com/cards/"

	post_data = {
		"query": query,
		"sort": sort,
		"mp": market,
		# This is probably the page number
		"tab_id": 1,
		# These are defined in sources, potentially not needed since they seem to be for frontend
		# TZ might be used for our date sorting. Unknown at the moment
		"tz": "America/New_York",
		"width": 400,
		"height": 800,
		# Session value, will potentially need to be refreshed (SessionVal)
		"tk": "dc848953a13185261a89",
	}
	try:
		response = requests.post(base_url, data=post_data, json=post_data)
		response_content = response.content
		
		response_content_decoded = response_content.decode("utf-8")
		soup = BeautifulSoup(response_content, "html.parser")
		
		typeText = soup.find(id="typeText")
		type_text_content = None
		if typeText:
			type_text_content = typeText.contents
		

		card_results = soup.find_all("tr", id="dRow")

		prices = []
		accumulated_price = 0
		for card_result in card_results:
			price_found = card_result.find_all(class_="priceSpan")
			date_found = card_result.find_all(id="dateText")
			dt = None
			if(date_found):
				date_found_str = date_found[0].contents[1].strip()
				date_found_str = date_found_str.replace("EDT", "-0400")
				date_found_str = date_found_str.replace("EST", "-0500")
				dt = datetime.strptime(date_found_str, "%a %d %b %Y %H:%M:%S %z")
			
			if end_dt and dt and end_dt > dt:
				# If we have an end date, and the current result was sold before the end date, then don't include this in our averages.
				# Continue so we are sort-agnostic (Run through all results)
				continue
				
			price_data = price_found[0].contents[0].strip().replace(",", "").split(" ")
			price = Decimal(price_data[0])
			prices.append(price)
			accumulated_price += price

		# print(prices)
		count_prices = len(prices)
		average_price = 0
		if count_prices > 0:
			average_price = accumulated_price / count_prices
		
		return {
			"prices": prices,
			"average_price": average_price,
			"type_text_content": type_text_content,
		}
	except Exception as e:
		# Catch blanket Exception cause we are lazy
		# TODO eventually shorten this to catch API Timeouts/Beautiful Soup errors for robust error messages
		print(e)
		return {
			"error": e,
			"error_message": f"Failed to retrieve results. Please try again.",
		}

# sample_query = "Dan Marino 2024 Bowman"
# sample_sort = "EndTimeSoonest"
# sample_market = "all"
# retrieve_cards_from_query(sample_query, sample_sort, sample_market, datetime(2024,5,26,12,0))

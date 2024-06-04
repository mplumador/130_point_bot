import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.commands import AutocompleteContext
from query_cards import retrieve_cards_from_query
from datetime import datetime
from pytz import timezone
# Used for windows to be able to use os.environ.get()
load_dotenv()

bot = discord.Bot()



BOT_TOKEN = os.environ.get("BOT_TOKEN")

def basic_embed(title, description, fields=[], color=discord.Colour.blurple(),):
	embed = discord.Embed(
		title=title,
		description=description,
		color=color
	)

	for field in fields:
		embed.add_field(name=field.get("name"), value=field.get("value"), inline=field.get("inline", False))
	
	embed.set_author(name="130 Point Bot", icon_url="https://130point.com/wp-content/uploads/2021/10/cropped-130Point-Logo-1a_Orange-32x32.png")
	return embed

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


async def get_bool_types(ctx:AutocompleteContext):
	return [
		discord.OptionChoice(name="True", value=1),
		discord.OptionChoice(name="False", value=0),
	]

async def get_market_types(ctx:AutocompleteContext):
	return [
		discord.OptionChoice(name="All", value="all",),
		discord.OptionChoice(name="eBay", value="ebay",),
		discord.OptionChoice(name="PWCC Marketplace", value="pwcc",),
		discord.OptionChoice(name="Goldin", value="goldin",),
		discord.OptionChoice(name="MySlabs", value="myslabs",),
		discord.OptionChoice(name="Pristin Auction", value="pristine",),
		discord.OptionChoice(name="Heritage Auctions", value="heritage",),
	]

@bot.slash_command(name="avg", description="Search for a card and average the last-sold prices. Follows 130 Point's query options.")
async def search_and_average(
	ctx: discord.ApplicationContext,
	card_query: discord.Option(str, description="Multiple Queries should be separated by a semicolon: Rookie1;Rookie2."),
	marketplace: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(get_market_types)),
	sold_after_date: discord.Option(str, description="month/day/year EX: 01/24/2024", required=False, default=''),
):
	sold_after_dt = None
	if sold_after_date != "":
		try:
			sold_after_dt = datetime.strptime(sold_after_date,"%m/%d/%Y")
			tz = timezone("US/Eastern")
			sold_after_dt = sold_after_dt.replace(hour=0, minute=0, second=0, tzinfo=tz)
		except Exception as e:
			print(e)
			await ctx.respond(f"Failed to parse sold_after_date. Please follow the format month/day/year: Ex January 1st, 2024 = 01/01/2024", ephemeral=True)
			return
	sort_key = "EndTimeSoonest"
	query_list = card_query.split(";")
	averages = []
	result_str = f""
	inline_fields = []
	if len(query_list) > 6:
		await ctx.respond(f"We can only search for up to 6 queries at a time. Please adjust your query.", ephemeral=True)
		return
	# Our queries may take a awhile. Discord requires us to send a response in 3 seconds, hence we defer
	await ctx.defer()
	for query in query_list:
		response_dict = retrieve_cards_from_query(query, sort_key, marketplace, sold_after_dt)
		query_text = query
		# If the header has "No Exact Matches Found", or anything else. Strikethrough the query
		if response_dict.get("type_text_content", None):
			query_text =  f"~~{query}~~"
		inline_fields.append(
				{
					"name": "Query",
					"value": query_text,
					"inline": True,
				}
			)
		if response_dict.get("error", None):
			error_message = response_dict.get("error_message")
			actual_error_message = str(response_dict.get("error"))
			inline_fields.append({
					"name": "Error",
					"value": error_message,
					"inline": True,
				})
			inline_fields.append({
					"name": "Error Actual",
					"value": actual_error_message,
					"inline": True,
				})

		else:
			average = response_dict.get("average_price")
			
			inline_fields.append({
					"name": "Average Price",
					"value": f"${average:.2f}",
					"inline": True,
				})
			inline_fields.append(
				{
					"name": "Result Count",
					"value": len(response_dict.get("prices")),
					"inline": True,
				}
				)
			# Include a spacer field to breakup the inline
			inline_fields.append({"name": "", "value": ""})
	embed_description = """
	To search for multiple variations of the same term, enclose them in parentheseis and separate them by a comma. EX: (PSA, BGS)
	Use a minus \"-\" sign to exclude terms from the search. EX: Lamelo Ball -box -case
	Use & to match only terms of that pattern. EX: Charizard PSA&10
	"""
    
	embed = basic_embed(f"Calculate Average Price", embed_description, inline_fields)

	await ctx.followup.send("Averages Calculated:", embed=embed)
	


@bot.event
async def on_ready():
	print(f"We have logged in as {bot.user}")


bot.run(BOT_TOKEN)
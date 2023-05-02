import logging
import discord
import time
import json
from discord.ext import commands
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification


logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', handlers=[logging.StreamHandler(), logging.FileHandler('bot.log', encoding='utf-8')])
logger = logging.getLogger(__name__)

tokenizer = AutoTokenizer.from_pretrained('michellejieli/NSFW_text_classifier')
model = AutoModelForSequenceClassification.from_pretrained('michellejieli/NSFW_text_classifier')
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


def is_spciy_content(message):
    result = classifier(message)
    logger.info(f"Output: {result}")
    return result[0]['label'], result[0]['score']


def save_user_xp():
    with open('user_xp.json', 'w') as f:
        json.dump(user_xp, f)


def load_user_xp():
    try:
        with open('user_xp.json', 'r') as f:
            loaded_data = json.load(f)
            return {str(key): value for key, value in loaded_data.items()}
    except FileNotFoundError:
        return {}


def save_reached_milestones():
    with open('reached_milestones.json', 'w') as f:
        json.dump(list(reached_milestones), f)


def load_reached_milestones():
    try:
        with open('reached_milestones.json', 'r') as f:
            loaded_data = json.load(f)
            return {(int(user_id), int(milestone)) for user_id, milestone in loaded_data}
    except FileNotFoundError:
        return set()


async def check_milestone(user_id, message):
    user_id = str(user_id)  # Ensure user_id is always a string
    user_current_sp = user_xp[user_id]
    for milestone, milestone_message in milestone_messages.items():
        if user_current_sp >= milestone and (user_id, milestone) not in reached_milestones:
            reached_milestones.add((user_id, milestone))
            save_reached_milestones()
            await send_milestone_message(message, milestone_message)

async def award_xp(user_id, excitement_score, message):
    user_id = str(user_id)  # Ensure user_id is always a string
    xp_to_award = int(round(excitement_score) * 10)  # You can adjust the multiplier as needed
    if user_id in user_xp:
        user_xp[user_id] += xp_to_award
    else:
        user_xp[user_id] = xp_to_award
    logger.info(f"Awarded {xp_to_award} SP to user {user_id}. Total SP: {user_xp[user_id]}")
    save_user_xp()

    await check_milestone(user_id, message)


async def send_milestone_message(message, milestone_message):
    await message.channel.send(f"{message.author.mention}, {milestone_message}")


def can_award_xp(user_id):
    user_id = str(user_id)  # Ensure user_id is always a string
    current_time = time.time()
    if user_id not in user_cooldowns or current_time - user_cooldowns[user_id] >= cooldown_time:
        user_cooldowns[user_id] = current_time
        return True
    return False


def load_token():
    with open('token.txt', 'r') as f:
        return f.read().strip()


@bot.command(name='spiceboards', help='Display the top N users by Spicy Points (SP).')
async def leaderboard(ctx, top_n: int = 10):
    user_xp = load_user_xp()
    sorted_xp = sorted(user_xp.items(), key=lambda x: x[1], reverse=True)
    leaderboard_embed = discord.Embed(title='Leaderboard', description=f'Top {top_n} users by Spicy Points (SP):', color=0x00ff00)
    for i, (user_id, xp) in enumerate(sorted_xp[:top_n], start=1):
        user = await bot.fetch_user(user_id)
        leaderboard_embed.add_field(name=f"{i}. {user.name}", value=f"{xp} SP", inline=False)
    await ctx.send(embed=leaderboard_embed)

@bot.command(name='spice', help='Get your current SP.')
async def spice(ctx):
    user_xp = load_user_xp()
    user_id = str(ctx.message.author.id)
    if user_id in user_xp:
        await ctx.send(f"{ctx.message.author.mention}, you currently have {user_xp[user_id]} Spice points (SP).")
    else:
        await ctx.send(f"{ctx.message.author.mention}, you don't have any SP yet.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{ctx.author.mention}, the command '{ctx.message.content}' was not found. Please check !help and try again.")
    else:
        raise error

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_message(message):
    logger.info(f'Message: {message.content}')
    if message.author == bot.user:
        return

    excitement_result, excitement_score = is_spciy_content(message.content)
    if excitement_result == 'NSFW' and excitement_score > 0.93 and can_award_xp(message.author.id):
        logger.info(f"Spicy content detected: {message.content}")
        award_xp(message.author.id, excitement_score, message)
        # await message.channel.send(f"{message.author.mention}, that's some spicy content! You've been awarded {int(excitement_score * 100)} SP!")

    await bot.process_commands(message)


user_xp = load_user_xp()
milestones = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 5000, 10000]
milestone_messages = {
    50: "Sheesh! You've reached 100 SP! Things are getting spicy!",
    100: "Sheesh! You've reached 200 SP! Things are actually getting spicy.",
    200: "Ugh! You've reached 300 SP! It's getting too hot to handle!",
    300: "Ew! You've reached 400 SP! Your taste buds are begging for mercy!",
    400: "Gross! You've reached 500 SP! This is way beyond edible.",
    500: "Yuck! You've reached 600 SP! This level of spice should be illegal.",
    600: "Oh no! You've reached 700 SP! It's like swallowing lava!",
    700: "Blech! You've reached 800 SP! This spice is more painful than a root canal!",
    800: "Disgusting! You've reached 900 SP! Your tongue has officially surrendered.",
    900: "Repulsive! You've reached 1000 SP! Congrats on making your taste buds cry.",
    1000: "Appalling! You've reached 5000 SP! This is the culinary equivalent of a nuclear meltdown!",
    5000: "Horrific! You've reached 10000 SP! The spice level is so high, it's a war crime.",
    # Add more milestones and messages here
}
reached_milestones = load_reached_milestones()
user_cooldowns = {}
cooldown_time = 60  # Cooldown time in seconds

TOKEN = load_token()
bot.run(TOKEN)
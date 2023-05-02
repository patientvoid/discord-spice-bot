import logging
import discord
import time
import json
from discord.ext import commands
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:[%(name)s]: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Initialize the tokenizer and model for the text classifier
tokenizer = AutoTokenizer.from_pretrained('michellejieli/NSFW_text_classifier')
model = AutoModelForSequenceClassification.from_pretrained('michellejieli/NSFW_text_classifier')
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)

# Create a bot instance with the given command prefix and intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


def is_spicy_content(message):
    """Classify message as NSFW or not and return the result and score."""
    result = classifier(message)
    logger.info(f"Output: {result}")
    return result[0]['label'], result[0]['score']


def save_user_xp():
    """Save user XP to a JSON file."""
    with open('user_xp.json', 'w') as f:
        json.dump(user_xp, f)


def load_user_xp():
    """Load user XP from a JSON file."""
    try:
        with open('user_xp.json', 'r') as f:
            loaded_data = json.load(f)
            return {(str(server_id), str(user_id)): value for server_id, user_id, value in loaded_data}
    except FileNotFoundError:
        return {}


def save_reached_milestones():
    """Save reached milestones to a JSON file."""
    with open('reached_milestones.json', 'w') as f:
        json.dump(list(reached_milestones), f)


def load_reached_milestones():
    """Load reached milestones from a JSON file."""
    try:
        with open('reached_milestones.json', 'r') as f:
            loaded_data = json.load(f)
            return {(str(server_id), int(user_id), int(milestone)) for server_id, user_id, milestone in loaded_data}
    except FileNotFoundError:
        return set()


async def check_milestone(user_id, server_id, message):
    """Check if a user has reached a milestone and send a message if they have."""
    user_key = (str(server_id), str(user_id))
    user_current_sp = user_xp[user_key]
    for milestone, milestone_message in milestone_messages.items():
        if user_current_sp >= milestone and (server_id, user_id, milestone) not in reached_milestones:
            reached_milestones.add((server_id, user_id, milestone))
            save_reached_milestones()
            await send_milestone_message(message, milestone_message)


async def award_xp(user_id, server_id, excitement_score, message):
    """Award XP to a user and check if they've reached a milestone."""
    user_key = (str(server_id), str(user_id))
    xp_to_award = int(round(excitement_score) * 10)
    if user_key in user_xp:
        user_xp[user_key] += xp_to_award
    else:
        user_xp[user_key] = xp_to_award
    logger.info(f"Awarded {xp_to_award} SP to user {user_id} in server {server_id}. Total SP: {user_xp[user_key]}")
    save_user_xp()

    await check_milestone(user_id, server_id, message)


async def send_milestone_message(message, milestone_message):
    """Send a message to the channel announcing that the     user reached a milestone."""
    await message.channel.send(f"{message.author.mention}, {milestone_message}")


def can_award_xp(user_id, server_id):
    """Check if a user can be awarded XP based on the cooldown."""
    user_key = (str(server_id), str(user_id))
    current_time = time.time()
    if user_key not in user_cooldowns or current_time - user_cooldowns[user_key] >= cooldown_time:
        user_cooldowns[user_key] = current_time
        return True
    return False


def load_token():
    """Load the bot token from a file."""
    with open('token.txt', 'r') as f:
        return f.read().strip()


@bot.command(name='spiceboards', help='Display the top N users by Spicy Points (SP).')
async def leaderboard(ctx, top_n: int = 10):
    """Show the leaderboard of top N users with the most Spicy Points."""
    user_xp = load_user_xp()
    sorted_xp = sorted(user_xp.items(), key=lambda x: x[1], reverse=True)
    leaderboard_embed = discord.Embed(
        title='Leaderboard',
        description=f'Top {top_n} users by Spicy Points (SP):',
        color=0x00ff00
    )
    for i, (user_id, xp) in enumerate(sorted_xp[:top_n], start=1):
        user = await bot.fetch_user(user_id)
        leaderboard_embed.add_field(name=f"{i}. {user.name}", value=f"{xp} SP", inline=False)
    await ctx.send(embed=leaderboard_embed)


@bot.command(name='spice', help='Get your current SP or the SP of a mentioned user.')
async def spice(ctx, member: discord.Member = None):
    """Show the user's current Spicy Points."""
    user_xp = load_user_xp()
    if member:
        user_id = str(member.id)
        user_mention = member.mention
    else:
        user_id = str(ctx.message.author.id)
        user_mention = ctx.message.author.mention

    if user_id in user_xp:
        await ctx.send(f"{user_mention}, you currently have {user_xp[user_id]} Spice points (SP).")
    else:
        await ctx.send(f"{user_mention}, you don't have any SP yet.")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"{ctx.author.mention}, the command '{ctx.message.content}' was not found. Please check !help and try again.")
    else:
        raise error


@bot.event
async def on_ready():
    """Log when the bot is connected to Discord."""
    logger.info(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_message(message):
    """Handle incoming messages, checking for NSFW content and awarding XP."""
    logger.info(f'Message: {message.content}')
    if message.author == bot.user:
        return

    server_id = str(message.guild.id)
    user_id = message.author.id
    excitement_result, excitement_score = is_spicy_content(message.content)
    if excitement_result == 'NSFW' and excitement_score > 0.93 and can_award_xp(user_id, server_id):
        logger.info(f"Spicy content detected: {message.content}")
        await award_xp(user_id, server_id, excitement_score, message)

    await bot.process_commands(message)


# Load data and set up variables
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

# Load the bot token and start the bot
TOKEN = load_token()
bot.run(TOKEN)

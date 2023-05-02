import logging
import discord
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

user_xp = {}
def award_xp(user_id, excitement_score):
    xp_to_award = int(excitement_score * 100)  # You can adjust the multiplier as needed
    if user_id in user_xp:
        user_xp[user_id] += xp_to_award
    else:
        user_xp[user_id] = xp_to_award
    logger.info(f"Awarded {xp_to_award} XP to user {user_id}. Total XP: {user_xp[user_id]}")

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_message(message):
    logger.info(f'Message: {message.content}')
    if message.author == bot.user:
        return

    excitement_result, excitement_score = is_spciy_content(message.content)
    if excitement_result == 'NSFW' and excitement_score > 0.9:
        logger.info(f"Spicy content detected: {message.content}")
        award_xp(message.author.id, excitement_score)
 

    await bot.process_commands(message)

TOKEN = 'MTEwMjY1MjI0OTM4NzMyMzQ0Mg.GpRKDf.7VR4lEd5nscPbsvPf44UVbgwgrQzBBP4kMFpF8'
bot.run(TOKEN)

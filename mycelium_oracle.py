import os
import time
import tweepy
from telegram import Bot
import logging

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Get tokens from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')

# Twitter username to fetch posts from
TWITTER_USERNAME = 'MycelialOracle'

# Define data directory for storing the last tweet ID
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)
LAST_TWEET_FILE = os.path.join(DATA_DIR, 'last_tweet_id.txt')

def load_last_tweet_id():
    try:
        with open(LAST_TWEET_FILE, 'r') as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return None

def save_last_tweet_id(tweet_id):
    with open(LAST_TWEET_FILE, 'w') as f:
        f.write(str(tweet_id))

def main():
    # Check for missing environment variables
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TWITTER_BEARER_TOKEN]):
        logger.error("One or more environment variables are missing.")
        exit(1)

    # Set up Twitter API v2 client
    client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

    # Set up Telegram bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    # Confirm TWITTER_USERNAME is defined and not empty
    if not TWITTER_USERNAME:
        logger.error("Error: TWITTER_USERNAME is not defined or is empty.")
        return

    logger.info(f"Monitoring Twitter account: @{TWITTER_USERNAME}")

    # Get the user ID from the username
    user_response = client.get_user(username=TWITTER_USERNAME)
    if user_response.data is None:
        logger.error(f"User @{TWITTER_USERNAME} not found or access is denied.")
        return
    else:
        user_id = user_response.data.id

    # Load last_tweet_id to avoid reposting old tweets
    last_tweet_id = load_last_tweet_id()

    while True:
        try:
            # Fetch the latest tweets since last_tweet_id
            tweets_response = client.get_users_tweets(
                id=user_id,
                since_id=last_tweet_id,
                max_results=5,
                tweet_fields=['created_at', 'text']
            )
            tweets = tweets_response.data

            if tweets:
                # Tweets are returned in reverse chronological order
                # We'll send them in chronological order
                for tweet in reversed(tweets):
                    message = f"{tweet.text}"
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
                    logger.info(f"Sent tweet ID {tweet.id} to Telegram.")
                    last_tweet_id = tweet.id  # Update last_tweet_id
                    save_last_tweet_id(last_tweet_id)  # Save to file
            else:
                logger.info(f"No new tweets found for user @{TWITTER_USERNAME}.")

            # Wait for a specified interval before checking again
            time.sleep(120)  # Wait for 2 minutes

        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            time.sleep(60)  # Wait before retrying

if __name__ == '__main__':
    main()

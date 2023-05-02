# Spicy Content Discord Bot

A Discord bot that monitors user messages for "spicy" content and awards them Spicy Points (SP). The bot features a leaderboard to display the top users with the most SP, notifies users when they reach certain milestones, and allows users to check their current SP.

## Features

- Award SP to users for sending "spicy" content in the server
- Display a leaderboard of the top users with the most SP
- Notify users when they reach certain milestones
- Allow users to check their current SP

## Commands

- `!spiceboards [top_n]`: Display the top N users by Spicy Points (SP). Default is the top 10 users.
- `!spice`: Get your current SP.

## Setup

1. Clone this repository or download the source code.

2. Install the required dependencies:

```
pip install -r requirements.txt
```


3. Replace the `TOKEN` variable in the script with your Discord bot token:

```python
TOKEN = 'YOUR_BOT_TOKEN_HERE'
```
4. Run the bot:
```
python bot.py
```
## Customization

You can customize the SP milestones and the corresponding messages by editing the `milestone_messages` dictionary in the `bot.py` script:
```
milestone_messages = {
    50: "Sheesh! You've reached 100 SP! Things are getting spicy!",
    100: "Sheesh! You've reached 200 SP! Things are actually getting spicy.",
    # Add or modify milestones and messages here
}
```

## License
This project is licensed under the GNU v3.0 License. See the LICENSE file for details.


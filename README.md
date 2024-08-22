## Hoyolab Auto Check-in

This Python script automates the daily check-in process for Hoyolab, allowing you to claim rewards for Genshin Impact and Honkai: Star Rail without manually visiting the website. It also supports sending notifications to Discord using webhooks.

### Features

* **Automated Check-in:** Automatically checks in for supported games and claims daily rewards.
* **Scheduled Check-in:** Check-ins are triggered between 05:00 and 22:00 UTC.
* **Discord Notifications:** Sends detailed check-in results to a Discord channel via webhook (optional).

### Prerequisites

* **Python 3.9 or higher:** Make sure you have Python 3.9 or a newer version installed on your system.

### Setup

1. **Obtain Your Hoyolab Cookie:**

   * Open your web browser and navigate to the Hoyolab Daily Check-in page
   * Log in to your Hoyolab account.
   * Open the browser's developer tools (usually by pressing F12).
   * Go to the "Console" tab.
   * Paste the following code into the console and press Enter:

     ```javascript
     document.cookie
     ```

   * Copy the entire output. This is your Hoyolab cookie.

2. **Get Your User Agent:**

   * Open your web browser and search for "my user agent" on Google.
   * Copy the user agent string that appears in the search results.

3. **Set Environment Variables:**

   * Create a `.env` file in the same directory as the script.
   * Add the following lines to the `.env` file, replacing the placeholders with your actual values:

     ```
     COOKIE=<your_hoyolab_cookie>
     USER_AGENT=<your_user_agent>
     DISCORD_WEBHOOK=<your_discord_webhook_url> (optional)
     ```

   **Using Multiple Cookies:**

   * If you have multiple Hoyolab accounts, you can use the script to check in for all of them.
   * Obtain the cookies for each account as described in step 1.
   * In your `.env` file, combine the cookies into a single string, separated by `#`:

     ```
     COOKIE=<cookie1>#<cookie2>#<cookie3> 
     ```

### Usage

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Satellaa/Hoyolab-auto-checkin.git
   cd Hoyolab-auto-checkin
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Script:** Execute the script from your terminal:

   ```bash
   python main.py
   ```

The script will start checking in for your linked Genshin Impact and Honkai: Star Rail accounts. If a Discord webhook URL is provided, you will receive notifications in your Discord channel.

### Important Notes

* **Cookie Security:** Keep your Hoyolab cookie safe and secure. Do not share it with anyone.
* **Unsupported Games:** The script currently supports Genshin Impact and Honkai: Star Rail. Other games may not work.
* **API Changes:** Hoyolab's API may change in the future, potentially breaking the script. Updates may be required to keep it functional.

### Disclaimer

This script is provided for convenience purposes only. Use it at your own risk. The author is not responsible for any issues or consequences that may arise from using this script.

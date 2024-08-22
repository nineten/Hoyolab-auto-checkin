## Hoyolab Auto Check-in

This Python script automates the daily check-in process for Hoyolab, allowing you to claim rewards for Genshin Impact, Honkai: Star Rail and Zenless Zone Zero without manually visiting the website. It also supports sending notifications to Discord using webhooks.

### Features

* **Automated Check-in:** Automatically checks in for supported games and claims daily rewards.
* **Scheduled Check-in:** Check-ins are triggered daily at 4:15 PM UTC.
* **Discord Notifications:** Sends detailed check-in results to a Discord channel via webhook (optional).

### Setup

1. **Fork this repository:** Click the "Fork" button at the top right corner of this page to create your own copy of this repository.

2. **Obtain Your Hoyolab Cookie:**

   * Open your web browser and navigate to the Hoyolab Daily Check-in page.
   * Log in to your Hoyolab account.
   * Open the browser's developer tools (usually by pressing F12).
   * Claim your daily reward.
   * Go to the "Network" tab in the developer tools.
   * Look for a request to a URL that contains the word "sign" (e.g., `https://sg-hk4e-api.hoyolab.com/event/sol/sign`).
   * Click on that request to view its details.
   * In the "Request Headers" section, find the `Cookie` header and copy its entire value. This is your Hoyolab cookie. 

3. **Get Your User Agent:**

   * Open your web browser and search for "my user agent" on Google.
   * Copy the user agent string that appears in the search results.

4. **Set Secrets in your forked repository:**

   * Go to the "Settings" tab of your forked repository.
   * Click on "Secrets and variables" -> "Actions".
   * Add the following secrets, replacing the placeholders with your actual values:
     * `COOKIE`: Your Hoyolab cookie.
     * `USER_AGENT`: Your user agent string.
     * `DISCORD_WEBHOOK`: Your Discord webhook URL (optional).

   **Using Multiple Cookies:**

   * If you have multiple Hoyolab accounts, you can use the script to check in for all of them.
   * Obtain the cookies for each account as described in step 2.
   * In the `COOKIE` secret, combine the cookies into a single string, separated by `#`:

     ```
     <cookie1>#<cookie2>#<cookie3> 
     ```

### Important Notes

* **Cookie Security:** Keep your Hoyolab cookie safe and secure. Do not share it with anyone.
* **Supported Games:** The script currently supports Genshin Impact, Honkai: Star Rail and Zenless Zone Zero.
* **API Changes:** Hoyolab's API may change in the future, potentially breaking the script. Updates may be required to keep it functional.

### Disclaimer

This script is provided for convenience purposes only. Use it at your own risk. The author is not responsible for any issues or consequences that may arise from using this script.

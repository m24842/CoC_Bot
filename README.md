<h1 align="center">Clash of Clans Bot</h1>
<p align="center">
    <img src="Cover_Image.png" alt="Cover Image" width="25%">
</p>

## Automated Features
* Resource collection 💰
* Building upgrades 🧱
* Hero upgrades 👑
* Laboratory upgrades 🔬
* Normal attacks ⚔️

## Quality of Life Features
* View status on web app 🚦
* Resume / pause execution through web app ⏯️
* SMS and web app notifications 🔔

## Dependencies
* Install python packages with [setup.py](setup.py)
* [Android Debug Bridge](https://developer.android.com/tools/releases/platform-tools)
    * Add to system path
* [BlueStacks](https://www.bluestacks.com/)
    * Device profile: Samsung Galaxy S22 Ultra
    * Display resolution: 1920 x 1080
    * Install Clash of Clans from Google Play
    * Enable Android Debug Bridge

## Setup Instructions
1. Install and configure dependencies listed above
2. Enter user configurations in [configs.py](src/configs.py)
    * __Note__: To configure SMS notifications, first enable 
    Google 2-Step Verification before generating an 
    [app password](https://myaccount.google.com/apppasswords)
3. Start web app: ```python app/app.py```
    * __Note__: Open port 1234 and configure port forwarding as necessary
4. Start the bot: ```python src/main.py```
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
* Multiple accounts 👥

## Quality of Life Features
* View status on web app 🚦
* Resume / pause execution through web app ⏯️
* Telegram and web app notifications 🔔

## Dependencies
1. Install python packages with [setup.py](setup.py)
2. [Android Debug Bridge](https://developer.android.com/tools/releases/platform-tools)
    * Add to system path
        * Verify with: ```adb --version```
3. [BlueStacks](https://www.bluestacks.com/)
    * Device profile: Samsung Galaxy S22 Ultra
    * Display resolution: 1920 x 1080
    * Enable Android Debug Bridge
    * Install Clash of Clans from Google Play
4. [minitouch](https://app.unpkg.com/minitouch-prebuilt-support10@1.2.0/files/prebuilt) 
(__OPTIONAL__: pyminitouch should automate this)
    * Download prebuilt binary
        * Run ```adb shell getprop ro.product.cpu.abi``` to determine appropriate architecture
    * Open BlueStacks
    * Connect to Android Debug Bridge: ```adb connect 127.0.0.1:5555```
    * Push the binary to BlueStacks:
        ```bash
        adb push <path-to-minitouch> /data/local/tmp/
        adb shell chmod 755 /data/local/tmp/minitouch
        ```
        * Verify with: ```adb shell /data/local/tmp/minitouch```

## Setup Instructions
1. Install and configure dependencies listed above
2. Enter user configurations in [configs.py](src/configs.py)
    * __Note__: To configure Telegram notifications, first set up a [Telegram bot](https://marketplace.creatio.com/sites/marketplace/files/app-guide/Instructions._Telegram_bot_1.pdf?utm_source=chatgpt.com) and send ```/start```. Enter the API token generated during the setup process for ```TELEGRAM_BOT_TOKEN```.
3. Start web app: ```python app/app.py```
    * __Note__: Open port 1234 (or whatever port ```WEB_APP_PORT``` is set to in [configs.py](src/configs.py)) and configure port forwarding as necessary. Each bot instance can be accessed at ```WEB_APP_ADDRESS/<instance_name>``` (the default instance name is main).
4. Start the bot: ```python src/main.py```
    * __Note__: The BlueStacks window can be minimized without disrupting the bot as all interactions are handled through Android Debug Bridge
    * __Note__: On MacOS, if ```DISABLE_DEEVICE_SLEEP = True``` in [configs.py](src/configs.py), the user password is required to toggle the ```disablesleep``` flag in power management settings
5. To run bots for multiple accounts just create additional BlueStacks instances with BlueStacks' multi-instance manager,
    set up the instance as usual, and append new instance names and their Android Debug Bridge addresses to ```INSTANCE_IDS``` and ```ADB_ADDRESSES``` in [configs.py](src/configs.py)
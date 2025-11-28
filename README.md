<h1 align="center">Clash of Clans Bot</h1>
<p align="center">
    <img src="Cover_Image.png" alt="Cover Image" width="25%">
</p>

## Automated Features (Both Villages)
* Resource collection 💰
* Building upgrades 🧱
* Hero upgrades 👑
* Laboratory upgrades 🔬
* Normal attacks ⚔️
* Multiple accounts 👥

## Quality of Life Features
* View bot status on web app 🚦
* Resume / pause bot execution from web app ⏯️
* iPhone shortcut to auto resume / pause bot when CoC is opened by user ⏯️
* Telegram and web app notifications 🔔

## Dependencies
1. Install python packages with [setup.py](setup.py)
2. [Android Debug Bridge](https://developer.android.com/tools/releases/platform-tools)
    * Add to system path
        * Verify with: ```adb --version```
3. [BlueStacks](https://www.bluestacks.com/)
    * Device profile: Samsung Galaxy S22 Ultra
    * Display resolution: 1920 x 1080
    * Frame rate: 60 (__NOTE__: Inconsistent touch events at lower fps)
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
    * __Note__: It is recommended to host the web app on [pythonanywhere](https://www.pythonanywhere.com) using the provided [wsgi.py](app/wsgi.py) template and [this tutorial](https://medium.com/@cssjhnnamae/how-to-deploy-a-python-app-on-pythonanywhere-cf399f4bbc01). Free accounts can host a single web app for an extendable period of 3 months.
    * __Note__: If you enable password protection on pythonanywhere, you'll need to enter the credentials into ```WEB_APP_AUTH_USERNAME``` and ```WEB_APP_AUTH_PASSWORD``` in [configs.py](src/configs.py)
    * __Note__: If hosting from a personal device, open port 1234 (or whatever port ```WEB_APP_PORT``` is set to in [configs.py](src/configs.py)) and configure port forwarding as necessary
    * Each bot instance can be accessed at ```WEB_APP_ADDRESS/<instance_name>``` (the default instance name is ```main```)
4. Setup iPhone shortcut:
    * Open the [provided shortcut](<CoC Bot Auto Pause.shortcut>) on an iPhone
    * Enter your ```WEB_APP_URL``` into the first Text variable
    * If applicable, enter your web app auth credentials into the second Text variable as ```WEB_APP_AUTH_USERNAME:WEB_APP_AUTH_PASSWORD```
    * Adjust the List variable containing instance names as necessary
    * Create an Automation task that runs when CoC opens and is set to run immediately
5. Start the bot: ```python src/main.py```
    * __Note__: ```src/start.sh``` uses tmux to start the bot in the background. It is recommended to just run the bot in the background by starting a tmux session, running ```src/main.py```, and detaching manually.
    * __Note__: The BlueStacks window can be minimized without disrupting the bot as all interactions are handled through Android Debug Bridge
    * __Note__: On MacOS, if ```DISABLE_DEEVICE_SLEEP = True``` in [configs.py](src/configs.py), the user password is required to toggle the ```disablesleep``` flag in power management settings.
    * To run bots for multiple accounts just create additional BlueStacks instances with BlueStacks' multi-instance manager, set up the instance as usual, and append new instance names and their Android Debug Bridge addresses to ```INSTANCE_IDS``` and ```ADB_ADDRESSES``` in [configs.py](src/configs.py)
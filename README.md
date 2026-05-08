<h1 align="center">Clash of Clans Bot</h1>
<p align="center">
    <a href="https://youtu.be/2xQgiqBmqAU">
        <img src="media/Cover_Image.png" alt="Cover Image" width="25%">
    </a>
    <br>
    <a href="https://youtu.be/2xQgiqBmqAU">Click for Demo Video</a>
</p>

## Automated Features (Both Villages)
* Resource collection 💰
* Hero upgrades 👑
* Building upgrades 🧱
* Laboratory upgrades 🔬
* Assistant assignment ⏩️
* Normal attacks ⚔️
* Full upgrade priority control 🚦
* Multiple accounts 👥

## Quality of Life Features
* View bot status on desktop or web app 🚦
* Resume / pause bot execution from desktop or web app ⏯️
* iPhone shortcut to auto resume / pause bot when CoC is opened by user ⏯️
* Telegram and web app notifications 🔔
* Automatic CoC app updates 🔼

## Dependencies
1. Install python packages with [setup.py](setup.py)
2. [Android Debug Bridge](https://developer.android.com/tools/releases/platform-tools)
    * Add to system path
        * Verify with: `adb --version`
3. [BlueStacks](https://www.bluestacks.com/)
    * Device profile: Samsung Galaxy S22 Ultra
    * Display resolution: 1920 x 1080
    * Frame rate: 60 (__NOTE__: Inconsistent touch events at lower fps)
    * Enable Android Debug Bridge
    * Install Clash of Clans from Google Play
        * Default troop deployment size
        * Standard or XL scenery
4. [minitouch](https://app.unpkg.com/minitouch-prebuilt-support10@1.2.0/files/prebuilt) 
(__OPTIONAL__: pyminitouch should automate this)
    * Download prebuilt binary
        * Run `adb shell getprop ro.product.cpu.abi` to determine appropriate architecture
    * Open BlueStacks
    * Connect to Android Debug Bridge: `adb connect 127.0.0.1:5555`
    * Push the binary to BlueStacks:
        ```bash
        adb push <path-to-minitouch> /data/local/tmp/
        adb shell chmod 755 /data/local/tmp/minitouch
        ```
        * Verify with: `adb shell /data/local/tmp/minitouch`

## Setup Instructions
1. Install and configure dependencies listed above

2. Enter user configurations in `configs.py`
    > ❗️ __Important__: [setup.py](setup.py) creates `configs.py` from [configs.template.py](src/configs.template.py)

    > ❗️ __Important__: By default, all capabilities are enabled. Many configurations can be overridden in real time if using the desktop or web app.

    > __Note__: If using priority upgrades, instructions for defining upgrade priorities can be found in `configs.py`.

    > __Note__: To configure Telegram notifications, first set up a [Telegram bot](https://marketplace.creatio.com/sites/marketplace/files/app-guide/Instructions._Telegram_bot_1.pdf?utm_source=chatgpt.com) and send `/start`. Enter the API token generated during the setup process for `TELEGRAM_BOT_TOKEN`.

    > __Note__: If local OCR is too slow, you can offload it to [groq](https://console.groq.com). Just make an account and set up an API key to use for `GROQ_API_KEY` in `configs.py`. The free tier will hit the token rate limit after a while after which the bot will revert to local OCR.

3. Start web app: `python app/app.py`
    > 💡 __Tip__: It is recommended to host the web app on [pythonanywhere](https://www.pythonanywhere.com) using the provided [wsgi.py](app/wsgi.py) template and [this tutorial](https://medium.com/@cssjhnnamae/how-to-deploy-a-python-app-on-pythonanywhere-cf399f4bbc01). Free accounts can host a single web app for an extendable period of 1 month (the bot can automatically extend hosting). If you want to enable automatic pythonanywhere hosting extension, enter your pythonanywhere username and passowrd into `PA_USERNAME` and `PA_PASSWORD` respectively in `configs.py`.
    
    > ❗️ __Important__: If hosting from a personal device, configure port forwarding as necessary
    
    * Each bot instance can be accessed at `WEB_APP_ADDRESS/<instance_name>` (the default instance name is `main`)
    * View a demo of the web app [here](https://youtu.be/_R6PbJ4_SzQ)

4. Setup iPhone shortcut:
    > __Note__: An [older version](<shortcut/CoC Bot Auto Pause Old.shortcut>) of the shortcut is provided that does not require Scriptable, but is incapable of handling request errors
    
    * Download [Scriptable](https://apps.apple.com/us/app/scriptable/id1405459188) and create a new script named "CoC Bot Script" with the contents of [CoC_Bot_Script.js](<shortcut/Scriptable.js>)
    * Open the [provided shortcut](<shortcut/CoC Bot Auto Pause.shortcut>)
    * Enter your `WEB_APP_URL` into the `url` item of the Dictionary
    * Adjust the `id` item containing an array of instance names as necessary
    * Create an Automation task that runs when CoC opens and is set to run immediately

5. Start the bot: `python src/main.py`
    > __Note__: [start.sh](scripts/start.sh) uses tmux to start the bot in the background.

    > __Note__: On MacOS, if `DISABLE_DEVICE_SLEEP = True` in `configs.py`, the user password is required to toggle the `disablesleep` flag in power management settings

    > 💡 __Tip__: The BlueStacks window can be minimized without disrupting the bot as all interactions are handled through Android Debug Bridge

    > 💡 __Tip__: If not using the bot for development purposes, it can be built into an executable or desktop app for convenience using [build.sh](scripts/build.sh). The desktop app GUI or command-line arguments can be used to specify the instance to run if using multiple bot instances. View a demo of the desktop app [here](https://youtube.com/shorts/zVZwBW8QIeY?feature=share).

    * To run bots for multiple accounts just create additional BlueStacks instances with BlueStacks' multi-instance manager, set up the instance as usual, and append new instance names and their Android Debug Bridge addresses to `INSTANCE_IDS` and `ADB_ADDRESSES` in `configs.py`. Specify the instance to run using the `--id` flag (e.g. `python src/main.py --id main`).
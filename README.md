<h1 align="center">Clash of Clans Bot</h1>
<p align="center">
    <a href="#updated-bot-demo">
        <img src="media/Cover_Image.png" alt="Cover Image" width="25%">
    </a>
    <br>
    <a href="#updated-bot-demo">Click for Demo Video</a>
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
* Automatic emulator instance launch / shutdown (BlueStacks or MuMu Player) 🔌

## Dependencies
1. [Android Debug Bridge](https://developer.android.com/tools/releases/platform-tools)
    * Add to system path
        * Verify with: `adb --version`
2. An Android emulator — either [BlueStacks](https://www.bluestacks.com/) or [MuMu Player](https://www.mumuplayer.com/) (set `EMULATOR_TYPE` accordingly in `configs.py`)
    * The specs below apply to whichever emulator you choose:
        * Device profile: Samsung Galaxy S22 Ultra
        * Display resolution: 1920 x 1080
        * Frame rate: 60 (__NOTE__: Inconsistent touch events at lower fps)
        * Install Clash of Clans from Google Play
            * Default troop deployment size
            * Standard or XL scenery

    __If using BlueStacks:__
    * Enable Android Debug Bridge in "Advanced" settings
    * In Multi-Instance Manager, rename instances to match instance IDs in `configs.py` (the default ID is main, see steps 3 and 6 in [Custom Setup Instructions](#custom-setup-instructions-recommended) for more details)

    __If using MuMu Player:__
    * In MuMu's multi-instance manager, rename instances to match instance IDs in `configs.py` (same convention as BlueStacks above)
    * The bot drives MuMu through its official `MuMuManager.exe` CLI (found under `<MuMu install dir>/nx_main/MuMuManager.exe`); if it's not auto-detected, set `MUMU_BIN_PATH` in `configs.py`
    * Windows only — MuMu Player support relies on `MuMuManager.exe`

## Default Setup Instructions
1. Install and configure [external dependencies](#dependencies)

1. Download the [latest release](https://github.com/m24842/CoC_Bot/releases/latest) for your OS
    > __Note__: Prebuilt releases are minimally configured and only support standard features. To set up the bot with custom configurations, see [Custom Setup Instructions](#custom-setup-instructions-recommended).

    > __Note__: Prebuilt releases generally will not have the most up-to-date features and may contain unpatched bugs. To stay up to date, it is suggested to run from source.

    * Releases are built for MacOS (Apple Silicon) and Windows only
    * GUI and CLI versions are available with each release

1. MacOS users must allow the app/binary to run by going to "Settings > Privacy & Security" and clicking "Open Anyways"

## Custom Setup Instructions (Recommended)
1. Install and configure [external dependencies](#dependencies)

1. Install python dependencies with [setup.py](setup.py)

1. Enter user configurations in `configs.py`
    > ❗️ __Important__: [setup.py](setup.py) creates `configs.py` from [configs.template.py](src/configs.template.py)

    > ❗️ __Important__: By default, all capabilities are enabled. Many configurations can be overridden in real time if using the desktop or web app.

    > __Note__: If using priority upgrades, instructions for defining upgrade priorities can be found in `configs.py`.

    > __Note__: To configure Telegram notifications, first set up a [Telegram bot](https://marketplace.creatio.com/sites/marketplace/files/app-guide/Instructions._Telegram_bot_1.pdf?utm_source=chatgpt.com) and send `/start`. Enter the API token generated during the setup process for `TELEGRAM_BOT_TOKEN`.

    > __Note__: If local OCR is too slow, you can offload it to [groq](https://console.groq.com). Just make an account and set up an API key to use for `GROQ_API_KEY` in `configs.py`. The free tier will hit the token rate limit after a while after which the bot will fallback to local OCR.

1. Start web app: `python app/app.py`
    > 💡 __Tip__: It is recommended to host the web app on [pythonanywhere](https://www.pythonanywhere.com) using the provided [wsgi.py](app/wsgi.py) template and [this tutorial](https://medium.com/@cssjhnnamae/how-to-deploy-a-python-app-on-pythonanywhere-cf399f4bbc01). Free accounts can host a single web app for an extendable period of 1 month (the bot can automatically extend hosting). If you want to enable automatic pythonanywhere hosting extension, enter your pythonanywhere username and passowrd into `PA_USERNAME` and `PA_PASSWORD` respectively in `configs.py`.
    
    > ❗️ __Important__: If hosting from a personal device, configure port forwarding as necessary
    
    * Each bot instance can be accessed at `WEB_APP_URL/<instance_id>` (the default instance ID is `main`)
    * View a demo of the web app [here](#web-app-demo)

1. Setup iPhone shortcut:
    > ❗️ __Important__: iOS will terminate long running shortcuts after about 30-60 mins (there's no reported limit so times may vary). To ensure the bot is paused for longer, it is suggested to set the shortcut to "run after confirmation" so that the pause duration can be set arbitrarily high through the web app when desired.

    > __Note__: An [older version](<shortcut/CoC Bot Auto Pause Old.shortcut>) of the shortcut is provided that does not require Scriptable, but is incapable of handling request errors
    
    * Download [Scriptable](https://apps.apple.com/us/app/scriptable/id1405459188) and create a new script named "CoC Bot Script" with the contents of [CoC_Bot_Script.js](<shortcut/Scriptable.js>)
    * Open the [provided shortcut](<shortcut/CoC Bot Auto Pause.shortcut>)
    * Enter your `WEB_APP_URL` into the `url` item of the Dictionary
    * Add your instance ids to the `ids` array in the Dictionary (main is added by default)
    * Create an Automation task that runs when CoC opens and is set to run immediately

1. Start the bot: `python src/main.py`
    > ❗️ __Important__: By default, the bot is configured to start and stop its emulator instance automatically. If this behavior is undesired or causing issues, just set `AUTO_START_EMULATOR = False` in `configs.py`

    > __Note__: On MacOS, if `DISABLE_DEVICE_SLEEP = True` in `configs.py`, the user password is required to toggle the `disablesleep` flag in power management settings

    > 💡 __Tip__: The emulator window can be minimized without disrupting the bot as all interactions are handled through Android Debug Bridge

    > 💡 __Tip__: If not using the bot for development purposes, it can be built into an executable or desktop app for convenience using [build.sh](scripts/build.sh). The desktop app GUI or command-line arguments can be used to specify the instance to run if using multiple bot instances. View a demo of the desktop app [here](#desktop-app-demo).

    * To run bots for multiple accounts just create additional instances with your emulator's multi-instance manager (ensuring instance names match bot instance IDs), set up the instance as usual, and append new instance names to `INSTANCE_IDS` in `configs.py`. Specify the instance to run using the `--id` flag (e.g. `python src/main.py --id main`).

## Miscellaneous
* Please report issues in the [Issues Tab](https://github.com/m24842/CoC_Bot/issues)
* For help with setup or usage, open a discussion in [Q&A](https://github.com/m24842/CoC_Bot/discussions/categories/q-a)
* Suggest new features in [Ideas](https://github.com/m24842/CoC_Bot/discussions/categories/ideas)

## Demos
### Updated Bot Demo
https://github.com/user-attachments/assets/88e4a675-758b-403a-8496-9490ccffe1b3

### Original Bot Demo
https://github.com/user-attachments/assets/735bb9c0-074d-4dcd-9e3a-e0256b2d9438

### Web App Demo
https://github.com/user-attachments/assets/3068863a-fa5a-4bef-bfb5-fb35f56ddd16

### Desktop App Demo
https://github.com/user-attachments/assets/a0893115-0feb-4dba-ab29-756a2f422a83

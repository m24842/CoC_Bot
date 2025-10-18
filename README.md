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
    * __Note__: To configure SMS notifications, first enable 
    Google 2-Step Verification before generating an 
    [app password](https://myaccount.google.com/apppasswords)
3. Start web app: ```python app/app.py```
    * __Note__: Open port 1234 and configure port forwarding as necessary
4. Start the bot: ```python src/main.py```
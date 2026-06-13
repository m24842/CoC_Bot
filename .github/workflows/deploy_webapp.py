import time
import argparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def deploy(host, username, password, token, console_id):
    login_url = f"{host}/login/"
    console_url = f"{host}/user/{username}/consoles/{console_id}/"
    console_input_url = f"{host}/api/v0/user/{username}/consoles/{console_id}/send_input/"
    webapp_reload_url = f"{host}/api/v0/user/{username}/webapps/{username}.pythonanywhere.com/reload/"

    headers = {"Referer": host}

    session = requests.Session()

    # Login
    session.get(login_url)
    session.post(
        login_url,
        data={
            "csrfmiddlewaretoken": session.cookies.get_dict().get("csrftoken"),
            "auth-username": username,
            "auth-password": password,
            "login_view-current_step": "auth",
        },
        headers=headers,
    )
    assert "Log out" in session.get(host).text, "Login failed."
    print("Login successful.")

    # Startup console process
    options = Options()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.get(host)
    for cookie in session.cookies:
        driver.add_cookie({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
        })
    driver.refresh()
    driver.get(console_url)
    time.sleep(3) # wait for console to startup
    assert driver.current_url == console_url, "Failed to startup console."
    print("Console started successfully.")

    # Send console input
    for _ in range(3):
        res = requests.post(
            console_input_url,
            headers={'Authorization': 'Token {token}'.format(token=token)},
            data={'input': 'git pull\n'}
        )
        if res.status_code == 200: break
        time.sleep(2)
    assert res.status_code == 200, "Failed to send git pull command to console."
    print("Git pull command sent successfully.")

    # Reload webapp
    res = requests.post(
        webapp_reload_url,
        headers={'Authorization': 'Token {token}'.format(token=token)}
    )
    assert res.status_code == 200, "Failed to reload webapp."
    print("Webapp reloaded successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="https://www.pythonanywhere.com", help="PythonAnywhere host URL")
    parser.add_argument("--username", type=str, required=True, help="PythonAnywhere username")
    parser.add_argument("--password", type=str, required=True, help="PythonAnywhere password")
    parser.add_argument("--token", type=str, required=True, help="PythonAnywhere API token")
    parser.add_argument("--console-id", type=int, required=True, help="ID of the console to send commands to")
    args = parser.parse_args()

    deploy(args.host, args.username, args.password, args.token, args.console_id)
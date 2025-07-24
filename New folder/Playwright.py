import asyncio
from playwright.async_api import async_playwright
import re
import math
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def is_camel_case(name):
    words = name.split()
    return all(word[0].isupper() and word[1:].islower() for word in words if word.isalpha())

def has_correct_suffix(name):
    if 'Inc' in name:
        return name.endswith(', Inc.')
    if 'LLC' in name.upper():
        return 'LLC' in name and name.endswith('LLC')
    return True

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto('https://demo.intellibank.io/login')

        cookies = [
            {'name': 'accessToken', 'value': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2ODVlMzI1OGRmYjhiZWZjZDY4OWRlZjUiLCJlbWFpbCI6ImlfdmlzaGFsQGRlbmF2ZS5jb20iLCJpYXQiOjE3NTI0NjgyMDYsImV4cCI6MTc1MjQ5NzAwNn0.PJsF8lqttlw84-SwnyF-67DLYNgHpJWQBF6NWh9fH24', 'domain':'demo.intellibank.io', 'path':'/'},
            {'name': 'session-id', 'value': '5b93fd25-2cb0-42a3-a7b1-0193af642ab2', 'domain':'demo.intellibank.io', 'path':'/'}, 
        ]
        await context.add_cookies(cookies)

        await page.goto('https://demo.intellibank.io/accounts?tab=accounts&tableTab=all&page=1&perPage=1000&sort=updatedAt%3Adesc')

        await page.wait_for_selector("//button[contains(@class,'text-white')]")
        button_text = await page.locator("//button[contains(@class,'text-white')]").inner_text()
        number_of_accounts = int(re.search(r'\d+', button_text).group())
        no_of_pages = math.ceil(number_of_accounts / 1000)

        print(f"✅ Total accounts detected: {number_of_accounts}")
        print(f"✅ Total pages calculated: {no_of_pages}")

        for page_num in range(1, no_of_pages + 1):
            current_url = page.url
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            query_params['page'] = [str(page_num)]
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))

            await page.goto(new_url)

            await page.wait_for_selector("//tbody//tr//td[1]//span//div//a", timeout=10000)
            await asyncio.sleep(2)

            account_elements = page.locator("//tbody//tr//td[1]//span//div//a")
            count = await account_elements.count()

            for i in range(count):
                account_name = (await account_elements.nth(i).inner_text()).strip()

                clean_name = re.sub(r'(, Inc\.| LLC)$', '', account_name).strip()
                camel_case_valid = is_camel_case(clean_name)
                suffix_valid = has_correct_suffix(account_name)

                if camel_case_valid and suffix_valid:
                    print(f"✅ Valid: {account_name}")
                else:
                    if not camel_case_valid:
                        print(f"❌ Camel Case Error: {account_name}")
                    if not suffix_valid:
                        print(f"❌ Suffix Format Error: {account_name}")

        await context.close()
        await browser.close()

asyncio.run(run())

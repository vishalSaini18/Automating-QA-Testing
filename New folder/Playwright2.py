
import re
import math
import asyncio
from playwright.async_api import async_playwright

# Set no. of accounts per page
NoAcc = 100

# Function to extract city and country from company overview page
async def extract_company_page_city_country(page):
    full_address = await page.locator("//span[@class='text-black w-fit']").text_content()
    full_address = full_address.strip()

    if ',' in full_address:
        city, country = full_address.split(',', 1)
        city = city.strip()
        country = country.strip()
        return city, country
    else:
        return None, None


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()

        # Open login page to set cookies
        await page.goto('https://demo.intellibank.io/login')

        # Set authentication cookies (use your valid tokens here)
        cookies = [
            {'name': 'accessToken', 'value': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2ODVlMzI1OGRmYjhiZWZjZDY4OWRlZjUiLCJlbWFpbCI6ImlfdmlzaGFsQGRlbmF2ZS5jb20iLCJpYXQiOjE3NTI0NzIwMzgsImV4cCI6MTc1MjUwMDgzOH0.Yd62Kpk71DJ10_Oe-3q5W512Oy7TLO4oqCLPQKBL3CY', 'domain': 'demo.intellibank.io', 'path': '/'},
            {'name': 'session-id', 'value': 'd5c7547f-5573-40c8-b349-cf54dc113c81', 'domain': 'demo.intellibank.io', 'path': '/'},
        ]
        await context.add_cookies(cookies)

        # Open accounts homepage
        await page.goto(f'https://demo.intellibank.io/accounts?tab=accounts&tableTab=all&page=1&perPage={NoAcc}&sort=updatedAt%3Adesc')

        # Wait for number of accounts to load
        await page.wait_for_selector("//button[contains(@class,'text-white')]")
        button_text = await page.locator("//button[contains(@class,'text-white')]").inner_text()

        # Extract total number of accounts
        number_of_accounts = int(re.search(r'\d+', button_text).group())
        no_of_pages = math.ceil(number_of_accounts / NoAcc)

        print(f"✅ Total accounts detected: {number_of_accounts}")
        print(f"✅ Total pages calculated: {no_of_pages}")

        # Iterate through each page
        for page_num in range(1, no_of_pages + 1):
            await page.goto(f'https://demo.intellibank.io/accounts?tab=accounts&tableTab=all&page={page_num}&perPage={NoAcc}&sort=updatedAt%3Adesc')

            await page.wait_for_selector("//tbody//tr//td[1]//span//div//a", timeout=15000)
            total_accounts_on_page = await page.locator("//tbody//tr//td[1]//span//div//a").count()

            for index in range(total_accounts_on_page):
                account_locator = page.locator(f"//tbody/tr[{index+1}]/td[1]/div[1]/span[1]/div[1]/a[1]")
                company_name = (await account_locator.inner_text()).strip()

                homepage_city = (await page.locator(f"//tbody/tr[{index+1}]//span[1]/div[1]/span[1]/span[1]").inner_text()).strip().rstrip(',')
                homepage_country = (await page.locator(f"//tbody/tr[{index+1}]//span[1]/div[1]/span[1]/span[2]").inner_text()).strip()

                # Open company details page in a new tab
                # Open company details page in a new tab
                details_page = await context.new_page()
                relative_url = await account_locator.get_attribute("href")
                full_url = f"https://demo.intellibank.io{relative_url}"
                await details_page.goto(full_url)
                await details_page.wait_for_selector("//span[@class='text-black w-fit']", timeout=15000)

                details_city, details_country = await extract_company_page_city_country(details_page)

                city_match = homepage_city == details_city
                country_match = homepage_country == details_country

                print(f"✅ Page [{page_num}]({index+1}), {company_name}:")
                print(f"   Homepage City: {homepage_city}, Homepage Country: {homepage_country}")
                print(f"   Details Page City: {details_city}, Details Page Country: {details_country}")
                print(f"   City Match:{'✅' if city_match else '❌'}, Country Match:{'✅' if country_match else '❌'}")

                await details_page.close()

        await context.close()
        await browser.close()

# Run the async script
asyncio.run(run())

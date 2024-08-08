import puppeteer from 'puppeteer';
import { type Page } from 'puppeteer';

const user = 'replaceme@example.com';
const password = 'REPLACE-ME';

const login = async (page: Page) => {
    await page.waitForSelector('#username');
    await page.type('#username', user);
    await page.waitForSelector('#password');
    await page.type('#password', password);
    page.keyboard.press('Enter');
    await page.waitForNavigation();
};

const main = async () => {
    const browser = await puppeteer.launch({
        args: ['--no-sandbox'],
        headless: false,
        slowMo: 10,
    });
    const page: Page = await browser.newPage();
    await page.setViewport({width: 1080, height: 1024});
    await page.goto('https://linkedin.com/login');
    await login(page);
};

main();
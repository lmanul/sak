import puppeteer from 'puppeteer';
import { type Page } from 'puppeteer';

const user = 'replaceme@example.com';
const password = 'REPLACE-ME';

const delay = (milliseconds: number) => {
    return new Promise(function(resolve) {
        setTimeout(resolve, milliseconds)
    });
 }

const login = async (page: Page) => {
    await page.waitForSelector('#username');
    await page.type('#username', user);
    await page.waitForSelector('#password');
    await page.type('#password', password);
    page.keyboard.press('Enter');
    await page.waitForNavigation();
};

// Returns whether we have actually archived a message.
const archiveFirstShownMessage = async (page: Page): Promise<boolean> => {
    let item;
    try {
        item = await page.waitForSelector('.msg-conversation-listitem__link', { timeout: 5000});
    } catch (TimeoutError) {
        // Looks like we're done.
        return false;
    }
    await item?.click();
    const dropdownButton = await page.waitForSelector(
        '.msg-overlay-conversation-bubble .msg-thread-actions__dropdown');
    await dropdownButton?.click();
    try {
      const archiveMenuItem = await page.waitForSelector('text/Archive');
      await archiveMenuItem?.click();
    } catch (TimeoutError) {
      // Oh well. Skip this one.
      return true;
    }
    return true;
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
    let keepGoing = true;
    while (keepGoing) {
        keepGoing = await archiveFirstShownMessage(page);
        await delay(300);
    }
    // There's also the "Other" tab.
    keepGoing = true;
    const otherTab = await page.waitForSelector('text/Other');
    await otherTab?.click();
    while (keepGoing) {
        keepGoing = await archiveFirstShownMessage(page);
        await delay(300);
    }
    browser.close();
};

main();
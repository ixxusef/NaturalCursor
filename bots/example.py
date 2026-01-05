# Import wanted classes from human_utils
from core.human_utils import Logger, BrowserManager, MouseManager, DelayManager, TypingManager

# Assign browser instance. Make sure to run ./open.ps1 to start chrome.
browser = BrowserManager("http://localhost:9222")

# Connect to the browser
context = browser.connect()

# Create page instance. This is the website you want to use.
page = browser.create_page("https://example.com")

# Assign additional instances 
logger = Logger()
mouse = MouseManager()
delay = DelayManager()
safe_keyboard = TypingManager

# Enable mouse tracking to visualize movement 
mouse.enable_cursor_tracking(page)

# Create a Playwright locator object of the heading 
heading = page.get_by_role("heading", name="Example Domain")

# Simulate reading/interest in the section by moving the cursor to that area and idling.
delay.idle_delay(
    page = page, 
    element = heading
    )

# Let's now automate some navigation!

learn_more_button = page.get_by_role("link", name="Learn more")

mouse.safe_click(page, learn_more_button)

logger.log("Clicked 'learn more", 1)

delay.human_delay(2,5,"because, just beacause!")

page = browser.create_page("https://google.com")

mouse.enable_cursor_tracking(page)

search_text_box = page.get_by_role("combobox", name="Search")

mouse.safe_click(page, search_text_box)

safe_keyboard.human_typing(page, search_text_box, "github")

page.keyboard.press("Enter")

logger.log("We're back!",1)

page.pause()
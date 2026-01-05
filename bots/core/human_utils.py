import time
import random
import math
import json
import requests
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, expect
from core.config import *
from enum import Enum
import filetype
"""
Human-like browser automation utilities built on Playwright.

Includes:
- Browser lifecycle management
- Config loading
- Human-like mouse, typing, scrolling, and delays
- Logging utilities
"""

class enums:
    class Categories(Enum):
        MOVERS = "movers"
        LIVE = "live"
        NEW = "new"


class BrowserManager:
    """
    Manages the lifecycle of a Playwright browser connection using Chrome DevTools Protocol (CDP).

    Responsibilities:
    - Establishing a connection to an already-running Chromium browser
    - Managing browser contexts
    - Creating, restarting, and closing pages
    - Cleaning up Playwright resources safely
    """

    def __init__(self, cdp_url: str = "http://localhost:9222"):
        """
        Initialize the BrowserManager.

        This does NOT connect to the browser immediately. Call `connect()` to
        establish the Playwright + CDP connection.

        :param cdp_url: URL of the Chrome DevTools Protocol endpoint.
                        The browser must be launched with
                        `--remote-debugging-port=9222`.
        :type cdp_url: str
        """
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None

    def connect(self) -> BrowserContext:
        """
        Connect to an existing Chromium-based browser via CDP.

        This method:
        - Starts Playwright
        - Connects to the browser over CDP
        - Selects the first available browser context
        - Stores the context for future page creation

        :raises Exception: If the browser is not reachable or Playwright fails to connect.
        :return: The active Playwright BrowserContext.
        :rtype: BrowserContext
        """
        Logger.log(f"Connecting to browser via CDP at {self.cdp_url}")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0]

            Logger.log(
                f"Successfully connected. Found {len(self.browser.contexts)} context(s)",
                1,
            )
            return self.context

        except Exception as e:
            Logger.log(f"Failed to connect to browser via CDP: {e}", 3)
            Logger.log(
                "Make sure Chrome/Edge is running with --remote-debugging-port=9222",
                2,
            )
            raise

    def create_page(self, url: str | None = None) -> Page:
        """
        Create a new page within the active browser context.

        Optionally navigates to a URL immediately after page creation.
        Navigation errors are logged but do not crash execution.

        :param url: Optional URL to navigate to after creating the page.
        :type url: str | None
        :return: The newly created Playwright Page object.
        :rtype: Page
        """
        page = self.context.new_page()

        if url:
            Logger.log(f"Navigating to {url}")
            try:
                page.goto(url, timeout=30_000)
                Logger.log(f"Successfully navigated to {url}", 1)
            except Exception as e:
                Logger.log(f"Failed to navigate to {url}: {e}", 3)
                Logger.log(f"Current URL: {page.url}", 2)

        return page

    def restart_page(
        self,
        old_page: Page | None = None,
        reason: str = "",
        url: str | None = None,
    ) -> Page:
        """
        Close an existing page (if provided) and create a fresh page.

        Useful for:
        - Crash recovery
        - Navigation dead-ends
        - Resetting state cleanly

        The method is fault-tolerant and will ignore failures when
        closing the old page.

        :param old_page: Existing Page object to close before restarting.
        :type old_page: Page | None
        :param reason: Optional reason for restart (used for logging).
        :type reason: str
        :param url: Optional URL to navigate to after creating the new page.
        :type url: str | None
        :return: The newly created Playwright Page object.
        :rtype: Page
        """
        Logger.log(f"RESTARTING PAGE ({reason})", 2)

        try:
            if old_page:
                old_page.close()
        except Exception:
            pass

        page = self.context.new_page()

        if url:
            page.goto(url, wait_until="domcontentloaded")

        return page

    def close(self) -> None:
        """
        Gracefully shut down the browser and Playwright instance.

        This method:
        - Closes the browser connection if active
        - Stops Playwright safely
        - Silently ignores cleanup errors

        Intended to be called during shutdown or fatal error handling.
        """
        try:
            if self.browser:
                self.browser.close()
        except Exception:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass


class Config:
    """Centralized configuration loaded once at startup."""

    _loaded = False

    # Mouse
    DEFAULT_MOUSE_X: int
    DEFAULT_MOUSE_Y: int
    MIN_CLICK_DELAY: float
    MAX_CLICK_DELAY: float

    # Keyboard
    KEYBOARD_ADJACENCY: dict[str, str]

    # Movement
    STEPS: int
    MAX_NON_OVERSHOOT_OFFSET: int
    MAX_OVERSHOOT_OFFSET: int

    @classmethod
    def load(cls, path: str | Path = "config.json"):
        if cls._loaded:
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ---- Mouse ----
        mouse = data["mouse"]
        cls.DEFAULT_MOUSE_X = mouse["position"]["DEFAULT_MOUSE_X"]
        cls.DEFAULT_MOUSE_Y = mouse["position"]["DEFAULT_MOUSE_Y"]
        cls.MIN_CLICK_DELAY = mouse["input"]["MIN_CLICK_DELAY"]
        cls.MAX_CLICK_DELAY = mouse["input"]["MAX_CLICK_DELAY"]

        # ---- Keyboard ----
        cls.KEYBOARD_ADJACENCY = data["keyboard"]["KEYBOARD_ADJACENCY"]

        # ---- Movement ----
        movement = data["movement"]
        cls.STEPS = movement["STEPS"]
        cls.MAX_NON_OVERSHOOT_OFFSET = movement["MAX_NON_OVERSHOOT_OFFSET"]
        cls.MAX_OVERSHOOT_OFFSET = movement["MAX_OVERSHOOT_OFFSET"]

        cls._loaded = True


class ConfigManager:
    '''Handles reading and defining configuration variables. \n
        Variables are hardcoded right now.
    '''

    
    @staticmethod
    def _unpack_config() -> dict:
        """
        Unpacks config.json into a dict.

        Returns:
            dict: The parsed configuration.
        """
        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "data" / "config.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        try:
            with config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        
    
    @staticmethod
    def define_config_variables() -> tuple:
        '''
        Parses config dict.

        Returns:
            tuple: List of config variables.

        Order of output:
            DEFAULT_MOUSE_Y, 
            DEFAULT_MOUSE_X, 
            MAX_CLICK_DELAY, 
            MIN_CLICK_DELAY, 
            KEYBOARD_ADJACENCY, 
            STEPS, 
            MAX_NON_OVERSHOOT_OFFSET,
            MAX_OVERSHOOT_OFFSET


        '''
        data = ConfigManager._unpack_config()
        mouse_pos = data["mouse"]["position"]
        DEFAULT_MOUSE_Y = mouse_pos["DEFAULT_MOUSE_Y"]
        DEFAULT_MOUSE_X = mouse_pos["DEFAULT_MOUSE_X"]

        mouse_input = data["mouse"]["input"]
        MAX_CLICK_DELAY = mouse_input["MAX_CLICK_DELAY"]
        MIN_CLICK_DELAY = mouse_input["MIN_CLICK_DELAY"]

        keyboard = data["keyboard"]
        KEYBOARD_ADJACENCY = keyboard["KEYBOARD_ADJACENCY"]

        movement = data["movement"]
        STEPS = movement["STEPS"]
        MAX_NON_OVERSHOOT_OFFSET = movement["MAX_NON_OVERSHOOT_OFFSET"]
        MAX_OVERSHOOT_OFFSET = movement["MAX_OVERSHOOT_OFFSET"]
        return DEFAULT_MOUSE_Y, DEFAULT_MOUSE_X, MAX_CLICK_DELAY, MIN_CLICK_DELAY, KEYBOARD_ADJACENCY, STEPS, MAX_NON_OVERSHOOT_OFFSET, MAX_OVERSHOOT_OFFSET
    

class Logger:
    """
    Handles Logger.logging to CLI with timestamps and levels.
    """

    
    @staticmethod
    def _timestamp() -> str:
        """
        Fetches current timestamp for Logger.logging.
        
        :return: Timestamp in Hour:Minute:Second format.
        :rtype: str
        """
        return datetime.now().strftime("%H:%M:%S")
    
    
    @staticmethod
    def log(message: str, level: int = 0) -> None:
        """
        Logger.logs events in the CLI using color coded severity levels 
        
        :param message: String to Logger.log.
        :type message: str
        :param level: Severity of the event:\n
            0. System (white)\n
            1. Success (green)\n
            2. Warning (yellow)\n
            3. Error (red)
        :type level: int
        """

        COLORS = {
            0: "\033[97m",  # system (white)
            1: "\033[92m",  # success (green)
            2: "\033[93m",  # warning (yellow)
            3: "\033[91m",  # error (red)
        }

        LEVEL_NAMES = {
            0: "SYSTEM",
            1: "SUCCESS",
            2: "WARNING",
            3: "ERROR",
        }

        RESET = "\033[0m"
        color = COLORS.get(level, COLORS[0])
        level_name = LEVEL_NAMES.get(level, LEVEL_NAMES[0])

        print(f"{color}[{Logger._timestamp()}] [{level_name}] {message}{RESET}", flush=True)


class DelayManager:
    """
    Handles human-like delays and idle behavior.
    """

    
    @staticmethod
    def type_delay(min: float, max: float) -> float:
        """
        Generates a random integer in a range. Used for readability. 
        
        :param min: Minimum delay constraint.
        :type min: float
        :param max: Maximum delay constraint.
        :type max: float
        :return: Random integer in the range of min and max.
        :rtype: float
        """
        return random.uniform(min,max)
    
    
    @staticmethod
    def human_delay(min_delay: float = 1.0, max_delay: float = 3.0, reason: str = "") -> None:
        """
        Pauses for a random amount of time and Logger.log the reason why. Used for readability. 
        
        :param min_delay: Minimum delay constraint.
        :type min_delay: float
        :param max_delay: Maximum delay constraint.
        :type max_delay: float
        :param reason: Reason for pause. Logger.logs with 'system' level severity.
        :type reason: str
        """

        delay = random.uniform(min_delay, max_delay)
        if reason:
            Logger.log(f"Sleeping {delay:.2f}s {reason}",0)
        time.sleep(delay)

    
    @staticmethod
    def idle_delay(page:Page, element:object, min_times:int = 1, max_times:int = 5) -> None:
        """
        Simulates human delay by moving mouse randomly around specified element.
        
        :param page: Page object from your Playwright page
        :type page: Page
        :param element: Playwright locator object.
        :type element: object
        :param min_times: Minimum times to move mouse constraint (default = 1).
        :type min_times: int
        :param max_times: Maximum times to move mouse constraint (default = 5).
        :type max_times: int
        """
        for i in range(random.randint(min_times,max_times)):
            MouseManager.human_movement(page, element)

class MouseManager:
    """
    Handles human-like mouse movement and mouse tracking.
    """
    _last_x: int | None = None
    _last_y: int | None = None
    
    @staticmethod
    def enable_cursor_tracking(page: Page) -> None:
        '''
        Inject Javascript code into the target page to render a red cursor for debugging or visualization.
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        '''
        page.evaluate('''const box=document.createElement("div");Object.assign(box.style,{position:"fixed",width:"10px",height:"10px",background:"red",borderRadius:"8px",pointerEvents:"none",transform:"translate(-50%, -50%)",zIndex:999999}),document.body.appendChild(box);let mouseX=0,mouseY=0,x=0,y=0;document.addEventListener("mousemove",(e=>{mouseX=e.clientX,mouseY=e.clientY})),function e(){x+=.15*(mouseX-x),y+=.15*(mouseY-y),box.style.left=x+"px",box.style.top=y+"px",requestAnimationFrame(e)}();''')

    @staticmethod
    def _get_mouse_last_location() -> tuple:
        """
        Retrives last mouse location. \n
        By default, the script only tracks automated mouse movement.
        
        :return: (x,y) value of mouse location.
        :rtype: tuple
        """
        
        BASE_DIR = Path(__file__).parent.parent
        json_file = BASE_DIR / "core" / "custominfo.json"

        json_file.parent.mkdir(parents=True, exist_ok=True)

        if json_file.exists():
            with open(json_file, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                    Logger.log("custominfo.json is corrupted. Resetting data.", 2)
        else:
            data = {}
            Logger.log("custominfo.json doesn't exist. Creating it in the 'core' directory.", 3)

        if "mouse_location" not in data:
            data["mouse_location"] = {"x": DEFAULT_MOUSE_X, "y": DEFAULT_MOUSE_Y}
            with open(json_file, "w") as f:
                json.dump(data, f, indent=4)
                Logger.log("custominfo.json empty. Populated with default mouse data.", 2)
                
        return data["mouse_location"]["x"], data["mouse_location"]["y"]

    
    @staticmethod
    def _update_mouse_last_location(x: int, y: int) -> None:
        """
        Update the mouse location.
        
        :param x: x-value of mouse location
        :type x: int
        :param y: y-value of mouse location
        :type y: int
        """
        BASE_DIR = Path(__file__).parent.parent
        json_file = BASE_DIR / "core" / "custominfo.json"

        # Ensure the core folder exists
        json_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data or create empty dict
        if json_file.exists():
            with open(json_file, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
                    Logger.log("custominfo.json is corrupted. Resetting data.", 2)
        else:
            data = {}
            Logger.log("custominfo.json doesn't exist. Creating it in the 'core' directory.", 3)

        # Update mouse location
        data["mouse_location"] = {"x": x, "y": y}

        # Save updated JSON
        with open(json_file, "w") as f:
            json.dump(data, f, indent=4)
        
    
    @staticmethod
    def _move_mouse_curved(page: Page, target_x : float, target_y : float, steps=STEPS) -> None:
        """
        Move the mouse along a randomized, imperfect curved path. 
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        :param target_x: Target x-value
        :type target_x: float
        :param target_y: Target y-value
        :type target_y: float
        :param steps: Controls smoothness of movement. Also impacts mouse speed.
        """
        start_x, start_y = MouseManager._get_mouse_last_location()
        viewport = MouseManager._get_viewport_size(page)

        # Randomize offset of control point
        ctrl_x = start_x + (target_x - start_x) * random.uniform(0.3, 0.7)
        ctrl_y = start_y + (target_y - start_y) * random.uniform(0.2, 0.8)

        # Calculate Euclidean distance between start and target
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)

        # Adjust steps: fewer steps for shorter distances (exponential decay)
        # You can tweak 50 here to control sensitivity
        steps = max(2, int(steps * (1 - math.exp(-distance / 75))))

        for i in range(steps + 1):
            t = i / steps
            # Quadratic Bezier formula
            x = (1 - t)**2 * start_x + 2 * (1 - t) * t * ctrl_x + t**2 * target_x
            y = (1 - t)**2 * start_y + 2 * (1 - t) * t * ctrl_y + t**2 * target_y

            # Clamp to viewport
            x = min(max(0, x), viewport["width"])
            y = min(max(0, y), viewport["height"])

            page.mouse.move(x, y)
            MouseManager._update_mouse_last_location(x, y)
    
    
    @staticmethod
    def _safe_cord_randomize(page: Page, x: float, y: float, min_offset: float=-50, max_offset: float=50) -> tuple:
        """
        Offset coordinates randomly without going off the visible page.
        
        :param page: Playwright Page object (you current page).
        :type page: Page
        :param x: Starting x-value
        :type x: float
        :param y: Starting y-value
        :type y: float
        :param min_offset: Minimum offset (fallback value -50).
        :type min_offset: float
        :param max_offset: Maximum offset (fallback value 50).
        :type max_offset: float
        :return: (x,y) values of new coordinates.
        :rtype: tuple
        """
        viewport = MouseManager._get_viewport_size(page)
        new_x = x + random.uniform(min_offset, max_offset)
        new_y = y + random.uniform(min_offset, max_offset)
        new_x = min(max(0, new_x), viewport["width"])
        new_y = min(max(0, new_y), viewport["height"])
        return new_x, new_y
    
    
    @staticmethod
    def _random_point_in_box(left: float, right: float, top: float, bottom: float) -> tuple:
        """
        Generate a random point inside a bounding box.
        
        :param left: Leftmost x-value.
        :type left: float
        :param right: Rightmost x-value.
        :type right: float
        :param top: Highest y-value.
        :type top: float
        :param bottom: Lowest y-value.
        :type bottom: float
        :return: (x,y) values of the random point.
        :rtype: tuple
        """
        x = random.uniform(left, right)
        y = random.uniform(top, bottom)
        return x,y
    
    
    @staticmethod
    def _get_location(element: object, name: str = "") -> dict:
        """
        Get the location information of a Playwright locator object.
        
        :param element: Playwright Locator object of the target element.
        :type element: object
        :param name: Optional name of the object (for readable Logger.logging).
        :type name: str
        :return: Python dictionary of location information
        :rtype: dict
        \n
        {
            "left": left,\n
            "top": top,\n
            "right": right,\n
            "bottom": bottom,\n
            "x": x,\n
            "y": y\n
            }
        """
        if not name:
            name = element

        element.scroll_into_view_if_needed()  
        box = element.bounding_box()          
        if not box:
            raise Exception(f"{name} not visible")
        
        left = box["x"]
        top = box['y']
        right = box["x"] + box["width"]
        bottom = box["y"] + box["height"]

        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2

        return {
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "x": x,
            "y": y
        }
    
    @staticmethod
    def _get_viewport_size(page: Page) -> dict[str,int]:
        """
        Get viewport size when not using built in browser.
        
        :param page: Playwright Page object
        :type page: Page
        :return: {"width":width, "height":height} dictionary.
        :rtype: dict[str, int]
        """
        size = page.viewport_size
        if size is None:
            # Fallback to querying via JS
            size = page.evaluate("""
                () => ({
                    width: window.innerWidth,
                    height: window.innerHeight
                })
            """)
        return size
    
    @staticmethod
    def human_movement(page: Page, element: object, click: bool = False) -> None:
        """
        Move the cursor to an element (doesn't click).
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        :param element: Playwright locator object of target element.
        :type element: object
        :param click: This is meant to be an internal variable. You should use safe_click to click objects.
        :type click: bool
        """
        coords = MouseManager._get_location(element)
        left = coords["left"]
        top = coords["top"]
        right = coords["right"]
        bottom = coords["bottom"]
        x = coords["x"]
        y = coords["y"]

        #==========#
        x_actual = x
        y_actual = y
        overshoot_options = ["x","y"]
        #==========#

        #Calulate amount of stages
        stages = random.randint(2,3)

        #Caluclate target location
        target_x, target_y = MouseManager._random_point_in_box(left,right,top,bottom)

        #Initial random 
        current_x,current_y = MouseManager._safe_cord_randomize(page, x_actual, y_actual)
        
        #move mouse to initial location
        MouseManager._move_mouse_curved(page, current_x, current_y, steps=STEPS)
        
        #Calculate if current_x is farther from x_actual or current_y is farther from y_actual
        delta_x = abs(current_x - x_actual)
        delta_y = abs(current_y - y_actual)
        #Handle all 3 cases
        if delta_x > delta_y: 
            overshoot = "x"
            max_offset_y = MAX_NON_OVERSHOOT_OFFSET
            max_offset_x = MAX_NON_OVERSHOOT_OFFSET

        elif delta_y > delta_x: 
            overshoot = "y"
            max_offset_x = MAX_NON_OVERSHOOT_OFFSET
            max_offset_y = MAX_OVERSHOOT_OFFSET

        elif delta_y == delta_x:
            overshoot = random.choice(overshoot_options)
            if overshoot == "x":
                max_offset_y = MAX_NON_OVERSHOOT_OFFSET
                max_offset_x = MAX_OVERSHOOT_OFFSET

            elif overshoot == "y":
                max_offset_x = MAX_NON_OVERSHOOT_OFFSET
                max_offset_y = MAX_OVERSHOOT_OFFSET


        mouse_x, mouse_y = current_x, current_y
        #Begin to iterate 
        for i in range(stages):
            factor = (stages - i) / stages
            offset_x = random.uniform(-max_offset_x, max_offset_x) * factor
            offset_y = random.uniform(-max_offset_y, max_offset_y) * factor
            
            if i == stages - 1: 
                current_x = target_x
                current_y = target_y
            else:
                current_x = target_x + offset_x
                current_y = target_y + offset_y

            MouseManager._move_mouse_curved(page, current_x, current_y)
        if click:
            DelayManager.human_delay(MIN_CLICK_DELAY, MAX_CLICK_DELAY)
            final_x, final_y = current_x, current_y
            page.mouse.click(final_x,final_y)

    @staticmethod
    def safe_click(page:Page, element: object) -> None:
        """
        Realstic clicking on an object.
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        :param element: Playwright locator object for the target element.
        :type element: object
        """
        MouseManager.human_movement(page, element, click=True)

class TypingManager:
    """
    Handles human-like typign behavior
    """
    
    def human_typing (
        page: Page,
        element: object ,          
        text: str,
        typo_chance: float = 0.1,
        min_delay: float = 0.05,
        max_delay: float = 0.2,
    ) -> None:
        """
        Types like a human with realstic typos. Custom keyboard can be configured in config.json.
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        :param element: Playwright locator object for target element.
        :type element: object
        :param text: Text to type
        :type text: str
        :param typo_chance: Chance of a typo (default = 0.1)
        :type typo_chance: float
        :param min_delay: Minimum delay between keypresses (default = 0.05). Converted to MS in script.
        :type min_delay: float
        :param max_delay: Minimum delay between keypresses (default = 0.2). Converted to MS in script.
        :type max_delay: float
        """
        element.focus()

        i = 0
        while i < len(text):
            chunk_size = random.randint(3, 5)
            chunk = text[i : i + chunk_size]

            typed_chunk = ""

            # --- type chunk (with possible typos) ---
            for char in chunk:
                if (
                    char.lower() in KEYBOARD_ADJACENCY
                    and random.random() < typo_chance
                ):
                    char_to_type = random.choice(KEYBOARD_ADJACENCY[char.lower()])
                else:
                    char_to_type = char

                element.type(char_to_type)
                typed_chunk += char_to_type

                page.wait_for_timeout(
                    random.uniform(min_delay, max_delay) * 1000
                )

            # --- correct if typo occurred ---
            if typed_chunk != chunk:
                # short "realization pause"
                page.wait_for_timeout(
                    random.uniform(0.15, 0.35) * 1000
                )

                # backspace at human speed
                for _ in typed_chunk:
                    element.press("Backspace")
                    page.wait_for_timeout(
                        random.uniform(min_delay, max_delay) * 1000
                    )

                # re-type chunk at NORMAL speed
                for char in chunk:
                    element.type(char)
                    page.wait_for_timeout(
                        random.uniform(min_delay, max_delay) * 1000
                    )

            i += chunk_size

class ScrollManager:
    "Handles human-like scrolling."

    
    @staticmethod
    def scroll(page: Page, total_pixels: int) -> None:
        """
        Human-like scroll behavior.
        
        :param page: Playwright Page object (your current page).
        :type page: Page
        :param total_pixels: Total pixels to scroll.
        :type total_pixels: int
        """
        remaining = total_pixels
        velocity = random.randint(80, 140)

        while remaining > 0:
            velocity *= random.uniform(0.88, 1)
            step = max(5, int(velocity))

            if step > remaining:
                step = remaining

            step += random.randint(-3, 3)

            page.mouse.wheel(0, step)
            remaining -= abs(step)

            delay = max(0.01, min(0.12, 1 / (velocity + 1)))
            page.wait_for_timeout(delay * 1000)

            if velocity < 8:
                break
    
class NetworkUtils:
    "Handles network operations"
    
    @staticmethod
    def url_to_bytes(url: str, timeout: int = 15) -> tuple[bytes, str]:
        """
        Fetch image bytes from a URL and return its type (format).

        :param url: Image URL.
        :param timeout: Timeout before failure (default=15)
        :return: Tuple containing image bytes and image type (e.g., 'png', 'jpeg').
        """
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        image_bytes = r.content

        kind = filetype.guess(image_bytes)
        image_type = kind.extension if kind else "unknown"
        print(image_type)

        return image_bytes, image_type
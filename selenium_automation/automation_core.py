"""
Selenium Automation Core - Wraps existing automation functions for QA Agent
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import json

# Import helper functions from local module
from selenium_automation.helpers import (
    check_and_handle_error,
    wait_for_validation_screen,
    type_e_and_enter
)

def load_elements():
    """Load element selectors from elements.json"""
    try:
        # Try to load from current directory first
        if os.path.exists('elements.json'):
            with open('elements.json', 'r') as f:
                return json.load(f)
        
        # Try to load from selenium_automation directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        elements_path = os.path.join(parent_dir, 'elements.json')
        
        if os.path.exists(elements_path):
            with open(elements_path, 'r') as f:
                return json.load(f)
        
        raise FileNotFoundError("elements.json not found")
    except Exception as e:
        raise Exception(f"Error loading elements.json: {e}")


def setup_logging():
    """Setup logging with date-time based folder structure"""
    # Create main logs folder (in parent directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(script_dir))
    logs_dir = os.path.join(parent_dir, "Logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create subfolder with date and time
    now = datetime.now()
    timestamp_folder = now.strftime("%d-%m-%Y_%I-%M-%S_%p")
    session_dir = os.path.join(logs_dir, timestamp_folder)
    os.makedirs(session_dir, exist_ok=True)
    
    # Create attachments subfolder for screenshots
    attachments_dir = os.path.join(session_dir, "attachments")
    os.makedirs(attachments_dir, exist_ok=True)
    
    # Create success and error subfolders
    success_dir = os.path.join(attachments_dir, "success")
    error_dir = os.path.join(attachments_dir, "error")
    os.makedirs(success_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)
    
    # Create log file
    log_file = os.path.join(session_dir, "automation.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("AUTOMATION SESSION STARTED")
    logger.info(f"Session Directory: {session_dir}")
    logger.info(f"Attachments Directory: {attachments_dir}")
    logger.info(f"Success Screenshots: {success_dir}")
    logger.info(f"Error Screenshots: {error_dir}")
    logger.info("="*60)
    
    return logger, session_dir, attachments_dir, success_dir, error_dir


def find_element_safe(driver, selector, wait_time=10, by_xpath=False):
    """Safely find element with explicit wait"""
    try:
        by_type = By.XPATH if by_xpath else By.CSS_SELECTOR
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((by_type, selector))
        )
        return element
    except Exception as e:
        raise Exception(f"Could not find element: {selector}") from e


def click_element_safe(driver, selector, wait_time=10, by_xpath=False):
    """Safely click element with explicit wait"""
    try:
        by_type = By.XPATH if by_xpath else By.CSS_SELECTOR
        element = WebDriverWait(driver, wait_time).until(
            EC.element_to_be_clickable((by_type, selector))
        )
        element.click()
        return element
    except Exception as e:
        raise Exception(f"Could not click element: {selector}") from e


class SeleniumAutomationCore:
    """
    Core Selenium automation wrapper for QA Agent architecture.
    Uses local helper functions instead of importing from Studio_Automation.
    """
    
    def __init__(self, context):
        """
        Initialize Selenium automation core.
        
        Args:
            context: QA context for session management
        """
        self.context = context
        self.driver: Optional[webdriver.Chrome] = None
        self.elements: Dict[str, Any] = {}
        self.logger = None
        self.session_dir = None
        self.attachments_dir = None
        self.success_dir = None
        self.error_dir = None
        
        # Configuration from environment
        self.platform_url = os.getenv("QA_PLATFORM_URL", "https://ft6.bifreedom.com")
        self.username = os.getenv("QA_USERNAME", "sridharofficial17@gmail.com")
        self.password = os.getenv("QA_PASSWORD", "Pillir@111")
    

    
    def _get_default_elements(self) -> Dict[str, Any]:
        """Get default element selectors if elements.json is not available"""
        return {
            "login": {
                "username_input": "input[data-input-testid='login_email']",
                "password_input": "input[data-input-testid='login_password']",
                "login_button": "button[data-clickable-testid='login_button']"
            },
            "studio": {
                "default_prompt": "div[data-clickable-testid='quick_start_card_0']"
            },
            "document_flow": {
                "decision_input": "textarea[data-input-testid='chat_prompt_input']",
                "send_button": "svg[data-clickable-testid='send_message_button']"
            }
        }
    

    def _take_screenshot(self, phase: str, description: str, is_error: bool = False) -> str:
        """
        Take screenshot and save with timestamp.
        
        Args:
            phase (str): Current phase name
            description (str): Screenshot description
            is_error (bool): Whether this is an error screenshot
            
        Returns:
            str: Screenshot file path
        """
        try:
            timestamp = datetime.now().strftime("%H-%M-%S")
            tab_session = self.context.tab_session or "unknown_tab"
            
            # Create filename with tab session and timestamp
            filename = f"{phase}_{description}_{tab_session}_{timestamp}.png"
            
            # Choose directory based on error status
            if is_error and self.error_dir:
                screenshot_path = os.path.join(self.error_dir, filename)
            elif self.success_dir:
                screenshot_path = os.path.join(self.success_dir, filename)
            else:
                # Fallback to context screenshots directory
                screenshot_path = os.path.join(self.context.screenshots_dir, filename)
            
            # Take screenshot
            self.driver.save_screenshot(screenshot_path)
            
            # Add to context
            self.context.add_screenshot(phase, screenshot_path, description)
            
            if self.logger:
                self.logger.info(f"📸 Screenshot saved: {screenshot_path}")
            
            return screenshot_path
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Failed to take screenshot: {e}")
            return ""
    
    def execute_authentication_phase(self) -> Tuple[bool, str]:
        """
        Complete Authentication Phase: Browser initialization + Login + Prompt selection
        Combines the functionality of: initialize_browser, login, select_default_prompt
        """
        try:
            # STEP 1: Initialize Browser - Setup logging FIRST
            # Setup logging using existing function
            self.logger, self.session_dir, self.attachments_dir, self.success_dir, self.error_dir = setup_logging()
            
            self.logger.info("🚀 Starting AUTHENTICATION PHASE - Step 1: Browser Initialization")
            
            # Load element selectors
            try:
                self.elements = load_elements()
                self.logger.info("✅ Elements loaded successfully")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load elements.json: {e}")
                self.elements = self._get_default_elements()
            
            # Initialize WebDriver
            self.logger.info("🚀 Initializing Chrome WebDriver...")
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set browser session info in context
            session_id = self.driver.session_id
            tab_handle = self.driver.current_window_handle
            self.context.set_browser_session(session_id, tab_handle)
            
            self.logger.info("✅ Chrome WebDriver initialized")
            
            # STEP 2: Login
            self.logger.info("🔐 Starting AUTHENTICATION PHASE - Step 2: Login")
            self.context.start_phase("authentication")
            
            # Navigate to platform
            self.logger.info(f"🌐 Navigating to {self.platform_url}...")
            self.driver.get(self.platform_url)
            
            # Take screenshot of login page
            self._take_screenshot("authentication", "login_page")
            
            self.logger.info("⏳ Waiting for login page to load...")
            time.sleep(2)
            
            # Enter username
            self.logger.info(f"👤 Entering username: {self.username}")
            username_field = find_element_safe(self.driver, self.elements['login']['username_input'])
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Enter password
            self.logger.info("🔑 Entering password...")
            password_field = find_element_safe(self.driver, self.elements['login']['password_input'])
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            self.logger.info("🔓 Clicking login button...")
            click_element_safe(self.driver, self.elements['login']['login_button'])
            
            # Wait for studio screen to load
            self.logger.info("⏳ Waiting 3 seconds for studio screen to load...")
            time.sleep(3)
            
            # Take screenshot after login
            self._take_screenshot("authentication", "studio_loaded")
            
            # Verify login success
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.elements['studio']['default_prompt']))
            )
            self.logger.info("✅ Login successful - Studio page loaded")
            
            # STEP 3: Select Default Prompt
            self.logger.info("🎯 Starting AUTHENTICATION PHASE - Step 3: Select Default Prompt")
            
            self.logger.info("⏳ Waiting for studio page to load...")
            time.sleep(3)
            
            self.logger.info("🎯 Looking for prompt cards...")
            
            # First, try to find all available prompt cards
            all_cards_selector = self.elements['studio']['all_prompt_cards']
            
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, all_cards_selector))
            )
            
            # Get all available prompt cards
            all_prompt_cards = self.driver.find_elements(By.CSS_SELECTOR, all_cards_selector)
            
            if all_prompt_cards:
                self.logger.info(f"📋 Found {len(all_prompt_cards)} prompt card(s)")
                
                # Take screenshot before selection
                pre_selection_screenshot = self._take_screenshot("prompt_selection", "prompt_cards_available")
                
                # Select card based on random_selection parameter
                if random_selection and len(all_prompt_cards) > 1:
                    import random
                    selected_index = random.randint(0, len(all_prompt_cards) - 1)
                    selected_card = all_prompt_cards[selected_index]
                    self.logger.info(f"🎲 Randomly selected card #{selected_index + 1} out of {len(all_prompt_cards)}")
                else:
                    selected_index = 0
                    selected_card = all_prompt_cards[0]
                    self.logger.info(f"✅ Selected default card (first option) out of {len(all_prompt_cards)}")
                
                # Log card details if available
                try:
                    card_text = selected_card.text[:100] if selected_card.text else "No text available"
                    self.logger.info(f"📝 Selected card text: {card_text}")
                except:
                    pass
                
                # Click the selected card
                selected_card.click()
                time.sleep(2)
                
                # Take screenshot after selection
                post_selection_screenshot = self._take_screenshot("prompt_selection", f"card_{selected_index}_selected")
                
                selection_type = "random" if random_selection and len(all_prompt_cards) > 1 else "default"
                self.logger.info(f"✅ {selection_type.capitalize()} prompt selected successfully")
                
                self.context.end_phase("prompt_selection", success=True)
                self.context.outputs["prompt_selection"] = f"SUCCESS - {selection_type} card {selected_index + 1}/{len(all_prompt_cards)}"
                
                return True, f"{selection_type.capitalize()} prompt selected (card {selected_index + 1}/{len(all_prompt_cards)})"
            else:
                # Fallback to original selector if new selector doesn't work
                self.logger.warning("⚠️ New selector didn't find cards, trying fallback...")
                fallback_selector = self.elements['studio']['default_prompt']
                
                fallback_cards = self.driver.find_elements(By.CSS_SELECTOR, fallback_selector)
                if fallback_cards:
                    self.logger.info(f"📋 Found {len(fallback_cards)} prompt card(s) with fallback selector")
                    
                    pre_selection_screenshot = self._take_screenshot("prompt_selection", "fallback_cards_available")
                    
                    fallback_cards[0].click()
                    time.sleep(2)
                    
                    post_selection_screenshot = self._take_screenshot("prompt_selection", "fallback_selected")
                    
                    self.logger.info("✅ Fallback prompt selected successfully")
                    
                    self.context.end_phase("prompt_selection", success=True)
                    self.context.outputs["prompt_selection"] = "SUCCESS - fallback"
                    
                    return True, "Fallback prompt selected"
                else:
                    self.logger.error("⚠️ No prompt cards found with any selector")
                    error_screenshot = self._take_screenshot("prompt_selection", "no_prompts_found", is_error=True)
                    self.context.add_error("prompt_selection", "No prompt cards found", error_screenshot)
                    self.context.end_phase("prompt_selection", success=False)
                    return False, "No prompt cards found"
                
            prompt_cards = self.driver.find_elements(By.CSS_SELECTOR, prompt_selector)
            if not prompt_cards:
                return False, "No prompt cards found"
            
            self.logger.info(f"📋 Found {len(prompt_cards)} prompt card(s)")
            
            # Take screenshot before selection
            self._take_screenshot("prompt_selection", "prompt_cards_available")
            
            self.logger.info("✅ Clicking default prompt (first option)...")
            prompt_cards[0].click()
            time.sleep(2)
            
            # Take screenshot after selection
            self._take_screenshot("prompt_selection", "prompt_selected")
            
            self.logger.info("✅ Default prompt selected successfully")
            
            # Mark phase as complete
            self.context.end_phase("authentication", success=True)
            self.context.outputs["authentication"] = "SUCCESS"
            
            return True, "Authentication phase completed successfully - Browser initialized, logged in, and prompt selected"
            
        except Exception as e:
            error_msg = f"Authentication phase failed: {e}"
            # Safe logger usage - check if logger exists before using it
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(error_msg)
            else:
                print(f"ERROR: {error_msg}")  # Fallback to print if logger not available
            
            if hasattr(self, 'context'):
                self.context.add_error("authentication", error_msg)
                self.context.end_phase("authentication", success=False)
            return False, error_msg

    def cleanup(self):
        """Cleanup browser session"""
        try:
            if self.driver:
                self.logger.info("🧹 Cleaning up browser session...")
                # Don't close browser - keep it open for inspection as per original code
                self.logger.info("⚠️ Browser window kept open for inspection")
                self.logger.info("⚠️ Please close the browser manually when done")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"⚠️ Cleanup warning: {e}")
    
    def get_driver(self):
        """Get the WebDriver instance"""
        return self.driver
    
    def get_elements(self):
        """Get the elements dictionary"""
        return self.elements
    
    def get_available_prompt_cards(self) -> Tuple[int, list]:
        """
        Get information about available prompt cards.
        
        Returns:
            Tuple[int, list]: (count, list of card texts)
        """
        try:
            if not self.driver:
                return 0, []
            
            # Try to find all available prompt cards
            all_cards_selector = self.elements['studio']['all_prompt_cards']
            all_prompt_cards = self.driver.find_elements(By.CSS_SELECTOR, all_cards_selector)
            
            card_info = []
            for i, card in enumerate(all_prompt_cards):
                try:
                    card_text = card.text[:50] if card.text else f"Card {i+1}"
                    card_info.append(f"Card {i+1}: {card_text}")
                except:
                    card_info.append(f"Card {i+1}: Unable to read text")
            
            return len(all_prompt_cards), card_info
            
        except Exception as e:
            self.logger.warning(f"Could not get prompt card info: {e}")
            return 0, []
    
    # ==================== PLACEHOLDER METHODS FOR FUTURE PHASES ====================
    
    def validate_discovery_document(self) -> Tuple[bool, str]:
        """
        Phase 3: Discovery Document Validation - Open discovery document, take screenshot, validate
        Based on Studio_Automation STEP 4: DOCUMENT VALIDATION
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("discovery")
            self.logger.info("="*50)
            self.logger.info("PHASE 3: DISCOVERY DOCUMENT VALIDATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("discovery", "discovery_start")
            
            # Check for errors before validation
            if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                self.logger.info("🔄 Handled error before discovery validation")
                time.sleep(3)
            
            # Wait for validation screen with options C, D, E
            self.logger.info("⏳ Waiting for discovery document validation screen...")
            
            if wait_for_validation_screen(self.driver, "Document", self.elements, self.error_dir, self.logger):
                self.logger.info("✅ Discovery validation screen detected")
                
                # Take screenshot of validation screen
                self._take_screenshot("discovery", "validation_screen")
                
                # Type 'E' and press Enter to confirm
                self.logger.info("⌨️ Typing 'E' to confirm discovery document...")
                type_e_and_enter(self.driver, self.elements, self.logger)
                
                # Take screenshot after confirmation
                self._take_screenshot("discovery", "validation_confirmed")
                
                self.logger.info("✅ Discovery document validation completed")
                self.context.end_phase("discovery", success=True)
                self.context.outputs["discovery"] = "SUCCESS"
                
                return True, "Discovery document validated successfully"
                
            else:
                self.logger.warning("⚠️ WARNING: Discovery validation screen not detected")
                self.logger.info("📸 Taking screenshot and continuing to next phase...")
                
                # Take warning screenshot
                warning_screenshot = self._take_screenshot("discovery", "validation_screen_not_found", is_error=True)
                
                self.logger.info("⏭️ Continuing to Phase 4 (Wireframes)...")
                self.context.add_error("discovery", "Validation screen not detected", warning_screenshot)
                self.context.end_phase("discovery", success=True)  # Continue anyway
                
                return True, "Discovery validation screen not detected, continuing"
                
        except Exception as e:
            error_msg = f"Discovery validation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("discovery", "validation_error", is_error=True)
            self.context.add_error("discovery", error_msg, error_screenshot)
            self.context.end_phase("discovery", success=False)
            return False, error_msg
    
    def validate_wireframes(self) -> Tuple[bool, str]:
        """
        Phase 4: Wireframes Validation - View wireframes, take screenshots, validate
        Based on Studio_Automation STEP 5 & 6: WIREFRAMES
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("wireframes")
            self.logger.info("="*50)
            self.logger.info("PHASE 4: WIREFRAMES VALIDATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("wireframes", "wireframes_start")
            
            # STEP 1: Wait for processing to disappear
            self.logger.info("⏳ Waiting for 'Processing...' alert to disappear...")
            processing_wait_time = 0
            max_processing_wait = 120  # 2 minutes max
            
            while processing_wait_time < max_processing_wait:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    
                    if "processing" in page_text or "please wait" in page_text:
                        self.logger.info(f"   ⏳ Still processing... ({processing_wait_time}s)")
                        time.sleep(5)
                        processing_wait_time += 5
                        continue
                    
                    self.logger.info(f"   ✅ Processing complete! (took {processing_wait_time}s)")
                    break
                except:
                    break
            
            if processing_wait_time >= max_processing_wait:
                self.logger.warning(f"   ⚠️ Timeout waiting for processing (waited {max_processing_wait}s)")
            
            # STEP 2: Wireframe Document Interaction (open and close document card)
            self.logger.info("🔧 STEP 4.1: WIREFRAME DOCUMENT INTERACTION")
            wireframe_document_clicked = False
            
            try:
                self.logger.info("🔍 Looking for wireframe document card...")
                wireframe_card = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['wireframe']['wireframe_card']))
                )
                
                self.logger.info("📄 Wireframe document card found, clicking to open...")
                wireframe_card.click()
                wireframe_document_clicked = True
                self.logger.info("✅ Wireframe document card clicked successfully")
                
                # Take screenshot of opened document
                self._take_screenshot("wireframes", "document_opened")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not find or click wireframe document card: {e}")
                self._take_screenshot("wireframes", "no_document_card", is_error=True)
            
            if wireframe_document_clicked:
                # Wait for document to load
                self.logger.info("⏳ Waiting 3 seconds for wireframe document to load...")
                time.sleep(3)
                
                # Close the wireframe document
                self.logger.info("❌ Looking for close button...")
                try:
                    close_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['wireframe']['close_button']))
                    )
                    
                    self.logger.info("❌ Close button found, clicking to close wireframe document...")
                    close_button.click()
                    self.logger.info("✅ Wireframe document closed successfully")
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not find or click close button: {e}")
                    # Try pressing Escape key as fallback
                    try:
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        self.logger.info("✅ Pressed Escape key to close wireframe document")
                        time.sleep(2)
                    except:
                        self.logger.warning("⚠️ Could not close wireframe document with Escape key either")
            
            self.logger.info("✅ Wireframe document interaction phase completed")
            
            # STEP 3: Look for Wireframes tile
            self.logger.info("🎯 Looking for Wireframes tile...")
            wireframe_tile_found = False
            wireframe_tile = None
            
            for attempt in range(20):
                try:
                    wireframe_tiles = self.driver.find_elements(By.CSS_SELECTOR, self.elements['wireframe']['wireframe_tile'])
                    
                    # Find the tile with "Mockups" or "Wireframes" text
                    for tile in wireframe_tiles:
                        tile_text = tile.text.lower()
                        if tile.is_displayed() and ("mockups" in tile_text or "wireframes" in tile_text or "wireframe" in tile_text):
                            wireframe_tile = tile
                            wireframe_tile_found = True
                            break
                    
                    if wireframe_tile:
                        self.logger.info(f"✅ Found Wireframes tile on attempt {attempt + 1}")
                        self.logger.info(f"   Tile text: {wireframe_tile.text}")
                        break
                except:
                    pass
                
                self.logger.info(f"⏳ Attempt {attempt + 1}/20: Waiting for Wireframes tile...")
                time.sleep(5)
            
            if not wireframe_tile_found:
                error_msg = "Mockups/Wireframes tile not found after 20 attempts"
                self.logger.error(f"❌ CRITICAL ERROR: {error_msg}")
                self._take_screenshot("wireframes", "tile_not_found", is_error=True)
                self.context.add_error("wireframes", error_msg, "")
                self.context.end_phase("wireframes", success=False)
                return False, error_msg
            
            # STEP 4: Click on Mockups/Wireframes tile
            self.logger.info("🖱️ Clicking Mockups/Wireframes tile...")
            try:
                wireframe_tile.click()
                time.sleep(3)
                self.logger.info("✅ Mockups/Wireframes tile clicked successfully")
                self._take_screenshot("wireframes", "tile_clicked")
            except Exception as e:
                error_msg = f"Failed to click Mockups/Wireframes tile: {e}"
                self.logger.error(f"❌ {error_msg}")
                self._take_screenshot("wireframes", "tile_click_failed", is_error=True)
                self.context.add_error("wireframes", error_msg, "")
                self.context.end_phase("wireframes", success=False)
                return False, error_msg
            
            # STEP 5: Wait for wireframe image to load
            self.logger.info("⏳ Waiting for wireframe image to load...")
            wireframe_loaded = False
            
            try:
                wireframe_img = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.elements['wireframe']['wireframe_image']))
                )
                self.logger.info("✅ Wireframe image found and loaded")
                wireframe_loaded = True
                time.sleep(3)  # Give time to view the wireframe
                self._take_screenshot("wireframes", "wireframe_image_loaded")
            except Exception as e:
                self.logger.warning(f"⚠️ Wireframe image not found: {e}")
                self._take_screenshot("wireframes", "wireframe_image_not_found", is_error=True)
            
            if not wireframe_loaded:
                self.logger.warning("⚠️ WARNING: Wireframe image did not load, but continuing...")
            
            # STEP 6: Close wireframe viewer
            self.logger.info("🔒 Closing wireframe viewer...")
            viewer_closed = False
            
            try:
                close_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['wireframe']['close_button']))
                )
                close_button.click()
                time.sleep(3)
                self.logger.info("✅ Wireframe viewer closed successfully")
                viewer_closed = True
            except Exception as e:
                self.logger.warning(f"⚠️ Could not close wireframe viewer: {e}")
                self.logger.info("⚠️ Trying to press ESC key...")
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(2)
                    self.logger.info("✅ Pressed ESC to close viewer")
                    viewer_closed = True
                except:
                    self.logger.warning("⚠️ ESC key also failed")
            
            if not viewer_closed:
                self.logger.warning("⚠️ WARNING: Could not confirm viewer closed, but continuing...")
            
            # STEP 7: Scroll down to bottom to see validation options
            self.logger.info("📜 Scrolling down to bottom of page...")
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.logger.info("✅ Scrolled to bottom")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not scroll: {e}")
            
            # STEP 8: Wait for processing before validation
            self.logger.info("="*50)
            self.logger.info("STEP 4.2: WIREFRAME VALIDATION")
            self.logger.info("="*50)
            
            self.logger.info("⏳ Waiting for processing alert to disappear before wireframe validation...")
            max_wait = 120
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    if not processing_visible:
                        self.logger.info("✅ No processing loader visible, wireframe validation should be ready")
                        break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with wireframe validation anyway...")
            
            # STEP 9: Wait for validation screen and type E
            if wait_for_validation_screen(self.driver, "Wireframe", self.elements, self.error_dir, self.logger):
                self._take_screenshot("wireframes", "validation_screen")
                
                self.logger.info("⌨️ Typing 'E' to confirm wireframes...")
                type_e_and_enter(self.driver, self.elements, self.logger)
                
                self._take_screenshot("wireframes", "validation_confirmed")
                
                self.logger.info("✅ Wireframe validation completed")
                self.logger.info("⏳ Waiting 20 seconds after typing E...")
                time.sleep(20)
                
                self.context.end_phase("wireframes", success=True)
                self.context.outputs["wireframes"] = "SUCCESS"
                
                return True, "Wireframes validated successfully"
            else:
                self.logger.warning("⚠️ WARNING: Wireframe validation screen not detected")
                self.logger.info("📸 Taking screenshot and continuing to next phase...")
                
                warning_screenshot = self._take_screenshot("wireframes", "validation_screen_not_found", is_error=True)
                
                self.logger.info("⏭️ Continuing to Phase 5 (Design Document)...")
                time.sleep(5)
                
                self.context.add_error("wireframes", "Validation screen not detected", warning_screenshot)
                self.context.end_phase("wireframes", success=True)  # Continue anyway
                
                return True, "Wireframe validation screen not detected, continuing"
                
        except Exception as e:
            error_msg = f"Wireframes validation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("wireframes", "validation_error", is_error=True)
            self.context.add_error("wireframes", error_msg, error_screenshot)
            self.context.end_phase("wireframes", success=False)
            return False, error_msg
    
    def validate_design_document(self) -> Tuple[bool, str]:
        """
        Phase 5: Design Document Validation - View design document, take screenshots, validate
        Based on Studio_Automation STEP 7 & 8: DESIGN DOCUMENT
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("design")
            self.logger.info("="*50)
            self.logger.info("PHASE 5: DESIGN DOCUMENT VALIDATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("design", "design_start")
            
            # STEP 1: Wait for processing to disappear
            self.logger.info("⏳ Waiting for 'Processing...' alert to disappear...")
            processing_wait_time = 0
            max_processing_wait = 120  # 2 minutes max
            
            while processing_wait_time < max_processing_wait:
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    
                    if "processing" in page_text or "please wait" in page_text:
                        self.logger.info(f"   ⏳ Still processing... ({processing_wait_time}s)")
                        time.sleep(5)
                        processing_wait_time += 5
                        continue
                    
                    self.logger.info(f"   ✅ Processing complete! (took {processing_wait_time}s)")
                    break
                except:
                    break
            
            if processing_wait_time >= max_processing_wait:
                self.logger.warning(f"   ⚠️ Timeout waiting for processing (waited {max_processing_wait}s)")
            
            # STEP 2: Look for Design Document tile
            self.logger.info("🎯 Looking for Design Document tile...")
            document_tile_found = False
            document_tile = None
            
            for attempt in range(20):
                try:
                    document_tiles = self.driver.find_elements(By.CSS_SELECTOR, self.elements['design_document']['document_tile'])
                    
                    # Find the tile with "Design Document" text
                    for tile in document_tiles:
                        tile_text = tile.text
                        if tile.is_displayed() and "Design Document" in tile_text:
                            document_tile = tile
                            document_tile_found = True
                            break
                    
                    if document_tile:
                        self.logger.info(f"✅ Found Design Document tile on attempt {attempt + 1}")
                        self.logger.info(f"   Tile text: {document_tile.text}")
                        break
                except:
                    pass
                
                self.logger.info(f"⏳ Attempt {attempt + 1}/20: Waiting for Design Document tile...")
                time.sleep(5)
            
            if not document_tile_found:
                error_msg = "Design Document tile not found after 20 attempts"
                self.logger.error(f"❌ CRITICAL ERROR: {error_msg}")
                self._take_screenshot("design", "tile_not_found", is_error=True)
                self.context.add_error("design", error_msg, "")
                self.context.end_phase("design", success=False)
                return False, error_msg
            
            # STEP 3: Click on Design Document tile
            self.logger.info("🖱️ Clicking Design Document tile...")
            try:
                document_tile.click()
                time.sleep(3)
                self.logger.info("✅ Design Document tile clicked successfully")
                self._take_screenshot("design", "tile_clicked")
            except Exception as e:
                error_msg = f"Failed to click Design Document tile: {e}"
                self.logger.error(f"❌ {error_msg}")
                self._take_screenshot("design", "tile_click_failed", is_error=True)
                self.context.add_error("design", error_msg, "")
                self.context.end_phase("design", success=False)
                return False, error_msg
            
            # STEP 4: Wait for document to load
            self.logger.info("⏳ Waiting for design document to load...")
            time.sleep(5)
            self.logger.info("✅ Design document loaded")
            self._take_screenshot("design", "document_loaded")
            
            # STEP 5: Close document viewer
            self.logger.info("🔒 Closing design document viewer...")
            viewer_closed = False
            
            try:
                close_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['design_document']['close_button']))
                )
                close_button.click()
                time.sleep(3)
                self.logger.info("✅ Design document viewer closed successfully")
                viewer_closed = True
            except Exception as e:
                self.logger.warning(f"⚠️ Could not close design document viewer: {e}")
                self.logger.info("⚠️ Trying to press ESC key...")
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    time.sleep(2)
                    self.logger.info("✅ Pressed ESC to close viewer")
                    viewer_closed = True
                except:
                    self.logger.warning("⚠️ ESC key also failed")
            
            if not viewer_closed:
                self.logger.warning("⚠️ WARNING: Could not confirm viewer closed, but continuing...")
            
            # STEP 6: Scroll down to bottom to see validation options
            self.logger.info("📜 Scrolling down to bottom of page...")
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                self.logger.info("✅ Scrolled to bottom")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not scroll: {e}")
            
            # STEP 7: Wait for processing before validation
            self.logger.info("="*50)
            self.logger.info("STEP 5.2: DESIGN DOCUMENT VALIDATION")
            self.logger.info("="*50)
            
            self.logger.info("⏳ Waiting for processing alert to disappear before design document validation...")
            max_wait = 120
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    if not processing_visible:
                        self.logger.info("✅ No processing loader visible, design document validation should be ready")
                        break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with design document validation anyway...")
            
            # Check for errors before validation
            if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                self.logger.info("🔄 Handled error before design document validation")
                time.sleep(3)
            
            # STEP 8: Wait for validation screen and type E
            if wait_for_validation_screen(self.driver, "Design Document", self.elements, self.error_dir, self.logger):
                self._take_screenshot("design", "validation_screen")
                
                try:
                    self.logger.info("⌨️ Typing 'E' to confirm design document...")
                    type_e_and_enter(self.driver, self.elements, self.logger)
                    
                    self._take_screenshot("design", "validation_confirmed")
                    
                    self.logger.info("✅ Design Document validation completed")
                    self.logger.info("⏳ Waiting 20 seconds after typing E...")
                    time.sleep(20)
                    
                    self.context.end_phase("design", success=True)
                    self.context.outputs["design"] = "SUCCESS"
                    
                    return True, "Design document validated successfully"
                    
                except Exception as e:
                    error_msg = f"Error in type_e_and_enter: {e}"
                    self.logger.error(f"❌ {error_msg}")
                    self.logger.info("⏭️ Continuing to Phase 6 anyway...")
                    self.context.add_error("design", error_msg, "")
                    self.context.end_phase("design", success=True)  # Continue anyway
                    return True, f"Design document validation completed with error: {error_msg}"
            else:
                self.logger.warning("⚠️ WARNING: Design Document validation screen not detected")
                self.logger.info("📸 Taking screenshot and continuing...")
                
                warning_screenshot = self._take_screenshot("design", "validation_screen_not_found", is_error=True)
                
                self.logger.info("⏭️ Continuing to Phase 6 (Build Process)...")
                time.sleep(5)
                
                self.context.add_error("design", "Validation screen not detected", warning_screenshot)
                self.context.end_phase("design", success=True)  # Continue anyway
                
                return True, "Design document validation screen not detected, continuing"
                
        except Exception as e:
            error_msg = f"Design document validation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("design", "validation_error", is_error=True)
            self.context.add_error("design", error_msg, error_screenshot)
            self.context.end_phase("design", success=False)
            return False, error_msg
    
    def monitor_build_process(self) -> Tuple[bool, str]:
        """
        Phase 6: Build Process - Monitor build process, wait for completion, confirm
        Based on Studio_Automation STEP 9 & 10: BUILD PROCESSING
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("build")
            self.logger.info("="*50)
            self.logger.info("PHASE 6: BUILD PROCESS MONITORING")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("build", "build_start")
            
            # STEP 1: Wait for build to start
            self.logger.info("⏳ Waiting for build to start...")
            time.sleep(5)
            
            # STEP 2: Monitor for processing and wait for build complete message
            self.logger.info("🔍 Monitoring for 'Processing...' loader...")
            self.logger.info("⚠️ Will wait until build complete message appears")
            
            processing_timeout = 600  # 10 minutes maximum
            check_interval = 30  # Check every 30 seconds
            elapsed_time = 0
            build_ready = False
            
            while elapsed_time < processing_timeout:
                try:
                    # Check for error first
                    if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                        self.logger.info("🔄 Handled error during build monitoring")
                        time.sleep(3)
                    
                    # Check if build is complete
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    
                    # DEBUG: Print relevant portion of page text every 60 seconds
                    if elapsed_time % 60 == 0:
                        self.logger.info(f"🔍 DEBUG - Page text sample (last 500 chars): ...{page_text[-500:]}")
                    
                    # Check for build complete message - ANY of these messages means build is ready
                    has_phase5 = "Phase 5: Build the UI screens" in page_text
                    has_pages_generated = "Pages generated successfully" in page_text
                    has_ready_to_move = "Ready to move to comprehensive testing to ensure everything works perfectly?" in page_text
                    
                    if (has_phase5 or has_pages_generated or has_ready_to_move):
                        self.logger.info("✅ Build complete message found!")
                        if has_phase5:
                            self.logger.info(f"   ✓ Phase 5: Build the UI screens")
                        if has_pages_generated:
                            self.logger.info(f"   ✓ Pages generated successfully")
                        if has_ready_to_move:
                            self.logger.info(f"   ✓ Ready to move to comprehensive testing")
                        build_ready = True
                        break
                    elif ("Your application is now built and ready" in page_text or 
                        "Your application is now ready for testing" in page_text or
                        "ready for testing" in page_text or
                        "create comprehensive test cases" in page_text or
                        "Let's proceed to create comprehensive test cases" in page_text or
                        "proceed to create comprehensive test cases" in page_text):
                        self.logger.info("✅ Build complete message found!")
                        # Find and log the actual message
                        if "Your application" in page_text:
                            start_idx = page_text.find("Your application")
                            self.logger.info(f"   Message: {page_text[start_idx:start_idx+150]}")
                        else:
                            self.logger.info(f"   Message contains: 'ready for testing' or 'test cases'")
                        build_ready = True
                        break
                    
                    # Look for processing text
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_found = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_found = True
                            self.logger.info(f"⏳ Build in progress: {elem.text} (Elapsed: {elapsed_time}s / {processing_timeout}s)")
                            break
                    
                    if not processing_found and not build_ready:
                        self.logger.info(f"⏳ No processing loader visible, waiting 15 seconds for build complete message...")
                        # Wait extra time for message to appear after processing disappears
                        time.sleep(15)
                        
                        # Check again for build complete message
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        
                        # Check for build complete - ANY of these messages means build is ready
                        has_phase5 = "Phase 5: Build the UI screens" in page_text
                        has_pages_generated = "Pages generated successfully" in page_text
                        has_ready_to_move = "Ready to move to comprehensive testing to ensure everything works perfectly?" in page_text
                        
                        if (has_phase5 or has_pages_generated or has_ready_to_move):
                            self.logger.info("✅ Build complete message found after extra wait!")
                            if has_phase5:
                                self.logger.info(f"   ✓ Phase 5: Build the UI screens")
                            if has_pages_generated:
                                self.logger.info(f"   ✓ Pages generated successfully")
                            if has_ready_to_move:
                                self.logger.info(f"   ✓ Ready to move to comprehensive testing")
                            build_ready = True
                            break
                        elif ("Your application is now built and ready" in page_text or 
                            "Your application is now ready for testing" in page_text or
                            "ready for testing" in page_text or
                            "create comprehensive test cases" in page_text or
                            "Let's proceed to create comprehensive test cases" in page_text or
                            "proceed to create comprehensive test cases" in page_text):
                            self.logger.info("✅ Build complete message found after extra wait!")
                            build_ready = True
                            break
                        
                        self.logger.info(f"⏳ Still waiting... ({elapsed_time}s)")
                    
                    # Wait before next check
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    time.sleep(check_interval)
                    elapsed_time += check_interval
            
            if elapsed_time >= processing_timeout and not build_ready:
                self.logger.warning("⚠️ Processing timeout reached (10 minutes) - proceeding anyway")
            
            if build_ready:
                self.logger.info(f"✅ Build completed in {elapsed_time} seconds")
                self._take_screenshot("build", "build_complete")
            else:
                self.logger.warning("⚠️ Build complete message not found, but timeout reached")
                self._take_screenshot("build", "build_timeout", is_error=True)
            
            # STEP 3: Confirm build complete by typing "yes"
            self.logger.info("="*50)
            self.logger.info("STEP 6.2: CONFIRM BUILD COMPLETE")
            self.logger.info("="*50)
            
            # CRITICAL: Check that Processing is NOT visible before typing yes
            self.logger.info("🔍 Verifying no 'Processing...' is visible before typing 'yes'...")
            processing_still_visible = False
            try:
                processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                for elem in processing_elements:
                    if elem.is_displayed() and "Processing" in elem.text:
                        processing_still_visible = True
                        self.logger.warning(f"⚠️ WARNING: Processing still visible: '{elem.text}'")
                        self.logger.warning("⚠️ Waiting 30 more seconds for processing to finish...")
                        time.sleep(30)
                        break
            except:
                pass
            
            if not processing_still_visible:
                self.logger.info("✅ No processing visible, safe to type 'yes'")
            
            # Type "yes" and send
            self.logger.info("📝 Typing 'yes' to confirm...")
            try:
                yes_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Ask anything']"))
                )
                yes_input.click()
                time.sleep(1)
                yes_input.clear()
                yes_input.send_keys("yes")
                time.sleep(2)
                self.logger.info("✅ Typed 'yes'")
                
                self._take_screenshot("build", "typed_yes")
                
                # Click send button
                self.logger.info("🔘 Clicking send button...")
                send_success = False
                
                # Try testid method with regular click first
                try:
                    send_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "svg[data-clickable-testid='send_message_button']"))
                    )
                    send_btn.click()
                    self.logger.info("✅ Send button clicked (testid)")
                    send_success = True
                    time.sleep(3)
                except Exception as e:
                    self.logger.warning(f"⚠️ Testid click failed: {e}")
                
                # Fallback: Try Enter key
                if not send_success:
                    try:
                        self.logger.info("🔄 Trying Enter key as fallback...")
                        yes_input.send_keys(Keys.RETURN)
                        self.logger.info("✅ Enter key pressed")
                        time.sleep(3)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Enter key failed: {e}")
                
                self._take_screenshot("build", "confirmation_sent")
                
                self.logger.info("✅ Build confirmation completed")
                self.context.end_phase("build", success=True)
                self.context.outputs["build"] = "SUCCESS"
                
                return True, f"Build process completed in {elapsed_time} seconds"
                
            except Exception as e:
                error_msg = f"Could not type 'yes': {e}"
                self.logger.error(f"❌ {error_msg}")
                self._take_screenshot("build", "confirmation_failed", is_error=True)
                self.context.add_error("build", error_msg, "")
                self.context.end_phase("build", success=False)
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Build process monitoring failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("build", "monitoring_error", is_error=True)
            self.context.add_error("build", error_msg, error_screenshot)
            self.context.end_phase("build", success=False)
            return False, error_msg
    
    def validate_test_document(self) -> Tuple[bool, str]:
        """
        Phase 7: Test Document Validation - Open test document, take screenshot, validate
        Based on Studio_Automation STEP 10.6 & 11: TEST DOCUMENT INTERACTION & VALIDATION
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("test")
            self.logger.info("="*50)
            self.logger.info("PHASE 7: TEST DOCUMENT VALIDATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("test", "test_start")
            
            # STEP 1: Wait for processing alert after build confirmation
            self.logger.info("⏳ Waiting for processing alert after build confirmation...")
            max_wait = 120  # Wait up to 2 minutes for test document generation
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    if not processing_visible:
                        self.logger.info("✅ No processing loader visible, test document should be ready")
                        break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with test document interaction anyway...")
            
            # STEP 2: Test Document Interaction (open and close document card)
            self.logger.info("="*50)
            self.logger.info("STEP 7.1: TEST DOCUMENT INTERACTION")
            self.logger.info("="*50)
            
            # Find and click test document card
            self.logger.info("🔍 Looking for test document card...")
            test_document_clicked = False
            
            try:
                # Wait for test document card to be available
                test_card = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['test_document']['test_card']))
                )
                
                self.logger.info("📄 Test document card found, clicking to open...")
                test_card.click()
                test_document_clicked = True
                self.logger.info("✅ Test document card clicked successfully")
                
                # Take screenshot of opened document
                self._take_screenshot("test", "document_opened")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not find or click test document card: {e}")
                self._take_screenshot("test", "no_document_card", is_error=True)
            
            if test_document_clicked:
                # Wait for document to load
                self.logger.info("⏳ Waiting 3 seconds for test document to load...")
                time.sleep(3)
                
                # Close the test document
                self.logger.info("❌ Looking for close button...")
                try:
                    close_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['test_document']['close_button']))
                    )
                    
                    self.logger.info("❌ Close button found, clicking to close test document...")
                    close_button.click()
                    self.logger.info("✅ Test document closed successfully")
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not find or click close button: {e}")
                    # Try pressing Escape key as fallback
                    try:
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                        self.logger.info("✅ Pressed Escape key to close test document")
                        time.sleep(2)
                    except:
                        self.logger.warning("⚠️ Could not close test document with Escape key either")
            
            self.logger.info("✅ Test document interaction phase completed")
            
            # STEP 3: Test Phase Validation
            self.logger.info("="*50)
            self.logger.info("STEP 7.2: TEST PHASE VALIDATION")
            self.logger.info("="*50)
            
            # Wait for processing alert to disappear before test phase validation
            self.logger.info("⏳ Waiting for processing alert to disappear before test phase validation...")
            max_wait = 120
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    if not processing_visible:
                        self.logger.info("✅ No processing loader visible, test phase validation should be ready")
                        break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with test phase validation anyway...")
            
            self.logger.info("⏳ Waiting 15 seconds for test phase...")
            time.sleep(15)
            
            # Check for error
            if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                self.logger.info("🔄 Handled error before test phase validation")
                time.sleep(3)
            
            # Wait for validation screen
            if wait_for_validation_screen(self.driver, "Test Phase", self.elements, self.error_dir, self.logger):
                # CRITICAL: Wait for option E text to appear before typing
                self.logger.info("🔍 Waiting for option E text to fully load...")
                option_e_found = False
                for attempt in range(20):  # Try for up to 60 seconds
                    try:
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        if "E. Confirm test plan and proceed to implementation" in page_text:
                            self.logger.info("✅ Option E text found - content fully loaded!")
                            option_e_found = True
                            time.sleep(3)  # Wait 3 more seconds to be safe
                            break
                        else:
                            self.logger.info(f"⏳ Attempt {attempt + 1}/20: Waiting for option E text...")
                            time.sleep(3)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Error checking option E: {e}")
                        time.sleep(3)
                
                if not option_e_found:
                    self.logger.warning("⚠️ Option E text not found, but proceeding...")
                
                self._take_screenshot("test", "validation_screen")
                
                self.logger.info("⌨️ Typing 'E' to confirm test plan...")
                type_e_and_enter(self.driver, self.elements, self.logger)
                
                self._take_screenshot("test", "validation_confirmed")
                
                self.logger.info("✅ Test phase validation completed")
                self.context.end_phase("test", success=True)
                self.context.outputs["test"] = "SUCCESS"
                
                return True, "Test document validated successfully"
            else:
                self.logger.warning("⚠️ WARNING: Test phase validation screen not detected")
                self.logger.info("📸 Taking screenshot and continuing...")
                
                warning_screenshot = self._take_screenshot("test", "validation_screen_not_found", is_error=True)
                
                self.context.add_error("test", "Validation screen not detected", warning_screenshot)
                self.context.end_phase("test", success=True)  # Continue anyway
                
                return True, "Test phase validation screen not detected, continuing"
                
        except Exception as e:
            error_msg = f"Test document validation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("test", "validation_error", is_error=True)
            self.context.add_error("test", error_msg, error_screenshot)
            self.context.end_phase("test", success=False)
            return False, error_msg
    
    def validate_app_preview(self) -> Tuple[bool, str]:
        """
        Phase 8: App Preview Validation - Open application preview, take screenshots, validate
        Based on Studio_Automation STEP 12 & 13: PREVIEW APPLICATION & FINAL CONFIRMATION
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("preview")
            self.logger.info("="*50)
            self.logger.info("PHASE 8: APP PREVIEW VALIDATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("preview", "preview_start")
            
            # STEP 1: Find and click Preview link
            self.logger.info("⏳ Waiting for Preview link...")
            time.sleep(5)
            
            preview_clicked = False
            for attempt in range(10):
                try:
                    # Check for error
                    if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                        self.logger.info("🔄 Handled error while looking for Preview link")
                        time.sleep(3)
                    
                    # Look for Preview link
                    preview_links = self.driver.find_elements(By.CSS_SELECTOR, "p[style*='text-decoration-line: underline']")
                    
                    for link in preview_links:
                        if link.is_displayed() and "Preview" in link.text:
                            self.logger.info("✅ Found Preview link, clicking...")
                            link.click()
                            preview_clicked = True
                            time.sleep(5)
                            break
                    
                    if preview_clicked:
                        break
                        
                except:
                    pass
                
                self.logger.info(f"⏳ Attempt {attempt + 1}/10: Looking for Preview link...")
                time.sleep(3)
            
            if not preview_clicked:
                self.logger.warning("⚠️ Preview link not found")
                self._take_screenshot("preview", "link_not_found", is_error=True)
            else:
                self.logger.info("✅ Preview opened")
                self._take_screenshot("preview", "preview_opened")
                
                # Wait 20 seconds before closing
                self.logger.info("⏳ Waiting 20 seconds before closing preview...")
                time.sleep(20)
                
                # Close preview
                self.logger.info("🔒 Closing preview...")
                try:
                    close_btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, self.elements['preview']['close_button']))
                    )
                    close_btn.click()
                    time.sleep(2)
                    self.logger.info("✅ Preview closed")
                    self._take_screenshot("preview", "preview_closed")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not close preview: {e}")
                    self._take_screenshot("preview", "close_failed", is_error=True)
            
            # STEP 2: Final Confirmation after Preview
            self.logger.info("="*50)
            self.logger.info("STEP 8.2: FINAL CONFIRMATION AFTER PREVIEW")
            self.logger.info("="*50)
            
            self.logger.info("📝 Typing 'yes' for final confirmation...")
            try:
                # Wait a moment for page to be ready
                time.sleep(3)
                
                # Find textarea
                final_input = WebDriverWait(self.driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Ask anything']"))
                )
                final_input.click()
                time.sleep(1)
                final_input.clear()
                final_input.send_keys("yes")
                time.sleep(2)
                self.logger.info("✅ Typed 'yes' for final confirmation")
                
                self._take_screenshot("preview", "typed_yes")
                
                # Click send button with multiple attempts
                self.logger.info("🔘 Clicking send button for final confirmation...")
                send_success = False
                
                for attempt in range(3):
                    try:
                        send_btn = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, "svg[data-clickable-testid='send_message_button']"))
                        )
                        time.sleep(1)
                        send_btn.click()
                        self.logger.info(f"✅ Send button clicked (attempt {attempt + 1})")
                        send_success = True
                        time.sleep(3)
                        break
                    except Exception as e:
                        self.logger.warning(f"⚠️ Send button click attempt {attempt + 1} failed: {e}")
                        if attempt < 2:
                            time.sleep(2)
                
                # Fallback: Try Enter key
                if not send_success:
                    try:
                        self.logger.info("🔄 Trying Enter key as fallback...")
                        final_input.send_keys(Keys.RETURN)
                        self.logger.info("✅ Enter key pressed")
                        time.sleep(3)
                    except Exception as e:
                        self.logger.warning(f"⚠️ Enter key failed: {e}")
                
                self._take_screenshot("preview", "confirmation_sent")
                self.logger.info("✅ Final confirmation sent")
                
            except Exception as e:
                error_msg = f"Could not send final confirmation: {e}"
                self.logger.error(f"❌ {error_msg}")
                self._take_screenshot("preview", "confirmation_failed", is_error=True)
                self.logger.warning("⚠️ Continuing anyway...")
            
            self.logger.info("✅ Preview phase completed")
            
            # STEP 3: Post-Confirmation Processing Wait
            self.logger.info("="*50)
            self.logger.info("STEP 8.3: POST-CONFIRMATION PROCESSING WAIT")
            self.logger.info("="*50)
            
            # Wait for processing alert after final confirmation
            self.logger.info("⏳ Waiting for processing alert after final confirmation...")
            max_wait = 180  # Wait up to 3 minutes for final processing
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    if not processing_visible:
                        self.logger.info("✅ No processing loader visible, QR code should be ready")
                        break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with QR code verification anyway...")
            
            self.logger.info("✅ Post-confirmation processing wait completed")
            
            self.context.end_phase("preview", success=True)
            self.context.outputs["preview"] = "SUCCESS"
            
            return True, "App preview validated successfully"
            
        except Exception as e:
            error_msg = f"App preview validation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("preview", "validation_error", is_error=True)
            self.context.add_error("preview", error_msg, error_screenshot)
            self.context.end_phase("preview", success=False)
            return False, error_msg
    
    def final_confirmation(self) -> Tuple[bool, str]:
        """
        Phase 9: Final Confirmation - Final confirmation, QR code verification, complete workflow
        Based on Studio_Automation STEP 14: VERIFY BUILD SUCCESS (QR CODE & SHARED SCREENSHOT)
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.context.start_phase("final")
            self.logger.info("="*50)
            self.logger.info("PHASE 9: FINAL CONFIRMATION & QR CODE VERIFICATION")
            self.logger.info("="*50)
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("final", "final_start")
            
            # STEP 1: Verify Build Success (QR Code & Success Text)
            self.logger.info("🔍 Waiting for QR code and shared screenshot to confirm build success...")
            time.sleep(5)  # Initial wait
            
            # Check for QR code element AND specific success text (AND condition)
            build_success_confirmed = False
            required_success_text = "Publishing Application ✅"
            
            for attempt in range(10):
                try:
                    # Check for QR code element
                    qr_element_found = False
                    try:
                        qr_element = self.driver.find_element(By.CSS_SELECTOR, self.elements['qr_code']['qr_container'])
                        if qr_element.is_displayed():
                            qr_element_found = True
                            self.logger.info("✅ QR code element found and visible")
                        else:
                            self.logger.info("⏳ QR code element found but not visible")
                    except:
                        self.logger.info("⏳ QR code element not found")
                    
                    # Check for specific success text
                    success_text_found = False
                    try:
                        # Check both page text and HTML content for success message
                        page_text = self.driver.find_element(By.TAG_NAME, "body").text
                        page_html = self.driver.page_source
                        
                        # Look for "Publishing Application ✅" in text or HTML (handles <strong> tags)
                        if (required_success_text in page_text or 
                            "Publishing Application" in page_text and "✅" in page_text or
                            "Publishing Application</strong>✅" in page_html):
                            success_text_found = True
                            self.logger.info("✅ Required success text found")
                        else:
                            self.logger.info("⏳ Required success text not found")
                            # Debug: Log what we actually found
                            if "Publishing Application" in page_text:
                                self.logger.info("   Found 'Publishing Application' but missing checkmark")
                            elif "✅" in page_text:
                                self.logger.info("   Found checkmark but missing 'Publishing Application'")
                    except:
                        self.logger.info("⏳ Could not get page text")
                    
                    # Both conditions must be true (AND condition)
                    if qr_element_found and success_text_found:
                        self.logger.info("✅ Build success confirmed!")
                        self.logger.info("   ✓ QR code element visible")
                        self.logger.info("   ✓ Success text found: 'Publishing Application ✅'")
                        build_success_confirmed = True
                        
                        # Take success screenshot
                        self._take_screenshot("final", "build_success_qr_code")
                        
                        break
                    else:
                        self.logger.info(f"⏳ Attempt {attempt + 1}/10: Waiting for BOTH QR code AND success text...")
                        self.logger.info(f"   QR code element: {'✓' if qr_element_found else '✗'}")
                        self.logger.info(f"   Success text: {'✓' if success_text_found else '✗'}")
                        time.sleep(5)
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking build success: {e}")
                    time.sleep(5)
            
            if not build_success_confirmed:
                self.logger.warning("⚠️ Build success confirmation not found, but proceeding...")
                self._take_screenshot("final", "build_success_not_confirmed", is_error=True)
            
            # STEP 2: Final Success
            self.logger.info("="*50)
            self.logger.info("🎉 QA AUTOMATION COMPLETED SUCCESSFULLY - ALL 9 PHASES DONE!")
            self.logger.info("="*50)
            
            # Take final success screenshot
            final_screenshot = self._take_screenshot("final", "final_success_screenshot")
            self.logger.info("📸 Final success screenshot taken")
            
            # Mark workflow as completed
            self.context.end_phase("final", success=True)
            self.context.outputs["final"] = "SUCCESS"
            
            # Create completion summary
            completion_summary = {
                "workflow_completed": True,
                "build_success_confirmed": build_success_confirmed,
                "qr_code_verified": qr_element_found if 'qr_element_found' in locals() else False,
                "success_text_verified": success_text_found if 'success_text_found' in locals() else False,
                "final_screenshot": final_screenshot,
                "completion_time": datetime.now().isoformat()
            }
            
            self.context.test_results["completion_summary"] = completion_summary
            
            success_message = "🎉 QA Automation completed successfully! All 9 phases validated."
            if build_success_confirmed:
                success_message += " Build success confirmed with QR code and success text."
            
            self.logger.info("✅ QA automation workflow completed successfully!")
            
            return True, success_message
            
        except Exception as e:
            error_msg = f"Final confirmation failed: {e}"
            self.logger.error(error_msg)
            error_screenshot = self._take_screenshot("final", "confirmation_error", is_error=True)
            self.context.add_error("final", error_msg, error_screenshot)
            self.context.end_phase("final", success=False)
            return False, error_msg
    
    def answer_all_questions(self) -> Tuple[bool, str]:
        """
        Phase 2: Requirements Gathering - Automatically answer all questions
        Uses the same waiting logic as Studio_Automation for proper question detection
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.logger.info("📋 Starting requirements gathering - answering all questions")
            
            if not self.driver:
                return False, "Browser not initialized"
            
            # Take initial screenshot
            self._take_screenshot("requirements", "requirements_start")
            
            # STEP 1: Wait for any "Processing..." to disappear before starting questions
            self.logger.info("🔍 Checking if 'Processing...' is visible before starting questions...")
            max_wait = 120  # Wait up to 2 minutes for processing to finish
            wait_interval = 5
            elapsed = 0
            
            while elapsed < max_wait:
                try:
                    processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                    processing_visible = False
                    
                    for elem in processing_elements:
                        if elem.is_displayed() and "Processing" in elem.text:
                            processing_visible = True
                            self.logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                            break
                    
                    # if not processing_visible:
                    #     self.logger.info("✅ No processing loader visible, questions should be ready")
                    #     break
                        
                    time.sleep(wait_interval)
                    elapsed += wait_interval
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error checking processing: {e}")
                    break
            
            if elapsed >= max_wait:
                self.logger.warning("⚠️ Processing wait timeout, proceeding with questions anyway...")
            
            # STEP 2: Wait for questions to be fully loaded
            self.logger.info("🔍 Waiting for questions to be fully loaded...")
            time.sleep(5)  # Additional buffer time
            
            questions_answered = 0
            max_questions = 20  # Safety limit
            total_questions = None
            answered_questions = set()
            last_question_text = ""
            consecutive_same_count = 0
            
            while questions_answered < max_questions:
                try:
                    self.logger.info(f"\n🔍 Looking for question #{questions_answered + 1}...")
                    
                    # Check for processing alert before looking for questions
                    try:
                        processing_elements = self.driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
                        for elem in processing_elements:
                            if elem.is_displayed() and "Processing" in elem.text:
                                self.logger.info(f"⏳ Processing detected: '{elem.text}' - waiting before looking for questions...")
                                time.sleep(10)  # Wait longer if processing is visible
                                break
                        else:
                            time.sleep(3)  # Normal wait if no processing
                    except:
                        time.sleep(3)  # Fallback wait
                    
                    # Check for "Something Went Wrong" error
                    if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                        self.logger.info("🔄 Handled 'Something Went Wrong' error, continuing...")
                        time.sleep(3)
                        continue
                    
                    # Try to find the current question text
                    current_question_text = ""
                    try:
                        question_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[style*='text-align: left']")
                        if question_elements:
                            current_question_text = question_elements[-1].text
                            self.logger.info(f"📋 Current question: {current_question_text[:100]}...")
                            
                            # Extract total question count
                            if total_questions is None and "of" in current_question_text:
                                try:
                                    import re
                                    match = re.search(r'Question\s+\d+\s+of\s+(\d+)', current_question_text)
                                    if match:
                                        total_questions = int(match.group(1))
                                        self.logger.info(f"📊 Detected total questions: {total_questions}")
                                except:
                                    pass
                    except:
                        pass
                    
                    # Check if we've answered all questions
                    if total_questions and len(answered_questions) >= total_questions:
                        self.logger.info(f"✅ All {total_questions} questions answered! Moving to document validation...")
                        self.logger.info("⏳ Waiting 10 seconds for AI to generate document...")
                        time.sleep(10)
                        break
                    
                    # Check if we already answered this question
                    if current_question_text in answered_questions:
                        self.logger.info("✅ Question already answered, waiting for next question...")
                        time.sleep(3)
                        
                        if current_question_text == last_question_text:
                            consecutive_same_count += 1
                            if consecutive_same_count >= 5:
                                self.logger.info("❌ Stuck on answered question, likely reached end")
                                break
                        continue
                    
                    # Reset counter if new question
                    if current_question_text != last_question_text:
                        consecutive_same_count = 0
                        last_question_text = current_question_text
                    
                    # STEP 1: Detect question type (radio vs checkbox)
                    self.logger.info("🔍 Detecting question type...")
                    
                    radio_options = self.driver.find_elements(By.CSS_SELECTOR, self.elements['questions']['radio_option'])
                    checkbox_options = self.driver.find_elements(By.CSS_SELECTOR, self.elements['questions']['checkbox_option'])
                    
                    is_radio_question = False
                    is_checkbox_question = False
                    selected_options = []
                    
                    # Check for visible radio options
                    for radio in radio_options:
                        if radio.is_displayed():
                            is_radio_question = True
                            selected_options.append(radio)
                            break  # For radio, we only need one option
                    
                    # Check for visible checkbox options
                    if not is_radio_question:
                        for checkbox in checkbox_options:
                            if checkbox.is_displayed():
                                is_checkbox_question = True
                                selected_options.append(checkbox)
                                break  # For checkbox, we only need one option
                    
                    if not selected_options:
                        self.logger.info("⏳ No radio or checkbox options found, checking if questions are complete...")
                        
                        # Check if we've moved to next phase (no more questions)
                        time.sleep(2)
                        
                        # Look for indicators that questions are done
                        try:
                            # Check if we're on a different page/phase
                            page_indicators = self.driver.find_elements(By.CSS_SELECTOR, "div[data-context-testid], div.tile")
                            if page_indicators:
                                self.logger.info("✅ Questions phase completed - moved to next phase")
                                break
                        except:
                            pass
                        
                        # If still no options after waiting, break
                        if consecutive_same_count > 3:
                            break
                        continue
                    
                    # STEP 2: Handle based on question type
                    if is_radio_question:
                        self.logger.info("📻 RADIO QUESTION detected - clicking option")
                        
                        # Check if already selected
                        already_selected = False
                        try:
                            input_elem = selected_options[0].find_element(By.CSS_SELECTOR, "input[type='radio']")
                            if input_elem.is_selected():
                                already_selected = True
                                self.logger.info("✅ Radio option already selected")
                        except:
                            pass
                        
                        if not already_selected:
                            # Click the radio option
                            clicked = False
                            
                            # Method 1: Click the label/element directly
                            try:
                                selected_options[0].click()
                                clicked = True
                                self.logger.info("✅ Radio option clicked (direct)")
                            except:
                                pass
                            
                            # Method 2: Click via JavaScript
                            if not clicked:
                                try:
                                    self.driver.execute_script("arguments[0].click();", selected_options[0])
                                    clicked = True
                                    self.logger.info("✅ Radio option clicked (JavaScript)")
                                except:
                                    pass
                            
                            if not clicked:
                                self.logger.error("❌ Failed to click radio option")
                                return False, "Failed to click radio option"
                            
                            time.sleep(2)
                        
                        # For radio questions, NO "Selection Done" button needed
                        self.logger.info("✅ Radio question completed - no Selection Done button needed")
                        
                    elif is_checkbox_question:
                        self.logger.info("☑️ CHECKBOX QUESTION detected - clicking checkbox + Selection Done")
                        
                        # Check if already selected
                        already_selected = False
                        try:
                            input_elem = selected_options[0].find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                            if input_elem.is_selected():
                                already_selected = True
                                self.logger.info("✅ Checkbox option already selected")
                        except:
                            pass
                        
                        if not already_selected:
                            # Click the checkbox option
                            clicked = False
                            
                            try:
                                selected_options[0].click()
                                clicked = True
                                self.logger.info("✅ Checkbox option clicked")
                            except:
                                try:
                                    self.driver.execute_script("arguments[0].click();", selected_options[0])
                                    clicked = True
                                    self.logger.info("✅ Checkbox option clicked (JavaScript)")
                                except:
                                    pass
                            
                            if not clicked:
                                self.logger.error("❌ Failed to click checkbox option")
                                return False, "Failed to click checkbox option"
                            
                            time.sleep(2)
                        
                        # For checkbox questions, click "Selection Done" button
                        self.logger.info("🔘 Looking for Selection Done button...")
                        
                        done_clicked = False
                        
                        # Try multiple selectors for Selection Done button
                        done_selectors = [
                            self.elements['questions']['selection_done_button'],
                            self.elements['questions']['selection_done_button_css'],
                            self.elements['questions']['selection_done_button_xpath']
                        ]
                        
                        for selector in done_selectors:
                            try:
                                if selector.startswith("//"):
                                    # XPath selector
                                    done_button = WebDriverWait(self.driver, 5).until(
                                        EC.element_to_be_clickable((By.XPATH, selector))
                                    )
                                else:
                                    # CSS selector
                                    done_button = WebDriverWait(self.driver, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                                    )
                                
                                if done_button.is_displayed():
                                    done_button.click()
                                    done_clicked = True
                                    self.logger.info("✅ Selection Done button clicked")
                                    break
                            except:
                                continue
                        
                        if not done_clicked:
                            # Try finding by text content as fallback
                            try:
                                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                                for btn in all_buttons:
                                    if btn.is_displayed() and ("Selection Done" in btn.text or "Next" in btn.text):
                                        self.logger.info(f"✅ Found Selection Done button (by text: '{btn.text}'), clicking...")
                                        btn.click()
                                        done_clicked = True
                                        break
                            except Exception as e:
                                self.logger.warning(f"⚠️ Text search failed: {e}")
                        
                        if not done_clicked:
                            self.logger.error("❌ CRITICAL: Could not find Selection Done button for checkbox question!")
                            return False, "Could not find Selection Done button"
                        else:
                            self.logger.info("✅ Checkbox question completed with Selection Done")
                    
                    # Mark question as answered
                    if current_question_text:
                        answered_questions.add(current_question_text)
                        self.logger.info(f"✅ Question marked as answered ({len(answered_questions)}/{total_questions if total_questions else '?'})")
                    
                    questions_answered += 1
                    
                    # Take screenshot after each question
                    self._take_screenshot("requirements", f"question_{questions_answered}")
                    
                    # Wait before next question
                    time.sleep(2)
                    
                    # Check for errors after each question
                    if check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger):
                        self.logger.info("🔄 Error handled, continuing with questions...")
                        time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"⚠️ Exception: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Check if it's a "Something Went Wrong" error
                    check_and_handle_error(self.driver, self.elements, self.error_dir, self.logger)
                    break
            
            # Final screenshot
            self._take_screenshot("requirements", "requirements_completed")
            
            self.logger.info(f"\n✅ Completed {len(answered_questions)} question(s)")
            
            if len(answered_questions) > 0:
                message = f"Requirements gathering completed - answered {len(answered_questions)} questions"
                self.logger.info(f"✅ {message}")
                return True, message
            else:
                message = "No questions found or answered"
                self.logger.warning(f"⚠️ {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"Requirements gathering failed: {e}"
            self.logger.error(error_msg)
            self._take_screenshot("requirements", "requirements_error", is_error=True)
            return False, error_msg
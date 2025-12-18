"""
Selenium Helper Functions
Extracted from Studio_Automation for use in QA Agent
"""

import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Global variable to track last retry click time
last_retry_time = 0


def check_and_handle_error(driver, elements, error_dir=None, logger=None):
    """Check for 'Something Went Wrong' error and click Retry if found"""
    global last_retry_time
    
    try:
        # Check if error message is present
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        if "Something Went Wrong" in page_text or "workflow encountered an error" in page_text:
            # Check if we just clicked retry (within last 25 seconds)
            current_time = time.time()
            if current_time - last_retry_time < 25:
                if logger:
                    logger.info("⏭️ Retry already clicked recently, skipping...")
                return False
            
            if logger:
                logger.warning("⚠️ ERROR DETECTED: 'Something Went Wrong!!!'")
                logger.info("🔄 Attempting to click Retry button...")
            
            # Take screenshot of error in error folder
            if error_dir:
                try:
                    timestamp = datetime.now().strftime("%H-%M-%S")
                    screenshot_path = f"{error_dir}/error_something_went_wrong_{timestamp}.png"
                    driver.save_screenshot(screenshot_path)
                    if logger:
                        logger.info(f"Error screenshot saved: {screenshot_path}")
                except:
                    pass
            
            # Try to click Retry button - multiple strategies
            retry_clicked = False
            
            # Strategy 1: Click label
            try:
                retry_label = driver.find_element(By.CSS_SELECTOR, elements['error_handling']['retry_button'])
                if retry_label.is_displayed():
                    retry_label.click()
                    retry_clicked = True
                    if logger:
                        logger.info("✅ Clicked Retry label")
            except:
                pass
            
            # Strategy 2: Click radio input
            if not retry_clicked:
                try:
                    retry_radio = driver.find_element(By.CSS_SELECTOR, elements['error_handling']['retry_radio'])
                    if retry_radio.is_displayed():
                        driver.execute_script("arguments[0].click();", retry_radio)
                        retry_clicked = True
                        if logger:
                            logger.info("✅ Clicked Retry radio button")
                except:
                    pass
            
            # Strategy 3: Find by text
            if not retry_clicked:
                try:
                    labels = driver.find_elements(By.TAG_NAME, "label")
                    for label in labels:
                        if "Retry" in label.text and label.is_displayed():
                            label.click()
                            retry_clicked = True
                            if logger:
                                logger.info("✅ Clicked Retry by text")
                            break
                except:
                    pass
            
            if retry_clicked:
                if logger:
                    logger.info("✅ Retry button clicked successfully")
                last_retry_time = time.time()  # Record the time we clicked retry
                time.sleep(3)
                return True
            else:
                if logger:
                    logger.error("❌ Failed to click Retry button")
                return False
        
        return False  # No error found
        
    except Exception as e:
        if logger:
            logger.warning(f"⚠️ Error while checking for errors: {e}")
        return False


def wait_for_validation_screen(driver, phase_name="", elements=None, error_dir=None, logger=None):
    """Wait for validation screen with options C, D, E"""
    if logger:
        logger.info(f"⏳ Waiting for {phase_name} validation screen with options C, D, E...")
        logger.info("⚠️ CRITICAL: Will NOT type 'E' until validation screen is confirmed!")
    time.sleep(5)
    
    # Different keywords for different phases
    if phase_name == "Wireframe":
        validation_keywords = [
            "User Experience",
            "Data Display",
            "design specification",
            "development step",
            "review the available options"
        ]
    elif phase_name == "Design Document":
        validation_keywords = [
            "design document",
            "specification",
            "proceed",
            "review the available options",
            "letter corresponding"
        ]
    else:
        validation_keywords = [
            "Request Modification",
            "Notification",
            "Confirm document",
            "review the available options",
            "letter corresponding"
        ]
    
    for attempt in range(15):
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Count keyword matches
            matches = sum(1 for keyword in validation_keywords if keyword in page_text)
            
            # Check for option letters C, D, E
            has_c = "C." in page_text
            has_d = "D." in page_text
            has_e = "E." in page_text or "E " in page_text  # E might have space instead of period
            has_options = (has_c and has_d) or (has_c and has_d and has_e)  # At least C and D
            
            # Debug output
            if logger:
                logger.info(f"   Attempt {attempt + 1}: matches={matches}, C={has_c}, D={has_d}, E={has_e}")
            
            # Less strict: Either 1+ matches with C&D, OR 2+ matches
            if (matches >= 1 and has_c and has_d) or (matches >= 2):
                if logger:
                    logger.info(f"✅ {phase_name} validation screen confirmed!")
                    logger.info(f"   - Matched {matches} keywords")
                    logger.info(f"   - Found options: C={has_c}, D={has_d}, E={has_e}")
                    for keyword in validation_keywords:
                        if keyword in page_text:
                            logger.info(f"   ✓ '{keyword}'")
                return True
        except Exception as e:
            if logger:
                logger.warning(f"   Error checking page: {e}")
        
        # Check for "Something Went Wrong" error while waiting
        if elements and error_dir:
            if check_and_handle_error(driver, elements, error_dir, logger):
                if logger:
                    logger.info("🔄 Error detected and handled, continuing wait...")
                time.sleep(3)
        
        time.sleep(5)
    
    if logger:
        logger.warning(f"⚠️ Timeout waiting for {phase_name} validation screen")
    return False


def type_e_and_enter(driver, elements, logger=None):
    """Type 'E' and press Enter in the decision input field"""
    
    # FIRST: Wait for any "Processing..." to disappear
    if logger:
        logger.info("🔍 Checking if 'Processing...' is visible...")
    max_wait = 120  # Wait up to 2 minutes for processing to finish
    wait_interval = 5
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            processing_elements = driver.find_elements(By.CSS_SELECTOR, "span[style*='font-weight: 600']")
            processing_visible = False
            
            for elem in processing_elements:
                if elem.is_displayed() and "Processing" in elem.text:
                    processing_visible = True
                    if logger:
                        logger.info(f"⏳ Processing still visible: '{elem.text}' - waiting... ({elapsed}s/{max_wait}s)")
                    break
            
            if not processing_visible:
                if logger:
                    logger.info("✅ No processing loader visible, input should be ready")
                break
                
            time.sleep(wait_interval)
            elapsed += wait_interval
            
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Error checking processing: {e}")
            break
    
    if elapsed >= max_wait:
        if logger:
            logger.warning("⚠️ Processing wait timeout, proceeding anyway...")
    
    # SECOND: Wait for the complete instruction message to appear
    if logger:
        logger.info("🔍 Waiting for complete instruction message...")
    instruction_found = False
    instruction_wait = 60  # Wait up to 1 minute
    instruction_elapsed = 0
    
    while instruction_elapsed < instruction_wait:
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "Please review the available options and type the letter corresponding to your choice" in page_text:
                if logger:
                    logger.info("✅ Complete instruction message found!")
                instruction_found = True
                # Wait extra 5 seconds after finding message to ensure page is fully loaded
                if logger:
                    logger.info("⏳ Waiting 5 more seconds for page to fully load...")
                time.sleep(5)
                break
            else:
                if logger:
                    logger.info(f"⏳ Waiting for instruction message... ({instruction_elapsed}s/{instruction_wait}s)")
                time.sleep(5)
                instruction_elapsed += 5
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Error checking instruction: {e}")
            break
    
    if not instruction_found:
        if logger:
            logger.warning("⚠️ Instruction message not found, proceeding anyway...")
            logger.info("⏳ Waiting 10 seconds before proceeding...")
        time.sleep(10)
    
    if logger:
        logger.info("⏳ Waiting for decision input field to become visible...")
    
    decision_input = None
    input_found = False
    
    # Strategy 1: Try the configured selector
    try:
        if logger:
            logger.info("📝 Strategy 1: Using configured selector...")
        decision_input = WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, elements['document_flow']['decision_input']))
        )
        input_found = True
        if logger:
            logger.info("✅ Input field found with configured selector")
    except Exception as e:
        if logger:
            logger.warning(f"⚠️ Strategy 1 failed: {e}")
    
    # Strategy 2: Try finding any visible textarea with placeholder
    if not input_found:
        try:
            if logger:
                logger.info("📝 Strategy 2: Looking for any textarea with placeholder...")
            all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
            for ta in all_textareas:
                if ta.is_displayed() and ta.get_attribute("placeholder"):
                    decision_input = ta
                    input_found = True
                    if logger:
                        logger.info(f"✅ Found visible textarea: placeholder='{ta.get_attribute('placeholder')}'")
                    break
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Strategy 2 failed: {e}")
    
    if not input_found or not decision_input:
        if logger:
            logger.error("❌ Could not find input field")
        raise Exception("Decision input field not found")
    
    if logger:
        logger.info("✅ Decision input field is ready")
    
    # Verify input is interactable before typing
    if logger:
        logger.info("🔍 Verifying input field is interactable...")
    try:
        # Wait for element to be clickable
        decision_input = WebDriverWait(driver, 10).until(
            lambda d: decision_input if decision_input.is_enabled() and decision_input.is_displayed() else None
        )
        if logger:
            logger.info("✅ Input field is interactable")
    except:
        if logger:
            logger.warning("⚠️ Input field may not be fully ready, waiting 5 more seconds...")
        time.sleep(5)
    
    # Type E and press Enter
    try:
        decision_input.click()
        time.sleep(2)  # Increased wait after click
    except:
        if logger:
            logger.warning("⚠️ Could not click input, trying to send keys directly...")
    
    try:
        decision_input.clear()
    except:
        pass
    
    decision_input.send_keys("E")
    time.sleep(3)  # Increased wait after typing
    if logger:
        logger.info("✅ Typed 'E'")
    
    if logger:
        logger.info("⏎ Pressing Enter/Send...")
    
    # Try multiple strategies to press Enter
    enter_pressed = False
    
    # Strategy 0: Try send button with testid (MOST RELIABLE)
    for retry_attempt in range(3):
        try:
            if logger:
                logger.info(f"📝 Strategy 0: Using send button with testid (attempt {retry_attempt + 1}/3)...")
            send_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, elements['document_flow']['send_button']))
            )
            
            # Wait a moment for button to be ready
            time.sleep(1)
            
            # Try multiple click methods
            clicked = False
            
            # Method 1: Regular click
            try:
                send_btn.click()
                clicked = True
                if logger:
                    logger.info("✅ Send button clicked (regular)")
            except:
                pass
            
            # Method 2: JavaScript click
            if not clicked:
                try:
                    driver.execute_script("arguments[0].click();", send_btn)
                    clicked = True
                    if logger:
                        logger.info("✅ Send button clicked (JavaScript)")
                except:
                    pass
            
            # Method 3: ActionChains click
            if not clicked:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(driver).move_to_element(send_btn).click().perform()
                    clicked = True
                    if logger:
                        logger.info("✅ Send button clicked (ActionChains)")
                except:
                    pass
            
            if clicked:
                time.sleep(3)
                if logger:
                    logger.info("✅ Send button (testid) clicked successfully!")
                enter_pressed = True
                break  # Success, exit retry loop
            else:
                if logger:
                    logger.warning(f"⚠️ All click methods failed for send button (attempt {retry_attempt + 1})")
                if retry_attempt < 2:
                    time.sleep(2)  # Wait before retry
                
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Send button (testid) not found (attempt {retry_attempt + 1}): {e}")
            if retry_attempt < 2:
                time.sleep(2)  # Wait before retry
    
    # Strategy 1: Keys.RETURN
    if not enter_pressed:
        try:
            decision_input.send_keys(Keys.RETURN)
            time.sleep(2)
            if logger:
                logger.info("✅ Pressed Enter (RETURN)")
            enter_pressed = True
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ RETURN failed: {e}")
    
    # Strategy 2: Keys.ENTER
    if not enter_pressed:
        try:
            decision_input.send_keys(Keys.ENTER)
            time.sleep(2)
            if logger:
                logger.info("✅ Pressed Enter (ENTER)")
            enter_pressed = True
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ ENTER failed: {e}")
    
    if not enter_pressed:
        if logger:
            logger.warning("⚠️ WARNING: Could not confirm Enter was pressed")
    
    time.sleep(3)

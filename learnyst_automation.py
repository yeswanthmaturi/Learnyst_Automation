import asyncio
import logging
from playwright.async_api import async_playwright
from config import add_log_message

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LearnystAutomation:
    """Class to handle Learnyst automation tasks with Playwright."""
    
    def __init__(self, username, password):
        """Initialize the automation with login credentials."""
        self.username = username
        self.password = password
        self.browser = None
        self.page = None
        self.is_logged_in = False
        
    async def initialize(self):
        """Initialize the browser and log in to Learnyst."""
        try:
            # Launch the browser with special configuration for Replit
            import os
            import subprocess
            import sys
            
            # Add detailed environment debug information
            logger.info(f"Python version: {sys.version}")
            add_log_message(f"Python version: {sys.version}")
            logger.info(f"Current working directory: {os.getcwd()}")
            add_log_message(f"Current working directory: {os.getcwd()}")
            
            # Try to verify playwright installation
            try:
                import playwright
                import pkg_resources
                playwright_version = pkg_resources.get_distribution("playwright").version
                logger.info(f"Playwright version: {playwright_version}")
                add_log_message(f"Playwright version: {playwright_version}")
            except Exception as e:
                logger.error(f"Error getting Playwright version: {str(e)}")
                add_log_message(f"Error getting Playwright version: {str(e)}")
            
            # Try to get the chromium path dynamically
            try:
                chromium_path = subprocess.check_output(['which', 'chromium']).decode('utf-8').strip()
                logger.info(f"Found Chromium at: {chromium_path}")
                add_log_message(f"Found Chromium at: {chromium_path}")
                
                # Check if chromium is executable
                if not os.access(chromium_path, os.X_OK):
                    logger.warning(f"Chromium at {chromium_path} is not executable")
                    add_log_message(f"Chromium at {chromium_path} is not executable")
            except Exception as e:
                chromium_path = '/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium'
                logger.warning(f"Could not find Chromium path automatically: {str(e)}. Using default path.")
                add_log_message(f"Using default Chromium path: {chromium_path}")
            
            # Start playwright
            logger.info("Starting async_playwright...")
            add_log_message("Starting async_playwright...")
            playwright = await async_playwright().start()
            
            # Use Replit-compatible browser configuration
            logger.info(f"Launching browser with executable path: {chromium_path}")
            add_log_message(f"Launching browser with executable path: {chromium_path}")
            
            # Try to launch the browser with executable path first
            try:
                self.browser = await playwright.chromium.launch(
                    headless=True,
                    executable_path=chromium_path,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-setuid-sandbox',
                        '--single-process'
                    ]
                )
                logger.info("Successfully launched browser with executable_path")
                add_log_message("Successfully launched browser with executable_path")
            except Exception as browser_launch_error:
                # If that fails, try to launch without specifying the executable path
                logger.warning(f"Failed to launch with executable_path: {str(browser_launch_error)}")
                add_log_message(f"Failed to launch with executable_path: {str(browser_launch_error)}")
                
                try:
                    logger.info("Trying to launch browser without executable_path...")
                    add_log_message("Trying to launch browser without executable_path...")
                    self.browser = await playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-setuid-sandbox',
                            '--single-process'
                        ]
                    )
                    logger.info("Successfully launched browser without executable_path")
                    add_log_message("Successfully launched browser without executable_path")
                except Exception as fallback_error:
                    logger.error(f"Failed to launch browser with fallback: {str(fallback_error)}")
                    add_log_message(f"Failed to launch browser with fallback: {str(fallback_error)}")
                    raise
            
            # Create a new page
            if self.browser:
                logger.info("Creating new browser page...")
                add_log_message("Creating new browser page...")
                self.page = await self.browser.new_page()
                logger.info("Browser page created successfully")
                add_log_message("Browser page created successfully")
            else:
                logger.error("Failed to create page: browser is None")
                add_log_message("Failed to create page: browser is None")
                raise Exception("Failed to create page: browser is None")
            
            # Set default timeout
            self.page.set_default_timeout(30000)  # 30 seconds
            
            # Log in to Learnyst
            await self._login()
            
            return True
        except Exception as e:
            error_message = f"Initialization error: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            if self.browser:
                await self.browser.close()
            self.browser = None
            self.page = None
            raise Exception(error_message)
    
    async def _login(self):
        """Log in to Learnyst admin dashboard."""
        try:
            # Navigate to the login page
            await self.page.goto("https://techpathai.learnyst.com/", timeout=60000)
            
            # Check if already logged in
            if await self._check_if_logged_in():
                self.is_logged_in = True
                return True
                
            # Wait for the login form to be visible
            await self.page.wait_for_selector('input[name="user[email]"]')
            
            # Fill the login form
            await self.page.fill('input[name="user[email]"]', self.username)
            await self.page.fill('input[name="user[password]"]', self.password)
            
            # Click the login button
            await self.page.click('button[type="submit"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Verify login success
            if await self._check_if_logged_in():
                self.is_logged_in = True
                add_log_message("Successfully logged in to Learnyst")
                return True
            else:
                error_message = "Failed to log in to Learnyst"
                logger.error(error_message)
                add_log_message(error_message)
                raise Exception(error_message)
        except Exception as e:
            error_message = f"Login error: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            raise Exception(error_message)
    
    async def _check_if_logged_in(self):
        """Check if we're logged in to Learnyst dashboard."""
        try:
            # Look for elements that indicate we're logged in
            selector = '.navbar-brand, .user-menu, .sidebar-menu'
            is_logged_in = await self.page.is_visible(selector, timeout=5000)
            return is_logged_in
        except:
            return False
    
    async def _ensure_logged_in(self):
        """Ensure we're logged in before performing actions."""
        if not self.is_logged_in or not await self._check_if_logged_in():
            await self._login()
    
    async def _navigate_to_learners(self):
        """Navigate to the learners tab in the admin dashboard."""
        try:
            # Ensure we're logged in
            await self._ensure_logged_in()
            
            # Navigate to the users tab
            await self.page.click('a:has-text("Users")', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            
            # Navigate to the learners tab
            await self.page.click('a:has-text("Learners")', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            
            return True
        except Exception as e:
            error_message = f"Navigation error: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            raise Exception(error_message)
    
    async def give_access(self, email, course_name):
        """Give access to a course for an existing user."""
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user by email
            await self.page.fill('input[placeholder="Search"]', email)
            await self.page.press('input[placeholder="Search"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            user_row_selector = f'tr:has-text("{email}")'
            if not await self.page.is_visible(user_row_selector, timeout=5000):
                return f"User with email {email} not found. Please provide full name to enroll them."
            
            # Click on the user row
            await self.page.click(user_row_selector)
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Add Product" button
            await self.page.click('button:has-text("Add Product")', timeout=10000)
            await self.page.wait_for_selector('select.form-control', state="visible")
            
            # Select the product/course
            product_selector = 'select.form-control >> nth=0'  # First dropdown (product selection)
            await self.page.select_option(product_selector, label=course_name)
            
            # Select "trail" in the type dropdown
            type_selector = 'select.form-control >> nth=1'  # Second dropdown (type selection)
            await self.page.select_option(type_selector, label="trial")
            
            # Click Save & Next
            await self.page.click('button:has-text("Save & Next")')
            await self.page.wait_for_load_state("networkidle")
            
            # Select the base plan and confirm
            await self.page.click('input[type="radio"]')  # Select the first radio button (base plan)
            
            # Click "Add Offline Payment" button
            await self.page.click('button:has-text("Add Offline Payment")')
            await self.page.wait_for_load_state("networkidle")
            
            # Handle any additional popups if they appear
            try:
                if await self.page.is_visible('.modal-dialog', timeout=5000):
                    await self.page.click('.modal-dialog button:has-text("Confirm")')
                    await self.page.wait_for_load_state("networkidle")
            except:
                # Ignore if no popup appears
                pass
            
            success_message = f"Successfully gave access to {course_name} for user {email}"
            add_log_message(success_message)
            return success_message
            
        except Exception as e:
            error_message = f"Error giving access: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            return f"Failed to give access: {str(e)}"
    
    async def enroll_user(self, email, full_name, course_name):
        """Enroll a new user to a course."""
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Click "+Add" button
            await self.page.click('button:has-text("+Add")', timeout=10000)
            await self.page.wait_for_selector('input[placeholder="Email"]', state="visible")
            
            # Fill user details
            await self.page.fill('input[placeholder="Email"]', email)
            await self.page.fill('input[placeholder="Full Name"]', full_name)
            
            # Select the product/course
            product_selector = 'select.form-control'  # Product dropdown
            await self.page.select_option(product_selector, label=course_name)
            
            # Click "Add" button to confirm
            await self.page.click('button:has-text("Add")')
            await self.page.wait_for_load_state("networkidle")
            
            # Handle any additional popups or confirmations
            try:
                if await self.page.is_visible('.modal-dialog', timeout=5000):
                    await self.page.click('.modal-dialog button:has-text("Confirm")')
                    await self.page.wait_for_load_state("networkidle")
            except:
                # Ignore if no popup appears
                pass
            
            success_message = f"Successfully enrolled {full_name} ({email}) to {course_name}"
            add_log_message(success_message)
            return success_message
            
        except Exception as e:
            error_message = f"Error enrolling user: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            return f"Failed to enroll user: {str(e)}"
    
    async def suspend_user(self, user_identifier):
        """Suspend a user account."""
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user
            await self.page.fill('input[placeholder="Search"]', user_identifier)
            await self.page.press('input[placeholder="Search"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            user_row_selector = f'tr:has-text("{user_identifier}")'
            if not await self.page.is_visible(user_row_selector, timeout=5000):
                return f"User with identifier {user_identifier} not found."
            
            # Click on the user row
            await self.page.click(user_row_selector)
            await self.page.wait_for_load_state("networkidle")
            
            # Click "More" button
            await self.page.click('button:has-text("More")', timeout=10000)
            
            # Click "Settings" option
            await self.page.click('a:has-text("Settings")')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Suspend Learner Account" tab
            await self.page.click('a:has-text("Suspend Learner Account")')
            await self.page.wait_for_load_state("networkidle")
            
            # Click the suspend button
            await self.page.click('button:has-text("Suspend")')
            
            # Confirm suspension
            await self.page.click('.modal-dialog button:has-text("Suspend")')
            await self.page.wait_for_load_state("networkidle")
            
            success_message = f"Successfully suspended user account for {user_identifier}"
            add_log_message(success_message)
            return success_message
            
        except Exception as e:
            error_message = f"Error suspending user: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            return f"Failed to suspend user: {str(e)}"
    
    async def delete_user(self, user_identifier):
        """Delete a user account."""
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user
            await self.page.fill('input[placeholder="Search"]', user_identifier)
            await self.page.press('input[placeholder="Search"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            user_row_selector = f'tr:has-text("{user_identifier}")'
            if not await self.page.is_visible(user_row_selector, timeout=5000):
                return f"User with identifier {user_identifier} not found."
            
            # Click on the user row
            await self.page.click(user_row_selector)
            await self.page.wait_for_load_state("networkidle")
            
            # Click "More" button
            await self.page.click('button:has-text("More")', timeout=10000)
            
            # Click "Settings" option
            await self.page.click('a:has-text("Settings")')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Delete Learner Account" tab
            await self.page.click('a:has-text("Delete Learner Account")')
            await self.page.wait_for_load_state("networkidle")
            
            # Click the delete button
            await self.page.click('button:has-text("Delete")')
            
            # Confirm deletion
            await self.page.click('.modal-dialog button:has-text("Delete")')
            await self.page.wait_for_load_state("networkidle")
            
            success_message = f"Successfully deleted user account for {user_identifier}"
            add_log_message(success_message)
            return success_message
            
        except Exception as e:
            error_message = f"Error deleting user: {str(e)}"
            logger.error(error_message)
            add_log_message(error_message)
            return f"Failed to delete user: {str(e)}"
    
    async def close(self):
        """Close the browser and release resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None
            self.is_logged_in = False

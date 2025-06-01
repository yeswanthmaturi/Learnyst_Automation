import os
import asyncio
import logging
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError
import secrets

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LearnystAutomation:
    """Class to handle Learnyst automation tasks with Playwright."""
    
    def __init__(self, username, password):
        """Initialize the automation with login credentials."""
        self.username = username
        self.password = password
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False
        self.base_url = "https://techpathai.learnyst.com"
        
    async def initialize(self):
        """Initialize the browser and log in to Learnyst."""
        try:
            # Start playwright and launch browser
            self.playwright = await async_playwright().start()
            
            # Launch browser with headless mode enabled for server environments
            # For local development, you might want to set headless=False for debugging
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Set to False for debugging
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Create a browser context with viewport settings
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800}
            )
            
            # Create a new page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(60000)  # 60 seconds
            
            # Log in to Learnyst
            await self._login()
            
            # Mark as initialized
            self.is_initialized = True
            logger.info("Browser initialized and logged in successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}")
            await self.close()
            raise
    
    async def _login(self):
        """Log in to Learnyst admin dashboard."""
        try:
            # Navigate to the login page
            await self.page.goto(f"{self.base_url}/admin/sign_in")
            
            # Wait for the login form to appear
            await self.page.wait_for_selector('input[name="admin[email]"]')
            
            # Fill in the login form
            await self.page.fill('input[name="admin[email]"]', self.username)
            await self.page.fill('input[name="admin[password]"]', self.password)
            
            # Click the login button
            await self.page.click('input[name="commit"]')
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            # Check if login was successful
            if await self._check_if_logged_in():
                logger.info("Successfully logged in to Learnyst")
                return True
            else:
                logger.error("Failed to log in to Learnyst")
                raise Exception("Login failed - could not verify successful login")
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise
    
    async def _check_if_logged_in(self):
        """Check if we're logged in to Learnyst dashboard."""
        try:
            # Look for elements that indicate we're logged in
            is_logged_in = await self.page.is_visible('.side-nav')
            
            return is_logged_in
        except Exception:
            return False
    
    async def _ensure_logged_in(self):
        """Ensure we're logged in before performing actions."""
        if not self.is_initialized:
            await self.initialize()
        
        if not await self._check_if_logged_in():
            logger.info("Session expired, logging in again")
            await self._login()
    
    async def _navigate_to_learners(self):
        """Navigate to the learners tab in the admin dashboard."""
        await self._ensure_logged_in()
        
        try:
            # Navigate to the users section
            await self.page.click('.side-nav a[href="/admin/learners"]')
            await self.page.wait_for_load_state("networkidle")
            
            # Click on the learners tab
            await self.page.click('.tab-list a[href="/admin/learners"]')
            await self.page.wait_for_load_state("networkidle")
            
            logger.info("Successfully navigated to learners tab")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to learners tab: {str(e)}")
            raise
    
    async def give_access(self, email, course_name):
        """Give access to a course for an existing user.
        
        Workflow:
        1. Search user by email
        2. Click on user
        3. Click "Add Product"
        4. Select course
        5. Select "Trial" access type
        6. Save & Next
        7. Select base plan
        8. Add offline payment with 2 months validity
        9. Save
        """
        await self._ensure_logged_in()
        
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user by email
            await self.page.fill('input[placeholder="Search by name or email"]', email)
            await self.page.press('input[placeholder="Search by name or email"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            search_results = await self.page.is_visible('//table//tbody//tr')
            if not search_results:
                return f"Error: User with email {email} not found"
            
            # Click on the user
            await self.page.click('//table//tbody//tr//td[contains(., "@")]')
            await self.page.wait_for_selector('//a[contains(text(), "Add Product")]')
            
            # Click "Add Product"
            await self.page.click('//a[contains(text(), "Add Product")]')
            await self.page.wait_for_selector('//select[@name="product_id"]')
            
            # Select course from dropdown
            await self.page.select_option('//select[@name="product_id"]', label=course_name)
            
            # Select "Trial" access type
            await self.page.select_option('//select[@name="access_type"]', label='Trial')
            
            # Click Save & Next
            await self.page.click('//button[contains(text(), "Save & Next")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Select base plan - assuming the first option is the base plan
            if await self.page.is_visible('//input[@name="plan_id"]'):
                await self.page.click('//input[@name="plan_id"]')
                await self.page.wait_for_load_state("networkidle")
            
            # Click Add Offline Payment
            await self.page.click('//button[contains(text(), "Add Offline")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Set expiry date to 2 months from now
            expiry_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
            date_input = await self.page.query_selector('input[type="date"]')
            if date_input:
                await date_input.fill(expiry_date)
            
            # Click Save
            await self.page.click('//button[contains(text(), "Save")]')
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Successfully gave access to {course_name} for user {email}")
            return f"✅ Successfully gave access to {course_name} for user {email}"
            
        except Exception as e:
            logger.error(f"Error giving access: {str(e)}")
            return f"❌ Error giving access: {str(e)}"
    
    async def enroll_user(self, email, full_name, course_name):
        """Enroll a new user to a course.
        
        Workflow:
        1. Go to learners tab
        2. Click "+ Add"
        3. Fill email and full name
        4. Select course and trial access type
        5. Set validity to 2 months
        6. Click "Add New Learner"
        """
        await self._ensure_logged_in()
        
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Click "+ Add" button
            await self.page.click('//a[contains(text(), "Add")]')
            await self.page.wait_for_selector('//input[@name="learner_email"]')
            
            # Fill email and full name
            await self.page.fill('//input[@name="learner_email"]', email)
            await self.page.fill('//input[@name="learner_name"]', full_name)
            
            # Select course from dropdown
            await self.page.select_option('//select[@name="product_id"]', label=course_name)
            
            # Select "Trial" access type
            await self.page.select_option('//select[@name="access_type"]', label='Trial')
            
            # Click "Add New Learner"
            await self.page.click('//button[contains(text(), "Add New Learner")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Check for success message
            success = await self.page.is_visible('//div[contains(@class, "alert-success")]')
            if success:
                logger.info(f"Successfully enrolled {full_name} ({email}) to {course_name}")
                return f"✅ Successfully enrolled {full_name} ({email}) to {course_name}"
            else:
                logger.error(f"Failed to enroll user {email}")
                return f"❌ Failed to enroll user {email} - please check email/name and try again"
            
        except Exception as e:
            logger.error(f"Error enrolling user: {str(e)}")
            return f"❌ Error enrolling user: {str(e)}"
    
    async def suspend_user(self, user_identifier):
        """Suspend a user account.
        
        Workflow:
        1. Search for user
        2. Click on user
        3. Click "More" button
        4. Click "Settings"
        5. Click "Suspend Learner Account" tab
        6. Click "Suspend" button
        7. Confirm suspension
        """
        await self._ensure_logged_in()
        
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user by identifier (email or name)
            await self.page.fill('input[placeholder="Search by name or email"]', user_identifier)
            await self.page.press('input[placeholder="Search by name or email"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            search_results = await self.page.is_visible('//table//tbody//tr')
            if not search_results:
                return f"Error: User with identifier {user_identifier} not found"
            
            # Click on the user
            await self.page.click('//table//tbody//tr//td[contains(., "@")]')
            await self.page.wait_for_selector('//button[contains(text(), "More")]')
            
            # Click "More" button
            await self.page.click('//button[contains(text(), "More")]')
            await self.page.wait_for_selector('//a[contains(text(), "Settings")]')
            
            # Click "Settings"
            await self.page.click('//a[contains(text(), "Settings")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Suspend Learner Account" tab
            await self.page.click('//a[contains(text(), "Suspend Learner Account")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Suspend" button
            await self.page.click('//button[contains(text(), "Suspend")]')
            
            # Confirm suspension by clicking confirm button
            await self.page.click('//button[contains(text(), "Suspend")]//following::button[contains(text(), "Suspend")]')
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Successfully suspended user {user_identifier}")
            return f"✅ Successfully suspended user {user_identifier}"
            
        except Exception as e:
            logger.error(f"Error suspending user: {str(e)}")
            return f"❌ Error suspending user: {str(e)}"
    
    async def delete_user(self, user_identifier):
        """Delete a user account.
        
        Workflow:
        1. Search for user
        2. Click on user
        3. Click "More" button
        4. Click "Settings"
        5. Click "Delete Learner Account" tab
        6. Click "Delete" button
        """
        await self._ensure_logged_in()
        
        try:
            # Navigate to learners tab
            await self._navigate_to_learners()
            
            # Search for the user by identifier (email or name)
            await self.page.fill('input[placeholder="Search by name or email"]', user_identifier)
            await self.page.press('input[placeholder="Search by name or email"]', 'Enter')
            await self.page.wait_for_load_state("networkidle")
            
            # Check if user exists
            search_results = await self.page.is_visible('//table//tbody//tr')
            if not search_results:
                return f"Error: User with identifier {user_identifier} not found"
            
            # Click on the user
            await self.page.click('//table//tbody//tr//td[contains(., "@")]')
            await self.page.wait_for_selector('//button[contains(text(), "More")]')
            
            # Click "More" button
            await self.page.click('//button[contains(text(), "More")]')
            await self.page.wait_for_selector('//a[contains(text(), "Settings")]')
            
            # Click "Settings"
            await self.page.click('//a[contains(text(), "Settings")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Delete Learner Account" tab
            await self.page.click('//a[contains(text(), "Delete Learner Account")]')
            await self.page.wait_for_load_state("networkidle")
            
            # Click "Delete" button
            await self.page.click('//button[contains(text(), "Delete")]')
            
            # Confirm deletion by clicking confirm button
            await self.page.click('//button[contains(text(), "Delete")]//following::button[contains(text(), "Delete")]')
            await self.page.wait_for_load_state("networkidle")
            
            logger.info(f"Successfully deleted user {user_identifier}")
            return f"✅ Successfully deleted user {user_identifier}"
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return f"❌ Error deleting user: {str(e)}"
    
    async def close(self):
        """Close the browser and release resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            self.browser = None
            self.context = None
            self.page = None
            self.playwright = None
            self.is_initialized = False
            
            logger.info("Browser closed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error closing browser: {str(e)}")
            return False

print(secrets.token_hex(32))
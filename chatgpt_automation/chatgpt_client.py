'''Class definition for ChatGPT_Client'''

import os
import logging
import time
import undetected_chromedriver as uc

# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions as Exceptions

from .helpers import detect_chrome_version

from bs4 import BeautifulSoup

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.WARNING
)

class ChatGPT_Client:
    '''ChatGPT_Client class to interact with ChatGPT'''

    login_xq    = '//button[//div[text()="Log in"]]'
    continue_xq = '//button[text()="Continue"]'
    tutorial_iq = 'radix-:ri:'
    button_tq   = 'button'
    done_xq     = '//button[//div[text()="Done"]]'

    chatbox_cq  = 'text-base'
    wait_cq     = 'text-2xl'
    reset_xq    = '//a[//span[text()="New chat"]]'
    regen_xq    = '//div[text()="Regenerate"]'
    textarea_tq = 'textarea'
    textarea_iq = 'prompt-textarea'
    gpt_xq    = '//span[text()="{}"]'
    extract_code = True
    def __init__(
        self,
        username :str = '',
        password :str = '',
        headless :bool = True,
        cold_start :bool = False,
        incognito :bool = True,
        driver_executable_path :str =None,
        driver_arguments : list = None,
        driver_version: int = None,
        verbose :bool = False
    ):
        username = username or os.environ.get('OPENAI_UNAME')
        password = password or os.environ.get('OPENAI_PWD')
        self.extract_code = extract_code
        if not username:
            logging.error('Either provide username or set the environment variable "OPENAI_UNAME"')
            return

        if not password:
            logging.error('Either provide password or set the environment variable "OPENAI_PWD"')
            return

        if verbose:
            logging.getLogger().setLevel(logging.INFO)
            logging.info('Verbose mode active')
        options = uc.ChromeOptions()
        if incognito:
            options.add_argument('--incognito')
        if headless:
            options.add_argument('--headless')
        if driver_arguments:
            for _arg in driver_arguments:
                options.add_argument(_arg)

        logging.info('Loading undetected Chrome')
        self.browser = uc.Chrome(
            driver_executable_path=driver_executable_path,
            options=options,
            headless=headless,
            version_main=detect_chrome_version(driver_version),
            log_level=10,
        )
        self.browser.set_page_load_timeout(15)
        logging.info('Loaded Undetected chrome')
        logging.info('Opening chatgpt')
        self.browser.get('https://chat.openai.com/auth/login?next=/chat')
        if not cold_start:
            self.pass_verification()
            self.login(username, password)
        logging.info('ChatGPT is ready to interact')

    def pass_verification(self):
        '''
        Performs the verification process on the page if challenge is present.

        This function checks if the login page is displayed in the browser.
        In that case, it looks for the verification button.
        This process is repeated until the login page is no longer displayed.

        Returns:
            None
        '''
        while self.check_login_page():
            verify_button = self.browser.find_elements(By.ID, 'challenge-stage')
            if len(verify_button):
                try:
                    verify_button[0].click()
                    logging.info('Clicked verification button')
                except Exceptions.ElementNotInteractableException:
                    logging.info('Verification button is not present or clickable')
            time.sleep(1)
        return

    def check_login_page(self):
        '''
        Checks if the login page is displayed in the browser.

        Returns:
            bool: True if the login page is not present, False otherwise.
        '''
        login_button = self.browser.find_elements(By.XPATH, self.login_xq)
        return len(login_button) == 0

    def login(self, username :str, password :str):
        '''
        Performs the login process with the provided username and password.

        This function operates on the login page.
        It finds and clicks the login button,
        fills in the email and password textboxes

        Args:
            username (str): The username to be entered.
            password (str): The password to be entered.

        Returns:
            None
        '''

        # Find login button, click it
        login_button = self.sleepy_find_element(By.XPATH, self.login_xq)
        login_button.click()
        logging.info('Clicked login button')
        time.sleep(1)

        # Find email textbox, enter e-mail
        email_box = self.sleepy_find_element(By.ID, 'username')
        email_box.send_keys(username)
        logging.info('Filled email box')

        # Click continue
        continue_button = self.sleepy_find_element(By.XPATH, self.continue_xq)
        continue_button.click()
        time.sleep(1)
        logging.info('Clicked continue button')

        # Find password textbox, enter password
        pass_box = self.sleepy_find_element(By.ID, 'password')
        pass_box.send_keys(password)
        logging.info('Filled password box')
        # Click continue
        pass_box.send_keys(Keys.ENTER)
        time.sleep(1)
        logging.info('Logged in')

        try:
            # Pass introduction
            next_button = WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.ID, self.tutorial_iq))
            )
            next_button.find_elements(By.TAG_NAME, self.button_tq)[0].click()

            logging.info('Info screen passed')
        except Exceptions.TimeoutException:
            logging.info('Info screen skipped')
        except Exception as exp:
            logging.error(f'Something unexpected happened: {exp}')

    def sleepy_find_element(self, by, query, attempt_count :int =20, sleep_duration :int =1):
        '''
        Finds the web element using the locator and query.

        This function attempts to find the element multiple times with a specified
        sleep duration between attempts. If the element is found, the function returns the element.

        Args:
            by (selenium.webdriver.common.by.By): The method used to locate the element.
            query (str): The query string to locate the element.
            attempt_count (int, optional): The number of attempts to find the element. Default: 20.
            sleep_duration (int, optional): The duration to sleep between attempts. Default: 1.

        Returns:
            selenium.webdriver.remote.webelement.WebElement: Web element or None if not found.
        '''
        for _count in range(attempt_count):
            item = self.browser.find_elements(by, query)
            if len(item) > 0:
                item = item[0]
                logging.info(f'Element {query} has found')
                break
            logging.info(f'Element {query} is not present, attempt: {_count+1}')
            time.sleep(sleep_duration)
        return item

    def wait_until_disappear(self, by, query, timeout_duration=15):
        '''
        Waits until the specified web element disappears from the page.

        This function continuously checks for the presence of a web element.
        It waits until the element is no longer present on the page.
        Once the element has disappeared, the function returns.

        Args:
            by (selenium.webdriver.common.by.By): The method used to locate the element.
            query (str): The query string to locate the element.
            timeout_duration (int, optional): The total wait time before the timeout exception. Default: 15.

        Returns:
            None
        '''
        logging.info(f'Waiting element {query} to disappear.')
        try:
            WebDriverWait(
                self.browser,
                timeout_duration
            ).until_not(
                EC.presence_of_element_located((by, query))
            )
            logging.info(f'Element {query} disappeared.')
        except Exceptions.TimeoutException:
            logging.info(f'Element {query} still here, something is wrong.')
        return

    def interact(self, question: str):
        '''
        Sends a question and retrieves the answer from the ChatGPT system.

        This function interacts with the ChatGPT.
        It takes the question as input and sends it to the system.
        The question may contain multiple lines separated by '\n'. 
        In this case, the function simulates pressing SHIFT+ENTER for each line.

        After sending the question, the function waits for the answer.
        Once the response is ready, the response is returned.

        Args:
            question (str): The interaction text.

        Returns:
            str: The generated answer.
        '''

        text_area = self.browser.find_elements(By.TAG_NAME, self.textarea_tq)
        if not text_area:
            print('Unable to locate text area tag. Switching to ID search')
            text_area = self.browser.find_elements(By.ID, self.textarea_iq)
        if not text_area:
            raise RuntimeError('Unable to find the text prompt area. Please raise an issue with verbose=True')

        text_area = text_area[0]

        text_to_insert = question.replace('"', '\\"').replace("'", "\\'").replace("\n", "\\n")


        # Send prompt by javascript
        js_script = f"""var textarea = document.querySelector('#prompt-textarea');
        textarea.value = '{text_to_insert}';
        """
        text_area.send_keys(Keys.SHIFT + Keys.ENTER)  # Enter in the textarea to allow the submit button to be clickable
        self.browser.execute_script(js_script)
        time.sleep(1.5)  # Waiting for the text to be inserted (to be sure)
        self.browser.find_elements(By.XPATH, "//form//button[contains(@class, 'p-1')]")[0].click()

        logging.info('-- Message sent, waiting for response --')
        time.sleep(1.5) # Waiting to be sure, that the "Stop generating" button appears
        # Lunch prompt
        self.wait_until_disappear(By.XPATH, '//button[//div[text()="Stop generating"]]', timeout_duration=300)

        answ = ""
        try:
            answer = self.browser.find_elements(By.CLASS_NAME, self.chatbox_cq)[-1]

            target_div = False
            if self.extract_code == True:
                html_content = answer.get_attribute('outerHTML')
                soup = BeautifulSoup(html_content, 'html.parser')
                target_div = soup.select_one('pre .overflow-y-auto')

            if target_div:  # Check if a code block exist
                answ = target_div.get_text()  # Get brut content and save \n
            else:
                answ = answer.text

        except Exception as e:
            print(f'No answer found : {e}')

        return answ

    def reset_thread(self):
        '''Function to close the current thread and start new one'''
        self.browser.find_element(By.XPATH, self.reset_xq).click()
        logging.info('New thread is ready')

    def regenerate_response(self):
        '''
        Closes the current thread and starts a new one.

        Args:
            None

        Returns:
            None
        '''
        try:
            regen_button = self.browser.find_element(By.XPATH, self.regen_xq)
            regen_button.click()
            logging.info('Clicked regenerate button')
            self.wait_until_disappear(By.CLASS_NAME, self.wait_cq)
            answer = self.browser.find_elements(By.CLASS_NAME, self.chatbox_cq)[-1]
            logging.info('New answer is ready')
        except Exceptions.NoSuchElementException:
            logging.error('Regenerate button is not present')
        return answer

    def switch_model(self, model_name : str):
        '''
        Switch the model for ChatGPT+ users.

        Args:
            model_name: str = The name of the model, either GPT-3.5 or GPT-4

        Returns:
            bool: True on success, False on fail
        '''
        if model_name in ['GPT-3.5', 'GPT-4']:
            logging.info(f'Switching model to {model_name}')
            try:
                self.browser.find_element(By.XPATH, self.gpt_xq.format(model_name)).click()
                return True
            except Exceptions.NoSuchElementException:
                logging.error('Button is not present')
        return False

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')
    args = parser.parse_args()

    chatgpt = ChatGPT_Client(args.username, args.password)
    result = chatgpt.interact('Hello, how are you today')
    print(result)

import os, sys
import utils

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(FILE_DIR)
sys.path.append(REPO_DIR)
import threading
from functools import partial
import time

def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")

running_apis = []

class AutoAPI:
    def __init__(self, openai_key, ai_name, ai_role, top_5_goals):
        print(openai_key)
        self.openai_key = openai_key
        newline = "\n"
        with open(os.path.join(REPO_DIR, "ai_settings.yaml"), "w") as f:
            f.write(
                f"""ai_goals:
{newline.join([f'- {goal[0]}' for goal in top_5_goals if goal[0]])}
ai_name: {ai_name}
ai_role: {ai_role}
"""
            )


        thread = threading.Thread(target=self.client_thread)
        thread.start()
        self.thread = thread
        self.pending_input = None
        self.awaiting_input = False
        self.messages = []
        self.last_message_read_index = -1

    def add_message(self, title, content):
        # print(f"{title}: {content}")
        self.messages.append((title, content))

    def client_thread(self):
        os.environ["OPENAI_API_KEY"] = self.openai_key
        import autogpt.config.config
        from autogpt.logs import logger
        from autogpt.cli import main
        import autogpt.utils
        from autogpt.spinner import Spinner


        def typewriter_log(self, title="", title_color="", content="", *args, **kwargs):
            self.add_message(title, content)

        def warn(self, message, title="", *args, **kwargs):
            self.add_message(title, message)
    
        def error(self, title, message="", *args, **kwargs):
            self.add_message(title, message)

        def clean_input(self, prompt=""):
            self.add_message(None, prompt)
            self.awaiting_input = True
            while self.pending_input is None:
                time.sleep(1)
            pending_input = self.pending_input
            self.pending_input = None
            print("Sending message:", pending_input)
            return pending_input
        
        def spinner_start(self):
            self.add_message(None, "Thinking...")
        
        logger.typewriter_log = partial(typewriter_log, self)
        logger.warn = partial(warn, self)
        logger.error = partial(error, self)
        autogpt.utils.clean_input = partial(clean_input, self)
        Spinner.spin = partial(spinner_start, self)

        main()

    def send_message(self, message="Y"):
        self.pending_input = message
        self.awaiting_input = False

    def get_chatbot_response(self):
        while (not self.awaiting_input) or self.last_message_read_index < len(self.messages) - 1:
            if self.last_message_read_index >= len(self.messages) - 1:
                time.sleep(1)
            else:
                self.last_message_read_index += 1
                title, content = self.messages[self.last_message_read_index]
                yield (f"**{title.strip()}** " if title else "") + utils.remove_color(content).replace("\n", "<br />")

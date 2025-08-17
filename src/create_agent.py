import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log/finance_chatbot.log', mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, client, system):
        self.client = client
        self.system = system
        self.messages = []

        if self.system is not None:
            self.messages.append({"role": "system", "content": self.system})

    def __call__(self, message=""):
        """
        Execute agent interaction.

        Args:
            message (str, optional): User message. Defaults to "".

        Returns:
            str: Agent's response
        """
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        return result

    def execute(self):
        """
        Execute Groq API call to generate agent response.

        Returns:
            str: Generated response from the language model
        """
        try:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                model="llama3-70b-8192",
            )
            result = completion.choices[0].message.content
            self.messages.append({"role": "assistant", "content": result})
            return result
        except Exception as e:
            logger.error(f"Error during Groq API call: {e}")
            return "Error: Unable to process your agent execute request at this time"
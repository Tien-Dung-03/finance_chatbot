import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
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
        
        if self.system:
            self.messages.append({"role": "system", "content": self.system})
            
    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        return result
    
    def execute(self):
        try:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                model="llama3-70b-8192",
            )
            result = completion.choices[0].message.content
            self.messages.append({"role": "assistant", "content": result})
            logger.debug(f"Groq API response: {result}")
            return result
        except Exception as e:
            logger.error(f"Error during Groq API call: {e}")
            return f"Error: Unable to process your request - {str(e)}"
        
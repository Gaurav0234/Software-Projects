from ..utils.messageUtil import MessageUtil
from .llmService import LLMService

class messageService:
    def __init__(self):
        self.messageUtil = MessageUtil();
        self.llmService = LLMService()

    def processMessage(self, message):
        if self.messageUtil.isBankSms(message):
            return self.llmService.runLLM(message)
        else:
            return None
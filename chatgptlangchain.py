# MIT License
#
# Copyright (c) 2023 PeriniDev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


#code for testing and learning LangChain Agents and Tools
#GPT And LangChain Agents 

import os
from dotenv import load_dotenv
load_dotenv()

from langchain.chains.conversation.memory import ConversationBufferMemory
from langchain import PromptTemplate, OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
import langchain 
from langchain import LLMChain, SQLDatabase
from langchain.cache import SQLiteCache
from langchain.agents import initialize_agent, AgentType, load_tools
from langchain.utilities.zapier import ZapierNLAWrapper
from langchain.tools import  Tool
from langchain_experimental.sql import SQLDatabaseChain
from pathlib import Path

from langchain.tools.file_management import (
    ReadFileTool,
    CopyFileTool,
    DeleteFileTool,
    MoveFileTool,
    WriteFileTool,
    ListDirectoryTool,
)
from langchain.agents.agent_toolkits import ZapierToolkit


#path this file and others
thispath = os.getcwd()

#llm
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1, max_tokens=500, cache=True, streaming=False )

#cache to agent chain - repeat the question, repeat the answer cached
cachedbpath = os.path.join(os.getcwd(), "cachedatabase.db")
cache = SQLiteCache(database_path=cachedbpath)
langchain.llm_cache = cache

#memory works only with CHAT AgentsType
memory = ConversationBufferMemory(memory_key="chat_history",return_messages=True)

#database (test with chinook itunes database)
DB_PATH = (Path(__file__).parent / "chinook.db").absolute()
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
db_chain = SQLDatabaseChain.from_llm(llm, db)

# begin define tools ------------------------------------------------------------------
searchtools = load_tools(
   ["ddg-search"]
   )

#works with agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION
read_file_tool = ReadFileTool() 
list_directory_tool = ListDirectoryTool()
delete_file_tool = DeleteFileTool()
#works only with agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
write_file_tool = WriteFileTool() 
copy_file_tool = CopyFileTool()
move_file_tool = MoveFileTool()

#load zapier tools from: https://nla.zapier.com/dev/actions/
#zapier a choose gmail, outlook tools,google drive, microsoft excel, google sheets all works with ZERO-SHOT agent
zapier = ZapierNLAWrapper()
zapier_toolkit = ZapierToolkit.from_zapier_nla_wrapper(zapier)

#database search tools
DBtool = [Tool(
    name="music-store-db-search",
    func=db_chain.run,
    description="useful when you need to answer questions about the music store database. Input should be in forme of a question containing "
    
     
    )]

#tools = toolkit.get_tools()+ [write_file_tool,list_directory_tool,delete_file_tool,move_file_tool,copy_file_tool,read_file_tool] +searchtools + DBtool
tools = zapier_toolkit.get_tools()+ [list_directory_tool,delete_file_tool,read_file_tool] +searchtools + DBtool  #Use it for ZERO-SHOT Agent

# end define tools ------------------------------------------------------------------

#use it to handle errors or use handle_parsing_errors=True
def _handle_error(error) -> str:
    return str(error)[:100]

#-----AgentType Selection - Choose the AgentType you want to use, CHAT_CONVERSATIONAL DO WORK WELL WITH TOOLS , ZERO_SHOT_REACT_DESCRIPTION WORK WELL WITH BUT THERE IS NO CHAT OR MEMORY

# Agent Options
opcoes = [
    "zero-shot-react-description",
    "conversational-react-description",
    "chat-zero-shot-react-description",
    "chat-conversational-react-description",
    "structured-chat-zero-shot-react-description"
]
# Options
print("Choose the AgentType you want to use:")
for i, opcao in enumerate(opcoes, 1):
    print(f"{i}. {opcao}")

while True:
    # user select
    try:
        escolha = int(input("Type the number of the option: "))
        if 1 <= escolha <= len(opcoes):
            Agent_type = opcoes[escolha - 1]
            print(f"You chose: {Agent_type}")
            break
        else:
            print("option not valid.")
    except ValueError:
        print("Option not valid please select a valid number.")


#selection of the agent to load. use case
agent = initialize_agent(
    tools,
    llm=llm,
    agent=Agent_type,
    verbose=True,
    memory=memory,
    max_iterations = 5, #durting the tests limit by 5 instead of 15
    early_stopping_method='generate',
    handle_parsing_errors=_handle_error 
)

#-------requests-----------
while True:
    with get_openai_callback() as cb:
        prompt=input('Digite human: ')
        result = agent.run(prompt)
    print("AI Result: ",result) # print final result
    print(str(cb)) #print openai costs and tokens used
        

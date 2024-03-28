from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import OpenAI
import pandas as pd

from src.utils.files import find


MEMORY = {
    "chat_history": [],
}

def csvQuery(path: str, query: str):
    print(f"\ndebug -- called csvQuery\n\n")
    print(f"\ndebug --MEMORY: {MEMORY}\n\n")
    print(f"\ndebug --query: {query}\n\n")
    print(f"\ndebug --path: {path}\n\n")

    df = pd.read_csv(find(path))
    print(f"debug --df: {df.head()}")
    llm = OpenAI(model="gpt-4-turbo")

    agent = create_pandas_dataframe_agent(llm, df, agent_type="openai-tools", verbose=True)
    result = agent.invoke(
        {
            "input": query,
            "chat_history": MEMORY["chat_history"],
        }
    )

    MEMORY["chat_history"].extend([
        HumanMessage(content=query),
        AIMessage(content=result["output"]),
    ])

    print(f"\ndebug --result: {result['output']}\n\n")

    return result["output"]
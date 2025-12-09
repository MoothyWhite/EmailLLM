import sys
import os

# 添加项目根目录到 Python 路径，确保能正确导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config
from agents import Agent, Runner, set_tracing_disabled

# 导入配置

set_tracing_disabled(True)
print(config.LLM_PROMPT)

if os.environ.get("DEEPSEEK_API_KEY"):
    model = "litellm/deepseek/deepseek-chat"

agent = Agent(name="Assistant", model=model, instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "你好")
print(result.final_output)

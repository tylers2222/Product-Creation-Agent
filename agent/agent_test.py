import os
import sys
import json

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agent.agent import invoke_agent
from pathlib import Path

res = invoke_agent("Can you make a product for Optimum Nutrition Gold Standard 100% Whey 5lb in Chocolate, the SKU is 523525 and barcode is 321542352, Price $59.95")
if not res:
    print("No Result Found By The Invoke")
    sys.exit()

try:
    file_path = Path("Product generating agent/agent/agent_test.json")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(res.model_dump_json(indent=3))
except Exception as e:
    print(res.model_dump_json(), indent=3)
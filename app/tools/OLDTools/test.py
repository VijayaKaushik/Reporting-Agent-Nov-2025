import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))


from app.tools.fetch_template import search_templates_tool
print(search_templates_tool.run("participant demographic")[:200])
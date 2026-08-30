"""
Clarea Model Context Protocol (MCP) Server for Claude Desktop and Claude Code.
Enables Claude to natively read social media metrics and produce structured business decisions.
"""

import json
import sys
from typing import Dict, Any, List
from clarea.core.parser import MetricParser
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.report import ReportGenerator

def handle_analyze_metrics(arguments: Dict[str, Any]) -> Dict[str, Any]:
    json_data = arguments.get("metrics_data")
    if isinstance(json_data, str):
        json_data = json.loads(json_data)
    
    summary = MetricParser.from_dict(json_data)
    analyzer = MetricAnalyzer(summary)
    insight = DiagnosisEngine.generate_local_insight(summary)
    markdown_report = ReportGenerator.to_markdown(summary, insight)

    return {
        "brand_name": summary.brand_name,
        "total_reach": summary.total_reach,
        "total_messages": summary.total_messages,
        "engagement_rate": analyzer.calculate_engagement_rate(),
        "conversion_rate": analyzer.calculate_message_conversion_rate(),
        "vanity_ratio": analyzer.calculate_vanity_vs_business_ratio(),
        "executive_summary": insight.executive_summary,
        "markdown_report": markdown_report
    }

def handle_generate_hooks(arguments: Dict[str, Any]) -> Dict[str, Any]:
    from clarea.generators.hooks import HookGenerator
    topic = arguments.get("topic", "General")
    brand = arguments.get("brand_name", "Brand")
    return {
        "topic": topic,
        "hooks": HookGenerator.generate_hooks(topic, brand),
        "ctas": HookGenerator.generate_ctas(topic)
    }

TOOLS_MANIFEST = [
    {
        "name": "clarea_analyze_metrics",
        "description": "Analyzes social media and marketing performance metrics, generating a business-level diagnosis and conversion optimization plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "metrics_data": {
                    "type": "object",
                    "description": "The JSON payload containing PeriodSummary and PostMetrics"
                }
            },
            "required": ["metrics_data"]
        }
    },
    {
        "name": "clarea_generate_hooks_and_ctas",
        "description": "Generates high-converting marketing hooks and direct-response CTAs tailored to a specific topic and brand.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The specific content category or product topic"},
                "brand_name": {"type": "string", "description": "The name of the company or brand"}
            },
            "required": ["topic", "brand_name"]
        }
    }
]

def run_stdio_server():
    """Runs a standard JSON-RPC Stdio MCP Server compatible with Claude Desktop and Claude Code."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")

            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"tools": TOOLS_MANIFEST}
                }
            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "clarea_analyze_metrics":
                    res = handle_analyze_metrics(args)
                elif name == "clarea_generate_hooks_and_ctas":
                    res = handle_generate_hooks(args)
                else:
                    res = {"error": f"Tool '{name}' not found"}

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, indent=2)}]}
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    run_stdio_server()

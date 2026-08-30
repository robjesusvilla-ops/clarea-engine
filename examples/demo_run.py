import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clarea.core.parser import MetricParser
from clarea.core.analyzer import MetricAnalyzer
from clarea.generators.diagnosis import DiagnosisEngine
from clarea.generators.report import ReportGenerator

def run_demo():
    sample_file = Path(__file__).parent / "sample_facebook_metrics.json"
    print(f"Loading sample data from {sample_file.name}...")
    
    summary = MetricParser.from_json_file(sample_file)
    analyzer = MetricAnalyzer(summary)
    
    print("\n--- STATISTICAL OVERVIEW ---")
    print(f"Brand: {summary.brand_name}")
    print(f"Platform: {summary.platform}")
    print(f"Total Reach: {summary.total_reach:,} ({summary.reach_growth_pct:+.1f}%)")
    print(f"Total Interactions: {summary.total_interactions:,} ({summary.interactions_growth_pct:+.1f}%)")
    print(f"Direct Inquiries (Messages): {summary.total_messages:,} ({summary.messages_growth_pct:+.1f}%)")
    print(f"Engagement Rate: {analyzer.calculate_engagement_rate()}%")
    print(f"Message Conversion Rate: {analyzer.calculate_message_conversion_rate()}%")
    print(f"Vanity vs Business Ratio: {analyzer.calculate_vanity_vs_business_ratio()}")

    print("\n--- CONTENT TOPIC RANKING (BY BUSINESS INTENT) ---")
    for rank, item in enumerate(analyzer.rank_topics_by_intent(), 1):
        print(f"#{rank} {item['topic']}: {item['total_messages']} inquiries | {item['posts']} posts | {item['conversion_rate']}% conv rate")

    print("\n--- GENERATING CLAREA STRATEGIC DIAGNOSIS ---")
    insight = DiagnosisEngine.generate_local_insight(summary)
    print("\n[EXECUTIVE SUMMARY]")
    print(insight.executive_summary)

    print("\n[RECOMMENDED ACTIONS]")
    for i, act in enumerate(insight.recommended_actions, 1):
        print(f"{i}. {act}")

    output_report = Path(__file__).parent / "generated_executive_report.md"
    report_md = ReportGenerator.to_markdown(summary, insight)
    with open(output_report, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n[OK] Generated full executive Markdown report: {output_report.name}")

if __name__ == "__main__":
    run_demo()

"""
SHAP-inspired explainability for SAR generation
Shows which features contributed most to flagging
"""

import json
from typing import Dict, List

class SARExplainer:
    def __init__(self):
        # Weight for each risk indicator type
        self.feature_weights = {
            'volume_ratio': 0.25,
            'transaction_count': 0.20,
            'time_pattern': 0.15,
            'cross_border': 0.15,
            'profile_mismatch': 0.15,
            'rapid_movement': 0.10
        }
    
    def calculate_feature_importance(self, alert_data: Dict) -> Dict:
        """Calculate SHAP-like feature importance scores"""
        
        importance_scores = {}
        explanations = {}
        
        # Analyze transaction volume
        txn_summary = alert_data.get('transaction_summary', {})
        profile = alert_data.get('customer_profile', {})
        
        # Volume ratio (amount vs income)
        total_amount = txn_summary.get('total_amount_received',
                                       txn_summary.get('total_amount', 0))
        annual_income = profile.get('declared_annual_income', 1)
        volume_ratio = total_amount / annual_income if annual_income > 0 else 0
        
        if volume_ratio > 5:
            importance_scores['Volume Inconsistency'] = min(100, volume_ratio * 10)
            explanations['Volume Inconsistency'] = f"Transaction volume {volume_ratio:.1f}x annual income (₹{annual_income:,})"
        
        # Transaction count
        sender_count = txn_summary.get('number_of_senders',
                                       txn_summary.get('number_of_deposits', 0))
        if sender_count > 10:
            importance_scores['Multiple Senders'] = min(100, sender_count * 2)
            explanations['Multiple Senders'] = f"{sender_count} discrete senders/deposits (structuring indicator)"
        
        # Time pattern
        timeframe = txn_summary.get('timeframe_days', 30)
        if timeframe < 14:
            importance_scores['Rapid Timeframe'] = min(100, (14 - timeframe) * 7)
            explanations['Rapid Timeframe'] = f"Activity compressed in {timeframe} days"
        
        # Cross-border
        if txn_summary.get('immediate_outbound_transfer') or 'foreign' in str(txn_summary).lower():
            importance_scores['Cross-Border Risk'] = 80
            explanations['Cross-Border Risk'] = "Immediate international transfer or foreign jurisdiction involvement"
        
        # Profile mismatch
        occupation = profile.get('occupation', '').lower()
        if 'unemployed' in occupation or 'homemaker' in occupation:
            if total_amount > 100000:
                importance_scores['Profile Mismatch'] = 90
                explanations['Profile Mismatch'] = f"{occupation.title()} with ₹{total_amount:,} transaction"
        
        # Rapid movement
        if txn_summary.get('immediate_withdrawal') or txn_summary.get('immediate_outbound_transfer'):
            importance_scores['Rapid Movement'] = 85
            explanations['Rapid Movement'] = "Funds moved out immediately after receipt (layering indicator)"
        
        # Normalize scores to 0-100
        if importance_scores:
            max_score = max(importance_scores.values())
            importance_scores = {k: (v/max_score)*100 for k, v in importance_scores.items()}
        
        return {
            'feature_importance': importance_scores,
            'explanations': explanations,
            'overall_risk_score': sum(importance_scores.values()) / len(importance_scores) if importance_scores else 0
        }
    
    def generate_shap_style_report(self, alert_data: Dict) -> str:
        """Generate SHAP-style explanation report"""
        
        analysis = self.calculate_feature_importance(alert_data)
        
        report = "="*80 + "\n"
        report += "EXPLAINABILITY REPORT (SHAP-Style Feature Importance)\n"
        report += "="*80 + "\n\n"
        
        report += f"Alert ID: {alert_data.get('alert_id', 'Unknown')}\n"
        report += f"Customer: {alert_data.get('customer_name', 'Unknown')}\n"
        report += f"Overall Risk Score: {analysis['overall_risk_score']:.1f}/100\n\n"
        
        report += "FEATURE IMPORTANCE (Why This Transaction is Suspicious):\n"
        report += "-"*80 + "\n\n"
        
        # Sort by importance
        sorted_features = sorted(
            analysis['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for feature, score in sorted_features:
            bar_length = int(score / 2)  # Scale to 50 chars max
            bar = "█" * bar_length
            
            report += f"{feature:.<30} {score:5.1f} {bar}\n"
            report += f"  └─ {analysis['explanations'].get(feature, 'N/A')}\n\n"
        
        report += "\n" + "="*80 + "\n"
        report += "NOTE: Scores show relative contribution to suspicion classification.\n"
        report += "Higher score = stronger indicator of suspicious activity.\n"
        report += "="*80 + "\n"
        
        return report


# Test
if __name__ == "__main__":
    # Load sample alert
    with open('data/sample_alerts.json', 'r') as f:
        alerts = json.load(f)
    
    explainer = SARExplainer()
    
    # Generate SHAP report for first alert
    report = explainer.generate_shap_style_report(alerts[0])
    print(report)
    
    # Get feature importance
    analysis = explainer.calculate_feature_importance(alerts[0])
    print("\nFeature Importance Scores:")
    for feature, score in analysis['feature_importance'].items():
        print(f"  {feature}: {score:.1f}")
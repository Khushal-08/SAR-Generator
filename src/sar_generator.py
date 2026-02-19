"""
SAR Narrative Generator - Core LLM Integration
Generates professional Suspicious Activity Reports using local LLMs
"""

import json
from src.rag_knowledge_base import RAGKnowledgeBase
from datetime import datetime
from typing import Dict, List, Tuple
import os

try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
except ImportError:
    print("ERROR: LangChain not installed. Run: pip install langchain langchain-community")
    exit(1)


class SARGenerator:
    """Main class for SAR narrative generation"""
    
    def __init__(self, model_name="llama3.2", use_rag=True):
        """
        Initialize SAR Generator with local LLM
        
        Args:
            model_name: Ollama model name (llama3.2 or mistral)
        """
        print(f"🔄 Initializing SAR Generator with model: {model_name}")

        # Existing LLM init
        self.llm = Ollama(
            model=model_name,
            temperature=0.3,
            num_ctx=4096
        )

        # NEW: Initialize RAG
        self.use_rag = use_rag
        if use_rag:
            self.rag_kb = RAGKnowledgeBase()
            print("✓ RAG Knowledge Base initialized")

        # Load templates (existing code)
        self._load_resources()
        
    def _load_resources(self):
        """Load SAR template and knowledge base files"""
        try:
            template_path = 'data/sar_templates/base_template.txt'
            if os.path.exists(template_path):
                with open(template_path, 'r' ,encoding='utf-8') as f:
                    self.base_template = f.read()
                print(f"✓ Loaded template: {template_path}")
            else:
                print(f"⚠ Template not found: {template_path}")
                self.base_template = self._get_default_template()
            
            typologies_path = 'data/knowledge_base/money_laundering_typologies.txt'
            if os.path.exists(typologies_path):
                with open(typologies_path, 'r', encoding='utf-8') as f:
                    self.typologies = f.read()
                print(f"✓ Loaded typologies: {typologies_path}")
            else:
                print(f"⚠ Typologies not found: {typologies_path}")
                self.typologies = "Standard money laundering patterns"
            
            regulations_path = 'data/knowledge_base/pmla_guidelines.txt'
            if os.path.exists(regulations_path):
                with open(regulations_path, 'r', encoding='utf-8') as f:
                    self.regulations = f.read()
                print(f"✓ Loaded regulations: {regulations_path}")
            else:
                print(f"⚠ Regulations not found: {regulations_path}")
                self.regulations = "PMLA Section 12, FATF Recommendations"
                
        except Exception as e:
            print(f"⚠ Error loading resources: {e}")
            self.base_template = self._get_default_template()
            self.typologies = "Money laundering typologies"
            self.regulations = "Regulatory guidelines"
    
    def _get_default_template(self):
        """Fallback template if file not found"""
        return """SUSPICIOUS ACTIVITY REPORT
        
Customer: [CUSTOMER_NAME]
Account: [ACCOUNT_NUMBER]

NARRATIVE:
[AI_GENERATED_NARRATIVE]

INDICATORS:
[AI_GENERATED_INDICATORS]

TYPOLOGY:
[TYPOLOGY_ANALYSIS]

REGULATIONS:
[REGULATORY_CITATIONS]
"""
    
    def generate_narrative(self, alert_data: Dict) -> Dict:
        """Generate SAR with RAG support"""
        
        print(f"\n🔄 Generating SAR for Alert: {alert_data.get('alert_id')}")
        
        # Extract key info
        typology = alert_data.get('typology_match', 'Unknown')
        alert_type = alert_data.get('alert_type', 'Unknown')
        
        # NEW: RETRIEVE relevant documents using RAG
        retrieved_docs = []
        retrieved_sources = []
        
        if self.use_rag:
            print("  📚 Retrieving relevant regulations...")
            
            retrieval_query = f"""
            {typology}
            {alert_type}
            PMLA Section 12
            SAR writing requirements
            suspicious transaction indicators
            """
            
            rag_results = self.rag_kb.retrieve(retrieval_query, n_results=5)
            retrieved_docs = rag_results['documents']
            retrieved_sources = rag_results['metadatas']
            
            print(f"  ✓ Retrieved {len(retrieved_docs)} relevant documents")
        
        # Build enhanced prompt with RAG context
        if retrieved_docs:
            rag_context = "\n\n".join([
                f"SOURCE {i+1} ({meta['source']}):\n{doc}"
                for i, (doc, meta) in enumerate(zip(retrieved_docs, retrieved_sources))
            ])
            
            prompt_template = f"""You are an expert compliance analyst writing a Suspicious Activity Report.

=== REGULATORY CONTEXT (Use ONLY this information) ===
{rag_context}
=== END CONTEXT ===

Now write a SAR for this transaction using ONLY the regulations provided above:

Customer: {{customer_name}}
Alert Type: {{alert_type}}
Transaction Summary: {{transaction_summary}}
Customer Profile: {{customer_profile}}
Risk Indicators: {{risk_indicators}}
Suspected Typology: {{typology}}

REQUIREMENTS:
- Write 3 paragraphs (What happened, Why suspicious, Regulatory classification)
- Cite ONLY regulations from the context above
- Use specific amounts and dates
- If information is missing, state "DATA GAP: [missing info]"
- Be factual, no speculation

SAR NARRATIVE:
"""
        else:
            prompt_template = """You are a compliance analyst writing a SAR...
            [your existing prompt]
            """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=[
                "customer_name", "alert_type", "transaction_summary",
                "customer_profile", "risk_indicators", "typology"
            ]
        )
        
        formatted_prompt = prompt.format(
            customer_name=alert_data.get('customer_name'),
            alert_type=alert_type,
            transaction_summary=json.dumps(alert_data.get('transaction_summary', {})),
            customer_profile=json.dumps(alert_data.get('customer_profile', {})),
            risk_indicators=json.dumps(alert_data.get('risk_indicators', [])),
            typology=typology
        )
        
        print("  ⏳ Generating narrative with LLM...")
        narrative = self.llm.invoke(formatted_prompt)
        print("  ✓ Narrative generated")
        
        indicators_summary = self._generate_indicators_summary(
            alert_data.get('risk_indicators', [])
        )
        typology_analysis = self._generate_typology_analysis(
            typology, alert_data.get('transaction_summary', {})
        )
        regulatory_refs = self._extract_regulatory_references(
            alert_data.get('fatf_guideline_ref', 'FATF Recommendation 10')
        )
        
        # NEW: Enhanced audit trail with RAG sources
        audit_trail = self._create_audit_trail(
            alert_data, narrative, indicators_summary, typology_analysis,
            retrieved_sources=retrieved_sources
        )
        
        return {
            'narrative': narrative.strip(),
            'indicators': indicators_summary,
            'typology': typology_analysis,
            'regulatory_refs': regulatory_refs,
            'audit_trail': audit_trail,
            'rag_sources_used': retrieved_sources
        }
    
    def _generate_indicators_summary(self, risk_indicators: List[Dict]) -> List[str]:
        summary = []
        for indicator in risk_indicators:
            summary.append(
                f"☑ {indicator['indicator']} ({indicator['severity']} RISK): "
                f"{indicator['description']}"
            )
        return summary
    
    def _generate_typology_analysis(self, typology: str, transaction_data: Dict) -> str:
        analyses = {
            "Trade-Based Money Laundering": "The pattern is consistent with Trade-Based Money Laundering typology.",
            "Smurfing/Structuring to Avoid CTR": "Structured transactions appear designed to evade reporting thresholds.",
            "Round-Tripping": "Circular flow of funds suggests round-tripping behavior."
        }
        return analyses.get(typology, f"The transaction pattern matches the {typology} typology.")
    
    def _extract_regulatory_references(self, fatf_ref: str) -> List[str]:
        refs = []
        refs.append("PMLA Section 12 (Obligation to Report Suspicious Transactions)")
        refs.append(fatf_ref)
        refs.append("RBI Master Direction on KYC (Know Your Customer)")
        return refs
    
    def _create_audit_trail(self, alert_data, narrative, indicators, typology,
                           retrieved_sources=None):
        """Enhanced audit trail with RAG sources"""
        
        audit = {
            'timestamp': datetime.now().isoformat(),
            'alert_id': alert_data.get('alert_id'),
            'model_used': 'llama3.2',
            'rag_enabled': self.use_rag,
            'data_sources': {
                'primary_alert': alert_data.get('alert_id'),
                'customer_kyc': f"KYC updated: {alert_data.get('customer_profile', {}).get('kyc_last_updated', 'Unknown')}",
                'transaction_data': f"Date: {alert_data.get('alert_date', 'Unknown')}",
                'knowledge_base': ['pmla_guidelines.txt', 'typologies.txt']
            },
            'rag_sources_used': retrieved_sources or [],
            'decision_logic': []
        }
        
        for indicator_data in alert_data.get('risk_indicators', []):
            audit['decision_logic'].append({
                'element': indicator_data['indicator'],
                'data_source': 'transaction_summary',
                'rule_triggered': f"{indicator_data['severity']}_RISK_THRESHOLD",
                'evidence': indicator_data['description'],
                'confidence': 'HIGH' if indicator_data['severity'] == 'HIGH' else 'MEDIUM'
            })
        
        audit['decision_logic'].append({
            'element': 'Typology Classification',
            'data_source': 'RAG Knowledge Base' if self.use_rag else 'knowledge_base/typologies.txt',
            'rule_triggered': 'PATTERN_MATCHING_ALGORITHM',
            'evidence': f"Matched: {alert_data.get('typology_match', 'Unknown')}",
            'confidence': 'HIGH'
        })
        
        return audit

    def generate_full_sar(
        self, 
        alert_data: Dict, 
        analyst_name: str = "Pending Review"
    ) -> Tuple[str, Dict]:
        result = self.generate_narrative(alert_data)
        
        sar_report = self.base_template
        
        txn_summary = alert_data.get('transaction_summary', {})
        total_amount = txn_summary.get('total_amount_received',
                                       txn_summary.get('total_amount',
                                       txn_summary.get('total_transactions', 0)))
        
        replacements = {
            '[AI_GENERATED_NARRATIVE]': result['narrative'],
            '[AI_GENERATED_INDICATORS]': '\n'.join(result['indicators']),
            '[TYPOLOGY_ANALYSIS]': result['typology'],
            '[REGULATORY_CITATIONS]': '\n'.join(result['regulatory_refs'])
        }
        
        for placeholder, value in replacements.items():
            sar_report = sar_report.replace(placeholder, str(value))
        
        return sar_report, result['audit_trail']
	# ------------------ TEST RUN ------------------
if __name__ == "__main__":
    print("🚀 SAR Generator Test Starting...")

    sample_alert = {
        "alert_id": "ALERT-001",
        "customer_name": "Test Customer",
        "alert_type": "Large Cash Deposit",
        "transaction_summary": {
            "amount": 500000,
            "date": "2026-02-14"
        },
        "customer_profile": {
            "occupation": "Business",
            "kyc_last_updated": "2025-12-01"
        },
        "risk_indicators": [
            {
                "indicator": "Large cash deposit",
                "description": "Multiple deposits detected",
                "severity": "HIGH"
            }
        ],
        "typology_match": "Smurfing/Structuring to Avoid CTR"
    }

    generator = SARGenerator()
    result = generator.generate_narrative(sample_alert)

    print("\n✅ GENERATED NARRATIVE:\n")
    print(result["narrative"][:500])


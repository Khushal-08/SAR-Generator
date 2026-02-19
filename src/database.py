"""
PostgreSQL Database for SAR storage and audit logs
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# Table Models
class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    alert_id = Column(String(50), unique=True, nullable=False)
    customer_name = Column(String(200))
    account_number = Column(String(50))
    alert_type = Column(String(100))
    alert_date = Column(String(20))
    transaction_summary = Column(JSON)
    customer_profile = Column(JSON)
    risk_indicators = Column(JSON)
    typology_match = Column(String(200))
    status = Column(String(50), default='PENDING')
    created_at = Column(DateTime, default=datetime.now)

class SAR(Base):
    __tablename__ = 'sars'
    
    id = Column(Integer, primary_key=True)
    sar_id = Column(String(50), unique=True)
    alert_id = Column(String(50))
    narrative = Column(Text)
    quality_score = Column(Float)
    generation_time = Column(Float)
    model_used = Column(String(50))
    rag_enabled = Column(Boolean, default=True)
    generated_by = Column(String(100), default='AI')
    generated_at = Column(DateTime, default=datetime.now)
    status = Column(String(50), default='DRAFT')
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    filed_with_fiu = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    sar_id = Column(String(50))
    alert_id = Column(String(50))
    timestamp = Column(DateTime, default=datetime.now)
    decision_element = Column(String(200))
    data_source = Column(String(200))
    rule_triggered = Column(String(200))
    evidence = Column(Text)
    confidence = Column(String(20))
    rag_source = Column(String(200))

class SARHistory(Base):
    __tablename__ = 'sar_history'
    
    id = Column(Integer, primary_key=True)
    sar_id = Column(String(50))
    version_number = Column(Integer)
    narrative_snapshot = Column(Text)
    edited_by = Column(String(100))
    edit_reason = Column(Text)
    edited_at = Column(DateTime, default=datetime.now)


class Database:
    def __init__(self, connection_string="postgresql://postgres:123@localhost:5432/sar_db"):
        """Initialize database connection"""
        
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        print("✓ Database connected")
    
    def save_alert(self, alert_data):
        """Save transaction alert"""
        
        alert = Alert(
            alert_id=alert_data['alert_id'],
            customer_name=alert_data.get('customer_name'),
            account_number=alert_data.get('account_number'),
            alert_type=alert_data.get('alert_type'),
            alert_date=alert_data.get('alert_date'),
            transaction_summary=alert_data.get('transaction_summary'),
            customer_profile=alert_data.get('customer_profile'),
            risk_indicators=alert_data.get('risk_indicators'),
            typology_match=alert_data.get('typology_match')
        )
        
        self.session.add(alert)
        self.session.commit()
        
        print(f"✓ Alert saved: {alert_data['alert_id']}")
        return alert.id
    
    def save_sar(self, sar_data, alert_id):
        """Save generated SAR"""
        
        sar_id = f"SAR-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        sar = SAR(
            sar_id=sar_id,
            alert_id=alert_id,
            narrative=sar_data['narrative'],
            quality_score=sar_data.get('quality_score', 0),
            generation_time=sar_data.get('generation_time', 0),
            model_used=sar_data.get('model_used', 'llama3.2'),
            rag_enabled=sar_data.get('rag_enabled', True)
        )
        
        self.session.add(sar)
        self.session.commit()
        
        # Save audit trail
        if 'audit_trail' in sar_data:
            self._save_audit_trail(sar_id, alert_id, sar_data['audit_trail'])
        
        print(f"✓ SAR saved: {sar_id}")
        return sar_id
    
    def _save_audit_trail(self, sar_id, alert_id, audit_trail):
        """Save audit trail entries"""
        
        for decision in audit_trail.get('decision_logic', []):
            log = AuditLog(
                sar_id=sar_id,
                alert_id=alert_id,
                decision_element=decision.get('element'),
                data_source=decision.get('data_source'),
                rule_triggered=decision.get('rule_triggered'),
                evidence=decision.get('evidence'),
                confidence=decision.get('confidence')
            )
            self.session.add(log)
        
        self.session.commit()
        print(f"✓ Audit trail saved for {sar_id}")
    
    def get_pending_alerts(self, limit=10):
        """Get pending alerts"""
        
        alerts = self.session.query(Alert).filter(
            Alert.status == 'PENDING'
        ).limit(limit).all()
        
        return [self._alert_to_dict(a) for a in alerts]
    
    def _alert_to_dict(self, alert):
        """Convert Alert object to dictionary"""
        
        return {
            'alert_id': alert.alert_id,
            'customer_name': alert.customer_name,
            'account_number': alert.account_number,
            'alert_type': alert.alert_type,
            'alert_date': alert.alert_date,
            'transaction_summary': alert.transaction_summary,
            'customer_profile': alert.customer_profile,
            'risk_indicators': alert.risk_indicators,
            'typology_match': alert.typology_match,
            'status': alert.status
        }
    
    def get_sar_history(self, days=30):
        """Get SAR generation history"""
        
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        sars = self.session.query(SAR).filter(
            SAR.generated_at >= cutoff
        ).all()
        
        return [{
            'sar_id': s.sar_id,
            'alert_id': s.alert_id,
            'generated_at': s.generated_at.isoformat(),
            'generation_time': s.generation_time,
            'status': s.status
        } for s in sars]


# Initialize sample data
def initialize_database():
    """Load sample alerts into database"""
    
    db = Database()
    
    # Load sample alerts from JSON
    import json
    with open('data/sample_alerts.json', 'r') as f:
        alerts = json.load(f)
    
    for alert in alerts:
        try:
            db.save_alert(alert)
        except:
            pass  # Skip if already exists
    
    print(f"✓ Initialized database with {len(alerts)} alerts")


if __name__ == "__main__":
    # Create database and load sample data
    initialize_database()
    
    # Test retrieval
    db = Database()
    pending = db.get_pending_alerts()
    print(f"\n📊 Found {len(pending)} pending alerts")
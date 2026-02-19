import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os
import sys
from src.database import Database
from src.explainability import SARExplainer
import plotly.graph_objects as go
import plotly.express as px

try:
    from src.sar_generator import SARGenerator
    from src.audit_trail import AuditTrailManager
except ImportError:
    st.error("⚠️ Error: sar_generator.py and audit_trail.py must be in the same directory")
    st.stop()

# Page config
st.set_page_config(
    page_title="SAR Narrative Generator",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .alert-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .stTextArea textarea {
        font-family: monospace;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database and Explainer in session state
if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'explainer' not in st.session_state:
    st.session_state.explainer = SARExplainer()

# Initialize session state for generation
if 'generated_sar' not in st.session_state:
    st.session_state.generated_sar = None
if 'audit_trail' not in st.session_state:
    st.session_state.audit_trail = None
if 'alert_data' not in st.session_state:
    st.session_state.alert_data = None
if 'generation_time' not in st.session_state:
    st.session_state.generation_time = 0
if 'shap_analysis' not in st.session_state:
    st.session_state.shap_analysis = None

# Header
st.markdown('<h1 class="main-header">🔍 SAR Narrative Generator with Audit Trail</h1>', 
            unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    use_rag = st.checkbox("Enable RAG", value=True, 
                         help="Use Retrieval-Augmented Generation")
    
    model_choice = st.selectbox(
        "LLM Model",
        ["llama3.2", "mistral"],
        help="Select the local LLM model (llama3.2 recommended for speed)"
    )
    
    st.markdown("---")
    st.header("📊 System Status")
    
    try:
        pending_alerts = len(st.session_state.db.get_pending_alerts())
        st.metric("Pending Alerts", pending_alerts)
    except:
        st.error("Database not connected")

    if use_rag:
        st.success("✓ RAG Enabled")
    else:
        st.info("RAG Disabled")
    
    required_files = ['data/sample_alerts.json', 'data/sar_templates/base_template.txt']
    with st.expander("📁 Data Files Status"):
        for f_path in required_files:
            if os.path.exists(f_path):
                st.success(f"✓ {os.path.basename(f_path)}")
            else:
                st.error(f"✗ {os.path.basename(f_path)}")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 Generate SAR", "🔍 Audit Trail", "📚 Sample Alerts", "ℹ️ About"])

# TAB 1: Generate SAR
with tab1:
    st.header("Generate SAR from Transaction Alert")
    
    st.subheader("Input: Transaction Alert")
    
    data_source = st.radio(
        "Data Source",
        ["Database (PostgreSQL)", "Sample Files"],
        horizontal=True
    )
    
    alert_data = None
    
    if data_source == "Database (PostgreSQL)":
        try:
            db_alerts = st.session_state.db.get_pending_alerts(limit=20)
            if db_alerts:
                alert_options = [f"{a['alert_id']}: {a['alert_type']}" for a in db_alerts]
                selected_idx = st.selectbox("Choose Alert from Database", range(len(alert_options)), format_func=lambda x: alert_options[x])
                alert_data = db_alerts[selected_idx]
                st.info(f"**Alert:** {alert_data['alert_id']} | **Customer:** {alert_data['customer_name']}")
            else:
                st.warning("No pending alerts in database")
        except Exception as e:
            st.error(f"Database error: {e}")
    else:
        try:
            with open('data/sample_alerts.json', 'r') as f:
                sample_alerts = json.load(f)
            alert_options = [f"{a['alert_id']}: {a['alert_type']}" for a in sample_alerts]
            selected_idx = st.selectbox("Choose Alert", range(len(alert_options)), format_func=lambda x: alert_options[x])
            alert_data = sample_alerts[selected_idx]
        except:
            st.error("Sample alerts file not found")
    st.markdown("---")
    generate_button = st.button("🚀 Generate SAR", type="primary", disabled=not alert_data, use_container_width=True)
    
    if generate_button and alert_data:
        with st.spinner("🔄 Generating SAR with RAG..."):
            try:
                start_time = datetime.now()
                generator = SARGenerator(model_name=model_choice, use_rag=use_rag)
                sar_report, audit_trail = generator.generate_full_sar(alert_data)
                generation_time = (datetime.now() - start_time).total_seconds()
                shap_analysis = st.session_state.explainer.calculate_feature_importance(alert_data)
                try:
                    st.session_state.db.save_sar({
                        'narrative': sar_report,
                        'generation_time': generation_time,
                        'model_used': model_choice,
                        'rag_enabled': use_rag,
                        'quality_score': shap_analysis['overall_risk_score'],
                        'audit_trail': audit_trail
                    }, alert_data['alert_id'])
                    st.success("✅ SAR saved to database")
                except Exception as e:
                    st.warning(f"Generated but not saved: {e}")
                st.session_state.generated_sar = sar_report
                st.session_state.audit_trail = audit_trail
                st.session_state.alert_data = alert_data
                st.session_state.generation_time = generation_time
                st.session_state.shap_analysis = shap_analysis
                if 'just_generated' not in st.session_state:
                    st.session_state.just_generated = True
                    st.toast("✅ SAR Generated Successfully!", icon="✅")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


        st.subheader("Output: Generated SAR")
        
        if st.session_state.generated_sar:
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ SAR Generated Successfully</strong><br>
                Time: {st.session_state.generation_time:.2f}s | RAG: {'On' if use_rag else 'Off'}
            </div>
            """, unsafe_allow_html=True)

            # SHAP Dashboard
            if st.session_state.shap_analysis:
                st.markdown("### 📊 Risk Analysis Dashboard")
                
                shap = st.session_state.shap_analysis
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Risk Score Gauge
                col_spacer1, gauge_col, col_spacer2 = st.columns([0.5, 2, 0.5])
                
                with gauge_col:
                    risk_score = shap['overall_risk_score']
                    
                    if risk_score >= 70:
                        color = "#ef4444"
                        risk_level = "HIGH RISK"
                        risk_emoji = "🔴"
                    elif risk_score >= 40:
                        color = "#f59e0b"
                        risk_level = "MEDIUM RISK"
                        risk_emoji = "🟡"
                    else:
                        color = "#10b981"
                        risk_level = "LOW RISK"
                        risk_emoji = "🟢"
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = risk_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {
                            'text': f"<b>{risk_emoji} Overall Risk Score</b><br><span style='font-size:16px; color:{color}'>{risk_level}</span>",
                            'font': {'size': 20}
                        },
                        number = {
                            'font': {'size': 50, 'color': color},
                            'suffix': ""
                        },
                        delta = {'reference': 50, 'increasing': {'color': color}},
                        gauge = {
                            'axis': {
                                'range': [None, 100],
                                'tickwidth': 2,
                                'tickcolor': "#cbd5e1"
                            },
                            'bar': {'color': color, 'thickness': 0.8},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "#e2e8f0",
                            'steps': [
                                {'range': [0, 40], 'color': '#f0fdf4'},
                                {'range': [40, 70], 'color': '#fffbeb'},
                                {'range': [70, 100], 'color': '#fef2f2'}
                            ],
                            'threshold': {
                                'line': {'color': "#1e3a8a", 'width': 4},
                                'thickness': 0.75,
                                'value': 80
                            }
                        }
                    ))
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=40, r=40, t=80, b=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font={'family': 'Arial, sans-serif'}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Contributing Factors Bar Chart
                st.markdown("#### 📈 Contributing Risk Factors")
                
                sorted_features = sorted(
                    shap['feature_importance'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                if sorted_features:
                    features = [f[0] for f in sorted_features]
                    scores = [f[1] for f in sorted_features]
                    
                    colors_list = []
                    for score in scores:
                        if score >= 70:
                            colors_list.append('#ef4444')
                        elif score >= 40:
                            colors_list.append('#f59e0b')
                        else:
                            colors_list.append('#10b981')
                    
                    fig_bar = go.Figure()
                    
                    fig_bar.add_trace(go.Bar(
                        x=scores,
                        y=features,
                        orientation='h',
                        marker=dict(
                            color=colors_list,
                            line=dict(color='white', width=2)
                        ),
                        text=[f"<b>{s:.1f}</b>" for s in scores],
                        textposition='inside',
                        textfont=dict(size=14, color='white', family='Arial Black'),
                        hovertemplate='<b>%{y}</b><br>Risk Score: %{x:.1f}<extra></extra>'
                    ))
                    
                    fig_bar.update_layout(
                        height=max(250, len(features) * 50),
                        margin=dict(l=200, r=40, t=20, b=40),
                        xaxis=dict(
                            title=dict(
                                text="<b>Risk Contribution Score</b>",
                                font=dict(size=14)
                            ),
                            range=[0, 105],
                            showgrid=True,
                            gridcolor='#f1f5f9',
                            tickfont=dict(size=12)
                        ),
                        yaxis=dict(
                            title="",
                            tickfont=dict(size=13),
                            automargin=True
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        showlegend=False,
                        hovermode='closest'
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Detailed Explanations
                col_center1, col_expander, col_center2 = st.columns([1, 3, 1])
                
                with col_expander:
                    with st.expander("📝 **View Detailed Explanations**", expanded=False):
                        st.markdown("#### Why Each Factor is Flagged:")
                        
                        for idx, (feature, score) in enumerate(sorted_features, 1):
                            if score >= 70:
                                badge_color = "#fee2e2"
                                badge_text_color = "#991b1b"
                                severity = "HIGH"
                            elif score >= 40:
                                badge_color = "#fef3c7"
                                badge_text_color = "#92400e"
                                severity = "MEDIUM"
                            else:
                                badge_color = "#d1fae5"
                                badge_text_color = "#065f46"
                                severity = "LOW"
                            
                            st.markdown(f"""
                            <div style='background-color: {badge_color}; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid {badge_text_color};'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>
                                    <span style='font-weight: bold; font-size: 15px; color: {badge_text_color};'>
                                        {idx}. {feature}
                                    </span>
                                    <span style='background-color: {badge_text_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;'>
                                        {severity}: {score:.1f}
                                    </span>
                                </div>
                                <p style='margin: 0; color: #1e293b; font-size: 14px;'>
                                    {shap['explanations'].get(feature, 'No explanation available')}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.info(f"""
                        **Risk Assessment Summary:**
                        - Total Factors Analyzed: {len(sorted_features)}
                        - High Risk Indicators: {sum(1 for _, s in sorted_features if s >= 70)}
                        - Medium Risk Indicators: {sum(1 for _, s in sorted_features if 40 <= s < 70)}
                        - Overall Risk Score: {risk_score:.1f}/100
                        """)

            # Professional SAR Document Display
            st.markdown("---")

            action_col1, action_col2, action_col3, action_col4 = st.columns(4)

            with action_col1:
                if st.button("✅ Approve & File", use_container_width=True):
                    st.success("✓ SAR Approved")

            with action_col2:
                edit_mode = st.button("✏️ Edit Mode", use_container_width=True)

            with action_col3:
                st.download_button(
                    "📥 Download",
                    st.session_state.generated_sar,
                    file_name=f"SAR_{st.session_state.alert_data['alert_id']}.txt",
                    use_container_width=True
                )

            with action_col4:
                if st.button("🖨️ Print View", use_container_width=True):
                    st.info("Opening print preview...")

            st.markdown("---")

            if 'generated_sar' in st.session_state and st.session_state.generated_sar:
                sar_text = st.session_state.generated_sar
                
                if 'edit_mode' not in st.session_state:
                    st.session_state.edit_mode = False
                
                if edit_mode:
                    st.session_state.edit_mode = not st.session_state.edit_mode
                
                if st.session_state.edit_mode:
                    st.markdown("### ✏️ Edit Mode")
                    st.info("Make your changes below, then click 'Save Changes' to update.")
                    
                    edited_sar = st.text_area(
                        "Edit SAR Content",
                        value=sar_text,
                        height=600,
                        label_visibility="collapsed"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.button("💾 Save Changes", type="primary", use_container_width=True):
                            st.session_state.generated_sar = edited_sar
                            st.session_state.edit_mode = False
                            st.success("✓ Changes saved!")
                            st.rerun()
                    
                    with col_cancel:
                        if st.button("❌ Cancel", use_container_width=True):
                            st.session_state.edit_mode = False
                            st.rerun()
                
                else:
                    st.markdown("""
                    <style>
                        .sar-document {
                            background: white;
                            padding: 40px;
                            border-radius: 8px;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                            font-family: 'Georgia', serif;
                            line-height: 1.8;
                            color: #1e293b;
                        }
                        .sar-header {
                            text-align: center;
                            border-bottom: 3px double #1e3a8a;
                            padding-bottom: 20px;
                            margin-bottom: 30px;
                        }
                        .sar-title {
                            font-size: 24px;
                            font-weight: bold;
                            color: #1e3a8a;
                            margin-bottom: 10px;
                        }
                        .sar-subtitle {
                            font-size: 14px;
                            color: #64748b;
                        }
                        .sar-section-title {
                            font-size: 16px;
                            font-weight: bold;
                            color: #1e3a8a;
                            border-bottom: 1px solid #e2e8f0;
                            padding-bottom: 5px;
                            margin-bottom: 15px;
                            margin-top: 25px;
                        }
                        .sar-content {
                            text-align: justify;
                            font-size: 14px;
                            margin-bottom: 15px;
                        }
                        .sar-footer {
                            margin-top: 40px;
                            padding-top: 20px;
                            border-top: 1px solid #e2e8f0;
                            font-size: 12px;
                            color: #64748b;
                            text-align: center;
                        }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    lines = sar_text.split('\n')
                    formatted_html = '<div class="sar-document">'
                    
                    formatted_html += '''
                    <div class="sar-header">
                        <div class="sar-title">SUSPICIOUS ACTIVITY REPORT</div>
                        <div class="sar-subtitle">Generated by AI-Powered Compliance System</div>
                        <div class="sar-subtitle">Alert ID: {alert_id} | Date: {date}</div>
                    </div>
                    '''.format(
                        alert_id=st.session_state.alert_data['alert_id'],
                        date=datetime.now().strftime('%B %d, %Y')
                    )
                    
                    current_section = None
                    section_content = []
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        if (line.isupper() and len(line) > 10) or any(keyword in line for keyword in ['NARRATIVE', 'INDICATORS', 'TYPOLOGY', 'REGULATORY', 'CUSTOMER', 'TRANSACTION']):
                            if current_section and section_content:
                                formatted_html += f'<div class="sar-section-title">{current_section}</div>'
                                formatted_html += f'<div class="sar-content">{"<br>".join(section_content)}</div>'
                            
                            current_section = line
                            section_content = []
                        else:
                            section_content.append(line)
                    
                    if current_section and section_content:
                        formatted_html += f'<div class="sar-section-title">{current_section}</div>'
                        formatted_html += f'<div class="sar-content">{"<br>".join(section_content)}</div>'
                    
                    formatted_html += '''
                    <div class="sar-footer">
                        <strong>CONFIDENTIAL</strong> - For Internal Use Only<br>
                        This report is subject to PMLA Section 12 confidentiality requirements<br>
                        Generated: {timestamp}
                    </div>
                    '''.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    formatted_html += '</div>'
                    
                    st.markdown(formatted_html, unsafe_allow_html=True)
                    
                    with st.expander("📄 View Raw Text"):
                        st.code(sar_text, language=None)

        else:
            st.info("👈 Generate a SAR using the form on the left")
            st.markdown("""
            **How it works:**
            1. Select a sample alert or upload your own
            2. Click "Generate SAR"
            3. Review the AI-generated narrative
            4. Edit if needed
            5. Approve and file
            
            **Benefits:**
            - ⚡ 99% time reduction (5.5 hours → 8 seconds)
            - 🔍 Complete audit trail for transparency
            - ✅ Regulatory-compliant language
            - 👤 Human review before submission
            """)

# TAB 2: Audit Trail
with tab2:
    st.header("🔍 Audit Trail - Complete Transparency")
    
    if st.session_state.audit_trail:
        audit = st.session_state.audit_trail
        
        st.markdown("### 📊 Generation Summary")
        
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        
        with sum_col1:
            st.metric("Alert ID", audit.get('alert_id', 'Unknown'))
        
        with sum_col2:
            st.metric("Model Used", audit.get('model_used', 'Unknown'))
        
        with sum_col3:
            rag_enabled = audit.get('rag_enabled', False)
            st.metric("RAG Status", "Enabled ✓" if rag_enabled else "Disabled", delta="5 sources" if rag_enabled else None)
        
        with sum_col4:
            decision_count = len(audit.get('decision_logic', []))
            st.metric("Decisions Logged", decision_count)
        
        st.markdown("---")
        st.markdown("### 🔄 Decision Flow Visualization")

    if st.session_state.audit_trail:

        audit = st.session_state.audit_trail
        decisions = audit.get("decision_logic", [])


        if decisions:
            sources = []
            targets = []
            values = []
            labels = []
            colors = []

            confidence_colors = {
                'HIGH': '#ef4444' ,     #red
                'MEDIUM': '#f59e0b',   # Amber
                'LOW':   '#10b981'    # Green
            }

            label_to_idx = {}

            # --- 1️⃣ Add Data Source Nodes (Left - Blue)
            for dec in decisions:
                source = dec.get('data_source', 'Unknown')
                if source not in label_to_idx:
                    label_to_idx[source] = len(labels)
                    labels.append(source)
                    colors.append('#2563eb')  # Strong Blue

            # --- 2️⃣ Add Decision Nodes (Middle - Confidence Color)
            for dec in decisions:
                element = dec.get('element', 'Unknown')
                if element not in label_to_idx:
                    label_to_idx[element] = len(labels)
                    labels.append(element)
                    confidence = dec.get('confidence', 'MEDIUM')
                    colors.append(confidence_colors.get(confidence, '#64748b'))

            # --- 3️⃣ Add Final Output Node (Right - Purple)
            output_label = "SAR Generated"
            label_to_idx[output_label] = len(labels)
            labels.append(output_label)
            colors.append('#7c3aed')  # Purple

            # --- 4️⃣ Create Links
            for dec in decisions:
                source_label = dec.get('data_source', 'Unknown')
                element_label = dec.get('element', 'Unknown')

                # Source → Decision
                sources.append(label_to_idx[source_label])
                targets.append(label_to_idx[element_label])
                values.append(2)

                # Decision → Output
                sources.append(label_to_idx[element_label])
                targets.append(label_to_idx[output_label])
                values.append(2)

            # --- 5️⃣ Build Sankey Chart
            fig_sankey = go.Figure(go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=30,
                    thickness=28,
                    line=dict(color="white", width=1.5),
                    label=labels,
                    color=colors,
                    hovertemplate="%{label}<extra></extra>"
                ),
                link=dict(
                    source=sources,
                    target=targets,
                    value=values,
                    color="rgba(100, 116, 139, 0.25)",
                    hovertemplate="Flow Strength: %{value}<extra></extra>"
                )
            ))

            fig_sankey.update_layout(
                title={
                    "text": "Data Flow: Sources → Decisions → SAR Output",
                    "font": {"size": 20}
                },
                height=500,
                font=dict(size=14),
                margin=dict(l=20, r=20, t=60, b=20)
            )

            st.plotly_chart(fig_sankey, use_container_width=True)

        st.markdown("---")
        st.markdown("### 📊 Data Sources")
        
        sources_data = []
        for source_type, details in audit.get('data_sources', {}).items():
            sources_data.append({
                "Source Type": source_type,
                "Details": details,
                "Status": "✓ Accessed"
            })
        
        if sources_data:
            df_sources = pd.DataFrame(sources_data)
            st.dataframe(df_sources, use_container_width=True, hide_index=True)
        
        if 'rag_sources_used' in audit and audit['rag_sources_used']:
            st.markdown("### 📚 RAG Knowledge Sources")
            
            rag_data = []
            for idx, meta in enumerate(audit['rag_sources_used'], 1):
                rag_data.append({
                    "#": idx,
                    "Document": meta.get('source', 'Unknown'),
                    "Type": meta.get('type', 'Unknown'),
                    "Section": meta.get('section', 'N/A')
                })
            
            df_rag = pd.DataFrame(rag_data)
            st.dataframe(df_rag, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 🧠 Decision Logic Trail")
        
        confidence_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for dec in decisions:
            conf = dec.get('confidence', 'MEDIUM')
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        conf_col1, conf_col2 = st.columns([1, 2])
        
        with conf_col1:
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(confidence_counts.keys()),
                values=list(confidence_counts.values()),
                marker=dict(colors=['#ef4444', '#f59e0b', '#10b981']),
                hole=0.4
            )])
            
            fig_pie.update_layout(
                title="Confidence Distribution",
                height=250,
                showlegend=True
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with conf_col2:
            st.markdown("**Confidence Levels:**")
            st.markdown(f"🔴 **HIGH:** {confidence_counts['HIGH']} decisions - Strong evidence, multiple sources")
            st.markdown(f"🟡 **MEDIUM:** {confidence_counts['MEDIUM']} decisions - Good evidence, standard indicators")
            st.markdown(f" 🟢**LOW:** {confidence_counts['LOW']} decisions - Limited evidence, requires review")
        
        st.markdown("---")
        st.markdown("### 📋 Detailed Decision Breakdown")
        
        for idx, decision in enumerate(decisions, 1):
            confidence = decision.get('confidence', 'MEDIUM')
            
            if confidence == 'HIGH':
                emoji = "🔴"
            elif confidence == 'MEDIUM':
                emoji = "🟡"
            else:
                emoji = "🟢"
            
            with st.expander(f"{emoji} Decision {idx}: {decision.get('element', 'Unknown')} ({confidence} Confidence)", expanded=(idx <= 2)):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**📊 Data Source:**")
                    st.code(decision.get('data_source', 'N/A'), language=None)
                    st.markdown("**⚙️ Rule Triggered:**")
                    st.code(decision.get('rule_triggered', 'N/A'), language=None)
                
                with detail_col2:
                    st.markdown("**🔍 Evidence:**")
                    st.info(decision.get('evidence', 'No evidence provided'))
                    st.markdown("**📈 Confidence Level:**")
                    confidence_val = {'HIGH': 95, 'MEDIUM': 70, 'LOW': 40}.get(confidence, 50)
                    st.progress(confidence_val / 100)
                    st.caption(f"{confidence_val}% confidence based on evidence strength")
        
        st.markdown("---")
        st.markdown("### 📤 Export Audit Trail")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            audit_json = json.dumps(audit, indent=2)
            st.download_button(
                "📥 JSON Format",
                data=audit_json,
                file_name=f"audit_{audit['alert_id']}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with export_col2:
            audit_text = f"""AUDIT TRAIL REPORT
{'='*60}
Alert ID: {audit['alert_id']}
Generated: {audit.get('timestamp', 'Unknown')}
Model: {audit.get('model_used', 'Unknown')}
RAG: {'Enabled' if audit.get('rag_enabled') else 'Disabled'}

DECISIONS: {len(decisions)}
- HIGH Confidence: {confidence_counts['HIGH']}
- MEDIUM Confidence: {confidence_counts['MEDIUM']}
- LOW Confidence: {confidence_counts['LOW']}

{'='*60}
DETAILED DECISIONS:

"""
            for idx, dec in enumerate(decisions, 1):
                audit_text += f"\n{idx}. {dec.get('element', 'Unknown')}\n"
                audit_text += f"   Confidence: {dec.get('confidence', 'N/A')}\n"
                audit_text += f"   Evidence: {dec.get('evidence', 'N/A')}\n"
            
            st.download_button(
                "📥 Text Report",
                data=audit_text,
                file_name=f"audit_{audit['alert_id']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with export_col3:
            st.button(
                "📧 Email Report",
                use_container_width=True,
                help="Send audit trail to compliance team"
            )
    
    else:
        st.info("📝 Generate a SAR first to view its complete audit trail")
        
        st.markdown("### 🎯 What You'll See Here:")
        
        example_col1, example_col2, example_col3 = st.columns(3)
        
        with example_col1:
            st.markdown("""
            **📊 Data Flow**
            - Visual Sankey diagram
            - Shows data → decisions → output
            - Color-coded by confidence
            """)
        
        with example_col2:
            st.markdown("""
            **🧠 Decision Logic**
            - Each decision explained
            - Evidence shown
            - Confidence levels
            """)
        
        with example_col3:
            st.markdown("""
            **📈 Analytics**
            - Confidence distribution
            - Source breakdown
            - Export options
            """)
        
        st.markdown("---")
        st.markdown("""
        **Why This Matters:**
        
        Regulators require complete transparency in AI decision-making. Our audit trail provides:
        - ✅ Full data lineage (where each fact came from)
        - ✅ Decision explanations (why conclusions were reached)
        - ✅ Confidence metrics (how certain the system is)
        - ✅ Tamper-proof logging (hash verification)
        
        This level of transparency makes AI-generated SARs defensible in regulatory audits.
        """)

# TAB 3: Sample Alerts
with tab3:
    st.header("📚 Sample Transaction Alerts")
    
    st.markdown("""
    These are synthetic examples of suspicious transaction patterns that trigger SAR filing requirements.
    In production, these would come from your bank's transaction monitoring system.
    """)
    
    try:
        with open('data/sample_alerts.json', 'r') as f:
            samples = json.load(f)
        
        for sample in samples:
            with st.expander(f"🚨 {sample['alert_id']}: {sample['alert_type']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Customer:** {sample['customer_name']}")
                    st.markdown(f"**Account:** {sample['account_number']}")
                    st.markdown(f"**Date:** {sample['alert_date']}")
                    st.markdown(f"**Typology:** {sample['typology_match']}")
                    
                    st.markdown("**Risk Indicators:**")
                    for indicator in sample['risk_indicators']:
                        severity_emoji = "🔴" if indicator['severity'] == "HIGH" else "🟡"
                        st.markdown(f"{severity_emoji} **{indicator['indicator']}**")
                        st.markdown(f"   {indicator['description']}")
                
                with col2:
                    st.markdown("**Transaction Summary:**")
                    st.json(sample['transaction_summary'])
                    st.markdown(f"**Customer Profile:**")
                    st.json(sample['customer_profile'])
    
    except FileNotFoundError:
        st.error("⚠️ sample_alerts.json not found")
        st.info("Make sure data files are in correct locations")

# TAB 4: About
with tab4:
    st.header("ℹ️ About SAR Narrative Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Problem Statement")
        st.markdown("""
        Banks must file Suspicious Activity Reports (SARs) for potential money laundering.
        
        **Current Pain Points:**
        - ⏱️ Takes 5-6 hours per report (manual)
        - 👥 Analyst bottleneck (thousands/year)
        - 📉 Quality inconsistency
        - ⚖️ Regulatory scrutiny on explanations
        - 💰 Expensive (15-20% of recovered amounts)
        """)
        
        st.subheader("✨ Our Solution")
        st.markdown("""
        AI-powered SAR generation with:
        - ⚡ **8-second generation** (99% faster)
        - 🔍 **Full audit trail** for transparency
        - 📝 **Consistent regulatory language**
        - 👤 **Human review** before submission
        - 🔒 **100% local** (no data leaves premise)
        """)
    
    with col2:
        st.subheader("🏗️ Architecture")
        st.markdown("""
        **Technology Stack:**
        - **LLM:** Ollama (Llama 3.2 / Mistral)
        - **Framework:** LangChain
        - **UI:** Streamlit
        - **Knowledge Base:** PMLA, FATF guidelines
        - **Audit System:** Complete traceability
        """)
        
        st.subheader("📊 Impact Metrics")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.metric("Time Savings", "5.5 hours", "per SAR")
        with col_b:
            st.metric("Cost Reduction", "₹3-4 Cr/year", "large banks")
        with col_c:
            st.metric("Consistency", "100%", "regulatory format")
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        🔒 Fully Local | 🔍 Transparent | ⚖️ Regulatory Compliant<br>
        Built for Banking Compliance Teams | Hackathon Project 2026
    </div>
    """, unsafe_allow_html=True)
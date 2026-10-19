"""AgentFlow | CA-3 Streamlit PoC | local, mock agents, no API key."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from agentflow import Ticket, process_ticket, flatten_result

st.set_page_config(page_title='AgentFlow | Support Operations', page_icon='🎯', layout='wide')
st.markdown('''<style>
.block-container{padding-top:1.6rem;max-width:1250px}
.hero{background:linear-gradient(115deg,#10233e,#193f6f);color:white;border-radius:18px;padding:25px 30px;margin-bottom:20px}
.hero h1{color:white;margin:0;font-size:2.1rem}.hero p{margin:8px 0 0;color:#d5e4ff}
.muted{color:#65758b;font-size:.93rem}
</style>''', unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>◈ AgentFlow</h1><p>Explainable multi-agent customer support automation · Offline PoC · Human-in-the-loop</p></div>',unsafe_allow_html=True)
st.caption('Synthetic data only · Deterministic mock agents · No customer data sent anywhere · Drafts are never automatically sent')

@st.cache_data
def load_samples():
    return pd.read_csv(Path(__file__).parent / 'data' / 'sample_tickets.csv').fillna('')

if 'results' not in st.session_state: st.session_state.results=[]
page = st.sidebar.radio('Workspace', ['Process a ticket', 'Batch processing', 'Operations dashboard', 'Architecture & agents'])
st.sidebar.info('Workflow: Plan → Classify → Prioritize → Research → Draft → Critic → Human review')

if page == 'Process a ticket':
    st.subheader('Ticket intake')
    df=load_samples()
    selection=st.selectbox('Try a synthetic ticket', ['Custom ticket']+[f"{r.ticket_id} — {r.subject}" for r in df.itertuples(index=False)])
    picked = None if selection=='Custom ticket' else df[df.ticket_id==selection.split(' — ')[0]].iloc[0]
    with st.form('intake'):
        c1,c2=st.columns(2)
        ticket_id=c1.text_input('Ticket ID',value=str(picked.ticket_id) if picked is not None else 'TKT-1007')
        customer=c2.text_input('Customer name (synthetic)',value=str(picked.customer) if picked is not None else 'Avery')
        subject=st.text_input('Subject',value=str(picked.subject) if picked is not None else 'Late package delivery')
        description=st.text_area('Description',value=str(picked.description) if picked is not None else 'My package is late and tracking has not updated in three days.',height=110)
        submit=st.form_submit_button('Run agent workflow',type='primary',use_container_width=True)
    if submit:
        if not ticket_id.strip() or not subject.strip() or not description.strip(): st.error('Ticket ID, subject, and description are required.')
        else:
            result=process_ticket(Ticket(ticket_id.strip(),customer.strip(),subject.strip(),description.strip()))
            st.session_state.results.append(result)
            st.session_state.latest=result
    if 'latest' in st.session_state:
        r=st.session_state.latest
        st.divider(); st.subheader('Agent decisions')
        cols=st.columns(4)
        cols[0].metric('Category',r['classification']['category'])
        cols[1].metric('Priority',r['priority']['priority'])
        cols[2].metric('Confidence',f"{r['classification']['confidence']:.0%}")
        cols[3].metric('Decision',r['validation']['status'])
        with st.expander('1. Planner — tasks',expanded=False): st.write(' → '.join(r['plan']['steps']))
        with st.expander('2. Classifier & priority — evidence'):
            st.json({'matched_terms':r['classification']['matched_terms'],'category_scores':r['classification']['scores'],'priority_reason':r['priority']['reason']})
        with st.expander('3. Research — knowledge base'):
            st.write(f"**{r['knowledge']['knowledge_id']}** — {r['knowledge']['guidance']}")
        with st.expander('4. Resolution — draft', expanded=True):
            st.text_area('Human-reviewable response (not sent)',r['resolution']['draft'],height=230)
            st.caption('Assigned team: '+r['resolution']['assigned_team'])
        with st.expander('5. Critic — validation',expanded=True):
            st.write(' | '.join(r['validation']['flags']))
            if r['validation']['status']=='Human Review': st.warning('Approval required. The system does not send or resolve tickets automatically.')
            else: st.success('Draft ready for optional human approval. No reply has been sent.')
        st.download_button('Download decision trace (JSON)',json.dumps(r,indent=2),file_name=r['ticket']['ticket_id']+'_trace.json',mime='application/json')

elif page == 'Batch processing':
    st.subheader('Batch ticket processing')
    st.write('Upload a CSV with columns **ticket_id, customer, subject, description**, or use the bundled demo data.')
    uploaded=st.file_uploader('Synthetic tickets CSV',type=['csv'])
    data=load_samples() if uploaded is None else pd.read_csv(uploaded).fillna('')
    needed={'ticket_id','customer','subject','description'}
    if not needed.issubset(data.columns): st.error('Missing columns: '+', '.join(sorted(needed-set(data.columns))))
    else:
        st.dataframe(data.head(15),use_container_width=True,hide_index=True)
        if st.button('Process batch',type='primary'):
            valid=data.astype(str)
            valid=valid[(valid.ticket_id.str.strip()!='') & (valid.subject.str.strip()!='') & (valid.description.str.strip()!='')]
            batch=[process_ticket(Ticket(**row)) for row in valid[list(needed)].to_dict('records')]
            st.session_state.results.extend(batch)
            st.success(f'Processed {len(batch)} tickets. {len(data)-len(batch)} incomplete rows skipped.')
            st.session_state.batch=batch
        if 'batch' in st.session_state:
            result_df=pd.DataFrame([flatten_result(x) for x in st.session_state.batch])
            st.dataframe(result_df.drop(columns=['response_draft']),use_container_width=True,hide_index=True)
            st.download_button('Download processed CSV',result_df.to_csv(index=False),file_name='agentflow_decisions.csv',mime='text/csv')

elif page == 'Operations dashboard':
    st.subheader('Ticket operations dashboard')
    results=st.session_state.results
    if not results: st.info('Process one or more sample tickets first. Results are held in your browser session.')
    else:
        rows=pd.DataFrame([flatten_result(x) for x in results]); c1,c2,c3=st.columns(3)
        c1.metric('Tickets processed',len(rows));c2.metric('Human review',int((rows.status=='Human Review').sum()));c3.metric('Draft ready',int((rows.status=='Draft Ready').sum()))
        a,b=st.columns(2)
        with a: st.markdown('**Ticket categories**');st.bar_chart(rows.category.value_counts())
        with b: st.markdown('**Priority distribution**');st.bar_chart(rows.priority.value_counts())
        st.dataframe(rows.drop(columns=['response_draft']),use_container_width=True,hide_index=True)
        st.download_button('Export results CSV',rows.to_csv(index=False),'agentflow_results.csv','text/csv')
        if st.button('Clear session results'): st.session_state.results=[];st.session_state.pop('latest',None);st.session_state.pop('batch',None);st.rerun()

else:
    st.subheader('How the agent workflow works')
    st.code('Ticket intake → Planner → Classification → Priority → Knowledge lookup → Resolution draft → Critic → Draft Ready / Human Review',language='text')
    st.markdown('''**Planner:** determines the work sequence.  
**Classification:** scores explainable keyword rules to infer ticket category.  
**Priority:** flags security/fraud triggers as critical and urgency signals as high.  
**Research:** retrieves an approved playbook from an embedded knowledge base.  
**Resolution:** creates a safe response draft and assigns a specialist team.  
**Critic:** checks missing details, low confidence and high-risk cases; routes to manual review.

This is an **agentic mock-model PoC**, not an LLM system. Agents coordinate through a Python orchestration function; routing is based on interpretable conditions. A real deployment would need approved integrations, authentication, monitoring and better evaluation.''')
    st.warning('All responses are drafts. No automated customer communications or live business integrations are implemented.')

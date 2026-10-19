from agentflow import Ticket, process_ticket, flatten_result

def make(text, subject='Issue'):
    return process_ticket(Ticket('TKT-TEST','Test User',subject,text))

def test_billing_classification():
    r=make('I was charged twice and need a refund.')
    assert r['classification']['category']=='Billing & Refund'

def test_security_escalation():
    r=make('An unauthorized transaction suggests fraud.')
    assert r['priority']['priority']=='Critical'
    assert r['validation']['status']=='Human Review'

def test_short_description_human_review():
    assert make('Issue.')['validation']['status']=='Human Review'

def test_normal_ticket_draft():
    r=make('My parcel delivery is late and tracking has not changed for several days.','Shipment delay')
    assert r['classification']['category']=='Delivery & Shipping'
    assert r['validation']['status']=='Draft Ready'
    assert 'TKT-TEST' in r['resolution']['draft']

def test_never_auto_send():
    assert make('I need my invoice from last billing cycle.')['validation']['auto_send'] is False

def test_flatten():
    assert flatten_result(make('The app crashes on launch.'))['team']=='Technical Support'

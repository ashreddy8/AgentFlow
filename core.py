"""Explainable, fully offline agentic customer-support workflow."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import re
from typing import Any

CATEGORIES = {
    'Billing & Refund': ['refund', 'charged', 'charge', 'invoice', 'billing', 'payment', 'money', 'deducted'],
    'Account & Login': ['login', 'sign in', 'password', 'locked', 'account', 'otp', 'reset'],
    'Delivery & Shipping': ['delivery', 'shipping', 'shipment', 'package', 'parcel', 'late', 'tracking', 'courier'],
    'Technical Issue': ['error', 'bug', 'crash', 'loading', 'app', 'website', 'technical', 'not working', 'broken'],
    'Product & Returns': ['return', 'damaged', 'defective', 'exchange', 'product', 'item', 'replacement'],
}
KB = {
    'Billing & Refund': ('Check the payment reference and refund policy; request an eligible refund review.', 'Billing / Payments', 'KB-101'),
    'Account & Login': ('Use the password reset flow; verify account ownership before changes.', 'Identity Support', 'KB-102'),
    'Delivery & Shipping': ('Check the order tracking status and investigate carrier exceptions.', 'Logistics Support', 'KB-103'),
    'Technical Issue': ('Capture device and error details; retry basic troubleshooting and escalate reproducible defects.', 'Technical Support', 'KB-104'),
    'Product & Returns': ('Verify the order, eligibility, and photos before offering return or replacement options.', 'Returns Team', 'KB-105'),
    'General Inquiry': ('Ask for the order/reference number and specific details before suggesting an action.', 'General Support', 'KB-106'),
}
URGENT = ['fraud', 'unauthorized', 'hacked', 'security breach', 'data leak', 'stolen', 'account takeover']
HIGH = ['urgent', 'asap', 'immediately', 'cannot access', 'double charged', 'overcharged', 'deadline', 'angry']

def contains(text: str, phrase: str) -> bool:
    return re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text.lower()) is not None

@dataclass
class Ticket:
    ticket_id: str
    customer: str
    subject: str
    description: str

class PlannerAgent:
    name = 'Planner Agent'
    def run(self, ticket: Ticket) -> dict[str, Any]:
        steps = ['Categorize complaint', 'Assess priority and risk', 'Retrieve approved knowledge', 'Draft response', 'Validate response and route']
        return {'steps': steps, 'length': len(ticket.description.strip()), 'complete': bool(ticket.description.strip())}

class ClassificationAgent:
    name = 'Classification Agent'
    def run(self, ticket: Ticket) -> dict[str, Any]:
        text = (ticket.subject + ' ' + ticket.description).lower()
        scores = {cat: sum(1 for k in terms if contains(text, k)) for cat, terms in CATEGORIES.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return {'category': 'General Inquiry', 'confidence': 0.35, 'matched_terms': [], 'scores': scores}
        # lower confidence when multiple categories match closely
        sorted_scores = sorted(scores.values(), reverse=True)
        confidence = round(min(0.95, 0.58 + 0.11 * sorted_scores[0] - (0.13 if sorted_scores[1] == sorted_scores[0] else 0)), 2)
        return {'category': best, 'confidence': confidence, 'matched_terms': [w for w in CATEGORIES[best] if contains(text,w)], 'scores': scores}

class PriorityAgent:
    name = 'Priority Agent'
    def run(self, ticket: Ticket) -> dict[str, str]:
        text = (ticket.subject + ' ' + ticket.description).lower()
        urgent_terms = [w for w in URGENT if contains(text, w)]
        high_terms = [w for w in HIGH if contains(text, w)]
        if urgent_terms: return {'priority': 'Critical', 'reason': 'Security/fraud trigger: ' + ', '.join(urgent_terms)}
        if high_terms: return {'priority': 'High', 'reason': 'Urgency trigger: ' + ', '.join(high_terms)}
        return {'priority': 'Medium' if len(text) > 65 else 'Low', 'reason': 'Rule-based assessment; no critical trigger'}

class ResearchAgent:
    name = 'Research Agent'
    def run(self, category: str) -> dict[str, str]:
        advice, team, ref = KB[category]
        return {'guidance': advice, 'team': team, 'knowledge_id': ref}

class ResolutionAgent:
    name = 'Resolution Agent'
    def run(self, ticket: Ticket, classification: dict, priority: dict, knowledge: dict) -> dict[str, str]:
        name = (ticket.customer or 'Customer').strip()
        first_name = re.sub(r'[^a-zA-Z -]', '', name).strip().split(' ')[0] or 'Customer'
        message = (f'Dear {first_name},\n\nThank you for contacting our support team regarding "{ticket.subject.strip()}". '
                   f'We understand your concern. {knowledge["guidance"]} '
                   'For your privacy, please do not share passwords, OTPs, or full payment card details. '
                   'A support representative will review the details before any account, payment, or order change is made.\n\n'
                   f'Your reference is {ticket.ticket_id}.\nBest regards,\nCustomer Support Team')
        return {'draft': message, 'assigned_team': knowledge['team'], 'proposed_action': knowledge['guidance']}

class CriticAgent:
    name = 'Critic Agent'
    def run(self, ticket: Ticket, classification: dict, priority: dict, resolution: dict) -> dict[str, Any]:
        flags = []
        if len(ticket.description.strip()) < 15: flags.append('Insufficient complaint detail')
        if classification['confidence'] < 0.6: flags.append('Low category confidence')
        if priority['priority'] in {'Critical', 'High'}: flags.append('High-risk case needs human approval')
        if not ticket.ticket_id.strip() or not ticket.subject.strip(): flags.append('Missing required ticket fields')
        if ticket.ticket_id not in resolution['draft']: flags.append('Reference number absent from draft')
        if 'guarantee' in resolution['draft'].lower(): flags.append('Unapproved guarantee detected')
        needs_review = bool(flags)
        return {'status': 'Human Review' if needs_review else 'Draft Ready', 'valid': not any('Missing required' in f or 'absent' in f for f in flags), 'flags': flags or ['All validation checks passed'], 'auto_send': False}

def process_ticket(ticket: Ticket) -> dict[str, Any]:
    """Orchestrate specialized agents. Never perform external side effects or send replies."""
    planner = PlannerAgent().run(ticket)
    classification = ClassificationAgent().run(ticket)
    priority = PriorityAgent().run(ticket)
    knowledge = ResearchAgent().run(classification['category'])
    resolution = ResolutionAgent().run(ticket, classification, priority, knowledge)
    validation = CriticAgent().run(ticket, classification, priority, resolution)
    return {'ticket': asdict(ticket), 'plan': planner, 'classification': classification,
            'priority': priority, 'knowledge': knowledge, 'resolution': resolution,
            'validation': validation, 'timestamp_utc': datetime.now(timezone.utc).isoformat()}


def flatten_result(result: dict) -> dict:
    t = result['ticket']
    return {'ticket_id': t['ticket_id'], 'customer': t['customer'], 'subject': t['subject'],
            'category': result['classification']['category'], 'confidence': result['classification']['confidence'],
            'priority': result['priority']['priority'], 'team': result['resolution']['assigned_team'],
            'status': result['validation']['status'], 'validation_flags': '; '.join(result['validation']['flags']),
            'response_draft': result['resolution']['draft']}

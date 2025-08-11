# Enhanced chatbot with comprehensive feature matching
import re
from datetime import datetime

# Import the feature database
from .feature_database import FEATURE_DATABASE, find_feature_match, get_feature_response

# Stokvel creation state tracking
stokvel_creation_state = {}

def enhanced_rule_based_chat(user_message, user_id, user_name):
    """
    Enhanced rule-based chat with comprehensive feature matching
    """
    user_message_lower = user_message.lower()
    response = None

    # Get or initialize user's creation state
    creation_state = stokvel_creation_state.get(user_id, {})

    # Direct Stokvel Creation Flow
    if 'create stokvel' in user_message_lower or creation_state.get('creating_stokvel'):
        if not creation_state.get('creating_stokvel'):
            # Start the creation flow
            stokvel_creation_state[user_id] = {
                'creating_stokvel': True,
                'step': 'name',
                'data': {}
            }
            return "Let's create your stokvel! What would you like to name it?"

        current_step = stokvel_creation_state[user_id]['step']
        data = stokvel_creation_state[user_id]['data']

        if current_step == 'name':
            data['name'] = user_message.strip()
            stokvel_creation_state[user_id]['step'] = 'monthly_contribution'
            return "Great! How much should the monthly contribution be? (Enter amount in Rands)"

        elif current_step == 'monthly_contribution':
            try:
                amount = float(user_message.replace('R', '').replace(',', '').strip())
                data['monthly_contribution'] = amount
                stokvel_creation_state[user_id]['step'] = 'target_amount'
                return "What's the target amount for this stokvel? (Enter 0 if no specific target)"
            except ValueError:
                return "Please enter a valid amount (e.g., 500 or R500)"

        elif current_step == 'target_amount':
            try:
                amount = float(user_message.replace('R', '').replace(',', '').strip())
                data['target_amount'] = amount
                stokvel_creation_state[user_id]['step'] = 'target_date'
                return "When do you want to reach this target? (Format: YYYY-MM-DD, or type 'none' for no specific date)"
            except ValueError:
                return "Please enter a valid amount (e.g., 5000 or R5000)"

        elif current_step == 'target_date':
            if user_message_lower == 'none':
                data['target_date'] = None
            else:
                try:
                    data['target_date'] = datetime.strptime(user_message.strip(), '%Y-%m-%d')
                except ValueError:
                    return "Please enter a valid date (YYYY-MM-DD) or 'none'"

            # Create the stokvel with all collected data
            try:
                from . import support
                description = f"Stokvel created via chat by {user_name}"
                query = """
                    INSERT INTO stokvels 
                    (name, description, created_by, monthly_contribution, target_amount, target_date) 
                    VALUES (%s, %s, %s, %s, %s, %s) 
                    RETURNING id
                """
                result = support.execute_query("insert", query, (
                    data['name'],
                    description,
                    user_id,
                    data['monthly_contribution'],
                    data.get('target_amount', 0),
                    data.get('target_date')
                ))

                if result and result[0]:
                    stokvel_id = result[0]
                    # Add creator as admin
                    support.execute_query("insert",
                        "INSERT INTO stokvel_members (stokvel_id, user_id, role) VALUES (%s, %s, %s)",
                        (stokvel_id, user_id, 'admin'))

                    # Clear the creation state
                    del stokvel_creation_state[user_id]

                    summary = (
                        f"Perfect! I've created your stokvel with these details:\n\n"
                        f"Name: {data['name']}\n"
                        f"Monthly Contribution: R{data['monthly_contribution']:.2f}\n"
                        f"Target Amount: {'R{:.2f}'.format(data['target_amount']) if data.get('target_amount') else 'Not set'}\n"
                        f"Target Date: {data['target_date'].strftime('%Y-%m-%d') if data.get('target_date') else 'Not set'}\n\n"
                        f"To add members, say: add member email@example.com to '{data['name']}'"
                    )
                    return summary
                else:
                    # Clear the creation state on error
                    if user_id in stokvel_creation_state:
                        del stokvel_creation_state[user_id]
                    return "Sorry, I couldn't create the stokvel. Please try again."

            except Exception as e:
                print(f"Error creating stokvel: {e}")
                # Clear the creation state on error
                if user_id in stokvel_creation_state:
                    del stokvel_creation_state[user_id]
                return "Sorry, I couldn't create the stokvel due to a system error. Please try again."

    # Direct Member Addition
    if 'add member' in user_message_lower:
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_message)
        stokvel_match = re.search(r'to\s+["\']?([^"\']+)["\']?', user_message)

        if not email_match or not stokvel_match:
            return "Please specify both the email and stokvel name. Example: add member user@example.com to 'My Stokvel'"

        email = email_match.group(0)
        stokvel_name = stokvel_match.group(1).strip()

        try:
            from . import support
            # Find stokvel
            query = "SELECT id FROM stokvels WHERE name = %s AND created_by = %s"
            result = support.execute_query("select", query, (stokvel_name, user_id))

            if result and result[0]:
                stokvel_id = result[0][0]
                # Add member
                support.execute_query("insert",
                    "INSERT INTO stokvel_members (stokvel_id, user_id, role, email) VALUES (%s, NULL, %s, %s)",
                    (stokvel_id, 'member', email))
                return f"✅ Added {email} to '{stokvel_name}'. They'll receive an invitation email."
            else:
                return "Sorry, I couldn't add the member. Please check the stokvel name and try again."
        except Exception as e:
            print(f"Error adding member: {e}")
            return "Sorry, I couldn't add the member due to a system error. Please try again."

    # Enhanced feature matching with comprehensive database
    feature_match, confidence = find_feature_match(user_message)
    
    if feature_match and confidence > 0.3:  # Threshold for acceptable match
        response = get_feature_response(feature_match)
        return response

    # Fallback response with comprehensive feature list
    if response is None:
        response = "I can help you with many KasiKash features! Try asking about:\n\n" + \
                  "• **Stokvels** - Create, manage, and contribute to community savings groups\n" + \
                  "• **Savings Goals** - Set personal financial targets and track progress\n" + \
                  "• **Payouts** - Request money from your stokvels\n" + \
                  "• **Profile & Settings** - Manage your account and preferences\n" + \
                  "• **Financial Advisor** - Get AI-powered financial advice\n" + \
                  "• **Notifications** - Stay updated on important activities\n" + \
                  "• **Payment Methods** - Manage your bank accounts and cards\n" + \
                  "• **KYC Verification** - Complete identity verification\n" + \
                  "• **Statements** - Download transaction history\n" + \
                  "• **Referrals** - Invite friends and earn rewards\n\n" + \
                  "💡 **Try these examples:**\n" + \
                  "• 'How do I create a stokvel?'\n" + \
                  "• 'Tell me about settings'\n" + \
                  "• 'How do I add members?'\n" + \
                  "• 'What is the financial advisor?'"

    return response 
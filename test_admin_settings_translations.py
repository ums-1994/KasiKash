#!/usr/bin/env python3
"""
Test script to verify admin settings translations have been added to all language files.
"""

import os
import polib
from pathlib import Path

def test_admin_settings_translations():
    """Test that admin settings translations are present in all language files."""
    
    # List of all admin settings message IDs
    admin_settings_messages = [
        "admin_settings",
        "switch_to_user_view", 
        "admin_settings_subtitle",
        "user_permissions",
        "financial_controls",
        "notifications",
        "meetings_events",
        "data_security",
        "languages",
        "select_admin_language",
        "english",
        "role_management",
        "assign_roles_help",
        "admin_full_access",
        "loan_approval_permissions",
        "choose_loan_approval_roles",
        "adminstreasurerssecretaries",
        "audit_logs",
        "theme",
        "view_audit_logs_help",
        "action",
        "performed_by",
        "target",
        "amount",
        "date",
        "cancel",
        "save_settings",
        "contribution_rules",
        "set_contribution_rules_help",
        "monthly_amount",
        "R",
        "100",
        "late_penalty",
        "10%",
        "grace_period",
        "7",
        "days",
        "loan_settings",
        "configure_loan_settings_help",
        "max_loan_percent",
        "50%",
        "interest_rate",
        "5%",
        "repayment_period",
        "6 months",
        "withdrawal_approvals",
        "require_dual_approval_help",
        "enable_dual_approval_for_withdrawals",
        "recurring_meetings",
        "schedule_meetings_help",
        "meeting_frequency",
        "monthly",
        "day_of_week",
        "monday",
        "time",
        "14:00",
        "send_automatic_reminders",
        "attendance_tracking",
        "record_attendance_help",
        "enable_attendance_tracking",
        "absence_penalty",
        "5after",
        "missed_meetings",
        "meeting",
        "present",
        "absent"
    ]
    
    # Language codes
    languages = ['en', 'af', 'zu', 'xh', 'nr', 'nso', 'st', 'tn', 'ss', 've', 'ts']
    
    print("Testing Admin Settings Translations")
    print("=" * 50)
    
    all_passed = True
    
    for lang in languages:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if not os.path.exists(po_file):
            print(f"❌ Missing translation file: {po_file}")
            all_passed = False
            continue
            
        try:
            po = polib.pofile(po_file)
            missing_messages = []
            
            for msg_id in admin_settings_messages:
                entry = po.find(msg_id)
                if not entry:
                    missing_messages.append(msg_id)
                elif not entry.msgstr:
                    missing_messages.append(f"{msg_id} (empty translation)")
            
            if missing_messages:
                print(f"❌ {lang.upper()}: Missing {len(missing_messages)} translations")
                for msg in missing_messages[:5]:  # Show first 5 missing
                    print(f"   - {msg}")
                if len(missing_messages) > 5:
                    print(f"   ... and {len(missing_messages) - 5} more")
                all_passed = False
            else:
                print(f"✅ {lang.upper()}: All {len(admin_settings_messages)} admin settings translations present")
                
        except Exception as e:
            print(f"❌ {lang.upper()}: Error reading file - {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All admin settings translations successfully added to all languages!")
    else:
        print("⚠️  Some translations are missing. Please check the files above.")
    
    return all_passed

def show_sample_translations():
    """Show sample translations from each language."""
    
    languages = ['en', 'af', 'zu', 'xh', 'nr', 'nso', 'st', 'tn', 'ss', 've', 'ts']
    
    print("\nSample Admin Settings Translations")
    print("=" * 50)
    
    sample_messages = [
        "admin_settings",
        "user_permissions", 
        "financial_controls",
        "languages",
        "role_management"
    ]
    
    for lang in languages:
        po_file = f"translations/{lang}/LC_MESSAGES/messages.po"
        
        if os.path.exists(po_file):
            try:
                po = polib.pofile(po_file)
                print(f"\n{lang.upper()}:")
                
                for msg_id in sample_messages:
                    entry = po.find(msg_id)
                    if entry and entry.msgstr:
                        print(f"  {msg_id}: {entry.msgstr}")
                    else:
                        print(f"  {msg_id}: ❌ Missing")
                        
            except Exception as e:
                print(f"  Error reading {lang}: {e}")

if __name__ == "__main__":
    test_admin_settings_translations()
    show_sample_translations() 
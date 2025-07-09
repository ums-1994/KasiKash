import os

# List of files to delete (relative to project root)
FILES_TO_DELETE = [
    'fix_chat_system.py',
    'fix_chat_system_complete.py',
    'simple_chat_fix.py',
    'list_chat_rooms.py',
    'list_chat_members.py',
    'print_chat_room_and_members.py',
    'print_chats_rows.py',
    'print_chats_columns.py',
    'debug_chat_system.py',
    'check_and_fix_all_chat_rooms_and_members.py',
    'check_and_fix_chat_room_membership.py',
    'check_chat_rooms_and_members.py',
    'fix_missing_chat_rooms_and_members.py',
    'create_missing_chat_rooms.py',
    'print_chat_members_columns.py',
    'list_stokvel_chat_status.py',
    'apply_create_stokvel_chat_tables.py',
    'apply_add_chat_advanced_features.py',
    'apply_add_user_device_tokens.py',
    'migrations/create_stokvel_chat_tables.sql',
    'migrations/add_chat_advanced_features.sql',
    'migrations/fix_chat_tables_to_text.sql',
    'migrations/alter_chat_tables_to_text.sql',
]

def delete_files(files):
    for file_path in files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        else:
            print(f"Not found (skipped): {file_path}")

if __name__ == "__main__":
    delete_files(FILES_TO_DELETE) 
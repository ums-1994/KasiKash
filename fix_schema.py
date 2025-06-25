from support import execute_query

def add_missing_columns():
    # Add columns to transactions
    execute_query('update', """
        ALTER TABLE transactions ADD COLUMN IF NOT EXISTS type VARCHAR(50);
    """)
    execute_query('update', """
        ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(50);
    """)

    # Add column to savings_goals
    execute_query('update', """
        ALTER TABLE savings_goals ADD COLUMN IF NOT EXISTS status VARCHAR(50);
    """)

    # Add column to payment_methods
    execute_query('update', """
        ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS type VARCHAR(50);
    """)

    # Add columns to users
    execute_query('update', """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences TEXT;
    """)
    execute_query('update', """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;
    """)
    execute_query('update', """
        ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
    """)

    # Add stokvel_id to savings_goals
    execute_query('update', """
        ALTER TABLE savings_goals ADD COLUMN IF NOT EXISTS stokvel_id INTEGER REFERENCES stokvels(id) ON DELETE SET NULL;
    """)

def fix_payment_methods_type_column():
    print('Fixing payment_methods.type column...')
    try:
        # 1. Try to rename method_type to type if type does not exist
        rename_sql = '''
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payment_methods' AND column_name='method_type') AND
               NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payment_methods' AND column_name='type') THEN
                EXECUTE 'ALTER TABLE payment_methods RENAME COLUMN method_type TO type';
            END IF;
        END$$;
        '''
        execute_query('update', rename_sql)
        # 2. Drop method_type if both method_type and type exist
        drop_sql = '''
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payment_methods' AND column_name='method_type') AND
               EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payment_methods' AND column_name='type') THEN
                EXECUTE 'ALTER TABLE payment_methods DROP COLUMN method_type';
            END IF;
        END$$;
        '''
        execute_query('update', drop_sql)
        # 3. Ensure type column exists
        execute_query('update', '''
            ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS type VARCHAR(50) NOT NULL DEFAULT 'bank_account';
        ''')
        print('payment_methods.type column fixed.')
    except Exception as e:
        print(f'Error fixing payment_methods.type column: {e}')

def add_payment_method_id_to_transactions():
    print('Ensuring payment_method_id column exists in transactions table...')
    try:
        execute_query('update', '''
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS payment_method_id INTEGER REFERENCES payment_methods(id);
        ''')
        print('payment_method_id column ensured in transactions.')
    except Exception as e:
        print(f'Error adding payment_method_id column: {e}')

def add_recurring_to_transactions():
    print('Ensuring recurring column exists in transactions table...')
    try:
        execute_query('update', '''
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS recurring BOOLEAN DEFAULT FALSE;
        ''')
        print('recurring column ensured in transactions.')
    except Exception as e:
        print(f'Error adding recurring column: {e}')

def add_transaction_type_to_transactions():
    print('Ensuring transaction_type column exists in transactions table...')
    try:
        execute_query('update', '''
            ALTER TABLE transactions ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(50) DEFAULT 'money';
        ''')
        print('transaction_type column ensured in transactions.')
    except Exception as e:
        print(f'Error adding transaction_type column: {e}')

if __name__ == "__main__":
    add_missing_columns()
    fix_payment_methods_type_column()
    add_payment_method_id_to_transactions()
    add_recurring_to_transactions()
    add_transaction_type_to_transactions()
    print("All missing columns added (if they did not already exist).") 
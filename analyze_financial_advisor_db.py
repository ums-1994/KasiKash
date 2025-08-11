#!/usr/bin/env python3
"""
Financial Advisor Database Analysis Script
Analyzes the financial advisor database tables and provides insights
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

def analyze_financial_advisor_database():
    """Analyze the financial advisor database tables"""
    
    try:
        from backend.support import db_connection
        
        print("🔍 Financial Advisor Database Analysis")
        print("=" * 50)
        
        with db_connection() as conn:
            with conn.cursor() as cur:
                
                # 1. Check if tables exist
                print("\n📋 Table Structure Analysis:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT table_name, column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name IN ('financial_statement_analysis', 'financial_advisor_chat')
                    ORDER BY table_name, ordinal_position
                """)
                
                tables = {}
                for row in cur.fetchall():
                    table_name, column_name, data_type, is_nullable = row
                    if table_name not in tables:
                        tables[table_name] = []
                    tables[table_name].append({
                        'column': column_name,
                        'type': data_type,
                        'nullable': is_nullable
                    })
                
                for table_name, columns in tables.items():
                    print(f"\n📊 {table_name}:")
                    for col in columns:
                        nullable = "NULL" if col['nullable'] == 'YES' else "NOT NULL"
                        print(f"  • {col['column']}: {col['type']} ({nullable})")
                
                # 2. Count records
                print("\n📈 Data Statistics:")
                print("-" * 30)
                
                cur.execute("SELECT COUNT(*) FROM financial_statement_analysis")
                analysis_count = cur.fetchone()[0]
                print(f"📄 Statement Analyses: {analysis_count}")
                
                cur.execute("SELECT COUNT(*) FROM financial_advisor_chat")
                chat_count = cur.fetchone()[0]
                print(f"💬 Chat Messages: {chat_count}")
                
                # 3. User activity
                print("\n👥 User Activity:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT COUNT(DISTINCT user_id) 
                    FROM financial_statement_analysis
                """)
                active_users = cur.fetchone()[0]
                print(f"Active Users: {active_users}")
                
                # 4. Recent activity
                print("\n⏰ Recent Activity (Last 7 days):")
                print("-" * 30)
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM financial_statement_analysis 
                    WHERE uploaded_at >= NOW() - INTERVAL '7 days'
                """)
                recent_analyses = cur.fetchone()[0]
                print(f"Recent Analyses: {recent_analyses}")
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM financial_advisor_chat 
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                """)
                recent_chats = cur.fetchone()[0]
                print(f"Recent Chat Messages: {recent_chats}")
                
                # 5. Top users
                print("\n🏆 Top Users by Analysis Count:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT user_id, COUNT(*) as analysis_count
                    FROM financial_statement_analysis
                    GROUP BY user_id
                    ORDER BY analysis_count DESC
                    LIMIT 5
                """)
                
                top_users = cur.fetchall()
                for i, (user_id, count) in enumerate(top_users, 1):
                    print(f"{i}. User {user_id[:8]}...: {count} analyses")
                
                # 6. File types
                print("\n📁 File Upload Analysis:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN file_name LIKE '%.pdf' THEN 'PDF'
                            WHEN file_name LIKE '%.png' THEN 'PNG'
                            WHEN file_name LIKE '%.jpg' THEN 'JPG'
                            WHEN file_name LIKE '%.jpeg' THEN 'JPEG'
                            ELSE 'Other'
                        END as file_type,
                        COUNT(*) as count
                    FROM financial_statement_analysis
                    WHERE file_name IS NOT NULL
                    GROUP BY file_type
                    ORDER BY count DESC
                """)
                
                file_types = cur.fetchall()
                for file_type, count in file_types:
                    print(f"{file_type}: {count} files")
                
                # 7. Data quality check
                print("\n🔍 Data Quality Check:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM financial_statement_analysis 
                    WHERE statement_text IS NULL OR statement_text = ''
                """)
                empty_texts = cur.fetchone()[0]
                print(f"Analyses with empty text: {empty_texts}")
                
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM financial_statement_analysis 
                    WHERE ai_analysis IS NULL OR ai_analysis = ''
                """)
                empty_analyses = cur.fetchone()[0]
                print(f"Analyses with empty AI analysis: {empty_analyses}")
                
                # 8. Performance recommendations
                print("\n⚡ Performance Recommendations:")
                print("-" * 30)
                
                # Check for indexes
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename IN ('financial_statement_analysis', 'financial_advisor_chat')
                """)
                indexes = [row[0] for row in cur.fetchall()]
                
                if not indexes:
                    print("❌ No indexes found - performance may be slow")
                    print("💡 Consider adding indexes on user_id and timestamp columns")
                else:
                    print(f"✅ Found {len(indexes)} indexes")
                    for index in indexes:
                        print(f"  • {index}")
                
                # 9. Storage analysis
                print("\n💾 Storage Analysis:")
                print("-" * 30)
                
                cur.execute("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('financial_statement_analysis')) as analysis_size,
                        pg_size_pretty(pg_total_relation_size('financial_advisor_chat')) as chat_size
                """)
                
                sizes = cur.fetchone()
                print(f"Statement Analysis Table: {sizes[0]}")
                print(f"Advisor Chat Table: {sizes[1]}")
                
        print("\n" + "=" * 50)
        print("✅ Database analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        return False
    
    return True

def run_migration_check():
    """Check if the database migration has been applied"""
    
    try:
        from backend.support import db_connection
        
        print("\n🔧 Migration Status Check:")
        print("-" * 30)
        
        with db_connection() as conn:
            with conn.cursor() as cur:
                
                # Check for foreign key constraints
                cur.execute("""
                    SELECT constraint_name, table_name
                    FROM information_schema.table_constraints
                    WHERE constraint_type = 'FOREIGN KEY'
                    AND table_name IN ('financial_statement_analysis', 'financial_advisor_chat')
                """)
                
                fk_constraints = cur.fetchall()
                
                if fk_constraints:
                    print("✅ Foreign key constraints found:")
                    for constraint, table in fk_constraints:
                        print(f"  • {constraint} on {table}")
                else:
                    print("❌ No foreign key constraints found")
                    print("💡 Run the migration script to add proper constraints")
                
                # Check for indexes
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename IN ('financial_statement_analysis', 'financial_advisor_chat')
                    AND indexname LIKE 'idx_%'
                """)
                
                indexes = [row[0] for row in cur.fetchall()]
                
                if indexes:
                    print("✅ Performance indexes found:")
                    for index in indexes:
                        print(f"  • {index}")
                else:
                    print("❌ No performance indexes found")
                    print("💡 Run the migration script to add indexes")
        
    except Exception as e:
        print(f"❌ Error checking migration status: {e}")

if __name__ == "__main__":
    print("🚀 Starting Financial Advisor Database Analysis...")
    
    # Run the analysis
    success = analyze_financial_advisor_database()
    
    if success:
        # Run migration check
        run_migration_check()
        
        print("\n📋 Summary:")
        print("-" * 30)
        print("✅ Database analysis completed")
        print("📊 Check the statistics above for insights")
        print("🔧 Review migration status for improvements")
        print("\n💡 Next steps:")
        print("  • Run migrations if needed")
        print("  • Monitor data quality")
        print("  • Consider data cleanup for old records")
    else:
        print("❌ Analysis failed - check database connection") 
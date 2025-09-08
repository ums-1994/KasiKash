"""
Enhanced Financial Advisor Database Support Functions
Provides improved database operations for the financial advisor module
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List
from psycopg2.extras import Json
import psycopg2
from .support import db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_statement_analysis_enhanced(
    user_id: str, 
    statement_text: str, 
    ai_analysis: str, 
    transactions: Dict[str, Any], 
    file_name: str, 
    ai_budget_plan: Optional[str] = None
) -> Optional[int]:
    """
    Enhanced function to save statement analysis with better error handling
    
    Args:
        user_id: User's Firebase UID
        statement_text: Raw OCR text from statement
        ai_analysis: AI-generated analysis
        transactions: Parsed transactions as dictionary
        file_name: Original uploaded file name
        ai_budget_plan: AI-generated budget plan (optional)
    
    Returns:
        Analysis ID if successful, None if failed
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Validate user_id exists
                cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid = %s", (user_id,))
                if not cur.fetchone():
                    logger.error(f"User {user_id} not found in users table")
                    return None
                
                # Validate input data
                if not statement_text or not statement_text.strip():
                    logger.error("Statement text cannot be empty")
                    return None
                
                if not ai_analysis or not ai_analysis.strip():
                    logger.error("AI analysis cannot be empty")
                    return None
                
                # Insert analysis
                cur.execute("""
                    INSERT INTO financial_statement_analysis
                    (user_id, statement_text, ai_analysis, transactions_json, file_name, ai_budget_plan)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, statement_text.strip(), ai_analysis.strip(), Json(transactions), file_name, ai_budget_plan))
                
                analysis_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Saved statement analysis {analysis_id} for user {user_id}")
                return analysis_id
                
    except Exception as e:
        logger.error(f"Error saving statement analysis: {e}")
        return None

def get_latest_analysis_enhanced(user_id: str, with_budget: bool = False) -> Optional[Tuple]:
    """
    Enhanced function to get latest analysis with better error handling
    
    Args:
        user_id: User's Firebase UID
        with_budget: Whether to include budget plan in result
    
    Returns:
        Tuple of (id, statement_text, ai_analysis, transactions_json, ai_budget_plan) or None
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                if with_budget:
                    cur.execute("""
                        SELECT id, statement_text, ai_analysis, transactions_json, ai_budget_plan, uploaded_at
                        FROM financial_statement_analysis
                        WHERE user_id = %s
                        ORDER BY uploaded_at DESC
                        LIMIT 1
                    """, (user_id,))
                else:
                    cur.execute("""
                        SELECT id, statement_text, ai_analysis, uploaded_at
                        FROM financial_statement_analysis
                        WHERE user_id = %s
                        ORDER BY uploaded_at DESC
                        LIMIT 1
                    """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    logger.info(f"Retrieved analysis for user {user_id}")
                else:
                    logger.info(f"No analysis found for user {user_id}")
                return result
                
    except Exception as e:
        logger.error(f"Error retrieving analysis for user {user_id}: {e}")
        return None

def save_advisor_chat_enhanced(
    user_id: str, 
    analysis_id: int, 
    message: str, 
    response: str
) -> bool:
    """
    Enhanced function to save advisor chat with validation
    
    Args:
        user_id: User's Firebase UID
        analysis_id: ID of the analysis this chat relates to
        message: User's message
        response: AI advisor's response
    
    Returns:
        True if successful, False if failed
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Validate analysis_id belongs to user
                cur.execute("""
                    SELECT id FROM financial_statement_analysis 
                    WHERE id = %s AND user_id = %s
                """, (analysis_id, user_id))
                
                if not cur.fetchone():
                    logger.error(f"Analysis {analysis_id} not found for user {user_id}")
                    return False
                
                # Validate input data
                if not message or not message.strip():
                    logger.error("Message cannot be empty")
                    return False
                
                if not response or not response.strip():
                    logger.error("Response cannot be empty")
                    return False
                
                # Insert chat
                cur.execute("""
                    INSERT INTO financial_advisor_chat
                    (user_id, statement_analysis_id, message, response)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, analysis_id, message.strip(), response.strip()))
                
                conn.commit()
                logger.info(f"Saved chat for user {user_id}, analysis {analysis_id}")
                return True
                
    except Exception as e:
        logger.error(f"Error saving advisor chat: {e}")
        return False

def get_chat_history_enhanced(user_id: str, limit: int = 50) -> list:
    """
    Get chat history for a user
    
    Args:
        user_id: User's Firebase UID
        limit: Maximum number of chat messages to return
    
    Returns:
        List of chat messages with timestamps
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT message, response, created_at, statement_analysis_id
                    FROM financial_advisor_chat
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (user_id, limit))
                
                results = cur.fetchall()
                logger.info(f"Retrieved {len(results)} chat messages for user {user_id}")
                return results
                
    except Exception as e:
        logger.error(f"Error retrieving chat history for user {user_id}: {e}")
        return []

def get_user_analysis_count(user_id: str) -> int:
    """
    Get the number of analyses a user has
    
    Args:
        user_id: User's Firebase UID
    
    Returns:
        Number of analyses
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE user_id = %s
                """, (user_id,))
                
                count = cur.fetchone()[0]
                logger.info(f"User {user_id} has {count} analyses")
                return count
                
    except Exception as e:
        logger.error(f"Error counting analyses for user {user_id}: {e}")
        return 0

def cleanup_old_data(days_to_keep: int = 90) -> int:
    """
    Clean up old financial advisor data
    
    Args:
        days_to_keep: Number of days of data to keep
    
    Returns:
        Number of records deleted
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Delete old chat messages
                cur.execute("""
                    DELETE FROM financial_advisor_chat
                    WHERE created_at < NOW() - INTERVAL '%s days'
                """, (days_to_keep,))
                chat_deleted = cur.rowcount
                
                # Delete old analyses
                cur.execute("""
                    DELETE FROM financial_statement_analysis
                    WHERE uploaded_at < NOW() - INTERVAL '%s days'
                """, (days_to_keep,))
                analysis_deleted = cur.rowcount
                
                conn.commit()
                logger.info(f"Cleaned up {chat_deleted} chat messages and {analysis_deleted} analyses")
                return chat_deleted + analysis_deleted
                
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return 0

# NEW ENHANCED FUNCTIONS

def get_user_analytics(user_id: str) -> Dict[str, Any]:
    """
    Get comprehensive analytics for a user
    
    Args:
        user_id: User's Firebase UID
    
    Returns:
        Dictionary with analytics data
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Get analysis count
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE user_id = %s
                """, (user_id,))
                analysis_count = cur.fetchone()[0]
                
                # Get chat count
                cur.execute("""
                    SELECT COUNT(*) FROM financial_advisor_chat
                    WHERE user_id = %s
                """, (user_id,))
                chat_count = cur.fetchone()[0]
                
                # Get latest activity
                cur.execute("""
                    SELECT MAX(uploaded_at) FROM financial_statement_analysis
                    WHERE user_id = %s
                """, (user_id,))
                last_analysis = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT MAX(created_at) FROM financial_advisor_chat
                    WHERE user_id = %s
                """, (user_id,))
                last_chat = cur.fetchone()[0]
                
                # Get file type distribution
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
                    WHERE user_id = %s AND file_name IS NOT NULL
                    GROUP BY file_type
                    ORDER BY count DESC
                """, (user_id,))
                file_types = dict(cur.fetchall())
                
                return {
                    'analysis_count': analysis_count,
                    'chat_count': chat_count,
                    'last_analysis': last_analysis,
                    'last_chat': last_chat,
                    'file_types': file_types,
                    'is_active': analysis_count > 0 or chat_count > 0
                }
                
    except Exception as e:
        logger.error(f"Error getting analytics for user {user_id}: {e}")
        return {}

def get_system_analytics() -> Dict[str, Any]:
    """
    Get system-wide analytics for the financial advisor module
    
    Returns:
        Dictionary with system analytics
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Total counts
                cur.execute("SELECT COUNT(*) FROM financial_statement_analysis")
                total_analyses = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM financial_advisor_chat")
                total_chats = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(DISTINCT user_id) FROM financial_statement_analysis")
                active_users = cur.fetchone()[0]
                
                # Recent activity (last 30 days)
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE uploaded_at >= NOW() - INTERVAL '30 days'
                """, ())
                recent_analyses = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT COUNT(*) FROM financial_advisor_chat
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                """, ())
                recent_chats = cur.fetchone()[0]
                
                # Storage usage
                cur.execute("""
                    SELECT 
                        pg_size_pretty(pg_total_relation_size('financial_statement_analysis')) as analysis_size,
                        pg_size_pretty(pg_total_relation_size('financial_advisor_chat')) as chat_size
                """)
                sizes = cur.fetchone()
                
                return {
                    'total_analyses': total_analyses,
                    'total_chats': total_chats,
                    'active_users': active_users,
                    'recent_analyses_30d': recent_analyses,
                    'recent_chats_30d': recent_chats,
                    'analysis_table_size': sizes[0],
                    'chat_table_size': sizes[1]
                }
                
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        return {}

def backup_user_data(user_id: str) -> Dict[str, Any]:
    """
    Create a backup of user's financial advisor data
    
    Args:
        user_id: User's Firebase UID
    
    Returns:
        Dictionary with backup data
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Get all analyses
                cur.execute("""
                    SELECT id, statement_text, ai_analysis, transactions_json, file_name, ai_budget_plan, uploaded_at
                    FROM financial_statement_analysis
                    WHERE user_id = %s
                    ORDER BY uploaded_at DESC
                """, (user_id,))
                analyses = cur.fetchall()
                
                # Get all chat messages
                cur.execute("""
                    SELECT message, response, created_at, statement_analysis_id
                    FROM financial_advisor_chat
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))
                chats = cur.fetchall()
                
                return {
                    'user_id': user_id,
                    'backup_date': datetime.now().isoformat(),
                    'analyses': analyses,
                    'chats': chats,
                    'analysis_count': len(analyses),
                    'chat_count': len(chats)
                }
                
    except Exception as e:
        logger.error(f"Error backing up data for user {user_id}: {e}")
        return {}

def validate_data_integrity() -> Dict[str, Any]:
    """
    Validate data integrity across financial advisor tables
    
    Returns:
        Dictionary with validation results
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                issues = []
                
                # Check for orphaned chat messages
                cur.execute("""
                    SELECT COUNT(*) FROM financial_advisor_chat fac
                    LEFT JOIN financial_statement_analysis fsa ON fac.statement_analysis_id = fsa.id
                    WHERE fsa.id IS NULL
                """)
                orphaned_chats = cur.fetchone()[0]
                if orphaned_chats > 0:
                    issues.append(f"Found {orphaned_chats} orphaned chat messages")
                
                # Check for empty analyses
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE statement_text IS NULL OR LENGTH(TRIM(statement_text)) = 0
                """)
                empty_texts = cur.fetchone()[0]
                if empty_texts > 0:
                    issues.append(f"Found {empty_texts} analyses with empty text")
                
                # Check for empty AI analyses
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE ai_analysis IS NULL OR LENGTH(TRIM(ai_analysis)) = 0
                """)
                empty_ai = cur.fetchone()[0]
                if empty_ai > 0:
                    issues.append(f"Found {empty_ai} analyses with empty AI analysis")
                
                # Check for invalid JSON in transactions
                cur.execute("""
                    SELECT COUNT(*) FROM financial_statement_analysis
                    WHERE transactions_json IS NULL
                """)
                null_transactions = cur.fetchone()[0]
                if null_transactions > 0:
                    issues.append(f"Found {null_transactions} analyses with null transactions")
                
                return {
                    'valid': len(issues) == 0,
                    'issues': issues,
                    'issue_count': len(issues)
                }
                
    except Exception as e:
        logger.error(f"Error validating data integrity: {e}")
        return {'valid': False, 'issues': [f"Validation error: {e}"], 'issue_count': 1}

def get_performance_metrics() -> Dict[str, Any]:
    """
    Get database performance metrics
    
    Returns:
        Dictionary with performance metrics
    """
    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                # Check index usage
                cur.execute("""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE tablename IN ('financial_statement_analysis', 'financial_advisor_chat')
                    ORDER BY idx_scan DESC
                """)
                index_stats = cur.fetchall()
                
                # Check table statistics
                cur.execute("""
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                    FROM pg_stat_user_tables
                    WHERE tablename IN ('financial_statement_analysis', 'financial_advisor_chat')
                """)
                table_stats = cur.fetchall()
                
                return {
                    'index_usage': index_stats,
                    'table_stats': table_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return {} 
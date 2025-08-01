"""
Enhanced Financial Advisor Database Support Functions
Provides improved database operations for the financial advisor module
"""

import json
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
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
                
                # Insert analysis
                cur.execute("""
                    INSERT INTO financial_statement_analysis
                    (user_id, statement_text, ai_analysis, transactions_json, file_name, ai_budget_plan)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, statement_text, ai_analysis, Json(transactions), file_name, ai_budget_plan))
                
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
                        SELECT id, statement_text, ai_analysis, transactions_json, ai_budget_plan
                        FROM financial_statement_analysis
                        WHERE user_id = %s
                        ORDER BY uploaded_at DESC
                        LIMIT 1
                    """, (user_id,))
                else:
                    cur.execute("""
                        SELECT id, statement_text, ai_analysis
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
                
                # Insert chat
                cur.execute("""
                    INSERT INTO financial_advisor_chat
                    (user_id, statement_analysis_id, message, response)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, analysis_id, message, response))
                
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
                    SELECT message, response, created_at
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
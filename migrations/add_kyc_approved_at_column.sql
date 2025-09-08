-- Migration: Add kyc_approved_at column to users table
-- Run this SQL to allow tracking of KYC approval timestamps

ALTER TABLE users
ADD COLUMN kyc_approved_at TIMESTAMP;

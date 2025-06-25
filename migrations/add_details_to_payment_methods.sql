-- Migration: Add 'details' column to payment_methods table
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS details TEXT NOT NULL DEFAULT '{}'; 
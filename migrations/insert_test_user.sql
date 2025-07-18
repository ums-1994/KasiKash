INSERT INTO users (
    firebase_uid, username, email, password, full_name, phone, id_number, date_of_birth, address, bio, profile_picture, kyc_status, last_login
) VALUES (
    'kasikashapp-4f72a', 'testuser', 'test@example.com', 'firebase', 'Test User', '0123456789', '1234567890123', '1990-01-01', '123 Test St', 'Test bio', '', 'pending', NOW()
); 
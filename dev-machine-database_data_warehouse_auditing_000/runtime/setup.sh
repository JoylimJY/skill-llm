#!/bin/bash
set -e

echo "=== Setting up mock datax SSH + MySQL environment ==="

# 1. Start MySQL service
service mysql start || mysqld_safe --user=mysql &
sleep 5

# 2. Set up MySQL: create dw database and tables with realistic data
mysql -u root <<'MYSQL_SETUP'
-- Create the dwuser
CREATE USER IF NOT EXISTS 'dwuser'@'localhost' IDENTIFIED BY 'Dw@2024Secure!';
CREATE USER IF NOT EXISTS 'dwuser'@'%' IDENTIFIED BY 'Dw@2024Secure!';

-- Create main dw database
CREATE DATABASE IF NOT EXISTS dw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges
GRANT SELECT ON dw.* TO 'dwuser'@'localhost';
GRANT SELECT ON dw.* TO 'dwuser'@'%';
FLUSH PRIVILEGES;

USE dw;

-- Create tr_user table
CREATE TABLE IF NOT EXISTS tr_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(200),
    phone VARCHAR(20),
    status TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    country_code VARCHAR(10) DEFAULT 'TH'
);

-- Create tr_order table
CREATE TABLE IF NOT EXISTS tr_order (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(50) NOT NULL,
    user_id INT,
    store_id INT,
    total_amount DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create tr_store table
CREATE TABLE IF NOT EXISTS tr_store (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_code VARCHAR(50),
    store_name VARCHAR(200),
    city VARCHAR(100),
    province VARCHAR(100),
    active TINYINT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create tr_client table
CREATE TABLE IF NOT EXISTS tr_client (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_name VARCHAR(200),
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Populate tr_user with 75 rows (more than LIMIT 50 to test the limit)
INSERT INTO tr_user (username, email, phone, status, country_code) VALUES
('alice_th', 'alice@retailco.th', '+6681234001', 1, 'TH'),
('bob_th', 'bob@retailco.th', '+6681234002', 1, 'TH'),
('charlie_sg', 'charlie@retailco.sg', '+6591234003', 1, 'SG'),
('diana_my', 'diana@retailco.my', '+6012345004', 0, 'MY'),
('evan_th', 'evan@retailco.th', '+6681234005', 1, 'TH'),
('fiona_th', 'fiona@retailco.th', '+6681234006', 1, 'TH'),
('george_sg', 'george@retailco.sg', '+6591234007', 1, 'SG'),
('helen_my', 'helen@retailco.my', '+6012345008', 1, 'MY'),
('ivan_th', 'ivan@retailco.th', '+6681234009', 0, 'TH'),
('jane_th', 'jane@retailco.th', '+6681234010', 1, 'TH'),
('kevin_sg', 'kevin@retailco.sg', '+6591234011', 1, 'SG'),
('lily_my', 'lily@retailco.my', '+6012345012', 1, 'MY'),
('mike_th', 'mike@retailco.th', '+6681234013', 1, 'TH'),
('nancy_th', 'nancy@retailco.th', '+6681234014', 0, 'TH'),
('oscar_sg', 'oscar@retailco.sg', '+6591234015', 1, 'SG'),
('penny_my', 'penny@retailco.my', '+6012345016', 1, 'MY'),
('quinn_th', 'quinn@retailco.th', '+6681234017', 1, 'TH'),
('rachel_th', 'rachel@retailco.th', '+6681234018', 1, 'TH'),
('steve_sg', 'steve@retailco.sg', '+6591234019', 1, 'SG'),
('tina_my', 'tina@retailco.my', '+6012345020', 0, 'MY'),
('user021', 'u021@mail.th', '+6681230021', 1, 'TH'),
('user022', 'u022@mail.th', '+6681230022', 1, 'TH'),
('user023', 'u023@mail.sg', '+6591230023', 1, 'SG'),
('user024', 'u024@mail.my', '+6012340024', 1, 'MY'),
('user025', 'u025@mail.th', '+6681230025', 0, 'TH'),
('user026', 'u026@mail.th', '+6681230026', 1, 'TH'),
('user027', 'u027@mail.sg', '+6591230027', 1, 'SG'),
('user028', 'u028@mail.my', '+6012340028', 1, 'MY'),
('user029', 'u029@mail.th', '+6681230029', 1, 'TH'),
('user030', 'u030@mail.th', '+6681230030', 1, 'TH'),
('user031', 'u031@mail.th', '+6681230031', 1, 'TH'),
('user032', 'u032@mail.th', '+6681230032', 1, 'TH'),
('user033', 'u033@mail.sg', '+6591230033', 1, 'SG'),
('user034', 'u034@mail.my', '+6012340034', 0, 'MY'),
('user035', 'u035@mail.th', '+6681230035', 1, 'TH'),
('user036', 'u036@mail.th', '+6681230036', 1, 'TH'),
('user037', 'u037@mail.sg', '+6591230037', 1, 'SG'),
('user038', 'u038@mail.my', '+6012340038', 1, 'MY'),
('user039', 'u039@mail.th', '+6681230039', 1, 'TH'),
('user040', 'u040@mail.th', '+6681230040', 1, 'TH'),
('user041', 'u041@mail.th', '+6681230041', 1, 'TH'),
('user042', 'u042@mail.th', '+6681230042', 0, 'TH'),
('user043', 'u043@mail.sg', '+6591230043', 1, 'SG'),
('user044', 'u044@mail.my', '+6012340044', 1, 'MY'),
('user045', 'u045@mail.th', '+6681230045', 1, 'TH'),
('user046', 'u046@mail.th', '+6681230046', 1, 'TH'),
('user047', 'u047@mail.sg', '+6591230047', 1, 'SG'),
('user048', 'u048@mail.my', '+6012340048', 1, 'MY'),
('user049', 'u049@mail.th', '+6681230049', 1, 'TH'),
('user050', 'u050@mail.th', '+6681230050', 1, 'TH'),
('user051', 'u051@mail.th', '+6681230051', 0, 'TH'),
('user052', 'u052@mail.th', '+6681230052', 1, 'TH'),
('user053', 'u053@mail.sg', '+6591230053', 1, 'SG'),
('user054', 'u054@mail.my', '+6012340054', 1, 'MY'),
('user055', 'u055@mail.th', '+6681230055', 1, 'TH'),
('user056', 'u056@mail.th', '+6681230056', 1, 'TH'),
('user057', 'u057@mail.sg', '+6591230057', 1, 'SG'),
('user058', 'u058@mail.my', '+6012340058', 0, 'MY'),
('user059', 'u059@mail.th', '+6681230059', 1, 'TH'),
('user060', 'u060@mail.th', '+6681230060', 1, 'TH'),
('user061', 'u061@mail.th', '+6681230061', 1, 'TH'),
('user062', 'u062@mail.th', '+6681230062', 1, 'TH'),
('user063', 'u063@mail.sg', '+6591230063', 1, 'SG'),
('user064', 'u064@mail.my', '+6012340064', 1, 'MY'),
('user065', 'u065@mail.th', '+6681230065', 0, 'TH'),
('user066', 'u066@mail.th', '+6681230066', 1, 'TH'),
('user067', 'u067@mail.sg', '+6591230067', 1, 'SG'),
('user068', 'u068@mail.my', '+6012340068', 1, 'MY'),
('user069', 'u069@mail.th', '+6681230069', 1, 'TH'),
('user070', 'u070@mail.th', '+6681230070', 1, 'TH'),
('user071', 'u071@mail.th', '+6681230071', 1, 'TH'),
('user072', 'u072@mail.th', '+6681230072', 0, 'TH'),
('user073', 'u073@mail.sg', '+6591230073', 1, 'SG'),
('user074', 'u074@mail.my', '+6012340074', 1, 'MY'),
('user075', 'u075@mail.th', '+6681230075', 1, 'TH');

-- Populate tr_order with 60 rows
INSERT INTO tr_order (order_no, user_id, store_id, total_amount, status) VALUES
('ORD-2024-001', 1, 1, 1250.00, 'completed'),
('ORD-2024-002', 2, 2, 890.50, 'completed'),
('ORD-2024-003', 3, 1, 2100.75, 'pending'),
('ORD-2024-004', 4, 3, 450.00, 'cancelled'),
('ORD-2024-005', 5, 2, 3200.00, 'completed'),
('ORD-2024-006', 6, 1, 780.25, 'completed'),
('ORD-2024-007', 7, 4, 1560.00, 'pending'),
('ORD-2024-008', 8, 2, 920.00, 'completed'),
('ORD-2024-009', 9, 3, 340.50, 'completed'),
('ORD-2024-010', 10, 1, 5600.00, 'completed'),
('ORD-2024-011', 11, 2, 890.00, 'pending'),
('ORD-2024-012', 12, 3, 1200.00, 'completed'),
('ORD-2024-013', 13, 4, 670.25, 'completed'),
('ORD-2024-014', 14, 1, 2340.00, 'cancelled'),
('ORD-2024-015', 15, 2, 1100.00, 'completed'),
('ORD-2024-016', 16, 3, 450.75, 'completed'),
('ORD-2024-017', 17, 4, 3400.00, 'pending'),
('ORD-2024-018', 18, 1, 780.00, 'completed'),
('ORD-2024-019', 19, 2, 920.50, 'completed'),
('ORD-2024-020', 20, 3, 1650.00, 'completed'),
('ORD-2024-021', 1, 4, 340.00, 'completed'),
('ORD-2024-022', 2, 1, 5100.25, 'pending'),
('ORD-2024-023', 3, 2, 870.00, 'completed'),
('ORD-2024-024', 4, 3, 1230.00, 'completed'),
('ORD-2024-025', 5, 4, 670.50, 'cancelled'),
('ORD-2024-026', 6, 1, 2560.00, 'completed'),
('ORD-2024-027', 7, 2, 1100.75, 'completed'),
('ORD-2024-028', 8, 3, 450.00, 'pending'),
('ORD-2024-029', 9, 4, 3200.00, 'completed'),
('ORD-2024-030', 10, 1, 780.25, 'completed'),
('ORD-2024-031', 11, 2, 920.00, 'completed'),
('ORD-2024-032', 12, 3, 1650.00, 'pending'),
('ORD-2024-033', 13, 4, 340.50, 'completed'),
('ORD-2024-034', 14, 1, 5000.00, 'completed'),
('ORD-2024-035', 15, 2, 890.75, 'cancelled'),
('ORD-2024-036', 16, 3, 1200.00, 'completed'),
('ORD-2024-037', 17, 4, 670.25, 'completed'),
('ORD-2024-038', 18, 1, 2340.00, 'pending'),
('ORD-2024-039', 19, 2, 1100.00, 'completed'),
('ORD-2024-040', 20, 3, 450.50, 'completed'),
('ORD-2024-041', 1, 4, 3600.00, 'completed'),
('ORD-2024-042', 2, 1, 780.00, 'completed'),
('ORD-2024-043', 3, 2, 920.25, 'pending'),
('ORD-2024-044', 4, 3, 1650.00, 'completed'),
('ORD-2024-045', 5, 4, 340.00, 'completed'),
('ORD-2024-046', 6, 1, 5200.75, 'cancelled'),
('ORD-2024-047', 7, 2, 870.00, 'completed'),
('ORD-2024-048', 8, 3, 1230.00, 'completed'),
('ORD-2024-049', 9, 4, 670.50, 'pending'),
('ORD-2024-050', 10, 1, 2560.00, 'completed'),
('ORD-2024-051', 11, 2, 1100.25, 'completed'),
('ORD-2024-052', 12, 3, 450.00, 'completed'),
('ORD-2024-053', 13, 4, 3200.75, 'pending'),
('ORD-2024-054', 14, 1, 780.00, 'completed'),
('ORD-2024-055', 15, 2, 920.50, 'completed'),
('ORD-2024-056', 16, 3, 1650.00, 'cancelled'),
('ORD-2024-057', 17, 4, 340.25, 'completed'),
('ORD-2024-058', 18, 1, 5100.00, 'completed'),
('ORD-2024-059', 19, 2, 890.75, 'pending'),
('ORD-2024-060', 20, 3, 1200.00, 'completed');

-- Populate tr_store with 15 rows
INSERT INTO tr_store (store_code, store_name, city, province, active) VALUES
('STR-BKK-001', 'Bangkok Central Store', 'Bangkok', 'Bangkok', 1),
('STR-BKK-002', 'Bangkok North Branch', 'Bangkok', 'Bangkok', 1),
('STR-CNX-001', 'Chiang Mai Main', 'Chiang Mai', 'Chiang Mai', 1),
('STR-PKT-001', 'Phuket Resort Store', 'Phuket', 'Phuket', 1),
('STR-KKN-001', 'Khon Kaen Branch', 'Khon Kaen', 'Khon Kaen', 0),
('STR-HYI-001', 'Hat Yai South', 'Hat Yai', 'Songkhla', 1),
('STR-NRT-001', 'Nakhon Ratchasima', 'Nakhon Ratchasima', 'Nakhon Ratchasima', 1),
('STR-UDN-001', 'Udon Thani Branch', 'Udon Thani', 'Udon Thani', 1),
('STR-BKK-003', 'Bangkok East Mall', 'Bangkok', 'Bangkok', 1),
('STR-PTY-001', 'Pattaya Beachfront', 'Pattaya', 'Chonburi', 1),
('STR-BKK-004', 'Bangkok Siam', 'Bangkok', 'Bangkok', 0),
('STR-LPG-001', 'Lampang Store', 'Lampang', 'Lampang', 1),
('STR-SBR-001', 'Samut Prakan', 'Samut Prakan', 'Samut Prakan', 1),
('STR-NPN-001', 'Nakhon Pathom', 'Nakhon Pathom', 'Nakhon Pathom', 1),
('STR-AYT-001', 'Ayutthaya Historic', 'Ayutthaya', 'Phra Nakhon Si Ayutthaya', 1);

-- Also create the sg_alith_sync_fle_tra database as mentioned in SKILL.md (Thailand project)
CREATE DATABASE IF NOT EXISTS sg_alith_sync_fle_tra;
GRANT SELECT ON sg_alith_sync_fle_tra.* TO 'dwuser'@'localhost';

MYSQL_SETUP

echo "MySQL setup complete."

# 3. Create devuser for SSH
useradd -m -s /bin/bash devuser 2>/dev/null || true
echo "devuser:devpass123" | chpasswd

# 4. Configure SSH server for password auth on port 2222
mkdir -p /etc/ssh/sshd_config.d
cat > /etc/ssh/sshd_config.d/datax_mock.conf <<'SSHCONF'
Port 2222
PasswordAuthentication yes
PermitRootLogin no
PubkeyAuthentication yes
SSHCONF

# Generate host keys if not present
ssh-keygen -A 2>/dev/null || true

# Start SSH daemon on port 2222
/usr/sbin/sshd -p 2222 &
sleep 2

# 5. Set up SSH key-based auth for root (so agent can do `ssh datax` without password)
mkdir -p /root/.ssh
ssh-keygen -t rsa -b 2048 -f /root/.ssh/datax_key -N "" -q 2>/dev/null || true

# Copy public key to devuser authorized_keys
mkdir -p /home/devuser/.ssh
cat /root/.ssh/datax_key.pub >> /home/devuser/.ssh/authorized_keys
chmod 700 /home/devuser/.ssh
chmod 600 /home/devuser/.ssh/authorized_keys
chown -R devuser:devuser /home/devuser/.ssh

# 6. Add datax entry to /etc/hosts pointing to localhost
echo "127.0.0.1 datax" >> /etc/hosts

# 7. Create SSH config for root so `ssh datax` works seamlessly
cat > /root/.ssh/config <<'SSHCONFIG'
Host datax
    HostName localhost
    Port 2222
    User devuser
    IdentityFile /root/.ssh/datax_key
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
SSHCONFIG
chmod 600 /root/.ssh/config

# 8. Test SSH connection
echo "Testing SSH connection to datax..."
ssh datax "echo 'SSH to datax works'" && echo "SSH OK" || echo "SSH FAILED"

# 9. Test MySQL connection via SSH
echo "Testing MySQL via SSH..."
ssh datax "mysql -h localhost -u dwuser -p'Dw@2024Secure!' dw -e 'show tables;'" && echo "MySQL via SSH OK" || echo "MySQL via SSH FAILED"

# 10. Write connection info file for agent to reference
cat > /workspace/DATAX_CONNECTION.txt <<'CONNINFO'
# datax 开发机连接信息
# SSH 别名已配置完毕，可直接使用: ssh datax
# MySQL 凭证:
#   用户: dwuser
#   密码: Dw@2024Secure!
#   数据库: dw
# 
# 示例:
#   ssh datax "mysql -u dwuser -p'Dw@2024Secure!' dw -e 'show tables;'"
CONNINFO

echo "=== Setup complete ==="
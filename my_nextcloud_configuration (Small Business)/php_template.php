<?php

/*
 * Nextcloud Primary Configuration File
 * Location: /var/www/nextcloud/config/config.php
 *
 * NOTE: Nextcloud automatically strips standard comments from this main file 
 * during core updates. To keep comments permanently, use split config files 
 * inside /var/www/nextcloud/config/*.config.php
 */

$CONFIG = array (

  // ---------------------------------------------------------------------------
  // Core Security Keys & Identifiers (DO NOT MODIFY MANUALLY)
  // ---------------------------------------------------------------------------
  'passwordsalt' => 'xxxx', // Cryptographic salt used for legacy password hashing algorithms
  'secret' => 'xxxx',       // Secret key used for signing session tokens, CSRF checks, and encryption
  'serverid' => 'xxxx',     // Unique server identifier generated at installation time
  'instanceid' => 'XXXX',   // Unique identifier for this specific Nextcloud deployment

  // ---------------------------------------------------------------------------
  // Network Routing & Domain Whitelisting
  // ---------------------------------------------------------------------------
  // Whitelist of domains and IP addresses allowed to access this instance.
  // Prevents Host Header Injection attacks.
  'trusted_domains' => 
  array (
    0 => 'your tailnet IP',            // Local Tailscale IP address access
    1 => 'XXXX.tailXXXX.ts.net',       // Full Tailscale MagicDNS domain path
  ),

  // URL rewrite parameters to force proper HTTPS links and redirect behaviors
  'overwrite.cli.url' => 'https://XXXX.tailXXXX.ts.net', // Canonical URL used when executing occ commands via CLI
  'overwriteprotocol' => 'https',                       // Enforces HTTPS scheme on all generated internal URLs
  'overwritehost' => 'XXXX.tailXXXX.ts.net',           // Overrides host routing to match the Tailscale DNS identity

  // Reverse Proxy & Header Trust settings
  'trusted_proxies' => 
  array (
    0 => '127.0.0.1', // Trust local Nginx reverse proxy loopback IPv4
    1 => '::1',       // Trust local Nginx reverse proxy loopback IPv6
  ),
  'forwarded_for_headers' => 
  array (
    0 => 'HTTP_X_FORWARDED_FOR', // Header used to determine true remote client IP through Nginx
  ),

  // ---------------------------------------------------------------------------
  // File Storage & Database Infrastructure
  // ---------------------------------------------------------------------------
  'datadirectory' => '/var/nextcloud-data', // Dedicated directory storing user files/blobs outside Web Root
  'version' => '34.0.2.1',                   // Internal Nextcloud codebase version tracking
  'installed' => true,                       // Maintenance flag verifying successful site installation

  // MySQL / MariaDB Relational Database Connections
  'dbtype' => 'mysql',            // Primary relational database backend engine
  'dbname' => 'nextcloud',        // Name of the Nextcloud database instance
  'dbhost' => 'localhost',        // Local socket/loopback host for database daemon
  'dbtableprefix' => 'oc_',       // Prefix added to all core application tables
  'dbuser' => 'XXXX',             // Database administrator/service account username
  'dbpassword' => 'XXXX@Nextcloud', // Database authentication credential
  'mysql.utf8mb4' => true,        // Full UTF-8 support enabling 4-byte Unicode characters (Emoji support)

  // ---------------------------------------------------------------------------
  // Performance Optimization: Memory Caching & File Locking
  // ---------------------------------------------------------------------------
  'memcache.local' => '\\OC\\Memcache\\APCu',  // Local PHP-level memory cache for standard web request velocity
  'memcache.locking' => '\\OC\\Memcache\\Redis', // Distributed lock engine preventing database deadlocks on sync

  // High-performance Unix Domain Socket binding for Redis cache daemon
  'redis' => 
  array (
    'host' => '/run/redis/redis-server.sock', // Path to Unix domain socket file
    'port' => 0,                               // TCP port disabled in favor of lower-latency Unix socket
  ),

  // ---------------------------------------------------------------------------
  // System Maintenance & Regional Localization
  // ---------------------------------------------------------------------------
  'maintenance_window_start' => 2, // Background job window (UTC 02:00 / 05:00 EEST local) for heavy cron tasks
  'maintenance' => false,            // Toggles Maintenance Mode off/on manually or during upgrades
  'default_phone_region' => 'GR',    // ISO 3166-1 country code used to parse regional phone numbers (Greece)
  'config_preset' => 2,              // Nextcloud internal preset configuration profile level

  // Media Previews & Storage Quota Savers
  'preview_max_x' => 512, // Maximum generated image preview width (pixels) to reduce CPU/Disk strain
  'preview_max_y' => 512, // Maximum generated image preview height (pixels) to reduce CPU/Disk strain

  // Session Security & Life Cycle Settings
  'remember_login_cookie_lifetime' => 604800, // Persistent login cookie expiration timeout (7 Days in seconds)
  'session_lifetime' => 86400,                // Idle active web session timeout limit (24 Hours in seconds)
  'session_keepalive' => false,               // Prevents idle session extension via automatic background pinging

  // ---------------------------------------------------------------------------
  // Security Policy & Two-Factor Authentication (2FA)
  // ---------------------------------------------------------------------------
  'twofactor_enforced' => 'true', // Forces 2FA setup across specified permission groups
  'twofactor_enforced_groups' => 
  array (
    0 => 'admin',     // Enforces 2FA for System Administrators
    1 => 'Users',     // Enforces 2FA for Standard Users
    2 => 'guest_app', // Enforces 2FA for Guest Accounts
  ),
  'twofactor_enforced_excluded_groups' => 
  array (
    // Groups explicitly exempted from mandatory 2FA enforcement
  ),

  // ---------------------------------------------------------------------------
  // Mail / SMTP Configuration (Gmail Transport Engine)
  // ---------------------------------------------------------------------------
  'mail_domain' => 'gmail.com',         // Default domain suffix for outgoing notification mailers
  'mail_from_address' => 'XXXX',        // Local-part username address sending notification emails
  'mail_smtpmode' => 'smtp',           // Direct SMTP socket protocol transport engine
  'mail_smtpsecure' => 'ssl',          // Implicit SSL/TLS transport wrapper (Port 465)
  'mail_smtphost' => 'smtp.gmail.com',  // External Google SMTP Relay host
  'mail_smtpport' => '465',            // Secure implicit TLS SMTP transport port
  'mail_sendmailmode' => 'smtp',       // Fallback transport mode overriding local sendmail binary
  'mail_smtpname' => 'XXXX',           // Full Gmail authentication account identity
  'mail_smtppassword' => 'REDACTED',   // Google App Password (REVOKE & REGENERATE IMMEDIATELY)
  'mail_smtpauth' => true,             // Enables standard AUTH LOGIN handshake on remote SMTP server

  // Strict TLS validation options for SMTP sockets
  'mail_smtpstreamoptions' => 
  array (
    'ssl' => 
    array (
      'allow_self_signed' => false, // Rejects unverified self-signed upstream mail certificates
      'verify_peer' => true,        // Enforces full certificate authority chain check on SMTP connection
      'verify_peer_name' => true,   // Matches target hostname explicitly against certificate SAN
    ),
  ),

  // ---------------------------------------------------------------------------
  // Application Overrides & Third-Party Extension Helpers
  // ---------------------------------------------------------------------------
  'app_install_overwrite' => 
  array (
    // Array listing non-standard or legacy apps permitted to run past version gates
  ),

  // Nextcloud Memories High-Performance Photos App Binary Extensions
  'memories.db.triggers.fcu' => true, // Enables database triggers for rapid photo search indexing
  'memories.exiftool' => '/var/www/nextcloud/apps/memories/bin-ext/exiftool-amd64-glibc', // Native binary for fast EXIF metadata parsing
  'memories.vod.path' => '/var/www/nextcloud/apps/memories/bin-ext/go-vod-amd64',           // Native Video-on-Demand transcoding binary
);
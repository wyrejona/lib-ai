#!/usr/bin/env python3
"""
Script to create a WordPress plugin zip file for the AI Chatbot Assistant.
Run this script to generate ai-chatbot-assistant.zip
"""

import os
import zipfile
from datetime import datetime

# Plugin structure with file contents
PLUGIN_FILES = {
    # Main plugin file
    "ai-chatbot-assistant.php": """<?php
/**
 * Plugin Name: AI Chatbot Assistant
 * Plugin URI: https://yourwebsite.com
 * Description: Integrate your custom AI chatbot into WordPress with customizable settings
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL v2 or later
 * Text Domain: ai-chatbot-assistant
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('AI_CHATBOT_VERSION', '1.0.0');
define('AI_CHATBOT_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('AI_CHATBOT_PLUGIN_URL', plugin_dir_url(__FILE__));
define('AI_CHATBOT_PLUGIN_BASENAME', plugin_basename(__FILE__));

// Autoload classes
spl_autoload_register(function ($class) {
    $prefix = 'AI_Chatbot_';
    $base_dir = AI_CHATBOT_PLUGIN_DIR . 'includes/';
    
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }
    
    $relative_class = substr($class, $len);
    $file = $base_dir . 'class-' . str_replace('_', '-', strtolower($relative_class)) . '.php';
    
    if (file_exists($file)) {
        require $file;
    }
});

// Initialize the plugin
function ai_chatbot_init() {
    $plugin = new AI_Chatbot_Init();
    $plugin->run();
}
add_action('plugins_loaded', 'ai_chatbot_init');

// Activation hook
register_activation_hook(__FILE__, function() {
    require_once AI_CHATBOT_PLUGIN_DIR . 'includes/class-ai-chatbot-init.php';
    AI_Chatbot_Init::activate();
});

// Deactivation hook
register_deactivation_hook(__FILE__, function() {
    require_once AI_CHATBOT_PLUGIN_DIR . 'includes/class-ai-chatbot-init.php';
    AI_Chatbot_Init::deactivate();
});
""",

    # includes/class-ai-chatbot-init.php
    "includes/class-ai-chatbot-init.php": """<?php
class AI_Chatbot_Init {
    
    public function run() {
        $this->load_dependencies();
        $this->set_locale();
        $this->define_admin_hooks();
        $this->define_public_hooks();
    }
    
    private function load_dependencies() {
        require_once AI_CHATBOT_PLUGIN_DIR . 'includes/class-ai-chatbot-admin.php';
        require_once AI_CHATBOT_PLUGIN_DIR . 'includes/class-ai-chatbot-frontend.php';
        require_once AI_CHATBOT_PLUGIN_DIR . 'includes/class-ai-chatbot-ajax.php';
    }
    
    private function set_locale() {
        load_plugin_textdomain(
            'ai-chatbot-assistant',
            false,
            dirname(AI_CHATBOT_PLUGIN_BASENAME) . '/languages/'
        );
    }
    
    private function define_admin_hooks() {
        $admin = new AI_Chatbot_Admin();
        add_action('admin_menu', array($admin, 'add_admin_menu'));
        add_action('admin_init', array($admin, 'register_settings'));
        add_action('admin_enqueue_scripts', array($admin, 'enqueue_admin_scripts'));
    }
    
    private function define_public_hooks() {
        $frontend = new AI_Chatbot_Frontend();
        add_action('wp_enqueue_scripts', array($frontend, 'enqueue_public_scripts'));
        add_action('wp_footer', array($frontend, 'display_chat_widget'));
        
        $ajax = new AI_Chatbot_Ajax();
        add_action('wp_ajax_send_chat_message', array($ajax, 'send_message'));
        add_action('wp_ajax_nopriv_send_chat_message', array($ajax, 'send_message'));
    }
    
    public static function activate() {
        // Default settings
        $defaults = array(
            'api_url' => 'http://41.89.240.119:8000/chat',
            'welcome_message' => 'Hi buddy, I am your AI assistant, how may I help you today?',
            'position' => 'bottom-right',
            'avatar_url' => AI_CHATBOT_PLUGIN_URL . 'assets/images/default-avatar.png',
            'enable_chat' => '1',
            'chat_title' => 'AI Assistant',
            'primary_color' => '#3a86ff',
            'text_color' => '#ffffff',
            'font_size' => '14',
            'auto_open' => '0',
            'show_on_mobile' => '1',
            'delay_seconds' => '3'
        );
        
        foreach ($defaults as $key => $value) {
            if (get_option('ai_chatbot_' . $key) === false) {
                add_option('ai_chatbot_' . $key, $value);
            }
        }
    }
    
    public static function deactivate() {
        // Clean up if needed
    }
}
""",

    # includes/class-ai-chatbot-admin.php
    "includes/class-ai-chatbot-admin.php": """<?php
class AI_Chatbot_Admin {
    
    public function add_admin_menu() {
        add_menu_page(
            'AI Chatbot Settings',
            'AI Chatbot',
            'manage_options',
            'ai-chatbot-settings',
            array($this, 'display_settings_page'),
            'dashicons-format-chat',
            30
        );
        
        add_submenu_page(
            'ai-chatbot-settings',
            'Settings',
            'Settings',
            'manage_options',
            'ai-chatbot-settings',
            array($this, 'display_settings_page')
        );
    }
    
    public function display_settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <form method="post" action="options.php" enctype="multipart/form-data">
                <?php
                settings_fields('ai_chatbot_settings');
                do_settings_sections('ai-chatbot-settings');
                submit_button('Save Settings');
                ?>
            </form>
            
            <div class="chatbot-preview">
                <h3>Live Preview</h3>
                <div id="chatbot-preview-container">
                    <!-- Preview will be loaded via JavaScript -->
                </div>
            </div>
        </div>
        <?php
    }
    
    public function register_settings() {
        // General Settings
        add_settings_section(
            'ai_chatbot_general',
            'General Settings',
            null,
            'ai-chatbot-settings'
        );
        
        add_settings_field(
            'ai_chatbot_api_url',
            'API Endpoint URL',
            array($this, 'api_url_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_general'
        );
        
        add_settings_field(
            'ai_chatbot_enable_chat',
            'Enable Chatbot',
            array($this, 'enable_chat_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_general'
        );
        
        // Appearance Settings
        add_settings_section(
            'ai_chatbot_appearance',
            'Appearance Settings',
            null,
            'ai-chatbot-settings'
        );
        
        add_settings_field(
            'ai_chatbot_position',
            'Chat Widget Position',
            array($this, 'position_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_appearance'
        );
        
        add_settings_field(
            'ai_chatbot_avatar',
            'Chatbot Avatar',
            array($this, 'avatar_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_appearance'
        );
        
        add_settings_field(
            'ai_chatbot_chat_title',
            'Chat Title',
            array($this, 'chat_title_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_appearance'
        );
        
        add_settings_field(
            'ai_chatbot_primary_color',
            'Primary Color',
            array($this, 'color_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_appearance',
            array('field' => 'primary_color')
        );
        
        add_settings_field(
            'ai_chatbot_text_color',
            'Text Color',
            array($this, 'color_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_appearance',
            array('field' => 'text_color')
        );
        
        // Behavior Settings
        add_settings_section(
            'ai_chatbot_behavior',
            'Behavior Settings',
            null,
            'ai-chatbot-settings'
        );
        
        add_settings_field(
            'ai_chatbot_welcome_message',
            'Welcome Message',
            array($this, 'welcome_message_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_behavior'
        );
        
        add_settings_field(
            'ai_chatbot_auto_open',
            'Auto Open on Page Load',
            array($this, 'auto_open_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_behavior'
        );
        
        add_settings_field(
            'ai_chatbot_delay_seconds',
            'Auto Open Delay (seconds)',
            array($this, 'delay_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_behavior'
        );
        
        add_settings_field(
            'ai_chatbot_show_on_mobile',
            'Show on Mobile Devices',
            array($this, 'mobile_callback'),
            'ai-chatbot-settings',
            'ai_chatbot_behavior'
        );
        
        // Register all settings
        $settings = array(
            'api_url',
            'enable_chat',
            'position',
            'avatar_url',
            'chat_title',
            'primary_color',
            'text_color',
            'welcome_message',
            'auto_open',
            'delay_seconds',
            'show_on_mobile',
            'font_size'
        );
        
        foreach ($settings as $setting) {
            register_setting('ai_chatbot_settings', 'ai_chatbot_' . $setting);
        }
    }
    
    public function api_url_callback() {
        $value = get_option('ai_chatbot_api_url', 'http://41.89.240.119:8000/chat');
        echo '<input type="url" class="regular-text" name="ai_chatbot_api_url" value="' . esc_attr($value) . '" placeholder="http://your-api-endpoint.com/chat">';
        echo '<p class="description">Enter the full URL to your AI chat API endpoint</p>';
    }
    
    public function enable_chat_callback() {
        $value = get_option('ai_chatbot_enable_chat', '1');
        echo '<label><input type="checkbox" name="ai_chatbot_enable_chat" value="1" ' . checked('1', $value, false) . '> Enable chatbot on website</label>';
    }
    
    public function position_callback() {
        $value = get_option('ai_chatbot_position', 'bottom-right');
        $positions = array(
            'bottom-right' => 'Bottom Right',
            'bottom-left' => 'Bottom Left',
            'floating' => 'Floating (center right)'
        );
        
        echo '<select name="ai_chatbot_position">';
        foreach ($positions as $key => $label) {
            echo '<option value="' . esc_attr($key) . '" ' . selected($value, $key, false) . '>' . esc_html($label) . '</option>';
        }
        echo '</select>';
    }
    
    public function avatar_callback() {
        $avatar_url = get_option('ai_chatbot_avatar_url', AI_CHATBOT_PLUGIN_URL . 'assets/images/default-avatar.png');
        echo '<div class="avatar-upload">';
        echo '<img id="avatar-preview" src="' . esc_url($avatar_url) . '" style="width: 100px; height: 100px; border-radius: 50%; margin-bottom: 10px;">';
        echo '<input type="hidden" id="ai_chatbot_avatar_url" name="ai_chatbot_avatar_url" value="' . esc_url($avatar_url) . '">';
        echo '<input type="button" class="button" value="Upload Avatar" onclick="uploadAvatar()">';
        echo '<p class="description">Upload or select an image for the chatbot avatar</p>';
        echo '</div>';
    }
    
    public function chat_title_callback() {
        $value = get_option('ai_chatbot_chat_title', 'AI Assistant');
        echo '<input type="text" class="regular-text" name="ai_chatbot_chat_title" value="' . esc_attr($value) . '">';
    }
    
    public function color_callback($args) {
        $field = $args['field'];
        $value = get_option('ai_chatbot_' . $field, $field === 'primary_color' ? '#3a86ff' : '#ffffff');
        echo '<input type="color" name="ai_chatbot_' . $field . '" value="' . esc_attr($value) . '">';
    }
    
    public function welcome_message_callback() {
        $value = get_option('ai_chatbot_welcome_message', 'Hi buddy, I am your AI assistant, how may I help you today?');
        echo '<textarea name="ai_chatbot_welcome_message" rows="3" cols="50" class="large-text">' . esc_textarea($value) . '</textarea>';
    }
    
    public function auto_open_callback() {
        $value = get_option('ai_chatbot_auto_open', '0');
        echo '<label><input type="checkbox" name="ai_chatbot_auto_open" value="1" ' . checked('1', $value, false) . '> Automatically open chat on page load</label>';
    }
    
    public function delay_callback() {
        $value = get_option('ai_chatbot_delay_seconds', '3');
        echo '<input type="number" min="0" max="60" name="ai_chatbot_delay_seconds" value="' . esc_attr($value) . '"> seconds';
    }
    
    public function mobile_callback() {
        $value = get_option('ai_chatbot_show_on_mobile', '1');
        echo '<label><input type="checkbox" name="ai_chatbot_show_on_mobile" value="1" ' . checked('1', $value, false) . '> Show chatbot on mobile devices</label>';
    }
    
    public function enqueue_admin_scripts($hook) {
        if ($hook !== 'toplevel_page_ai-chatbot-settings') {
            return;
        }
        
        wp_enqueue_media();
        wp_enqueue_style('ai-chatbot-admin', AI_CHATBOT_PLUGIN_URL . 'assets/css/admin.css', array(), AI_CHATBOT_VERSION);
        wp_enqueue_script('ai-chatbot-admin', AI_CHATBOT_PLUGIN_URL . 'assets/js/admin.js', array('jquery'), AI_CHATBOT_VERSION, true);
        
        wp_localize_script('ai-chatbot-admin', 'ai_chatbot_admin', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('ai_chatbot_admin_nonce'),
            'plugin_url' => AI_CHATBOT_PLUGIN_URL
        ));
    }
}
""",

    # includes/class-ai-chatbot-frontend.php
    "includes/class-ai-chatbot-frontend.php": """<?php
class AI_Chatbot_Frontend {
    
    public function enqueue_public_scripts() {
        if (!get_option('ai_chatbot_enable_chat', '1')) {
            return;
        }
        
        wp_enqueue_style('ai-chatbot-frontend', AI_CHATBOT_PLUGIN_URL . 'assets/css/frontend.css', array(), AI_CHATBOT_VERSION);
        wp_enqueue_script('ai-chatbot-frontend', AI_CHATBOT_PLUGIN_URL . 'assets/js/frontend.js', array('jquery'), AI_CHATBOT_VERSION, true);
        
        $settings = array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'api_url' => get_option('ai_chatbot_api_url', 'http://41.89.240.119:8000/chat'),
            'welcome_message' => get_option('ai_chatbot_welcome_message', 'Hi buddy, I am your AI assistant, how may I help you today?'),
            'position' => get_option('ai_chatbot_position', 'bottom-right'),
            'avatar_url' => get_option('ai_chatbot_avatar_url', AI_CHATBOT_PLUGIN_URL . 'assets/images/default-avatar.png'),
            'chat_title' => get_option('ai_chatbot_chat_title', 'AI Assistant'),
            'primary_color' => get_option('ai_chatbot_primary_color', '#3a86ff'),
            'text_color' => get_option('ai_chatbot_text_color', '#ffffff'),
            'auto_open' => get_option('ai_chatbot_auto_open', '0') === '1',
            'delay_seconds' => intval(get_option('ai_chatbot_delay_seconds', '3')),
            'show_on_mobile' => get_option('ai_chatbot_show_on_mobile', '1') === '1',
            'nonce' => wp_create_nonce('ai_chatbot_nonce')
        );
        
        wp_localize_script('ai-chatbot-frontend', 'ai_chatbot_settings', $settings);
    }
    
    public function display_chat_widget() {
        if (!get_option('ai_chatbot_enable_chat', '1')) {
            return;
        }
        
        $show_on_mobile = get_option('ai_chatbot_show_on_mobile', '1') === '1';
        $is_mobile = wp_is_mobile();
        
        if (!$show_on_mobile && $is_mobile) {
            return;
        }
        
        include AI_CHATBOT_PLUGIN_DIR . 'templates/chat-widget.php';
    }
}
""",

    # includes/class-ai-chatbot-ajax.php
    "includes/class-ai-chatbot-ajax.php": """<?php
class AI_Chatbot_Ajax {
    
    public function send_message() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'ai_chatbot_nonce')) {
            wp_die('Security check failed');
        }
        
        $message = sanitize_text_field($_POST['message']);
        $api_url = get_option('ai_chatbot_api_url', 'http://41.89.240.119:8000/chat');
        
        // Prepare the request to your AI API
        $response = wp_remote_post($api_url, array(
            'timeout' => 30,
            'body' => json_encode(array('message' => $message)),
            'headers' => array('Content-Type' => 'application/json')
        ));
        
        if (is_wp_error($response)) {
            wp_send_json_error(array('message' => 'Sorry, I am having trouble connecting right now.'));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (isset($data['response'])) {
            wp_send_json_success(array('message' => $data['response']));
        } else {
            wp_send_json_error(array('message' => 'Sorry, I could not process your request.'));
        }
    }
}
""",

    # templates/chat-widget.php
    "templates/chat-widget.php": """<?php
/**
 * Chat widget template
 */
?>
<div id="ai-chatbot-widget" class="ai-chatbot-widget" style="display: none;">
    <div class="ai-chatbot-header">
        <div class="ai-chatbot-avatar">
            <img src="<?php echo esc_url(get_option('ai_chatbot_avatar_url', AI_CHATBOT_PLUGIN_URL . 'assets/images/default-avatar.png')); ?>" alt="AI Assistant">
        </div>
        <div class="ai-chatbot-info">
            <h3 class="ai-chatbot-title"><?php echo esc_html(get_option('ai_chatbot_chat_title', 'AI Assistant')); ?></h3>
            <span class="ai-chatbot-status">Online</span>
        </div>
        <button class="ai-chatbot-minimize">−</button>
        <button class="ai-chatbot-close">×</button>
    </div>
    
    <div class="ai-chatbot-body">
        <div class="ai-chatbot-messages">
            <div class="ai-chatbot-welcome-message">
                <?php echo esc_html(get_option('ai_chatbot_welcome_message', 'Hi buddy, I am your AI assistant, how may I help you today?')); ?>
            </div>
        </div>
    </div>
    
    <div class="ai-chatbot-footer">
        <div class="ai-chatbot-input-container">
            <input type="text" class="ai-chatbot-input" placeholder="Type your message here..." maxlength="500">
            <button class="ai-chatbot-send">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        </div>
    </div>
</div>

<button id="ai-chatbot-toggle" class="ai-chatbot-toggle">
    <div class="ai-chatbot-toggle-avatar">
        <img src="<?php echo esc_url(get_option('ai_chatbot_avatar_url', AI_CHATBOT_PLUGIN_URL . 'assets/images/default-avatar.png')); ?>" alt="AI Assistant">
    </div>
</button>
""",

    # assets/css/frontend.css
    "assets/css/frontend.css": """.ai-chatbot-widget {
    position: fixed;
    width: 380px;
    height: 600px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 5px 40px rgba(0, 0, 0, 0.16);
    display: flex;
    flex-direction: column;
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    overflow: hidden;
}

.ai-chatbot-widget.bottom-right {
    bottom: 100px;
    right: 30px;
}

.ai-chatbot-widget.bottom-left {
    bottom: 100px;
    left: 30px;
}

.ai-chatbot-widget.floating {
    bottom: 50%;
    right: 30px;
    transform: translateY(50%);
}

.ai-chatbot-header {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    background: var(--ai-primary-color, #3a86ff);
    color: var(--ai-text-color, #ffffff);
}

.ai-chatbot-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    overflow: hidden;
    margin-right: 12px;
    border: 2px solid rgba(255, 255, 255, 0.3);
}

.ai-chatbot-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.ai-chatbot-info {
    flex: 1;
}

.ai-chatbot-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
}

.ai-chatbot-status {
    font-size: 12px;
    opacity: 0.9;
}

.ai-chatbot-minimize,
.ai-chatbot-close {
    background: none;
    border: none;
    color: inherit;
    font-size: 24px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    opacity: 0.8;
    transition: opacity 0.2s;
}

.ai-chatbot-minimize:hover,
.ai-chatbot-close:hover {
    opacity: 1;
}

.ai-chatbot-body {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background: #f8f9fa;
}

.ai-chatbot-messages {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.ai-chatbot-welcome-message {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border-top-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    font-size: 14px;
    line-height: 1.5;
}

.ai-chatbot-message {
    padding: 12px 16px;
    border-radius: 12px;
    max-width: 80%;
    line-height: 1.5;
    font-size: 14px;
}

.ai-chatbot-user-message {
    background: var(--ai-primary-color, #3a86ff);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}

.ai-chatbot-bot-message {
    background: white;
    color: #333;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.ai-chatbot-typing-indicator {
    background: white;
    padding: 12px 16px;
    border-radius: 12px;
    border-bottom-left-radius: 4px;
    align-self: flex-start;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.ai-chatbot-typing-dots {
    display: flex;
    gap: 4px;
}

.ai-chatbot-typing-dots span {
    width: 8px;
    height: 8px;
    background: #ccc;
    border-radius: 50%;
    animation: typing-dot 1.4s infinite ease-in-out both;
}

.ai-chatbot-typing-dots span:nth-child(1) {
    animation-delay: -0.32s;
}

.ai-chatbot-typing-dots span:nth-child(2) {
    animation-delay: -0.16s;
}

@keyframes typing-dot {
    0%, 80%, 100% {
        transform: scale(0.8);
        opacity: 0.5;
    }
    40% {
        transform: scale(1);
        opacity: 1;
    }
}

.ai-chatbot-footer {
    padding: 20px;
    border-top: 1px solid #e9ecef;
    background: white;
}

.ai-chatbot-input-container {
    display: flex;
    gap: 8px;
    align-items: center;
}

.ai-chatbot-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #e0e0e0;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}

.ai-chatbot-input:focus {
    border-color: var(--ai-primary-color, #3a86ff);
}

.ai-chatbot-send {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    background: var(--ai-primary-color, #3a86ff);
    border: none;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
}

.ai-chatbot-send:hover {
    background: var(--ai-primary-color-dark, #2a76ef);
}

.ai-chatbot-toggle {
    position: fixed;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: var(--ai-primary-color, #3a86ff);
    border: none;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    z-index: 999998;
    transition: transform 0.3s, box-shadow 0.3s;
}

.ai-chatbot-toggle:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.25);
}

.ai-chatbot-toggle.bottom-right {
    bottom: 20px;
    right: 20px;
}

.ai-chatbot-toggle.bottom-left {
    bottom: 20px;
    left: 20px;
}

.ai-chatbot-toggle.floating {
    bottom: 50%;
    right: 20px;
    transform: translateY(50%);
}

.ai-chatbot-toggle-avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid rgba(255, 255, 255, 0.3);
}

.ai-chatbot-toggle-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .ai-chatbot-widget {
        width: 100%;
        height: 100%;
        bottom: 0;
        right: 0;
        border-radius: 0;
    }
    
    .ai-chatbot-widget.floating {
        transform: none;
    }
    
    .ai-chatbot-toggle {
        width: 56px;
        height: 56px;
    }
    
    .ai-chatbot-toggle-avatar {
        width: 46px;
        height: 46px;
    }
}

/* Animation */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.ai-chatbot-widget {
    animation: slideIn 0.3s ease-out;
}
""",

    # assets/css/admin.css
    "assets/css/admin.css": """.chatbot-preview {
    margin-top: 30px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.chatbot-preview h3 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #23282d;
}

#chatbot-preview-container {
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.avatar-upload img {
    border: 2px solid #0073aa;
}

.form-table th {
    padding: 20px 10px 20px 0;
    width: 200px;
}

.form-table td {
    padding: 15px 10px;
}

input[type="color"] {
    width: 50px;
    height: 30px;
    padding: 0;
    border: 1px solid #8c8f94;
    border-radius: 4px;
}

input[type="color"]::-webkit-color-swatch-wrapper {
    padding: 0;
}

input[type="color"]::-webkit-color-swatch {
    border: none;
    border-radius: 3px;
}

textarea.large-text {
    min-height: 80px;
}

input.regular-text {
    width: 100%;
    max-width: 400px;
}

.wrap h1 {
    color: #23282d;
    margin-bottom: 20px;
}
""",

    # assets/js/frontend.js
    "assets/js/frontend.js": """(function($) {
    'use strict';
    
    const settings = window.ai_chatbot_settings;
    
    class Chatbot {
        constructor() {
            this.widget = $('#ai-chatbot-widget');
            this.toggle = $('#ai-chatbot-toggle');
            this.messagesContainer = $('.ai-chatbot-messages');
            this.input = $('.ai-chatbot-input');
            this.sendButton = $('.ai-chatbot-send');
            this.minimizeButton = $('.ai-chatbot-minimize');
            this.closeButton = $('.ai-chatbot-close');
            this.isOpen = false;
            this.isMobile = window.innerWidth <= 768;
            
            this.init();
        }
        
        init() {
            this.applyPosition();
            this.applyColors();
            this.bindEvents();
            
            if (settings.auto_open && !this.isMobile) {
                setTimeout(() => {
                    this.open();
                }, settings.delay_seconds * 1000);
            }
        }
        
        applyPosition() {
            this.widget.addClass(settings.position);
            this.toggle.addClass(settings.position);
            
            if (settings.position === 'floating') {
                this.widget.css({
                    'bottom': '50%',
                    'right': '30px',
                    'transform': 'translateY(50%)'
                });
                this.toggle.css({
                    'bottom': '50%',
                    'right': '20px',
                    'transform': 'translateY(50%)'
                });
            }
        }
        
        applyColors() {
            document.documentElement.style.setProperty('--ai-primary-color', settings.primary_color);
            document.documentElement.style.setProperty('--ai-text-color', settings.text_color);
            
            if (settings.position === 'floating') {
                this.toggle.css('background-color', settings.primary_color);
            }
        }
        
        bindEvents() {
            this.toggle.on('click', () => this.toggleChat());
            this.minimizeButton.on('click', () => this.close());
            this.closeButton.on('click', () => this.close());
            this.sendButton.on('click', () => this.sendMessage());
            this.input.on('keypress', (e) => {
                if (e.which === 13) {
                    this.sendMessage();
                }
            });
            
            // Close on click outside
            $(document).on('click', (e) => {
                if (this.isOpen && 
                    !$(e.target).closest('#ai-chatbot-widget').length && 
                    !$(e.target).closest('#ai-chatbot-toggle').length) {
                    this.close();
                }
            });
        }
        
        toggleChat() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        }
        
        open() {
            this.widget.fadeIn(200);
            this.toggle.fadeOut(200);
            this.isOpen = true;
            this.input.focus();
        }
        
        close() {
            this.widget.fadeOut(200);
            this.toggle.fadeIn(200);
            this.isOpen = false;
        }
        
        sendMessage() {
            const message = this.input.val().trim();
            if (!message) return;
            
            this.addMessage(message, 'user');
            this.input.val('');
            
            this.showTypingIndicator();
            
            $.ajax({
                url: settings.ajax_url,
                type: 'POST',
                data: {
                    action: 'send_chat_message',
                    message: message,
                    nonce: settings.nonce
                },
                success: (response) => {
                    this.removeTypingIndicator();
                    if (response.success) {
                        this.addMessage(response.data.message, 'bot');
                    } else {
                        this.addMessage('Sorry, there was an error processing your request.', 'bot');
                    }
                },
                error: () => {
                    this.removeTypingIndicator();
                    this.addMessage('Sorry, I am having trouble connecting right now. Please try again later.', 'bot');
                }
            });
        }
        
        addMessage(text, sender) {
            const messageClass = sender === 'user' ? 'ai-chatbot-user-message' : 'ai-chatbot-bot-message';
            const messageHtml = `
                <div class="ai-chatbot-message ${messageClass}">
                    <div class="ai-chatbot-message-content">${this.escapeHtml(text)}</div>
                </div>
            `;
            
            this.messagesContainer.append(messageHtml);
            this.scrollToBottom();
        }
        
        showTypingIndicator() {
            const typingHtml = `
                <div class="ai-chatbot-typing-indicator">
                    <div class="ai-chatbot-typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            
            this.messagesContainer.append(typingHtml);
            this.scrollToBottom();
        }
        
        removeTypingIndicator() {
            $('.ai-chatbot-typing-indicator').remove();
        }
        
        scrollToBottom() {
            this.messagesContainer.scrollTop(this.messagesContainer[0].scrollHeight);
        }
        
        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    }
    
    // Initialize when DOM is ready
    $(document).ready(() => {
        new Chatbot();
    });
    
})(jQuery);
""",

    # assets/js/admin.js
    "assets/js/admin.js": """(function($) {
    'use strict';
    
    function uploadAvatar() {
        const frame = wp.media({
            title: 'Select Chatbot Avatar',
            button: {
                text: 'Use this image'
            },
            multiple: false
        });
        
        frame.on('select', function() {
            const attachment = frame.state().get('selection').first().toJSON();
            $('#avatar-preview').attr('src', attachment.url);
            $('#ai_chatbot_avatar_url').val(attachment.url);
        });
        
        frame.open();
    }
    
    function updatePreview() {
        // Update live preview based on settings
        const position = $('select[name="ai_chatbot_position"]').val();
        const primaryColor = $('input[name="ai_chatbot_primary_color"]').val();
        const textColor = $('input[name="ai_chatbot_text_color"]').val();
        const avatarUrl = $('#ai_chatbot_avatar_url').val();
        
        $('#chatbot-preview-container').html(`
            <div class="preview-widget" style="
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                max-width: 300px;
                margin: 0 auto;
            ">
                <div class="preview-header" style="
                    background: ${primaryColor};
                    color: ${textColor};
                    padding: 15px;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                ">
                    <img src="${avatarUrl}" alt="Preview" style="
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        border: 2px solid rgba(255,255,255,0.3);
                    ">
                    <div>
                        <div style="font-weight: bold;">${$('input[name="ai_chatbot_chat_title"]').val()}</div>
                        <div style="font-size: 12px; opacity: 0.9;">Online</div>
                    </div>
                </div>
                <div class="preview-body" style="
                    padding: 15px;
                    background: #f8f9fa;
                    border-radius: 0 0 8px 8px;
                ">
                    <div style="
                        background: white;
                        padding: 10px;
                        border-radius: 8px;
                        font-size: 14px;
                        margin-bottom: 10px;
                    ">${$('textarea[name="ai_chatbot_welcome_message"]').val()}</div>
                    <div style="
                        display: flex;
                        gap: 10px;
                    ">
                        <input type="text" placeholder="Type message..." style="
                            flex: 1;
                            padding: 8px 12px;
                            border: 1px solid #ddd;
                            border-radius: 20px;
                            font-size: 14px;
                        " disabled>
                        <button style="
                            width: 36px;
                            height: 36px;
                            border-radius: 50%;
                            background: ${primaryColor};
                            border: none;
                            color: white;
                            cursor: pointer;
                        ">→</button>
                    </div>
                </div>
            </div>
            <p style="text-align: center; margin-top: 10px; color: #666;">
                Position: ${position} | Colors will update in real-time
            </p>
        `);
    }
    
    $(document).ready(function() {
        window.uploadAvatar = uploadAvatar;
        
        // Update preview when settings change
        $('input, select, textarea').on('change input', function() {
            updatePreview();
        });
        
        // Initial preview
        updatePreview();
    });
    
})(jQuery);
""",

    # Default avatar image (base64 encoded)
    "assets/images/default-avatar.png": """iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAAF
    +0lEQVR4nO2aa2xURRTHf6Vt6ba0wC4PW1hgl02p0IAtUh5SAg0fJI2JiKChfFCTikYTRSNS
    UIkaNUGJEl8xajQqNYZG4wONfPCDxg/GxEeM+kGNiTEaMfGjMRrjA42J8cNp7+7svXNn7r13
    t9tC7i+T3Zk5c+7/nDlzzpzHDAwcJf+P0CqXShL9wGEgBUwCHwN3AJX5Eiy44n7gNtPPKeCA
    +P8acG2+xAqq+AIZ2XvAqAy/In7fAHyYS7G8C5LQdpT6v1b8bgD2Ab0Z8p0EZjT87wI6gJfl
    rBPI9VdgLbAoq+w2g2xvGsVi3PuAeZn7H5Jr7Bmfyw1hN0a1CphR7t8OrC6k8Eq8AVwCDAB/
    AV8AK4AJl/wW8IJyv9wlfwJ4HJh2yR0Dtgh2LAA5fxaCkg/4EBgHtgrl5oFVwKtif4eJX4Gu
    DK8h4C7gQrl/p/DVl0q2Fw0uTACfA1Ue8u8BVxfTABNKpVIBXAC8J/cPA5eJ368AF7l49IrM
    WAF8CpQAzcCDmfvPCOapMmPlfZ6h8I+AnhDyr0I4z2IY4B3gVmnEduAJ4bT3gClgF/AuUAv8
    LlOqC5gD7pb7Y8CtwKfyXZ0A1sv/1wN/atq+3oHPIeBp7f6we/9uKKYBiuqAHqAqQ/4g8Aqw
    X+6vl/vzrq30uMtfzdL/hNx/RWvgJuCkXN+Qa9e15OQYcIs3H9cADcBgIQwQ2qncA15QyH+g
    5A3J/WG5rvKkfV/+P4JH6nXhcZb8b/YwD0h9AH4B7gO+g+CdYFfH9oP7o0L5DrmOK/lDwj8P
    LMdrz/2eDuTPF57r8GxrG54W7sBjWw+cIfL79wC/I7RDeRE4F3gWmEfEmf9nDB6fCP9aYDvx
    H/9BoBWvL6jBs6d7gUo8c3MHMEayjxLYqXvM5B/A/WiUOQfoA+4EHgNuB+4DdgJNwEI0zrEQ
    OJX/X7/6/s8xr2I4waI5wIIDpHbIQ+EX8ZjF/T/w/wmOzjGv/OE/5vz8mOvl16MAAAAASUVO
    RK5CYII=""",

    # uninstall.php
    "uninstall.php": """<?php
/**
 * Uninstall script for AI Chatbot Assistant
 * 
 * This file is called when the plugin is deleted from WordPress.
 * It removes all plugin options from the database.
 */

// If uninstall is not called from WordPress, exit
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

// Delete all plugin options
$options = array(
    'ai_chatbot_api_url',
    'ai_chatbot_welcome_message',
    'ai_chatbot_position',
    'ai_chatbot_avatar_url',
    'ai_chatbot_enable_chat',
    'ai_chatbot_chat_title',
    'ai_chatbot_primary_color',
    'ai_chatbot_text_color',
    'ai_chatbot_font_size',
    'ai_chatbot_auto_open',
    'ai_chatbot_show_on_mobile',
    'ai_chatbot_delay_seconds'
);

foreach ($options as $option) {
    delete_option($option);
}

// If using multisite, delete from all sites
if (is_multisite()) {
    $sites = get_sites();
    foreach ($sites as $site) {
        switch_to_blog($site->blog_id);
        foreach ($options as $option) {
            delete_option($option);
        }
        restore_current_blog();
    }
}
""",

    # README.txt
    "README.txt": """=== AI Chatbot Assistant ===
Contributors: yourname
Tags: chatbot, ai, assistant, chat, widget
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 1.0.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Integrate your custom AI chatbot into WordPress with customizable settings.

== Description ==

AI Chatbot Assistant allows you to integrate your custom AI chatbot API into your WordPress website with a beautiful, customizable chat widget.

= Features =

* Connect to your AI API endpoint
* Customizable chatbot avatar
* Multiple position options (bottom-right, bottom-left, floating)
* Customizable welcome message
* Color scheme customization
* Mobile-responsive design
* Auto-open on page load
* Configurable delay for auto-open
* Option to hide on mobile devices
* Live preview in admin settings

= Installation =

1. Upload the `ai-chatbot-assistant` folder to the `/wp-content/plugins/` directory
2. Activate the plugin through the 'Plugins' menu in WordPress
3. Go to AI Chatbot > Settings to configure your chatbot
4. Set your API endpoint URL and customize the appearance

= Configuration =

1. **API Endpoint URL**: Enter your AI chat API URL (e.g., http://41.89.240.119:8000/chat)
2. **Chatbot Avatar**: Upload or select an image for your chatbot
3. **Position**: Choose where the chat widget appears (bottom-right, bottom-left, or floating)
4. **Welcome Message**: Set the initial greeting message
5. **Colors**: Customize primary and text colors
6. **Behavior**: Configure auto-open, delay, and mobile visibility

= API Integration =

The plugin sends POST requests to your API endpoint with the following JSON format:
{
    "message": "user message here"
}

Your API should respond with JSON in this format:
{
    "response": "chatbot reply here"
}

== Frequently Asked Questions ==

= What API format does the plugin use? =
The plugin sends JSON POST requests to your API endpoint and expects JSON responses.

= Can I customize the chatbot appearance? =
Yes! You can change colors, position, avatar, and welcome message from the settings page.

= Does it work on mobile? =
Yes, the chat widget is fully responsive and works on all devices.

= Can I disable the chatbot on certain pages? =
Currently, the plugin shows the chatbot on all pages. Future updates may include page-specific controls.

== Changelog ==

= 1.0.0 =
* Initial release
* Basic chat functionality
* Admin settings interface
* Customizable appearance
* API integration

== Upgrade Notice ==

= 1.0.0 =
Initial release of AI Chatbot Assistant.
""",
}

def create_plugin_zip():
    """Create a zip file containing the complete WordPress plugin."""
    zip_filename = "ai-chatbot-assistant.zip"
    
    print(f"Creating {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Create directories first
        directories = [
            "includes/",
            "assets/",
            "assets/css/",
            "assets/js/",
            "assets/images/",
            "templates/"
        ]
        
        for directory in directories:
            # Add directory entry to zip
            zipf.writestr(f"ai-chatbot-assistant/{directory}", "")
        
        # Add all files
        for file_path, content in PLUGIN_FILES.items():
            full_path = f"ai-chatbot-assistant/{file_path}"
            
            # Handle base64 encoded image
            if file_path == "assets/images/default-avatar.png":
                import base64
                binary_content = base64.b64decode(content)
                zipf.writestr(full_path, binary_content)
            else:
                zipf.writestr(full_path, content)
            
            print(f"  Added: {file_path}")
    
    print(f"\n✅ Successfully created {zip_filename}")
    print(f"📦 File size: {os.path.getsize(zip_filename) / 1024:.1f} KB")
    print("\n📋 Installation instructions:")
    print("1. Extract the zip file")
    print("2. Upload the 'ai-chatbot-assistant' folder to /wp-content/plugins/")
    print("3. Activate the plugin in WordPress Admin → Plugins")
    print("4. Configure settings at AI Chatbot → Settings")
    print("\n⚙️ Default API URL: http://41.89.240.119:8000/chat")

if __name__ == "__main__":
    create_plugin_zip()

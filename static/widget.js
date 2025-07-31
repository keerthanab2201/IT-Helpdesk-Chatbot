/*
 * IT Helpdesk Widget - Working Implementation
 * This version includes comprehensive debugging and error handling
 */

(function() {
  'use strict';

  console.log('🚀 Widget.js loading...');

  // Configuration
  const config = Object.assign({
    apiUrl: window.location.origin,
    position: 'bottom-right',
    theme: 'dark',
    primaryColor: '#667eea',
    secondaryColor: '#764ba2'
  }, window.HelpdeskWidget || {});

  console.log('📋 Widget config:', config);

  let widgetOpen = false;
  let isMaximized = false;

  // Widget HTML
  const widgetHTML = `
    <div class="helpdesk-widget-container" id="helpdeskWidgetContainer" style="
      position: fixed; 
      bottom: 20px; 
      ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'} 
      z-index: 999999; 
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    ">
      <!-- Chat Button -->
      <button class="helpdesk-chat-button" id="helpdeskChatButton" style="
        width: 60px; 
        height: 60px; 
        border-radius: 50%; 
        background: linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%); 
        border: none; 
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        transition: all 0.3s ease; 
        color: white; 
        font-size: 24px;
        position: relative;
        outline: none;
      ">
        <span id="helpdeskButtonIcon">💬</span>
      </button>
      
      <!-- Chat Container -->
      <div class="helpdesk-chat-container" id="helpdeskChatContainer" style="
        position: absolute; 
        bottom: 80px; 
        ${config.position === 'bottom-left' ? 'left: 0;' : 'right: 0;'} 
        width: 420px; 
        height: 650px; 
        background: #121212; 
        border-radius: 15px; 
        box-shadow: 0 20px 60px rgba(0,0,0,0.5); 
        transform: translateY(20px) scale(0.9); 
        opacity: 0; 
        visibility: hidden; 
        transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); 
        overflow: hidden;
        border: 1px solid #333;
        display: none;
      ">
        <!-- Loading Screen -->
        <div id="helpdeskLoading" style="
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: #121212;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          color: white;
          z-index: 1000;
        ">
          <div style="
            width: 40px;
            height: 40px;
            border: 3px solid #333;
            border-top: 3px solid ${config.primaryColor};
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
          "></div>
          <p style="margin: 0; font-size: 14px; color: #aaa;">Loading chat...</p>
        </div>
        
        <!-- Chat Iframe -->
        <iframe 
          id="helpdeskChatFrame" 
          src="${config.apiUrl}/chat?widget=true" 
          style="
            width: 100%; 
            height: 100%; 
            border: none; 
            border-radius: 15px;
            background: transparent;
          "
          onload="window.helpdeskWidgetLoaded()"
        ></iframe>
        
        <!-- Controls -->
        <div class="helpdesk-controls" id="helpdeskControls" style="
          position: absolute; 
          top: 15px; 
          right: 15px; 
          z-index: 1001; 
          display: flex; 
          gap: 8px;
          opacity: 0;
          transition: opacity 0.3s ease;
        ">
          <button id="helpdeskMaximize" style="
            background: rgba(0,0,0,0.8); 
            color: white; 
            border: none; 
            padding: 8px; 
            border-radius: 50%; 
            cursor: pointer; 
            width: 35px; 
            height: 35px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 16px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
          " title="Maximize">⛶</button>
          <button id="helpdeskClose" style="
            background: rgba(220, 53, 69, 0.9); 
            color: white; 
            border: none; 
            padding: 8px; 
            border-radius: 50%; 
            cursor: pointer; 
            width: 35px; 
            height: 35px; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            font-size: 18px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
          " title="Close">×</button>
        </div>
      </div>
    </div>
  `;

  // CSS Styles
  const widgetCSS = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .helpdesk-chat-button:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 25px rgba(102, 126, 234, 0.8);
    }

    .helpdesk-chat-button:active {
      transform: scale(0.95);
    }

    .helpdesk-chat-container.show {
      display: block !important;
      transform: translateY(0) scale(1);
      opacity: 1;
      visibility: visible;
    }

    .helpdesk-chat-container.show .helpdesk-controls {
      opacity: 1;
    }

    .helpdesk-chat-container:hover .helpdesk-controls {
      opacity: 1;
    }

    .helpdesk-chat-container.maximized {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      border-radius: 0 !important;
      z-index: 1000000;
      transform: none !important;
    }

    .helpdesk-controls button:hover {
      background: rgba(0,0,0,1) !important;
      transform: scale(1.1);
    }

    #helpdeskClose:hover {
      background: rgba(220, 53, 69, 1) !important;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
      .helpdesk-chat-container {
        width: calc(100vw - 40px) !important;
        max-width: 400px !important;
        height: 70vh !important;
        max-height: 600px !important;
      }
      
      .helpdesk-chat-button {
        width: 55px !important;
        height: 55px !important;
        font-size: 22px !important;
      }
    }

    @media (max-width: 480px) {
      .helpdesk-chat-container {
        width: calc(100vw - 20px) !important;
        height: 80vh !important;
        bottom: 70px !important;
      }
    }
  `;

  // Global function for iframe load callback
  window.helpdeskWidgetLoaded = function() {
    console.log('✅ Chat iframe loaded successfully');
    const loading = document.getElementById('helpdeskLoading');
    if (loading) {
      loading.style.display = 'none';
    }
  };

  // Initialize widget
  function initWidget() {
    console.log('🔧 Initializing widget...');

    // Remove any existing widget
    const existing = document.getElementById('helpdeskWidgetContainer');
    if (existing) {
      existing.remove();
      console.log('🗑️ Removed existing widget');
    }

    // Add CSS
    const styleId = 'helpdesk-widget-styles';
    let existingStyle = document.getElementById(styleId);
    if (!existingStyle) {
      const style = document.createElement('style');
      style.id = styleId;
      style.textContent = widgetCSS;
      document.head.appendChild(style);
      console.log('🎨 Added widget styles');
    }

    // Add HTML
    document.body.insertAdjacentHTML('beforeend', widgetHTML);
    console.log('🏗️ Added widget HTML');

    // Setup event listeners
    setupEventListeners();
  }

  function setupEventListeners() {
    console.log('🔗 Setting up event listeners...');

    const chatButton = document.getElementById('helpdeskChatButton');
    const chatContainer = document.getElementById('helpdeskChatContainer');
    const closeButton = document.getElementById('helpdeskClose');
    const maximizeButton = document.getElementById('helpdeskMaximize');

    if (!chatButton) {
      console.error('❌ Chat button not found!');
      return;
    }

    if (!chatContainer) {
      console.error('❌ Chat container not found!');
      return;
    }

    // Chat button click
    chatButton.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      console.log('🖱️ Chat button clicked');
      toggleWidget();
    });

    // Close button click
    if (closeButton) {
      closeButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('🖱️ Close button clicked');
        closeWidget();
      });
    }

    // Maximize button click
    if (maximizeButton) {
      maximizeButton.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('🖱️ Maximize button clicked');
        toggleMaximize();
      });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && widgetOpen) {
        if (isMaximized) {
          toggleMaximize();
        } else {
          closeWidget();
        }
      }
    });

    console.log('✅ Event listeners set up successfully');
  }

  function toggleWidget() {
    console.log('🔄 Toggling widget, current state:', widgetOpen);

    const chatButton = document.getElementById('helpdeskChatButton');
    const chatContainer = document.getElementById('helpdeskChatContainer');
    const buttonIcon = document.getElementById('helpdeskButtonIcon');

    if (!chatButton || !chatContainer || !buttonIcon) {
      console.error('❌ Widget elements not found during toggle');
      return;
    }

    widgetOpen = !widgetOpen;

    if (widgetOpen) {
      console.log('📖 Opening widget');
      chatContainer.classList.add('show');
      buttonIcon.textContent = '×';
      chatButton.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
      
      // Reset iframe if needed
      const iframe = document.getElementById('helpdeskChatFrame');
      if (iframe && !iframe.src.includes('?widget=true')) {
        iframe.src = config.apiUrl + '/chat?widget=true';
      }
    } else {
      console.log('📕 Closing widget');
      chatContainer.classList.remove('show');
      chatContainer.classList.remove('maximized');
      buttonIcon.textContent = '💬';
      chatButton.style.background = `linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%)`;
      document.body.style.overflow = '';
      isMaximized = false;
    }
  }

  function closeWidget() {
    console.log('❌ Closing widget');
    widgetOpen = false;
    isMaximized = false;

    const chatButton = document.getElementById('helpdeskChatButton');
    const chatContainer = document.getElementById('helpdeskChatContainer');
    const buttonIcon = document.getElementById('helpdeskButtonIcon');

    if (chatContainer) {
      chatContainer.classList.remove('show');
      chatContainer.classList.remove('maximized');
    }

    if (buttonIcon) {
      buttonIcon.textContent = '💬';
    }

    if (chatButton) {
      chatButton.style.background = `linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%)`;
    }

    document.body.style.overflow = '';
  }

  function toggleMaximize() {
    console.log('🔍 Toggling maximize, current state:', isMaximized);

    const chatContainer = document.getElementById('helpdeskChatContainer');
    const maximizeButton = document.getElementById('helpdeskMaximize');

    if (!chatContainer || !maximizeButton) {
      console.error('❌ Maximize elements not found');
      return;
    }

    isMaximized = !isMaximized;
    chatContainer.classList.toggle('maximized');

    if (isMaximized) {
      maximizeButton.innerHTML = '⮌';
      maximizeButton.title = 'Restore';
      document.body.style.overflow = 'hidden';
    } else {
      maximizeButton.innerHTML = '⛶';
      maximizeButton.title = 'Maximize';
      document.body.style.overflow = '';
    }
  }

  // Public API
  window.HelpdeskWidget = {
    toggle: toggleWidget,
    close: closeWidget,
    maximize: toggleMaximize,
    open: function() {
      if (!widgetOpen) toggleWidget();
    },
    config: config,
    isOpen: () => widgetOpen,
    isMaximized: () => isMaximized,
    reinit: initWidget
  };

  // Initialize when DOM is ready
  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initWidget);
    } else {
      initWidget();
    }
  }

  // Start initialization
  init();

  console.log('🎉 Widget.js loaded successfully');

})();

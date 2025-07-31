/*
 * IT Helpdesk Widget - Using existing enhanced_chat.html
 */

(function() {
  'use strict';

  // Default configuration
  const defaultConfig = {
    apiUrl: window.location.origin,
    position: 'bottom-right'
  };

  // Merge with user config
  const config = Object.assign({}, defaultConfig, window.HelpdeskWidget || {});
  
  let widgetOpen = false;

  // Widget HTML - Minimal wrapper around your existing chat
  const widgetHTML = `
    <div class="helpdesk-widget" id="helpdeskWidget" style="position: fixed; bottom: 20px; ${config.position === 'bottom-left' ? 'left: 20px;' : 'right: 20px;'} z-index: 10000; font-family: 'Segoe UI', sans-serif;">
      <!-- Floating Chat Button -->
      <button class="widget-trigger" id="widgetTrigger" style="width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.3s ease; color: white; font-size: 24px;">
        💬
      </button>
      
      <!-- Widget Container - Your existing chat interface -->
      <div class="widget-container" id="widgetContainer" style="position: absolute; bottom: 80px; ${config.position === 'bottom-left' ? 'left: 0;' : 'right: 0;'} width: 420px; height: 650px; background: #121212; border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); transform: translateY(20px) scale(0.9); opacity: 0; visibility: hidden; transition: all 0.3s ease; overflow: hidden;">
        
        <!-- Your existing chat interface will be loaded here -->
        <iframe id="chatFrame" src="${config.apiUrl}/chat?widget=true" style="width: 100%; height: 100%; border: none; border-radius: 15px;"></iframe>
        
        <!-- Minimize/Maximize controls overlay -->
        <div class="widget-controls" style="position: absolute; top: 15px; right: 15px; z-index: 1000; display: flex; gap: 8px;">
          <button id="widgetMaximize" style="background: rgba(0,0,0,0.7); color: white; border: none; padding: 8px; border-radius: 50%; cursor: pointer; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-size: 16px;" title="Maximize">⛶</button>
          <button id="widgetClose" style="background: rgba(0,0,0,0.7); color: white; border: none; padding: 8px; border-radius: 50%; cursor: pointer; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-size: 18px;" title="Close">×</button>
        </div>
      </div>
    </div>
  `;

  // Widget CSS
  const widgetCSS = `
    .widget-trigger:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
    }

    .widget-trigger.active {
      background: linear-gradient(135deg, #dc3545, #c82333) !important;
    }

    .widget-container.show {
      transform: translateY(0) scale(1);
      opacity: 1;
      visibility: visible;
    }

    .widget-container.maximized {
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      right: 0 !important;
      bottom: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      border-radius: 0 !important;
      z-index: 20000;
      transform: none !important;
    }

    .widget-controls button:hover {
      background: rgba(0,0,0,0.9) !important;
      transform: scale(1.1);
    }

    /* Responsive */
    @media (max-width: 768px) {
      .widget-container {
        width: calc(100vw - 40px) !important;
        right: 20px !important;
        left: 20px !important;
        height: 80vh !important;
      }
      
      .widget-trigger {
        width: 55px !important;
        height: 55px !important;
        font-size: 22px !important;
      }
    }
  `;

  // Initialize widget
  function init() {
    // Add CSS
    const style = document.createElement('style');
    style.textContent = widgetCSS;
    document.head.appendChild(style);

    // Add HTML
    document.body.insertAdjacentHTML('beforeend', widgetHTML);

    // Setup event listeners
    setupEventListeners();
  }

  function setupEventListeners() {
    const trigger = document.getElementById('widgetTrigger');
    const closeBtn = document.getElementById('widgetClose');
    const maximizeBtn = document.getElementById('widgetMaximize');

    if (trigger) trigger.addEventListener('click', toggleWidget);
    if (closeBtn) closeBtn.addEventListener('click', closeWidget);
    if (maximizeBtn) maximizeBtn.addEventListener('click', toggleMaximize);

    // Escape key to close maximized widget
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        const container = document.getElementById('widgetContainer');
        if (container && container.classList.contains('maximized')) {
          toggleMaximize();
        }
      }
    });
  }

  function toggleWidget() {
    const trigger = document.getElementById('widgetTrigger');
    const container = document.getElementById('widgetContainer');
    
    widgetOpen = !widgetOpen;
    
    if (widgetOpen) {
      container.classList.add('show');
      trigger.classList.add('active');
      trigger.innerHTML = '×';
    } else {
      container.classList.remove('show');
      container.classList.remove('maximized');
      trigger.classList.remove('active');
      trigger.innerHTML = '💬';
      document.body.style.overflow = '';
    }
  }

  function closeWidget() {
    widgetOpen = false;
    const container = document.getElementById('widgetContainer');
    const trigger = document.getElementById('widgetTrigger');
    
    if (container) {
      container.classList.remove('show');
      container.classList.remove('maximized');
    }
    if (trigger) {
      trigger.classList.remove('active');
      trigger.innerHTML = '💬';
    }
    
    document.body.style.overflow = '';
  }

  function toggleMaximize() {
    const container = document.getElementById('widgetContainer');
    const maximizeBtn = document.getElementById('widgetMaximize');
    
    if (container && maximizeBtn) {
      container.classList.toggle('maximized');
      
      if (container.classList.contains('maximized')) {
        maximizeBtn.innerHTML = '⮌';
        maximizeBtn.title = 'Restore';
        document.body.style.overflow = 'hidden';
      } else {
        maximizeBtn.innerHTML = '⛶';
        maximizeBtn.title = 'Maximize';
        document.body.style.overflow = '';
      }
    }
  }

  // Public API
  window.HelpdeskWidget = {
    toggle: toggleWidget,
    close: closeWidget,
    maximize: toggleMaximize,
    config: config
  };

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
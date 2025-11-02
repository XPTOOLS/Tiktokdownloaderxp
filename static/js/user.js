// Track user visit
fetch('/api/track-visit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    page: 'user',
    timestamp: new Date().toISOString()
  })
}).catch(err => console.error('Error tracking visit:', err));

// Check for notifications
checkNotifications();

document.getElementById("downloadBtn").addEventListener("click", downloadVideo);
document.getElementById("tiktokUrl").addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    downloadVideo();
  }
});

// Close notification dialog
document.getElementById("closeDialog").addEventListener("click", closeNotification);
document.getElementById("cancelBtn").addEventListener("click", closeNotification);

// Loading screen
window.addEventListener('load', function() {
  setTimeout(() => {
    document.getElementById('loadingScreen').classList.add('fade-out');
    setTimeout(() => {
      document.getElementById('loadingScreen').style.display = 'none';
    }, 500);
  }, 2000);
});

async function downloadVideo() {
  const tiktokUrl = document.getElementById("tiktokUrl").value.trim();
  const loadingEl = document.getElementById("loading");
  const errorEl = document.getElementById("error");
  const successEl = document.getElementById("success");
  const resultsEl = document.getElementById("results");
  const downloadBtn = document.getElementById("downloadBtn");

  if (!tiktokUrl) {
    showError("Please enter a TikTok URL");
    return;
  }

  if (!isValidTikTokUrl(tiktokUrl)) {
    showError("Please enter a valid TikTok URL");
    return;
  }

  loadingEl.style.display = "flex";
  errorEl.style.display = "none";
  successEl.style.display = "none";
  resultsEl.innerHTML = "";
  downloadBtn.disabled = true;

  try {
    // Track download attempt
    await fetch('/api/track-download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: tiktokUrl,
        timestamp: new Date().toISOString()
      })
    });

    const apiUrl = `https://old-studio-tiktok-down.oldhacker7866.workers.dev/?url=${encodeURIComponent(tiktokUrl)}`;

    const fetchPromise = fetch(apiUrl);
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Request timeout")), 15000)
    );

    const response = await Promise.race([fetchPromise, timeoutPromise]);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    let videoUrl = null;

    // Multiple response format handling
    if (typeof data === "string" && data.startsWith("http")) {
      videoUrl = data;
    } else if (data && data.videoUrl) {
      videoUrl = data.videoUrl;
    } else if (data && data.url) {
      videoUrl = data.url;
    } else if (data && data.download_url) {
      videoUrl = data.download_url;
    } else if (data && data.data && data.data.videoUrl) {
      videoUrl = data.data.videoUrl;
    } else if (data) {
      for (let key in data) {
        if (typeof data[key] === "string" && data[key].startsWith("http")) {
          videoUrl = data[key];
          break;
        }
      }
    }

    if (!videoUrl) {
      throw new Error("No video URL found in response");
    }

    if (!videoUrl.startsWith("http")) {
      videoUrl = "https:" + videoUrl;
    }

    displayVideo(videoUrl);
    loadingEl.style.display = "none";
    downloadBtn.disabled = false;
  } catch (error) {
    console.error("Error:", error);
    loadingEl.style.display = "none";
    downloadBtn.disabled = false;

    if (error.name === "AbortError" || error.message === "Request timeout") {
      showError("Request timeout. Please try again.");
    } else {
      showError("Failed to download video. Please check the URL and try again.");
    }
  }
}

function displayVideo(videoUrl) {
  const resultsEl = document.getElementById("results");
  const videoContainer = document.createElement("div");
  videoContainer.className = "video-container";

  videoContainer.innerHTML = `
    <video class="video-preview" controls>
      <source src="${videoUrl}" type="video/mp4">
      Your browser does not support the video tag.
    </video>
    <br>
    <button class="video-download-btn" onclick="forceDownload('${videoUrl}')">
      <i class="fas fa-download"></i>
      Download Video
    </button>
  `;

  resultsEl.appendChild(videoContainer);
}

async function forceDownload(videoUrl) {
  const downloadBtn = document.querySelector(".video-download-btn");
  const originalText = downloadBtn.innerHTML;

  try {
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';
    downloadBtn.disabled = true;

    const response = await fetch(videoUrl);
    const blob = await response.blob();
    const blobUrl = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = "tiktok_video_" + Date.now() + ".mp4";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.URL.revokeObjectURL(blobUrl);

    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
    
    // Track successful download
    await fetch('/api/track-successful-download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        timestamp: new Date().toISOString()
      })
    });
    
    showSuccess("✅ Video downloaded successfully!");
  } catch (error) {
    console.error("Download error:", error);
    downloadBtn.innerHTML = originalText;
    downloadBtn.disabled = false;
    showError("❌ Download failed. Please try again.");
  }
}

async function checkNotifications() {
  try {
    const response = await fetch('/api/notifications');
    const notifications = await response.json();
    
    if (notifications.length > 0) {
      const notification = notifications[0]; // Show latest notification
      showNotification(notification.message, notification.actionUrl, notification.actionText);
    }
  } catch (error) {
    console.error('Error checking notifications:', error);
  }
}

function showNotification(message, actionUrl, actionText) {
  const dialog = document.getElementById('notificationDialog');
  const messageEl = document.getElementById('notificationMessage');
  const actionBtn = document.getElementById('actionBtn');
  const cancelBtn = document.getElementById('cancelBtn');

  messageEl.textContent = message;
  
  if (actionUrl && actionText) {
    actionBtn.textContent = actionText;
    actionBtn.style.display = 'block';
    actionBtn.onclick = () => {
      window.open(actionUrl, '_blank');
      closeNotification();
    };
  } else {
    actionBtn.style.display = 'none';
  }

  cancelBtn.textContent = actionUrl ? 'Cancel' : 'Close';
  dialog.style.display = 'flex';
}

function closeNotification() {
  document.getElementById('notificationDialog').style.display = 'none';
}

function isValidTikTokUrl(url) {
  const tiktokUrlPattern = /(https?:\/\/)?(www\.)?(vm\.|vt\.)?tiktok\.com\/(.*)/;
  return tiktokUrlPattern.test(url);
}

function showError(message) {
  const errorEl = document.getElementById("error");
  errorEl.textContent = message;
  errorEl.style.display = "block";
  document.getElementById("success").style.display = "none";
}

function showSuccess(message) {
  const successEl = document.getElementById("success");
  successEl.textContent = message;
  successEl.style.display = "block";
  document.getElementById("error").style.display = "none";

  setTimeout(() => {
    successEl.style.display = "none";
  }, 3000);
}

// Create animated background
function createAnimatedBackground() {
  const background = document.createElement('div');
  background.className = 'background-animation';
  
  for (let i = 0; i < 3; i++) {
    const shape = document.createElement('div');
    shape.className = `floating-shape shape-${i + 1}`;
    background.appendChild(shape);
  }
  
  document.body.appendChild(background);
}

createAnimatedBackground();
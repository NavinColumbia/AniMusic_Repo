
if (typeof browser === "undefined") var browser = chrome;


console.log("[Content] loaded");


let watchTimer = null;
let accumulated = 0;
let lastTick = 0;
let currentVid = null;
let duration = 0;

function start() {
  lastTick = Date.now();
  if (watchTimer) clearInterval(watchTimer);
  watchTimer = setInterval(() => {
    if (!document.hidden) {
      const now = Date.now();
      accumulated += (now - lastTick) / 1000;
      lastTick = now;
    } else {
      lastTick = Date.now();
    }
  }, 1000);
}

function stop(sendFeedback = true) {
  if (watchTimer) {
    clearInterval(watchTimer);
    watchTimer = null;
  }
  if (sendFeedback && currentVid) {
    browser.runtime.sendMessage({
      type: "autofeedback",
      data: {
        song_id: currentVid,
        watch_time: accumulated,
        total_video_time: duration
      }
    });
  }
  accumulated = 0;
}


function hookVideo(v) {
  if (!v) return;
  currentVid = new URL(location.href).searchParams.get("v");
  duration   = v.duration || 0;

  v.addEventListener("play", start);
  v.addEventListener("pause", () => stop(false));
  v.addEventListener("ended", () => stop(true));
  v.addEventListener("seeking", () => stop(false));
  v.addEventListener("seeked", start);

  if (!v.paused) start();
}


window.addEventListener("yt-navigate-start", () => {
  stop(true);      
});

function waitForVideo() {
  const v = document.querySelector("video");
  if (v) { hookVideo(v); return; }
  const obs = new MutationObserver((m, o) => {
    const vv = document.querySelector("video");
    if (vv) { hookVideo(vv); o.disconnect(); }
  });
  obs.observe(document, { childList: true, subtree: true });
}

waitForVideo();
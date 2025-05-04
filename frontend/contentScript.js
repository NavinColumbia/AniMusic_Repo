
console.log("[ContentScript] loaded on:", window.location.href);
let watchInterval = null, accumulated = 0, lastTick = 0;

function startTimer(){
  lastTick = Date.now();
  if (watchInterval) clearInterval(watchInterval);
  watchInterval = setInterval(() => {
    if (!document.hidden) {
      const now = Date.now();
      accumulated += (now - lastTick)/1000;
      lastTick = now;
    } else lastTick = Date.now();
  }, 1000);
}
function stopTimer(){
  if (watchInterval) {
    clearInterval(watchInterval);
    console.log("[CS] watch time:", accumulated.toFixed(1),"s");
    accumulated = 0;
  }
}
function attach(v){
  v.addEventListener("play", startTimer);
  v.addEventListener("pause", stopTimer);
  v.addEventListener("ended", stopTimer);
  v.addEventListener("seeking", () => { stopTimer(); });
  v.addEventListener("seeked", startTimer);
  if (!v.paused) startTimer();
}
(function init(){
  const v = document.querySelector("video");
  if (v) attach(v);
  else new MutationObserver((_,obs) => {
    const vv = document.querySelector("video");
    if (vv) { attach(vv); obs.disconnect(); }
  }).observe(document,{childList:true,subtree:true});
})();
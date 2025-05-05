import { API_BASE, ANILIST_CLIENT_ID, OAUTH_REDIRECT_URI } from "./config.js";


document.addEventListener("DOMContentLoaded", () => {
  const browser = window.browser || window.chrome;


  const $ = id => document.getElementById(id);
  const loginBtn         = $("loginBtn");
  const uploadProfileBtn = $("uploadProfileBtn");
  const fetchPlaylistBtn = $("fetchPlaylistBtn");
  const prevBtn          = $("prevBtn");
  const nextBtn          = $("nextBtn");
  const favBtn           = $("favBtn");
  const userInfo         = $("userInfo");
  const statusEl         = $("status");
  const playlistList     = $("playlistList");


  loginBtn.addEventListener("click", () => {
    const clientId    = ANILIST_CLIENT_ID;
    const redirectUri = encodeURIComponent(OAUTH_REDIRECT_URI);
    const url = `https://anilist.co/api/v2/oauth/authorize`
              + `?client_id=${clientId}`
              + `&response_type=token`;
    window.open(url, "_blank", "width=500,height=600");
  });

  window.addEventListener("message", ev => {
    if (typeof ev.data === "string" && ev.data.startsWith("#access_token")) {
      const tok = new URLSearchParams(ev.data.substring(1)).get("access_token");
      if (tok) {
        browser.storage.sync.set({ anilist_token: tok }, loadViewer);
      }
    }
  });


  const CACHE_KEY = "viewer_cache";
  const CACHE_TTL = 10 * 60 * 1000;
  function setVC(tok, data) {
    browser.storage.local.set({ [CACHE_KEY]: { ts:Date.now(), token:tok, data } });
  }
  function getVC(tok) {
    return new Promise(res => {
      browser.storage.local.get([CACHE_KEY], o => {
        const c = o[CACHE_KEY];
        if (c && c.token === tok && Date.now() - c.ts < CACHE_TTL) {
          res(c.data);
        } else {
          res(null);
        }
      });
    });
  }
  function showViewer(d) {
    userInfo.textContent = `AniList: ${d.viewerName} (Anime:${d.animeCount})`;
    browser.storage.sync.set({ anilist_username: d.viewerName });
  }


  function loadViewer() {
    browser.storage.sync.get(["anilist_token"], async ({ anilist_token:tok }) => {
      if (!tok) {
        userInfo.textContent = "Not logged in with AniList.";
        return;
      }
      const cached = await getVC(tok);
      if (cached) {
        showViewer(cached);
      } else {
        browser.runtime.sendMessage({ type:"fetchUserAndCount" }, resp => {
          if (resp.data) {
            showViewer(resp.data);
            setVC(tok, resp.data);
          } else {
            userInfo.textContent = "AniList error";
          }
        });
      }
    });
  }
  loadViewer();


  uploadProfileBtn.addEventListener("click", async () => {
    statusEl.textContent = "Uploading AniList profile…";
    browser.storage.sync.get(["anilist_token","anilist_username"], async items => {
      const token = items.anilist_token;
      const uname = items.anilist_username;
      if (!token || !uname) {
        statusEl.textContent = "Please log in first.";
        return;
      }
    
      let userId;
      try {
        const userResp = await fetch("https://graphql.anilist.co", {
          method: "POST",
          headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            query: `query($n:String){User(name:$n){id}}`,
            variables: { n: uname }
          })
        }).then(r => r.json());
        userId = userResp.data.User.id;
      } catch {
        statusEl.textContent = "Failed to fetch AniList user ID.";
        return;
      }
   
      let mal_ids = [];
      try {
        const malResp = await fetch("https://graphql.anilist.co", {
          method: "POST",
          headers: {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            query: `
              query($uid:Int){
                MediaListCollection(userId:$uid,type:ANIME){
                  lists{ entries{ media{ idMal } } }
                }
              }`,
            variables: { uid: userId }
          })
        }).then(r => r.json());
        malResp.data.MediaListCollection.lists.forEach(l =>
          l.entries.forEach(e => e.media.idMal && mal_ids.push(e.media.idMal))
        );
      } catch {
        statusEl.textContent = "Failed to fetch MAL IDs.";
        return;
      }
     
      browser.runtime.sendMessage({
        type: "uploadAniListProfile",
        payload: { anilist_username: uname, mal_ids }
      }, resp => {
        if (resp.count != null) {
          statusEl.textContent = `Uploaded ${resp.count} MAL IDs.`;
        } else {
          statusEl.textContent = "Upload error: " + (resp.error || "unknown");
        }
      });
    });
  });

 
  fetchPlaylistBtn.addEventListener("click", () => {
    statusEl.textContent = "Fetching playlist…";
    browser.storage.sync.get(["anilist_username"], ({ anilist_username }) => {
      const name = anilist_username || "guest";
      const url = `${API_BASE}/playlist?anilist_username=${encodeURIComponent(name)}`;
      fetch(url)
        .then(r => r.json())
        .then(data => {
          if (!data.videos?.length) {
            statusEl.textContent = "No videos returned.";
            return;
          }
          const pd = {
            playlist: data.videos.map(v => ({ ...v, isFavorite:false })),
            currentVideoIndex: 0
          };
          browser.storage.local.set({ playlistData: pd }, () => {
            statusEl.textContent = "Playlist loaded.";
            renderPlaylist(pd);
            browser.tabs.query({ active:true,currentWindow:true }, tabs => {
              if (tabs[0]) browser.tabs.update(tabs[0].id, { url: pd.playlist[0].youtube_url });
            });
          });
        })
        .catch(() => statusEl.textContent = "Error fetching playlist.");
    });
  });

  function renderPlaylist(pd) {
    playlistList.innerHTML = "";
    pd.playlist.forEach((item, idx) => {
      const li = document.createElement("li");
      li.textContent = `[${item.recommended_by}] ${item.song} — ${item.anime}`
                     + (item.isFavorite ? " ♥" : "");
      if (idx === pd.currentVideoIndex) li.classList.add("current");
      playlistList.appendChild(li);
    });
    favBtn.textContent = pd.playlist[pd.currentVideoIndex].isFavorite ? "♥" : "♡";
  }
  browser.storage.local.get(["playlistData"], ({ playlistData: pd }) => {
    if (pd && pd.playlist && pd.playlist.length) {
      renderPlaylist(pd);
    }
  });


  prevBtn.addEventListener("click", () => handleNav("prev"));
  nextBtn.addEventListener("click", () => handleNav("next"));
  favBtn.addEventListener("click", async () => {
    const { playlistData: pd } = await new Promise(r =>
      browser.storage.local.get(["playlistData"], r)
    );
    const cur = pd.playlist[pd.currentVideoIndex];
    cur.isFavorite = !cur.isFavorite;
    browser.storage.local.set({ playlistData: pd }, () => {
      renderPlaylist(pd);
      statusEl.textContent = cur.isFavorite ? "Marked favorite" : "Unmarked favorite";
    });
  });

  async function handleNav(direction) {
    const { playlistData: pd } = await new Promise(r =>
      browser.storage.local.get(["playlistData"], r)
    );
    if (!pd?.playlist.length) {
      statusEl.textContent = "No playlist to navigate.";
      return;
    }
  
    let videoData = { currentTime:0, duration:0, videoId:null };
    try { videoData = await getWatchTime(); } catch {}
    const cur = pd.playlist[pd.currentVideoIndex];
    const fb = {
      anilist_username: await getAniListUsername(),
      song_id: videoData.videoId || cur.youtube_video_id,
      recommended_by: cur.recommended_by,
      watch_time: videoData.currentTime,
      total_video_time: videoData.duration,
      liked: cur.isFavorite
    };
    statusEl.textContent = "Recording feedback…";
    browser.runtime.sendMessage({ type:"recordFeedback", feedback:fb }, () => {
      statusEl.textContent = "Feedback recorded";
    });

  
    pd.currentVideoIndex = direction === "next"
      ? (pd.currentVideoIndex + 1) % pd.playlist.length
      : (pd.currentVideoIndex - 1 + pd.playlist.length) % pd.playlist.length;

 
    browser.storage.local.set({ playlistData: pd }, () => {
      renderPlaylist(pd);
      const nextItem = pd.playlist[pd.currentVideoIndex];
      browser.tabs.query({ active:true,currentWindow:true }, tabs => {
        if (tabs[0]) browser.tabs.update(tabs[0].id, { url: nextItem.youtube_url });
      });
    });
  }


  function getWatchTime() {
    return new Promise((resolve,reject) => {
      browser.tabs.query({ active:true,currentWindow:true }, tabs => {
        if (!tabs[0]?.url.includes("youtube.com/watch")) return reject();
        browser.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => {
            const v = document.querySelector("video");
            return {
              currentTime: v?.currentTime||0,
              duration:    v?.duration||0,
              videoId:     new URL(location.href).searchParams.get("v")
            };
          }
        }, results => {
          if (browser.runtime.lastError) return reject();
          resolve(results[0].result);
        });
      });
    });
  }


  function getAniListUsername() {
    return new Promise(res =>
      browser.storage.sync.get(["anilist_username"], ({ anilist_username }) =>
        res(anilist_username||"guest")
      )
    );
  }
});
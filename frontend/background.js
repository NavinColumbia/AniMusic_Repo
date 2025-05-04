const API_BASE = location.hostname === "localhost"
               ? "http://localhost:8000"
               : "https://sideproject-production-fc87.up.railway.app";

if (typeof browser === "undefined") var browser = chrome;


let viewerCache = { ts:0, data:null, promise:null };
const CACHE_TTL = 10 * 60 * 1000;

async function graphql(token, query, vars={}) {
  const res = await fetch("https://graphql.anilist.co", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + token,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query, variables: vars })
  });
  const j = await res.json();
  if (!res.ok || j.errors) throw new Error("AniList error");
  return j.data;
}

async function fetchViewer(token) {
  const v = await graphql(token, `query{Viewer{id name}}`);
  const uid = v.Viewer.id, name = v.Viewer.name;
  const l = await graphql(token, `
    query($uid:Int){
      MediaListCollection(userId:$uid,type:ANIME){
        lists{ entries{id} }
      }
    }`, { uid });
  let count = 0;
  (l.MediaListCollection.lists||[]).forEach(lst => count += lst.entries.length);
  return { viewerName:name, animeCount:count };
}


browser.storage.onChanged.addListener((changes,area) => {
  if (area==="sync" && changes.anilist_token) {
    viewerCache = { ts:0, data:null, promise:null };
  }
});


browser.runtime.onMessage.addListener((req,_s,sendResponse) => {
  
  if (req.type === "fetchUserAndCount") {
    browser.storage.sync.get(["anilist_token"], ({ anilist_token:tok }) => {
      if (!tok) {
        sendResponse({ error:"No AniList token. Please log in." });
        return;
      }
      const now = Date.now();
      if (viewerCache.data && now - viewerCache.ts < CACHE_TTL) {
        sendResponse({ data: viewerCache.data });
        return;
      }
      if (viewerCache.promise) {
        viewerCache.promise.then(d => sendResponse({ data:d }))
                           .catch(e => sendResponse({ error:String(e) }));
        return true;
      }
      viewerCache.promise = fetchViewer(tok)
        .then(d => {
          viewerCache = { ts:Date.now(), data:d, promise:null };
          sendResponse({ data:d });
        })
        .catch(e => {
          viewerCache.promise = null;
          sendResponse({ error:String(e) });
        });
      return true;
    });
    return true;
  }

  
  if (req.type === "uploadAniListProfile") {
    fetch(`${API_BASE}/upload_anilist_profile`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify(req.payload)
    })
    .then(r => r.json())
    .then(d => sendResponse(d))
    .catch(e => sendResponse({ error:String(e) }));
    return true;
  }


  if (req.type === "recordFeedback" || req.type==="autofeedback") {
    fetch(`${API_BASE}/feedback`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body: JSON.stringify(req.feedback)
    })
    .then(r=>r.json())
    .then(d=>sendResponse(d))
    .catch(e=>sendResponse({ error:String(e) }));
    return true;
  }
});
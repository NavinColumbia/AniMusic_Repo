# AniMusic

This is the repo for the **AniMusic** Chrome Extension&nbsp;:  
[Chrome Web Store Link](https://chromewebstore.google.com/detail/bpnflfbnnekkledjfcdnkaoanfkflpho?utm_source=item-share-cb)

Animusic is a Chrome extension that recommends anime songs on YouTube. Animusic avails the wealth of structured metadata available publicly on anime-songs at websites like AniDB, Anilist, and MyAnimeList for free. It is designed for a low-resource environment like start-ups, which do not have a large dataset of user-item interaction history. 

This repo includes code for data‑collection, backend, frontend (Chrome extension) and post‑deployment analysis.  

Follow the README top to bottom to reproduce everything.

---

## Repo Structure
| path | content |
|------|---------------|
| `data_collection_and_embedding/` | notebook and scripts for data scraping and embedding |
| `backend-deploy/` | FastAPI backend, Dockerfile, `songs.csv` dataset, model .pkl files |
| `frontend/` | Chrome extension source code |
| `analysis/` | Jupyter notebook for result analysis |
| `milestone_docs/` | proposal, progress report, final report in PDF format |
| `.docker-compose.yml` | container orchestration (API and Postgres) |
| `.env_example` | template env‑file |

---

## Prerequisites

* Python 3.12 + pip (backend / notebooks)  
* Anaconda (or plain Jupyter)  
* Docker Desktop (or cli)  
* Railway (or any other PaaS)  
* Google Chrome  
* Accounts  
  * AniList (OAuth)  
  * MyAnimeList (API)  
* Common Python Libraries:  
  ```
     pip install -r requirements_min.txt
  ```



## Quick Start (local)

```bash
git clone https://github.com/NavinColumbia/AniMusic_Repo.git
cd AniMusic_Repo

cp .env_example .env 
nano .env # edit MAL_CLIENT_ID, DATABASE_URL, BACKEND_ORIGIN

# install postgres (this is for mac)
brew install postgresql
brew services start postgresql

# create user, db
createuser -s animusic_user
createdb -O animusic_user animusic_db
psql -d animusic_db -c "ALTER USER animusic_user WITH PASSWORD 'animusic_pass';"

# backend and db
docker‑compose up --build

# API docs can be visited in browser: http://localhost:8080/docs
```

**Load extension locally**

```
cd frontend
# edit ./frontend/config.js like ANILIST_CLIENT_ID OAUTH_REDIRECT_URI, API_BASE, etc

# visit chrome://extensions 
# enable Dev Mode,  “Load unpacked”, select ./frontend
# pin the AniMusic icon
```

---

## Data Collection  (optional – dataset already included)

**Create a MAL Client** : [https://myanimelist.net/apiconfig](https://myanimelist.net/apiconfig), paste `MAL_CLIENT_ID` into `.env`.

| step                 | notebook                                                      |
| -------------------- | ------------------------------------------------------------- |
| fetch anime metadata | `data_collection_and_embedding/Anime_Data_Collection.ipynb`   |
| fetch YouTube stats  | `data_collection_and_embedding/Youtube_Data_Collection.ipynb` |

 **To-Note**: rate‑limits are strict. This will take  \~2–3 weeks to run if you scrape from zero for a 1000+ animes, if you do 50-100 animes a day.

The experimentally‑evaluated dataset (`backend-deploy/data/songs.csv`, **14 885 rows**) is already version‑controlled, so you can skip scraping and still reproduce the results.

---

## Model Training  (optional)

* Pre‑computed `.pkl` files live in `backend-deploy/model_files/`.
* To regenerate:

```bash
python ./data_collection_and_embedding/embedding_songs.py
python ./data_collection_and_embedding/embedding_songs_mpnet.py
# recommender.pkl auto‑builds on first time backend start‑up
```

---

## Frontend

1. **Create AniList dev client** : [https://anilist.co/settings/developer](https://anilist.co/settings/developer) , set `redirect_uri` to  hosted `static/oauth_done.html`.
2. Edit `frontend/config.js`:

   ```js
   export const API_BASE           = "https://<backend>";
   export const ANILIST_CLIENT_ID  = "<anilist-id>";
   export const OAUTH_REDIRECT_URI = "https://<backend>/static/oauth_done.html";
   ```
3. If deploying, update  `host_permissions` in `manifest.json`.

To publish, follow the official [Chrome Web Store guide](https://developer.chrome.com/docs/webstore/publish).

---

## Backend deployment

Inside `backend-deploy/` there is :

* `app/` – FastAPI source code
* `static/` – OAuth landing page
* `requirements.txt` + `Dockerfile`

Deploy anywhere Docker runs, Railway example:

```bash
#  create a new git repo with only backend and deploy it via railway GUI.
# add Postgres plugin in GUI, copy DATABASE_URL then update it in .env
```

if quick-start not done already and you want to deploy locally and not to prod, do below instead:

```bash
docker-compose up --build  # API starts on port:8080, DB starts on port 65432
```

---

## Post‑deployment Analysis

* Set `ANALYSIS_DATABASE_URL` in `.env`.
* Open `./analysis/analysis.ipynb` , Click Run All, figures appear under `./analysis/demo_figs_permodel/` as well in notebook cell output.

---

## Contributing

1. `cp .env_example .env`, edit
2. `docker-compose up --build`
3. Adjust `frontend/config.js`, (and `manifest.json` host permission if needed)
4. Load/refresh extension via `Load Unpacked`
5. Submit PRs or issues

### Adding a new model

* Implement in `backend-deploy/app/` (see `master_recommender.py`)
* Add its label to `BigMasterRecommender.BUCKETS`

### API Schema

* Swagger UI : `${BACKEND_ORIGIN}/docs`
* ReDoc : `${BACKEND_ORIGIN}/redoc`

### Debug tips

* `brew services list` - stop Postgres if ports clash
* `docker-compose down -v` - clean volume
* `docker-compose logs -f api` -  backend logs

---

## Milestone Docs

See `milestone_docs/` for **proposal, progress report, final report**.

---

## Author

Navinashok Swaminathan <br/>
UNI : NS3886



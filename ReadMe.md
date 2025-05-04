# AniMusic

This is the repo for the AniMusic Chrome Extension : [Chrome Webstore Install Link](https://chromewebstore.google.com/detail/bpnflfbnnekkledjfcdnkaoanfkflpho?utm_source=item-share-cb)

<br/>
This repo contains code for data collection, backend code, frontend chrome extension code, scripts for post deployment analysis.  <br/>





## Data Collection

The collected data is present under `./backend-deploy/data/songs.csv` If you wish to reproduce data collection :  <br/>

In ./data_collection_and_embedding <br/>
1)Use Anime_Data_Collection.ipynb to fetch data. <br/>
2)Then use Youtube_Data_Collection to fetch youtube stats. <br/>





## Model Training

The generated pkl files can be found in `./backend-deploy/model_files`. If you wish to reproduce pkl file generation : <br/>

1)Then use embedding_songs.py and embeeding_songs_mpnet.py to get pkl for MiniLm and Mpnet. <br/>
2)Recommender.pkl is generated on startup. <br/>


## FrontEnd

The chrome extension frontend code is present in `./frontend`. You can  go to go to chrome://extensions/, enable developer mode and load unpacked entire folder if you wish to test chrome extension locally. <br/>




## BackEnd

The backend code is present at `./backend_deploy` <br/>

 `./backend-deploy/app` contains the source py files. <br/>
  `./backend-deploy/static` contains the html page redircted to on anilist login. <br/> There is also a `requirements.txt` containing dependencies. A Dockerfile is also present. <br/> 
  To deploy the code create a new repo and push backend-deploy to it, then you can deploy the repo via railway. You can create a postgres db in the same environment in the GUI and get the postgresql url.




## Post-deployment analysis

`./analysis/analysis.ipynb` can be run to see charts of how the models compare. Figs for per model graph for the last cell in the ipynb can be found under `.analysis/demo_figs_permodel/`




## Important Note

MAL client id, and Postgresql url, hosted backend url have been removed for security reasons, you can replace them to reproduce the work. csv_paths will also have to be updated based on where you stored them/want to store them. This work is reproducible.


## Mile Stone Documents

`./milestone_docs` contains  proposal , progress report and final report

## Author

Navinashok Swaminathan <br/>
UNI : NS3886

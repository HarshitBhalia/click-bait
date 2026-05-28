# Catch-Bait: Indian YouTube Clickbait Detection

Catch-Bait is a multimodal AI-based system designed to detect clickbait content in Indian YouTube videos. The project combines textual, visual, and metadata-based analysis to identify misleading thumbnails and exaggerated titles commonly used to manipulate viewer engagement.

## Features

* Multimodal clickbait detection
* Hindi/Hinglish understanding using MuRIL BERT
* Thumbnail analysis using CLIP ViT-B/32
* Metadata-driven feature extraction
* XGBoost-based classification
* Streamlit web application for interactive predictions
* Custom Indian YouTube dataset creation using YouTube API

## Tech Stack

* Python
* Streamlit
* Transformers
* MuRIL BERT
* OpenCLIP
* XGBoost
* Scikit-learn
* YouTube API

## Workflow

1. Data collection using YouTube API
2. Thumbnail, title, transcript, and metadata extraction
3. Exploratory Data Analysis (EDA)
4. Feature engineering
5. Multimodal feature fusion
6. XGBoost classification
7. Streamlit deployment

## Objective

The goal of this project is to reduce misinformation and improve digital trust by identifying misleading YouTube content targeted toward Indian audiences.

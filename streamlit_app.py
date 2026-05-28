# app.py — put this in a new folder with requirements.txt
import streamlit as st
import numpy as np
import pickle, json, re, requests, torch, os
import open_clip
from PIL import Image
from io import BytesIO
from transformers import AutoTokenizer, AutoModel
from sklearn.preprocessing import normalize

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="Indian YouTube Clickbait Detector",
    page_icon="🎯",
    layout="centered"
)

# ── Load all models once (cached) ────────────────────────
@st.cache_resource
def load_all():
    clf         = pickle.load(open("clickbait_xgb_v1.pkl", "rb"))
    cfg         = json.load(open("feature_config.json"))
    tokenizer   = AutoTokenizer.from_pretrained("google/muril-base-cased")
    text_model  = AutoModel.from_pretrained("google/muril-base-cased").eval()
    clip_model, _, clip_prep = open_clip.create_model_and_transforms(
        "ViT-B-32", pretrained="openai"
    )
    clip_model.eval()
    return clf, cfg, tokenizer, text_model, clip_model, clip_prep

clf, cfg, tokenizer, text_model, clip_model, clip_prep = load_all()

HINDI_BAIT = [
    "सच्चाई","खुलासा","धमाका","तबाही","चौंकाने","हैरान","क्या हुआ",
    "आप नहीं जानते","सामने आई","बड़ा खुलासा","सनसनी","विस्फोट",
    "shocking","exposed","leaked","you won't believe","watch till end",
    "must watch","viral","mind-blowing","breaking","exclusive","secret"
]

# ── Feature extraction helpers ────────────────────────────
def get_text_embedding(text):
    enc = tokenizer(text, return_tensors="pt", truncation=True,
                    padding=True, max_length=128)
    with torch.no_grad():
        out = text_model(**enc)
    mask = enc["attention_mask"].unsqueeze(-1).float()
    emb  = (out.last_hidden_state * mask).sum(1) / mask.sum(1)
    return emb.squeeze().numpy()

def get_image_embedding(pil_img):
    tensor = clip_prep(pil_img).unsqueeze(0)
    with torch.no_grad():
        emb = clip_model.encode_image(tensor)
    return emb.squeeze().numpy()

def get_meta_features(title, view_count=0, like_count=0,
                      comment_count=0, duration_sec=0, tags="", h_score=0):
    t     = str(title)
    views = max(float(view_count), 1)
    return np.array([
        np.log1p(views),
        float(like_count)    / views,
        float(comment_count) / views,
        min(duration_sec / 3600, 24),
        len(t) / 100,
        sum(1 for c in t if c.isupper()) / max(len(t),1),
        min(len(re.findall(r'[\U00010000-\U0010ffff]', t)) / 5, 1),
        min(sum(1 for w in HINDI_BAIT if w in t.lower()) / 5, 1),
        int("?" in t),
        int("!" in t),
        min(len([x for x in str(tags).split(",") if x.strip()]) / 20, 1),
        float(h_score) / 10,
    ], dtype=np.float32)

def extract_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url)
    return m.group(1) if m else None

def fetch_video_meta(video_id, api_key):
    url = (f"https://www.googleapis.com/youtube/v3/videos"
           f"?part=snippet,statistics,contentDetails"
           f"&id={video_id}&key={api_key}")
    r = requests.get(url, timeout=10).json()
    if not r.get("items"):
        return None
    item = r["items"][0]
    s, st, cd = item["snippet"], item["statistics"], item["contentDetails"]
    return {
        "title"        : s.get("title",""),
        "description"  : s.get("description","")[:300],
        "channel"      : s.get("channelTitle",""),
        "published_at" : s.get("publishedAt",""),
        "view_count"   : int(st.get("viewCount",  0)),
        "like_count"   : int(st.get("likeCount",  0)),
        "comment_count": int(st.get("commentCount",0)),
        "duration"     : cd.get("duration",""),
        "tags"         : ",".join(s.get("tags",[])),
        "thumbnail_url": (s.get("thumbnails",{}).get("maxres") or
                          s.get("thumbnails",{}).get("high",{})).get("url",""),
    }

def predict(title, thumbnail_pil, view_count=0, like_count=0,
            comment_count=0, duration_sec=0, tags="", h_score=5):
    t_emb  = normalize(get_text_embedding(title).reshape(1,-1))[0]
    i_emb  = normalize(get_image_embedding(thumbnail_pil).reshape(1,-1))[0]
    m_feat = get_meta_features(title, view_count, like_count,
                                comment_count, duration_sec, tags, h_score)
    X      = np.concatenate([t_emb, i_emb, m_feat]).reshape(1,-1)
    prob   = clf.predict_proba(X)[0][1]
    return prob

# ── UI ────────────────────────────────────────────────────
st.title("🎯 Indian YouTube Clickbait Detector")
st.caption("Supports Hindi · Hinglish · English — trained on 2,066 videos from 50+ Indian channels")

tab1, tab2 = st.tabs(["🔗 Analyse by URL", "✏️ Manual input"])

# ── TAB 1: URL mode ──
with tab1:
    api_key = st.text_input(
        "YouTube Data API key (free from console.cloud.google.com)",
        type="password", help="Only used for metadata fetch, never stored"
    )
    url = st.text_input("YouTube video URL")

    if st.button("Analyse URL", type="primary") and url:
        vid = extract_video_id(url)
        if not vid:
            st.error("Could not parse video ID from URL")
        elif not api_key:
            st.warning("Enter an API key to fetch metadata automatically")
        else:
            with st.spinner("Fetching metadata…"):
                meta = fetch_video_meta(vid, api_key)
            if not meta:
                st.error("Video not found or API key invalid")
            else:
                with st.spinner("Running inference…"):
                    thumb_url = meta["thumbnail_url"] or \
                                f"https://img.youtube.com/vi/{vid}/hqdefault.jpg"
                    img_data  = requests.get(thumb_url, timeout=10).content
                    pil_img   = Image.open(BytesIO(img_data)).convert("RGB")
                    prob      = predict(
                        meta["title"], pil_img,
                        meta["view_count"], meta["like_count"],
                        meta["comment_count"], 0,
                        meta["tags"]
                    )

                col1, col2 = st.columns([1, 1.6])
                with col1:
                    st.image(pil_img, use_column_width=True)
                with col2:
                    st.markdown(f"**{meta['title']}**")
                    st.caption(f"Channel: {meta['channel']} · "
                               f"{meta['view_count']:,} views")

                st.divider()
                if prob >= 0.5:
                    st.error(f"### 🎯 CLICKBAIT — {prob:.0%} confidence")
                else:
                    st.success(f"### ✅ Not clickbait — {1-prob:.0%} confidence")

                st.progress(float(prob))

                with st.expander("Signal breakdown"):
                    title = meta["title"]
                    hits  = [w for w in HINDI_BAIT if w in title.lower()]
                    st.write(f"**Bait words found:** {hits if hits else 'none'}")
                    caps  = sum(1 for c in title if c.isupper()) / max(len(title),1)
                    st.write(f"**Caps ratio:** {caps:.0%}")
                    emoji_count = len(re.findall(r'[\U00010000-\U0010ffff]', title))
                    st.write(f"**Emoji count:** {emoji_count}")
                    st.write(f"**Has question mark:** {'yes' if '?' in title else 'no'}")
                    st.write(f"**Has exclamation:** {'yes' if '!' in title else 'no'}")

# ── TAB 2: Manual mode (no API key needed) ──
with tab2:
    st.caption("Paste a title and upload a thumbnail manually")
    m_title  = st.text_input("Video title")
    m_thumb  = st.file_uploader("Thumbnail image", type=["jpg","jpeg","png"])
    m_views  = st.number_input("View count", min_value=0, value=100000)
    m_likes  = st.number_input("Like count",  min_value=0, value=5000)

    if st.button("Analyse manual", type="primary") and m_title and m_thumb:
        pil_img = Image.open(m_thumb).convert("RGB")
        prob    = predict(m_title, pil_img, m_views, m_likes)
        st.image(pil_img, width=320)
        if prob >= 0.5:
            st.error(f"### 🎯 CLICKBAIT — {prob:.0%} confidence")
        else:
            st.success(f"### ✅ Not clickbait — {1-prob:.0%} confidence")
        st.progress(float(prob))
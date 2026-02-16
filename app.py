import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 抽出・要約関数は前回と同様 ---
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        for s in soup(["script", "style", "header", "footer", "nav", "aside"]):
            s.decompose()
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text() for p in paragraphs])
        return text[:2500] 
    except Exception as e:
        return f"エラー: {e}"

def summarize_article(title, text, url):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたはSNSでの情報発信に長けた広報担当です。"},
                {"role": "user", "content": f"""
以下の記事を要約し、X（Twitter）向けの投稿案を作成してください。
最後に必ず「元記事のURL」を添えてください。

【ルール】
1. 【見出し】を30文字以内で作成。
2. 内容を100文字程度で要約。
3. 最後に「記事詳細はこちら：{url}」と、ハッシュタグを2つ記載。

記事タイトル: {title}
本文: {text}
"""}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"要約エラー: {e}"

# --- UI 部分 ---
st.set_page_config(page_title="News Summarizer", page_icon="🔗")
st.title("📡 RSS News Summarizer")

# テーマごとのソース設定（ここを最新・専門ソースに更新）
THEMES = {
    "生成AI最新情報 (ITmedia AI+)": "https://www.itmedia.co.jp/news/subtop/ai/index.xml",
    "生成AI/テック (ギズモード)": "https://www.gizmodo.jp/index.xml",
    "暗号資産/Web3 (CoinPost)": "https://coinpost.jp/?feed=rss2",
    "最新技術動向 (Publickey)": "https://www.publickey1.jp/atom.xml"
}

theme_choice = st.sidebar.radio("テーマを選択", list(THEMES.keys()))

if st.button(f"{theme_choice} の記事を取得"):
    st.session_state['feed'] = feedparser.parse(THEMES[theme_choice])

if 'feed' in st.session_state:
    for entry in st.session_state['feed'].entries[:5]:
        with st.container():
            st.write(f"### {entry.title}")
            # --- ここで事前に確認できるようにリンクを設置 ---
            st.markdown(f"[🔗 元記事をブラウザで確認する]({entry.link})")
            
            if st.button("この内容を要約する", key=entry.link):
                st.session_state['selected_url'] = entry.link
                st.session_state['selected_title'] = entry.title
                
                with st.spinner("要約を生成中..."):
                    content = extract_text_from_url(entry.link)
                    summary = summarize_article(entry.title, content, entry.link)
                    st.session_state['final_summary'] = summary

# 最終結果の表示
if 'final_summary' in st.session_state:
    st.divider()
    st.subheader("📝 生成された投稿内容（確認用）")
    # テキストエリアなら修正も可能
    edited_summary = st.text_area("必要に応じて微調整してください：", st.session_state['final_summary'], height=200)
    
    st.info(f"送信先URL確認: {st.session_state['selected_url']}")
    
    if st.button("🚀 Xへ投稿（デモ）"):
        st.success("投稿機能を連携すれば、この内容がそのまま送信されます！")
import streamlit as st
import re
import csv
import io
import socket
import time
import urllib.parse
from datetime import datetime

import requests

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="YouTube Expired Domain Hunter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM CSS - CLEAN LIGHT THEME WITH HIGH CONTRAST
# ============================================================
st.markdown("""
<style>
    /* Force light background everywhere */
    .stApp {
        background-color: #ffffff !important;
    }
    .main .block-container {
        background-color: #ffffff !important;
        padding-top: 2rem;
        max-width: 900px;
    }

    /* Typography */
    h1 {
        color: #1a1a2e !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -0.02em;
    }
    h2 {
        color: #1a1a2e !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    h3 {
        color: #1a1a2e !important;
        font-weight: 600 !important;
        font-size: 1.2rem !important;
    }
    p, label, .stMarkdown {
        color: #4a4a6a !important;
        font-size: 1rem !important;
    }

    /* Inputs - clean white with visible borders */
    .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    .stTextArea > div > div > textarea {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1 !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border: none !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #4f46e5 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #f1f5f9 !important;
        color: #64748b !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #e2e8f0 !important;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #6366f1 !important;
    }

    /* Cards */
    .login-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 2.5rem;
        max-width: 480px;
        margin: 0 auto;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    .stats-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    .stats-number {
        font-size: 2.5rem;
        font-weight: 800;
        color: #6366f1;
        line-height: 1;
    }
    .stats-label {
        font-size: 0.875rem;
        color: #64748b;
        margin-top: 0.5rem;
        font-weight: 500;
    }

    /* Alert boxes */
    .success-box {
        background-color: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #166534;
        font-weight: 500;
    }
    .error-box {
        background-color: #fef2f2;
        border: 1px solid #fca5a5;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #991b1b;
        font-weight: 500;
    }
    .info-box {
        background-color: #eff6ff;
        border: 1px solid #93c5fd;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        color: #1e40af;
        font-weight: 500;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8fafc;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 500;
        color: #64748b;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #6366f1;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        overflow: hidden;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 10px;
        font-weight: 600;
        color: #1a1a2e;
    }

    /* Divider */
    hr {
        border-color: #e2e8f0 !important;
        margin: 2rem 0 !important;
    }

    /* Code */
    code {
        background-color: #f1f5f9 !important;
        color: #6366f1 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.9em !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'results' not in st.session_state:
    st.session_state.results = []
if 'scanning' not in st.session_state:
    st.session_state.scanning = False

# ============================================================
# AUTH
# ============================================================
DEMO_USERS = {
    "demo@example.com": "demo123",
    "admin@hunter.app": "admin2026"
}

def show_login():
    # Hero section
    st.markdown("<div style='text-align:center; padding: 3rem 0 2rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h1>YouTube Expired Domain Hunter</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:1.15rem; max-width:500px; margin:0 auto;'>Find expired domains hiding in YouTube video descriptions. Scan, filter, and export in seconds.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Login card
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        st.markdown("<h3 style='text-align:center; margin-bottom:0.5rem; color:#1a1a2e;'>Member Access</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#64748b; font-size:0.9rem; margin-bottom:1.5rem;'>Sign in to start hunting domains</p>", unsafe_allow_html=True)

        email = st.text_input("Email address", placeholder="you@example.com", key="login_email", label_visibility="visible")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password", label_visibility="visible")

        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            if st.button("Sign In →", use_container_width=True):
                if email in DEMO_USERS and DEMO_USERS[email] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.markdown("<div class='error-box' style='margin-top:1rem;'>Invalid email or password. Try the demo credentials below.</div>", unsafe_allow_html=True)

        st.markdown("<div style='text-align:center; margin-top:1.5rem; padding-top:1rem; border-top:1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94a3b8; font-size:0.85rem; margin:0;'>Demo access</p>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; font-size:0.9rem; margin:0.25rem 0 0 0;'><code>demo@example.com</code> / <code>demo123</code></p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Footer features
    st.markdown("<div style='text-align:center; margin-top:3rem; padding-bottom:2rem;'>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown("""
        <div style='text-align:center; padding:1rem;'>
            <div style='font-size:1.5rem; margin-bottom:0.5rem; color:#6366f1; font-weight:700;'>[1]</div>
            <div style='font-weight:600; color:#1a1a2e; font-size:0.95rem;'>Bulk Scan</div>
            <div style='color:#64748b; font-size:0.85rem; margin-top:0.25rem;'>Search queries or direct URLs</div>
        </div>
        """, unsafe_allow_html=True)
    with f2:
        st.markdown("""
        <div style='text-align:center; padding:1rem;'>
            <div style='font-size:1.5rem; margin-bottom:0.5rem; color:#6366f1; font-weight:700;'>[2]</div>
            <div style='font-weight:600; color:#1a1a2e; font-size:0.95rem;'>Live Check</div>
            <div style='color:#64748b; font-size:0.85rem; margin-top:0.25rem;'>DNS availability in real-time</div>
        </div>
        """, unsafe_allow_html=True)
    with f3:
        st.markdown("""
        <div style='text-align:center; padding:1rem;'>
            <div style='font-size:1.5rem; margin-bottom:0.5rem; color:#6366f1; font-weight:700;'>[3]</div>
            <div style='font-weight:600; color:#1a1a2e; font-size:0.95rem;'>CSV Export</div>
            <div style='color:#64748b; font-size:0.85rem; margin-top:0.25rem;'>Download results instantly</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================

def extract_urls(text):
    url_pattern = re.compile(
        r'https?://(?:[-\w.])+(?::\d+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
        re.IGNORECASE
    )
    return url_pattern.findall(text)

def clean_domain(url):
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def is_major_platform(domain):
    platforms = {
        'youtube.com', 'youtu.be', 'google.com', 'goo.gl',
        'facebook.com', 'fb.me', 'fb.com', 'instagram.com',
        'twitter.com', 'x.com', 't.co', 'linkedin.com',
        'pinterest.com', 'tiktok.com', 'reddit.com',
        'amazon.com', 'amzn.to', 'ebay.com',
        'paypal.com', 'stripe.com', 'shopify.com',
        'wikipedia.org', 'wikimedia.org',
        'apple.com', 'microsoft.com', 'github.com',
        'wordpress.com', 'blogspot.com', 'medium.com',
        'mailchimp.com', 'convertkit.com', 'substack.com',
        'bit.ly', 'tinyurl.com', 't.ly', 'short.io',
        'discord.com', 'discord.gg', 'telegram.org',
        'spotify.com', 'soundcloud.com', 'vimeo.com',
        'dropbox.com', 'drive.google.com', 'docs.google.com',
    }
    return domain in platforms or any(domain.endswith('.' + p) for p in platforms)

def check_domain_availability(domain):
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname(domain)
        return 'taken'
    except socket.gaierror:
        return 'likely_available'
    except socket.timeout:
        return 'timeout'
    except Exception:
        return 'error'

def get_video_details(video_id, api_key):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {'part': 'snippet,statistics', 'id': video_id, 'key': api_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]
    except:
        return None
    return None

def search_youtube_videos(query, api_key, max_results=50):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'id,snippet', 'q': query, 'type': 'video',
        'maxResults': max_results, 'key': api_key, 'order': 'relevance'
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if 'items' in data:
            return data['items']
    except:
        return []
    return []

def extract_video_id(url_or_id):
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None

# ============================================================
# MAIN APP
# ============================================================

def show_app():
    # Header
    col1, col2 = st.columns([6, 2])
    with col1:
        st.markdown("<h2 style='margin-bottom:0;'>YouTube Expired Domain Hunter</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#64748b; margin-top:0.25rem;'>Welcome back, <b>{st.session_state.user_email}</b></p>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='text-align:right; padding-top:0.5rem;'>", unsafe_allow_html=True)
        if st.button("Sign Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # --- CONFIGURATION ---
    with st.expander("Configuration", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            api_key = st.text_input(
                "YouTube Data API Key",
                type="password",
                placeholder="AIzaSy...",
                help="Free key from console.cloud.google.com → YouTube Data API v3"
            )
        with col2:
            max_results = st.slider("Max videos per search query", 10, 50, 25)

        st.markdown("<p style='color:#94a3b8; font-size:0.8rem;'>Free quota: 10,000 units/day. Search = 100 units, video details = 1 unit.</p>", unsafe_allow_html=True)

    # --- INPUTS ---
    st.markdown("<h3>What do you want to scan?</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;'>Enter search queries, video URLs, or video IDs — one per line.</p>", unsafe_allow_html=True)

    inputs_text = st.text_area(
        "Inputs",
        placeholder="best plumbing tools 2019\nhttps://youtube.com/watch?v=ABC123\nroofing contractor tips",
        height=140,
        label_visibility="collapsed"
    )

    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 6])
    with col1:
        start_scan = st.button("Start Hunt", use_container_width=True, disabled=st.session_state.scanning, type="primary")
    with col2:
        if st.button("Clear Results", use_container_width=True, type="secondary"):
            st.session_state.results = []
            st.rerun()

    # --- SCANNING ---
    if start_scan and api_key and inputs_text.strip():
        st.session_state.scanning = True
        st.session_state.results = []

        raw_inputs = [line.strip() for line in inputs_text.strip().split('\n') if line.strip()]
        video_ids = []
        search_queries = []
        for inp in raw_inputs:
            vid = extract_video_id(inp)
            if vid:
                video_ids.append(vid)
            else:
                search_queries.append(inp)

        total_targets = len(video_ids) + len(search_queries)

        # Progress section
        st.markdown("<div style='background:#f8fafc; border-radius:12px; padding:1.5rem; margin:1rem 0;'>", unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        st.markdown("</div>", unsafe_allow_html=True)

        all_domains = set()
        results = []
        processed = 0

        # Process direct videos
        for vid in video_ids:
            processed += 1
            progress = processed / max(total_targets, 1)
            progress_bar.progress(min(progress, 0.99))
            status_text.markdown(f"<p style='color:#64748b; margin:0;'>Fetching video: <code>{vid}</code> ({processed}/{total_targets})</p>", unsafe_allow_html=True)

            video = get_video_details(vid, api_key)
            if video:
                snippet = video.get('snippet', {})
                stats = video.get('statistics', {})
                title = snippet.get('title', 'Unknown')
                desc = snippet.get('description', '')
                channel = snippet.get('channelTitle', 'Unknown')
                published = snippet.get('publishedAt', '')[:10]
                views = stats.get('viewCount', '0')

                urls = extract_urls(desc)
                for url in urls:
                    domain = clean_domain(url)
                    if not domain or is_major_platform(domain) or domain in all_domains:
                        continue
                    all_domains.add(domain)
                    status = check_domain_availability(domain)
                    time.sleep(0.2)

                    results.append({
                        'domain': domain,
                        'full_url': url,
                        'availability': status,
                        'video_title': title,
                        'video_id': vid,
                        'channel': channel,
                        'published': published,
                        'views': views,
                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

            time.sleep(0.5)

        # Process search queries
        for query in search_queries:
            processed += 1
            progress = processed / max(total_targets, 1)
            progress_bar.progress(min(progress, 0.99))
            status_text.markdown(f"<p style='color:#64748b; margin:0;'>Searching: <b>{query}</b> ({processed}/{total_targets})</p>", unsafe_allow_html=True)

            videos = search_youtube_videos(query, api_key, max_results)
            for item in videos:
                vid = item['id']['videoId']
                snippet = item['snippet']
                title = snippet.get('title', 'Unknown')
                desc = snippet.get('description', '')
                channel = snippet.get('channelTitle', 'Unknown')
                published = snippet.get('publishedAt', '')[:10]

                urls = extract_urls(desc)
                for url in urls:
                    domain = clean_domain(url)
                    if not domain or is_major_platform(domain) or domain in all_domains:
                        continue
                    all_domains.add(domain)
                    status = check_domain_availability(domain)
                    time.sleep(0.2)

                    results.append({
                        'domain': domain,
                        'full_url': url,
                        'availability': status,
                        'video_title': title,
                        'video_id': vid,
                        'channel': channel,
                        'published': published,
                        'views': 'unknown',
                        'found_at': datetime.now().strftime('%Y-%m-%d %H:%M')
                    })

                time.sleep(0.3)

        progress_bar.progress(1.0)
        status_text.markdown("<div class='success-box' style='margin-top:0.5rem;'>Scan complete! Found {} unique domains.</div>".format(len(results)), unsafe_allow_html=True)
        st.session_state.results = results
        st.session_state.scanning = False
        time.sleep(0.5)
        st.rerun()

    elif start_scan and not api_key:
        st.markdown("<div class='error-box'>Please enter your YouTube Data API key in Configuration above.</div>", unsafe_allow_html=True)
    elif start_scan and not inputs_text.strip():
        st.markdown("<div class='error-box'>Please enter at least one search query or video URL.</div>", unsafe_allow_html=True)

    # --- RESULTS ---
    if st.session_state.results:
        results = st.session_state.results

        st.divider()
        st.markdown("<h3>Results</h3>", unsafe_allow_html=True)

        # Stats cards
        available = [r for r in results if r['availability'] == 'likely_available']
        taken = [r for r in results if r['availability'] == 'taken']
        errors = [r for r in results if r['availability'] in ('error', 'timeout')]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number'>{len(results)}</div>
                <div class='stats-label'>Total Domains</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#22c55e;'>{len(available)}</div>
                <div class='stats-label'>Likely Available</div>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#ef4444;'>{len(taken)}</div>
                <div class='stats-label'>Taken / Active</div>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class='stats-card'>
                <div class='stats-number' style='color:#f59e0b;'>{len(errors)}</div>
                <div class='stats-label'>Errors</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filter tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Available", "Taken", "Errors", "All Results"])

        def show_table(data, tab):
            if not data:
                tab.markdown("<p style='color:#94a3b8; text-align:center; padding:2rem;'>No results in this category.</p>", unsafe_allow_html=True)
                return

            df_data = []
            for r in data:
                status_label = {
                    'likely_available': 'AVAILABLE',
                    'taken': 'TAKEN',
                    'error': 'ERROR',
                    'timeout': 'TIMEOUT'
                }.get(r['availability'], 'UNKNOWN')

                status_color = {
                    'likely_available': '#22c55e',
                    'taken': '#ef4444',
                    'error': '#f59e0b',
                    'timeout': '#f59e0b'
                }.get(r['availability'], '#94a3b8')

                df_data.append({
                    'Status': f"<span style='color:{status_color}; font-weight:700; font-size:0.75rem;'>{status_label}</span>",
                    'Domain': r['domain'],
                    'Video': r['video_title'][:50] + '...' if len(r['video_title']) > 50 else r['video_title'],
                    'Channel': r['channel'],
                    'Published': r['published'],
                    'Views': r['views'],
                    'Link': r['full_url']
                })

            tab.dataframe(df_data, use_container_width=True, hide_index=True)

        show_table(available, tab1)
        show_table(taken, tab2)
        show_table(errors, tab3)
        show_table(results, tab4)

        # CSV Export
        st.divider()
        st.markdown("<h3>Export Results</h3>", unsafe_allow_html=True)

        if results:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['domain', 'full_url', 'availability', 'video_title', 'video_id', 'channel', 'published', 'views', 'found_at'])
            writer.writeheader()
            writer.writerows(results)
            csv_bytes = output.getvalue().encode('utf-8')

            col1, col2 = st.columns([2, 4])
            with col1:
                st.download_button(
                    label="Download CSV",
                    data=csv_bytes,
                    file_name=f"expired_domains_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                st.markdown(f"<p style='color:#94a3b8; padding-top:0.75rem;'>File: <code>expired_domains_{datetime.now().strftime('%Y%m%d_%H%M')}.csv</code> • {len(results)} rows</p>", unsafe_allow_html=True)

# ============================================================
# ROUTING
# ============================================================
if not st.session_state.logged_in:
    show_login()
else:
    show_app()

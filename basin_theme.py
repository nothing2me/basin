"""Presentation styles and a shortcut to Streamlit's native theme picker.

Native themes keep canvas dataframes, popup menus and plots in sync. The small
browser-only shortcut uses the installed Streamlit menu instead of changing
server config or reloading a user's workspace.
"""
import streamlit as st


def apply_design():
    st.html("""<style>
body{
    --basin-text-strong:#182127;--basin-text:#20292E;--basin-muted:#4D5C66;
    --basin-surface:#F3F6FA;--basin-surface-elevated:#FFFFFF;--basin-surface-soft:#E2EAF2;
    --basin-border:#8796A0;--basin-info-text:#075985;--basin-success-text:#166534;
    --basin-warning-text:#92400E;--basin-danger-text:#991B1B;
    --basin-user-avatar-bg:#23856d;
}
body.basin-theme-dark{
    --basin-text-strong:#F7FAFC;--basin-text:#E7ECEF;--basin-muted:#B6C2CA;
    --basin-surface:#171C20;--basin-surface-elevated:#1E262C;--basin-surface-soft:#252D33;
    --basin-border:#65737D;--basin-info-text:#7DD3FC;--basin-success-text:#86EFAC;
    --basin-warning-text:#FCD34D;--basin-danger-text:#FCA5A5;
    --basin-user-avatar-bg:#23856d;
}
body.basin-theme-light{
    --basin-text-strong:#182127;--basin-text:#20292E;--basin-muted:#4D5C66;
    --basin-surface:#F3F6FA;--basin-surface-elevated:#FFFFFF;--basin-surface-soft:#E2EAF2;
    --basin-border:#8796A0;--basin-info-text:#075985;--basin-success-text:#166534;
    --basin-warning-text:#92400E;--basin-danger-text:#991B1B;
    --basin-user-avatar-bg:#23856d;
}
.block-container{padding:4.25rem 2.8rem 6.5rem;max-width:1560px}
[data-testid="stAppDeployButton"], #MainMenu, [data-testid="stMainMenuButton"], .stDeployButton{display:none!important}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{border-right:1px solid color-mix(in srgb,currentColor 12%,transparent)}
[data-testid="stSidebarUserContent"]{padding-top:.25rem!important}
[data-testid="stVerticalBlock"]{gap:.7rem}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.5rem}
.basin-brand{margin:0 0 .65rem}
.basin-brand img{display:block;width:min(100%,220px);height:auto;margin-bottom:.35rem;background:#20292E;padding:10px;border-radius:8px;box-sizing:border-box}
.basin-brand small{font-size:.73rem;color:var(--basin-muted)!important;letter-spacing:.08em;text-transform:uppercase}
.basin-eyebrow{font-size:.67rem;font-weight:700;letter-spacing:.14em;color:var(--basin-muted)!important;margin-top:8px}
h1,h2,h3{letter-spacing:-.025em}
h3{font-size:1.6rem!important;font-weight:650!important}
[data-testid="stMetric"]{border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:13px;padding:11px 14px;background:color-mix(in srgb,currentColor 2%,transparent)}
[data-testid="stMetricValue"]{font-size:1.7rem;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:-.025em}
[data-testid="stMetricLabel"]{font-size:.76rem;color:var(--basin-muted)!important;opacity:1}
[data-testid="stCaptionContainer"]{font-size:.78rem;color:var(--basin-muted)!important;opacity:1}
[data-testid="stCaptionContainer"] *{color:inherit!important}
[data-testid="stSidebar"] [role="radiogroup"]{gap:5px}
[data-testid="stSidebar"], [data-testid="stSidebarNav"], button[data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"]{display:none!important}
.basin-top-brand{text-align:center;font-size:2.3rem;font-weight:900;letter-spacing:.14em;margin:0;line-height:1.1}
.basin-top-sub{text-align:center;font-size:.75rem;letter-spacing:.16em;color:var(--basin-muted)!important;text-transform:uppercase;margin:2px 0 0}
.basin-header-text-btn{padding:0;margin:6px 0 0;text-align:center}
.basin-header-text-btn [data-testid="stButton"] button{
    background:transparent!important;
    border:none!important;
    border-radius:0!important;
    box-shadow:none!important;
    outline:none!important;
    min-height:auto!important;
    height:auto!important;
    padding:8px 4px 14px 4px!important;
    width:100%!important;
    justify-content:center!important;
    transition:color .15s ease, border-bottom .15s ease!important;
}
.basin-header-text-btn [data-testid="stButton"] button p{
    font-size:1.45rem!important;
    line-height:1.2!important;
    letter-spacing:-.02em!important;
    margin:0!important;
}
.basin-nav-active [data-testid="stButton"] button{
    border-bottom:3.5px solid currentColor!important;
}
.basin-nav-active [data-testid="stButton"] button p{
    font-weight:800!important;
    color:currentColor!important;
    opacity:1!important;
}
.basin-nav-ready [data-testid="stButton"] button{
    border-bottom:3.5px solid transparent!important;
    cursor:pointer!important;
}
.basin-nav-ready [data-testid="stButton"] button p{
    font-weight:600!important;
    color:var(--basin-muted)!important;
    opacity:1!important;
}
.basin-nav-ready [data-testid="stButton"] button:hover{
    border-bottom:3.5px solid color-mix(in srgb,currentColor 35%,transparent)!important;
}
.basin-nav-ready [data-testid="stButton"] button:hover p{
    opacity:1!important;
}
.basin-nav-locked [data-testid="stButton"] button{
    border-bottom:3.5px solid transparent!important;
    opacity:.62!important;
    cursor:not-allowed!important;
}
.basin-nav-locked [data-testid="stButton"] button p{
    font-weight:500!important;
    color:var(--basin-muted)!important;
}
.basin-top-logo-wrap{display:flex;justify-content:center;align-items:center;padding:2px 0;margin:0 auto;text-align:center}
.basin-top-logo-dark{height:54px;width:auto;max-width:280px;object-fit:contain;display:block;background:#1e293b;border:1px solid rgba(255,255,255,0.08);padding:6px 20px;border-radius:10px;box-sizing:content-box;box-shadow:0 2px 6px rgba(0,0,0,0.18)}
.basin-top-logo-light{display:none;height:54px;width:auto;max-width:280px;object-fit:contain;background:#e2e8f0;border:1px solid rgba(0,0,0,0.08);padding:6px 20px;border-radius:10px;box-sizing:content-box;box-shadow:0 2px 6px rgba(0,0,0,0.05)}
body.basin-theme-light .basin-top-logo-dark{display:none}
body.basin-theme-light .basin-top-logo-light{display:block}
body.basin-theme-dark .basin-top-logo-dark{display:block}
body.basin-theme-dark .basin-top-logo-light{display:none}

/* Tactile smooth micro-interactions on clicks & hovers (0ms loading time overhead) */
[data-testid="stButton"] button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"], [role="tab"], .stSelectbox div[data-baseweb="select"] {
    transition: transform 0.12s cubic-bezier(0.16, 1, 0.3, 1), background-color 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease !important;
}
[data-testid="stButton"] button:active, [data-testid="stBaseButton-secondary"]:active, [data-testid="stBaseButton-primary"]:active, [role="tab"]:active {
    transform: scale(0.985) !important;
}
.stTabs [role="tab"] {
    transition: color 0.14s ease, border-color 0.14s ease, background-color 0.14s ease !important;
}
.st-key-notes_slide_drawer{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:min(680px,94vw)!important;z-index:99995!important;transition:left .35s cubic-bezier(0.16, 1, 0.3, 1)!important;pointer-events:none!important}
.st-key-notes_slide_drawer *{pointer-events:none!important}
.st-key-notes_slide_drawer button, .st-key-notes_slide_drawer textarea, .st-key-notes_slide_drawer input, .st-key-notes_slide_drawer a{pointer-events:auto!important}
body.basin-assistant-open .st-key-notes_slide_drawer{left:calc((100vw - var(--basin-assistant-width, 520px))/2)!important}
@media(max-width:950px){body.basin-assistant-open .st-key-notes_slide_drawer{left:50%!important}}
.st-key-notes_drawer_closed,.st-key-notes_drawer_panel{background:var(--basin-surface-elevated, #FFFFFF)!important;color:var(--basin-text, #20292E)!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-bottom:none!important;border-radius:14px 14px 0 0!important;padding:8px 20px 18px 20px!important;box-shadow:0 -4px 20px rgba(0,0,0,.15)!important;height:520px!important;max-height:78vh!important;transform:translate3d(0, calc(100% - 44px), 0)!important;overflow:hidden!important;transition:transform .32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow .32s ease!important;will-change:transform}
body.basin-notes-open .st-key-notes_drawer_panel,.st-key-notes_drawer_panel.is-open{background:var(--basin-surface-elevated, #FFFFFF)!important;color:var(--basin-text, #20292E)!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-bottom:none!important;border-radius:14px 14px 0 0!important;padding:8px 20px 18px 20px!important;box-shadow:0 -8px 36px rgba(0,0,0,.25)!important;height:520px!important;max-height:78vh!important;transform:translate3d(0, 0, 0)!important;overflow-y:auto!important;transition:transform .32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow .32s ease!important;will-change:transform}
.st-key-notes_header_btn{display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;height:44px!important}
.st-key-notes_header_btn button{background:transparent!important;border:none!important;font-size:.92rem!important;font-weight:750!important;letter-spacing:-.01em!important;text-align:center!important;display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;height:44px!important;padding:0 8px!important;cursor:pointer!important;box-shadow:none!important;color:var(--basin-text-strong, #182127)!important}
.st-key-notes_header_btn button *{color:var(--basin-text-strong, #182127)!important}
.st-key-notes_header_btn button:hover{background:color-mix(in srgb,currentColor 8%,transparent)!important;border-radius:8px!important}
.st-key-notes_drawer_panel [data-testid="stCaptionContainer"],.st-key-notes_drawer_panel [data-testid="stCaptionContainer"] *{color:var(--basin-muted, #4D5C66)!important}
.st-key-notes_drawer_panel textarea,.st-key-notes_drawer_panel [data-testid="stTextArea"] textarea,.st-key-notes_drawer_panel div[data-baseweb="textarea"]{background:var(--basin-surface, #F3F6FA)!important;color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-radius:8px!important;font-size:0.95rem!important;line-height:1.55!important}
.st-key-notes_drawer_panel [data-testid="stTextArea"] div[data-baseweb="textarea"]{background:var(--basin-surface, #F3F6FA)!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-radius:8px!important}
.st-key-notes_drawer_panel [data-testid="stTextArea"] textarea{background:transparent!important;border:none!important;color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important;font-size:0.95rem!important;line-height:1.55!important}
.st-key-notes_drawer_panel textarea:focus,.st-key-notes_drawer_panel [data-testid="stTextArea"] textarea:focus,.st-key-notes_drawer_panel div[data-baseweb="textarea"]:focus-within{border-color:#2b7a9e!important;box-shadow:0 0 0 2px color-mix(in srgb, #2b7a9e 20%, transparent)!important}
.st-key-notes_drawer_panel textarea::placeholder{color:var(--basin-muted, #4D5C66)!important;-webkit-text-fill-color:var(--basin-muted, #4D5C66)!important}
.basin-decision-summary-hero{padding:16px 20px!important;border-radius:12px!important;background:color-mix(in srgb,currentColor 3%,transparent)!important;border:1.5px solid color-mix(in srgb,currentColor 18%,transparent)!important;margin:8px 0 16px 0!important}
.basin-decision-summary-hero h3{margin:0 0 10px 0!important;font-size:1.3rem!important;font-weight:750!important;letter-spacing:-.02em!important}
.basin-scen-grid{display:grid!important;grid-template-columns:repeat(auto-fit, minmax(170px, 1fr))!important;gap:10px!important;margin:10px 0 14px 0!important}
.basin-scen-card{padding:12px 14px!important;border-radius:8px!important;background:color-mix(in srgb,currentColor 4%,transparent)!important;border:1px solid color-mix(in srgb,currentColor 12%,transparent)!important}
.basin-scen-card .scen-lbl{font-size:.74rem!important;font-weight:750!important;text-transform:uppercase!important;opacity:.78!important;letter-spacing:.04em!important}
.basin-scen-card .scen-val{font-size:1.25rem!important;font-weight:800!important;line-height:1.25!important;margin:3px 0!important}
.basin-scen-card .scen-sub{font-size:.76rem!important;opacity:.8!important;line-height:1.35!important}
.basin-notes-tab-title{font-size:.88rem;font-weight:750;line-height:2.2;letter-spacing:-.01em;text-align:center}
.st-key-review_accept_box [data-testid="stButton"] button{font-size:1.35rem!important;font-weight:800!important;min-height:3.8rem!important;padding:14px 28px!important;border-radius:12px!important;letter-spacing:.05em!important;text-transform:uppercase!important;background:#0ea5e9!important;color:#fff!important;border:none!important;box-shadow:0 4px 18px rgba(14,165,233,.35)!important;margin:10px auto!important;display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important}
.st-key-review_accept_box [data-testid="stButton"] button:hover{background:#0284c7!important;box-shadow:0 6px 24px rgba(14,165,233,.5)!important}
.st-key-review_accept_box [data-testid="stButton"] button *{color:#fff!important}
.basin-scenario-summary{background:var(--basin-surface-soft)!important;border-left:4px solid #0ea5e9!important;color:var(--basin-text)!important;padding:14px 18px!important;border-radius:4px 10px 10px 4px!important;margin:10px 0 14px 0!important;font-size:0.95rem!important;line-height:1.55!important;font-weight:500!important;box-shadow:0 1px 3px rgba(0,0,0,0.12)!important}
body.basin-theme-bw .basin-scenario-summary{background:#111!important;border-left:4px solid #fff!important;color:#fff!important}
.basin-callout-card{padding:14px 20px!important;border-radius:10px!important;background:color-mix(in srgb,currentColor 4%,transparent)!important;border:1px solid color-mix(in srgb,currentColor 15%,transparent)!important;margin:12px 0 14px 0!important}
.basin-callout-card .metric-label{font-size:0.84rem!important;font-weight:700!important;letter-spacing:0.04em!important;text-transform:uppercase!important;opacity:0.82!important;margin-bottom:4px!important}
.basin-callout-card .metric-val{font-size:1.4rem!important;font-weight:800!important;line-height:1.25!important;margin:4px 0!important}
.basin-callout-card .metric-desc{font-size:0.85rem!important;opacity:0.85!important;line-height:1.45!important;margin-top:4px!important}
body.basin-theme-bw .basin-callout-card{background:#000!important;border:1.5px solid #fff!important}
body.basin-theme-bw,body.basin-theme-bw .stApp,body.basin-theme-bw [data-testid="stAppViewContainer"],body.basin-theme-bw [data-testid="stHeader"]{background-color:#000!important;background-image:none!important;color:#fff!important}
body.basin-theme-bw .block-container{background-color:#000!important}
body.basin-theme-bw p,body.basin-theme-bw span,body.basin-theme-bw label,body.basin-theme-bw h1,body.basin-theme-bw h2,body.basin-theme-bw h3,body.basin-theme-bw [data-testid="stMarkdownContainer"] *{color:#fff!important}
body.basin-theme-bw [data-testid="stMetric"],body.basin-theme-bw .basin-gate-card,body.basin-theme-bw [data-testid="stExpander"]{background-color:#000!important;border:1.5px solid #fff!important}
body.basin-theme-bw button[kind="primary"],body.basin-theme-bw button[data-testid="stBaseButton-primary"],body.basin-theme-bw .st-key-review_accept_box button{background-color:#fff!important;color:#000!important;border:2px solid #fff!important}
body.basin-theme-bw button[kind="primary"] *,body.basin-theme-bw button[data-testid="stBaseButton-primary"] *,body.basin-theme-bw .st-key-review_accept_box button *{color:#000!important}
body.basin-theme-bw button[kind="secondary"],body.basin-theme-bw button[data-testid="stBaseButton-secondary"]{background-color:#000!important;color:#fff!important;border:1.5px solid #fff!important}
body.basin-theme-bw button[kind="secondary"] *,body.basin-theme-bw button[data-testid="stBaseButton-secondary"] *{color:#fff!important}
body.basin-theme-bw .basin-nav-active [data-testid="stButton"] button{border-bottom:4px solid #fff!important}
body.basin-theme-bw .basin-nav-divider{border-bottom:1.5px solid #fff!important}
body.basin-theme-bw .basin-top-logo{filter:none!important}
body.basin-theme-bw .basin-top-logo-dark{display:block!important;filter:none!important}
body.basin-theme-bw .basin-top-logo-light{display:none!important}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:7px 10px;margin:0;transition:background .15s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:has([aria-checked="true"]){background:color-mix(in srgb,#356273 28%,transparent);font-weight:650}
[data-testid="stExpander"]{border-radius:11px!important}
[data-testid="stExpander"] details summary{font-size:.86rem;padding-block:10px}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:11px;overflow:hidden}
[data-testid="stButton"],[data-testid="stDownloadButton"],[data-testid="stFormSubmitButton"]{width:100%!important}
[data-testid="stButton"]>button,[data-testid="stDownloadButton"]>button,[data-testid="stFormSubmitButton"]>button{
    width:100%!important;min-width:100%!important;min-height:2.75rem!important;box-sizing:border-box!important;cursor:pointer;touch-action:manipulation
}
[data-testid="stButton"]>button *,[data-testid="stDownloadButton"]>button *,[data-testid="stFormSubmitButton"]>button *{pointer-events:none!important}
[data-testid="stButton"]>button:disabled,[data-testid="stDownloadButton"]>button:disabled,[data-testid="stFormSubmitButton"]>button:disabled{cursor:not-allowed}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{font-size:.86rem;font-weight:550}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"],[data-testid="stDownloadButton"] button[kind="primary"],button[data-testid="stBaseButton-primary"]{color:#fff!important}
[data-testid="stButton"] button[kind="primary"] *,[data-testid="stFormSubmitButton"] button[kind="primary"] *,[data-testid="stDownloadButton"] button[kind="primary"] *,button[data-testid="stBaseButton-primary"] *{color:#fff!important}
[data-tag]{background:#356273!important;color:#fff!important}
[data-tag] *{color:#fff!important}
[data-testid="stButtonGroup"] [data-selected],
[data-testid="stSegmentedControl"] [data-selected],
[data-baseweb="button-group"] [data-selected],
button[data-variant="segmented_control"][data-selected],
button[data-variant="pills"][data-selected],
[data-baseweb="button-group"] button[aria-checked="true"],
[data-baseweb="button-group"] button[data-checked="true"],
[data-testid="stButtonGroup"] button[aria-checked="true"],
.st-key-step1_goal_segmented [data-selected],
.st-key-step1_goal_segmented button[data-selected] {
    background-color: #2b7a9e !important;
    color: #ffffff !important;
}
[data-testid="stButtonGroup"] [data-selected] *,
[data-testid="stSegmentedControl"] [data-selected] *,
[data-baseweb="button-group"] [data-selected] *,
button[data-variant="segmented_control"][data-selected] *,
button[data-variant="pills"][data-selected] *,
[data-baseweb="button-group"] button[aria-checked="true"] *,
[data-baseweb="button-group"] button[data-checked="true"] *,
[data-testid="stButtonGroup"] button[aria-checked="true"] *,
.st-key-step1_goal_segmented [data-selected] *,
.st-key-step1_goal_segmented button[data-selected] * {
    color: #ffffff !important;
    fill: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stButtonGroup"] [data-selected]:hover,
[data-testid="stSegmentedControl"] [data-selected]:hover,
button[data-variant="segmented_control"][data-selected]:hover,
.st-key-step1_goal_segmented [data-selected]:hover {
    background-color: #236785 !important;
    color: #ffffff !important;
}
[data-testid="stButtonGroup"] [data-selected]:hover *,
[data-testid="stSegmentedControl"] [data-selected]:hover *,
button[data-variant="segmented_control"][data-selected]:hover *,
.st-key-step1_goal_segmented [data-selected]:hover * {
    color: #ffffff !important;
    fill: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-testid="stTabs"] button[aria-selected="true"],
[data-baseweb="tab"][aria-selected="true"] {
    color: var(--basin-primary, #2b7a9e) !important;
    font-weight: 700 !important;
}
body.basin-theme-light [data-testid="stTabs"] button[aria-selected="true"] p,
body.basin-theme-light [data-baseweb="tab"][aria-selected="true"] p {
    color: #1a5670 !important;
    font-weight: 750 !important;
}
button:focus-visible,a:focus-visible{outline:2px solid currentColor!important;outline-offset:3px}
[data-testid="stCheckbox"]:has(input:focus-visible),[data-testid="stRadio"]:has(input:focus-visible){outline:2px solid currentColor!important;outline-offset:3px;border-radius:6px}
.st-key-welcome{padding:30px 34px;border:1px solid color-mix(in srgb,currentColor 24%,transparent);border-radius:18px;background:color-mix(in srgb,currentColor 3%,transparent);margin:6px 0 16px}
.welcome-title{font-size:2rem!important;line-height:1.25!important;margin:8px 0 14px!important;font-weight:650!important}
.welcome-copy{max-width:610px;line-height:1.6;opacity:.8;font-size:1rem}
.welcome-steps{display:flex;flex-wrap:wrap;gap:14px 32px;padding-top:18px;border-top:1px solid color-mix(in srgb,currentColor 12%,transparent);font-size:.8rem;opacity:.85}
.welcome-steps b{font-variant-numeric:tabular-nums;color:inherit;margin-right:8px}
.st-key-decision_summary{padding:10px 14px!important;border-color:color-mix(in srgb,currentColor 18%,transparent)!important;background:color-mix(in srgb,currentColor 2%,transparent)}
.st-key-decision_summary [data-testid="stMarkdownContainer"] p{margin-bottom:0}
.st-key-decision_summary [data-testid="stCaptionContainer"]{margin-top:0}
.st-key-tutorial_guide{background:color-mix(in srgb,currentColor 4%,transparent);border:1px solid color-mix(in srgb,currentColor 30%,transparent);border-left:4px solid currentColor;border-radius:12px;padding:18px 22px;margin:4px 0 12px}
[data-testid="stSidebar"] .st-key-tutorial_guide{padding:10px;margin:0}
[data-testid="stSidebar"] .tutorial-description,[data-testid="stSidebar"] .tutorial-location{display:none}
[data-testid="stSidebar"] .tutorial-title{font-size:.9rem}
[data-testid="stSidebar"] .tutorial-action{font-size:.8rem;line-height:1.4}
.tutorial-meta{font-size:.67rem;letter-spacing:.09em;opacity:.85;margin-bottom:7px}
.tutorial-title{font-size:1.06rem;font-weight:650;margin:0 0 6px}
.tutorial-description{font-size:.83rem;opacity:.85;margin:0 0 10px;line-height:1.5;max-width:960px}
.tutorial-action{font-size:.88rem;margin:0 0 10px;line-height:1.5}
.tutorial-location,.tutorial-target-label{font-size:.75rem;font-weight:650;opacity:.85;line-height:1.4}
.tutorial-anchor{scroll-margin-top:5rem}
.st-key-tutorial_guide a{color:inherit;text-decoration-color:currentColor;text-underline-offset:3px}
.basin-theme-picker{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;padding:2px 0 10px;border-bottom:1px solid color-mix(in srgb,currentColor 20%,transparent)}
.basin-theme-picker button{font:inherit;cursor:pointer;border:0;border-radius:10px;background:transparent;color:inherit;padding:9px 5px 8px;display:flex;flex-direction:column;align-items:center;gap:4px;line-height:1.1}
.basin-theme-picker button:hover,.basin-theme-picker button:focus-visible{background:color-mix(in srgb,currentColor 12%,transparent)}
.basin-theme-icon{font-size:1.45rem;line-height:1;font-weight:500}
.basin-theme-label{font-size:.78rem;font-weight:560}
.basin-theme-status{font-size:.72rem;line-height:1.35;margin:5px 0 0;opacity:.8}
div[data-testid="stPopoverBody"]{background:var(--basin-surface-elevated, #FFFFFF)!important;color:var(--basin-text, #20292E)!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-radius:12px!important;box-shadow:0 8px 30px rgba(0,0,0,0.18)!important}
div[data-testid="stPopoverBody"] p,div[data-testid="stPopoverBody"] span,div[data-testid="stPopoverBody"] label,div[data-testid="stPopoverBody"] div{color:var(--basin-text, #20292E)!important}
div[data-testid="stPopoverBody"] strong,div[data-testid="stPopoverBody"] h1,div[data-testid="stPopoverBody"] h2,div[data-testid="stPopoverBody"] h3,div[data-testid="stPopoverBody"] h4{color:var(--basin-text-strong, #182127)!important}
div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"],div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] *,div[data-testid="stPopoverBody"] small{color:var(--basin-muted, #4D5C66)!important}
div[data-testid="stPopoverBody"] button[kind="secondary"],div[data-testid="stPopoverBody"] button[data-testid="stBaseButton-secondary"]{color:var(--basin-text-strong, #182127)!important;background:var(--basin-surface, #F3F6FA)!important;border:1.5px solid var(--basin-border, #8796A0)!important}
div[data-testid="stPopoverBody"] button[kind="secondary"] *,div[data-testid="stPopoverBody"] button[data-testid="stBaseButton-secondary"] *{color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important}
div[data-testid="stPopoverBody"] button[kind="primary"],div[data-testid="stPopoverBody"] button[data-testid="stBaseButton-primary"]{background:#356273!important;color:#FFFFFF!important;border:none!important}
div[data-testid="stPopoverBody"] button[kind="primary"] *,div[data-testid="stPopoverBody"] button[data-testid="stBaseButton-primary"] *{color:#FFFFFF!important;-webkit-text-fill-color:#FFFFFF!important}
div[data-baseweb="popover"] ul[role="listbox"]{background:var(--basin-surface-elevated, #FFFFFF)!important;color:var(--basin-text, #20292E)!important;border:1px solid var(--basin-border, #8796A0)!important}
div[data-baseweb="popover"] li[role="option"]{color:var(--basin-text, #20292E)!important}
div[data-baseweb="popover"] li[role="option"]:hover,div[data-baseweb="popover"] li[aria-selected="true"]{background:var(--basin-surface-soft, #E2EAF2)!important;color:var(--basin-text-strong, #182127)!important}
div[data-testid="stPopoverBody"]:has(.basin-theme-picker){min-width:310px!important;max-width:340px!important;padding:14px 12px!important;border-radius:10px!important}
div[data-testid="stPopoverBody"]:has(.basin-theme-picker) [data-testid="stExpander"]{border:0!important;border-top:1px solid color-mix(in srgb,currentColor 20%,transparent)!important;border-radius:0!important;margin:0!important}
div[data-testid="stPopoverBody"]:has(.basin-theme-picker) [data-testid="stExpander"] details summary{padding:12px 3px!important;font-size:.84rem!important;font-weight:560!important}
.st-key-home_map_card,.st-key-home_upload_card,.st-key-home_rainfall_card,.st-key-home_sources_card{background:color-mix(in srgb,currentColor 2.5%,transparent)!important;border-color:color-mix(in srgb,currentColor 20%,transparent)!important;border-radius:14px!important}
.st-key-home_map_card,.st-key-home_upload_card{height:100%!important}
@media(max-width:800px){.block-container{padding:4rem 1rem 5rem}.st-key-welcome{padding:20px}.welcome-title{font-size:1.65rem!important}.st-key-tutorial_guide{padding:14px}h3{font-size:1.3rem!important}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
.st-key-assistant_drawer{position:fixed!important;top:0!important;right:0!important;width:var(--basin-assistant-width, 520px);min-width:380px;max-width:92vw;height:100vh!important;background:var(--basin-surface-elevated, #FFFFFF)!important;color:var(--basin-text, #20292E)!important;border-left:1.5px solid var(--basin-border, #8796A0)!important;box-shadow:-14px 0 42px rgba(3,10,14,.18)!important;z-index:99998!important;padding:1.45rem 1.4rem 1.75rem!important;resize:horizontal!important;overflow-x:hidden!important;overflow-y:auto!important;transform:translate3d(100%, 0, 0)!important;transition:transform .32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow .32s ease, width .22s cubic-bezier(0.16, 1, 0.3, 1)!important;will-change:transform;pointer-events:none!important;visibility:hidden}
body.basin-theme-dark .st-key-assistant_drawer{box-shadow:-14px 0 42px rgba(3,10,14,.42)!important}
body.basin-assistant-open .st-key-assistant_drawer{transform:translate3d(0, 0, 0)!important;pointer-events:auto!important;visibility:visible!important}
.block-container,[data-testid="stMainBlockContainer"]{transition:margin-right .32s cubic-bezier(0.16, 1, 0.3, 1), max-width .32s cubic-bezier(0.16, 1, 0.3, 1)!important}
body.basin-assistant-open .block-container,body.basin-assistant-open [data-testid="stMainBlockContainer"]{margin-right:calc(var(--basin-assistant-width, 520px) + 5px)!important;max-width:calc(100% - var(--basin-assistant-width, 520px) - 15px)!important;padding-right:1.5rem!important}
@media(max-width:950px){body.basin-assistant-open .block-container,body.basin-assistant-open [data-testid="stMainBlockContainer"]{margin-right:0!important;max-width:100%!important}}
.st-key-assistant_tab_closed,.st-key-assistant_tab_open{position:fixed!important;top:50%!important;transform:translateY(-50%)!important;width:42px!important;max-width:42px!important;height:120px!important;min-height:120px!important;overflow:visible!important;z-index:99999!important;pointer-events:none!important;margin:0!important;padding:0!important;transition:right .32s cubic-bezier(0.16, 1, 0.3, 1)!important}
.st-key-assistant_tab_closed *,.st-key-assistant_tab_open *{pointer-events:none!important}
.st-key-assistant_tab_closed > div,.st-key-assistant_tab_open > div{width:42px!important;margin:0!important;padding:0!important}
.st-key-assistant_tab_closed [data-testid="stElementContainer"],.st-key-assistant_tab_open [data-testid="stElementContainer"]{width:42px!important;margin:0!important;padding:0!important}
.st-key-assistant_tab_closed button,.st-key-assistant_tab_open button{pointer-events:auto!important;width:42px!important;margin:0!important}
.st-key-assistant_tab_closed{right:0!important}
.st-key-assistant_tab_open{right:var(--basin-assistant-width, 520px)!important}
body.basin-assistant-open .st-key-assistant_tab_closed,body.basin-assistant-open .st-key-assistant_tab_open{right:var(--basin-assistant-width, 520px)!important}
body:not(.basin-assistant-open) .st-key-assistant_tab_open,body:not(.basin-assistant-open) .st-key-assistant_tab_closed{right:0!important}
@media(max-width:550px){body.basin-assistant-open .st-key-assistant_tab_open,body.basin-assistant-open .st-key-assistant_tab_closed{right:92vw!important}.st-key-assistant_drawer{width:92vw!important}}
.st-key-assistant_tab_closed button,.st-key-assistant_tab_open button{border-radius:8px 0 0 8px!important;padding:18px 8px!important;writing-mode:vertical-rl!important;text-orientation:mixed!important;transform:none!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.09em!important;text-transform:uppercase!important;background:#24596c!important;color:#fff!important;border:1px solid color-mix(in srgb,#fff 18%,transparent)!important;border-right:none!important;box-shadow:-4px 0 14px rgba(0,0,0,.24)!important;cursor:pointer!important;min-height:120px!important}
.st-key-assistant_tab_closed button:hover,.st-key-assistant_tab_open button:hover{background:#2878A0!important;box-shadow:-5px 0 18px rgba(5,21,29,.3)!important}
@media(max-width:760px){
    .block-container,[data-testid="stMainBlockContainer"]{padding:4rem .8rem 5rem!important}
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector){
        display:grid!important;grid-template-columns:1fr 1fr!important;gap:.55rem!important;align-items:center!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]{
        width:auto!important;min-width:0!important;flex:unset!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(1){grid-column:1;grid-row:2}
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(2){grid-column:1 / -1;grid-row:1}
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(3){grid-column:2;grid-row:2}
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(3) [data-testid="stHorizontalBlock"]{
        display:grid!important;grid-template-columns:1fr 1fr!important;gap:.35rem!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(3) [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{
        width:auto!important;min-width:0!important;flex:unset!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-global_unit_selector)>[data-testid="stColumn"]:nth-child(3) button{
        min-height:2.6rem!important;padding:.35rem!important;font-size:.72rem!important
    }
    .basin-top-logo-wrap{padding:0}
    .basin-top-logo-dark{height:34px;padding:5px 9px}
    .basin-top-logo-light{height:34px;width:auto;max-width:200px;padding:5px 9px;object-fit:contain;box-sizing:content-box}
    [data-testid="stHorizontalBlock"]:has(.st-key-nav_tab_Data){
        display:grid!important;grid-template-columns:1fr 1fr!important;gap:.4rem!important;margin-top:.25rem!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-nav_tab_Data)>[data-testid="stColumn"]{
        width:auto!important;min-width:0!important;flex:unset!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-nav_tab_Data) [data-testid="stButton"] button{
        min-height:2.6rem!important;height:2.6rem!important;padding:.35rem .45rem!important;
        border:1px solid color-mix(in srgb,currentColor 22%,transparent)!important;border-radius:9px!important
    }
    [data-testid="stHorizontalBlock"]:has(.st-key-nav_tab_Data) [data-testid="stButton"] button p{
        font-size:.78rem!important;line-height:1.15!important;white-space:normal!important
    }
    .st-key-notes_slide_drawer{left:50%!important;transform:translateX(-50%)!important;width:calc(100vw - 20px)!important}
    .st-key-notes_drawer_closed{transform:translateY(calc(100% - 44px))!important;height:480px!important}
    .st-key-notes_drawer_open{transform:translateY(0)!important;height:480px!important}
    .basin-notes-tab-title{font-size:.76rem;line-height:2.25}
    .st-key-assistant_tab_closed,.st-key-assistant_tab_open{
        top:auto!important;bottom:8px!important;left:auto!important;right:10px!important;transform:none!important;
        width:54px!important;max-width:54px!important;height:42px!important;min-height:42px!important
    }
    .st-key-assistant_tab_open{top:8px!important;bottom:auto!important;left:8px!important;right:auto!important}
    .st-key-assistant_tab_closed>div,.st-key-assistant_tab_open>div,
    .st-key-assistant_tab_closed [data-testid="stElementContainer"],.st-key-assistant_tab_open [data-testid="stElementContainer"]{
        width:54px!important;height:42px!important
    }
    .st-key-assistant_tab_closed button,.st-key-assistant_tab_open button{
        width:54px!important;height:42px!important;min-height:42px!important;padding:7px!important;
        border-radius:10px!important;border:1px solid color-mix(in srgb,#fff 20%,transparent)!important;
        writing-mode:horizontal-tb!important;font-size:0!important;letter-spacing:0!important
    }
    .st-key-assistant_tab_closed button::after{content:"AI";font-size:.78rem!important;font-weight:800}
    .st-key-assistant_tab_open button::after{content:"Close";font-size:.7rem!important;font-weight:800}
    .st-key-assistant_tab_closed button p,.st-key-assistant_tab_open button p{display:none!important}
    .st-key-assistant_drawer{width:100vw!important;max-width:100vw!important;min-width:0!important;padding:3.5rem 1rem 1.5rem!important;resize:none!important}
}
.basin-assistant-header{padding:1px 0 15px}
.basin-assistant-title{font-size:1.12rem!important;font-weight:750!important;letter-spacing:-.02em!important;line-height:1.2!important;margin:0 0 6px!important;color:var(--basin-text-strong, #182127)!important}
.basin-assistant-status{display:flex!important;align-items:flex-start!important;gap:8px!important;color:var(--basin-text, #20292E)!important;font-size:.75rem!important;line-height:1.25!important}
.basin-assistant-status-dot{width:8px!important;height:8px!important;border-radius:50%!important;background:#16a34a!important;box-shadow:0 0 0 3px color-mix(in srgb,#16a34a 20%,transparent)!important;margin-top:3px!important;flex:0 0 auto!important}
body.basin-theme-dark .basin-assistant-status-dot{background:#64d69b!important;box-shadow:0 0 0 3px color-mix(in srgb,#64d69b 20%,transparent)!important}
.basin-assistant-status strong{display:block!important;color:var(--basin-success-text, #166534)!important;font-size:.75rem!important;font-weight:700!important}
body.basin-theme-dark .basin-assistant-status strong{color:#7fe0ad!important}
.basin-assistant-status small{display:block!important;margin-top:2px!important;color:var(--basin-muted, #4D5C66)!important;font-size:.7rem!important;font-weight:500!important}
.st-key-assistant_close_x button{width:34px!important;height:34px!important;min-height:34px!important;border-radius:8px!important;padding:0!important;font-size:1.3rem!important;font-weight:400!important;border:1.5px solid var(--basin-border, #8796A0)!important;background:var(--basin-surface, #F3F6FA)!important;color:var(--basin-text-strong, #182127)!important}
.st-key-assistant_close_x button:hover{background:var(--basin-surface-soft, #E2EAF2)!important;border-color:#2b7a9e!important;color:var(--basin-text-strong, #182127)!important}
.basin-assistant-header-avatar{width:36px!important;height:36px!important;object-fit:contain!important;flex:0 0 36px!important;border-radius:6px!important}
.basin-assistant-empty{text-align:center;padding:24px 16px 18px;max-width:390px;margin:0 auto}
.basin-assistant-mark{width:190px!important;height:190px!important;margin:0 auto 16px!important;display:block!important;object-fit:contain!important;filter:drop-shadow(0 4px 18px rgba(0,0,0,0.18))!important}
.basin-assistant-empty h2{font-size:1.25rem!important;line-height:1.28!important;letter-spacing:-.02em!important;margin:0 0 8px!important;font-weight:750!important;color:var(--basin-text-strong, #182127)!important}
.basin-assistant-empty p{font-size:.84rem!important;line-height:1.55!important;margin:0!important;color:var(--basin-muted, #4D5C66)!important}
.st-key-quick_top1 button,.st-key-quick_compare button,.st-key-quick_concur button,.st-key-quick_ranking button,.st-key-quick_crop_et button,.st-key-quick_export button{width:100%!important;min-height:52px!important;justify-content:center!important;text-align:center!important;padding:6px 2px!important;margin-bottom:4px!important;border-radius:8px!important;border:1.5px solid var(--basin-border, #8796A0)!important;background:var(--basin-surface, #F3F6FA)!important;box-shadow:0 1px 3px rgba(0,0,0,0.04)!important;font-size:.67rem!important;font-weight:650!important;position:relative!important;display:flex!important;flex-direction:column!important;align-items:center!important;gap:2px!important;transition:background .15s ease,border-color .15s ease,transform .12s ease!important;color:var(--basin-text-strong, #182127)!important}
.st-key-quick_top1 button p,.st-key-quick_compare button p,.st-key-quick_concur button p,.st-key-quick_ranking button p,.st-key-quick_crop_et button p,.st-key-quick_export button p{font-size:.66rem!important;line-height:1.15!important;white-space:normal!important;word-break:normal!important;text-align:center!important;margin:0!important;padding:0!important;color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important;font-weight:650!important}
.st-key-quick_top1 button::before{content:"📊";font-size:1.15rem;margin:0}
.st-key-quick_compare button::before{content:"⚖️";font-size:1.15rem;margin:0}
.st-key-quick_concur button::before{content:"⚡";font-size:1.15rem;margin:0}
.st-key-quick_ranking button::before{content:"🎯";font-size:1.15rem;margin:0}
.st-key-quick_crop_et button::before{content:"🌾";font-size:1.15rem;margin:0}
.st-key-quick_export button::before{content:"📦";font-size:1.15rem;margin:0}
.st-key-quick_top1 button::after,.st-key-quick_compare button::after,.st-key-quick_concur button::after,.st-key-quick_ranking button::after,.st-key-quick_crop_et button::after,.st-key-quick_export button::after{display:none!important;content:""!important}
.st-key-quick_top1 button:hover,.st-key-quick_compare button:hover,.st-key-quick_concur button:hover,.st-key-quick_ranking button:hover,.st-key-quick_crop_et button:hover,.st-key-quick_export button:hover{border-color:#2b7a9e!important;background:var(--basin-surface-soft, #E2EAF2)!important;transform:translateY(-1px)!important}
.st-key-quick_top1 button:focus-visible,.st-key-quick_compare button:focus-visible,.st-key-quick_concur button:focus-visible,.st-key-quick_ranking button:focus-visible,.st-key-quick_crop_et button:focus-visible,.st-key-quick_export button:focus-visible,.st-key-assistant_close_x button:focus-visible{outline:2px solid #2b7a9e!important;outline-offset:2px!important}
.st-key-assistant_conversation{min-height:520px!important;margin-top:10px!important;margin-bottom:12px!important;padding:0!important}
.st-key-assistant_conversation [data-testid="stVerticalBlockBorderWrapper"]{min-height:520px!important;border:1.5px solid var(--basin-border, #8796A0)!important;border-radius:12px!important;background:var(--basin-surface, #F3F6FA)!important;padding:12px 14px!important;box-shadow:inset 0 1px 3px rgba(0,0,0,0.05)!important}
@media (max-height:850px){
    .st-key-assistant_conversation{min-height:420px!important}
    .st-key-assistant_conversation [data-testid="stVerticalBlockBorderWrapper"]{min-height:420px!important}
}
.st-key-assistant_drawer [data-testid="stChatInput"],.st-key-assistant_drawer div[data-testid="stChatInput"]{border:1.5px solid var(--basin-border, #8796A0)!important;border-radius:10px!important;background:var(--basin-surface-elevated, #FFFFFF)!important;box-shadow:0 1px 4px rgba(0,0,0,0.06)!important}
.st-key-assistant_drawer [data-testid="stChatInput"]:focus-within{border-color:#2b7a9e!important;box-shadow:0 0 0 2px color-mix(in srgb,#2b7a9e 20%,transparent)!important}
.st-key-assistant_drawer [data-testid="stChatInput"] textarea{color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important;background:transparent!important;font-size:0.92rem!important}
.st-key-assistant_drawer [data-testid="stChatInput"] textarea::placeholder{color:var(--basin-muted, #4D5C66)!important;-webkit-text-fill-color:var(--basin-muted, #4D5C66)!important;opacity:1!important}
.st-key-assistant_drawer [data-testid="stChatInput"] button{color:var(--basin-text-strong, #182127)!important}
.basin-suggested-label{font-size:.76rem!important;font-weight:750!important;letter-spacing:.04em!important;color:var(--basin-muted, #4D5C66)!important;margin:6px 0 6px!important;text-transform:uppercase!important}
.st-key-assistant_suggestions{position:sticky!important;bottom:0!important}
.st-key-assistant_suggestions{padding:2px 0 0!important}
.basin-assistant-trust{font-size:.7rem!important;line-height:1.45!important;text-align:center!important;color:var(--basin-muted, #4D5C66)!important;margin:8px 0 12px!important}
.st-key-assistant_clear_chat button{min-height:42px!important;border-radius:8px!important;font-size:.75rem!important;font-weight:600!important;border:1.5px solid var(--basin-border, #8796A0)!important;background:var(--basin-surface, #F3F6FA)!important;color:var(--basin-text, #20292E)!important;box-shadow:none!important;padding:6px 8px!important}
.st-key-assistant_clear_chat button:hover{background:var(--basin-surface-soft, #E2EAF2)!important;color:var(--basin-danger-text, #991B1B)!important;border-color:var(--basin-danger-text, #991B1B)!important}
.st-key-assistant_drawer [data-testid="stChatMessage"],.st-key-assistant_conversation [data-testid="stChatMessage"]{background:transparent!important;padding-left:14px!important;padding-right:14px!important;margin-left:2px!important;margin-right:2px!important;box-sizing:border-box!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] [data-testid^="stChatMessageAvatar"],.st-key-assistant_conversation [data-testid="stChatMessage"] > div:first-child,.st-key-assistant_conversation [data-testid="stChatMessage"] > img:first-child{margin-left:4px!important;margin-right:8px!important;flex-shrink:0!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] p,
.st-key-assistant_conversation [data-testid="stChatMessage"] span,
.st-key-assistant_conversation [data-testid="stChatMessage"] div,
.st-key-assistant_conversation [data-testid="stChatMessage"] li,
.st-key-assistant_conversation [data-testid="stChatMessage"] h1,
.st-key-assistant_conversation [data-testid="stChatMessage"] h2,
.st-key-assistant_conversation [data-testid="stChatMessage"] h3,
.st-key-assistant_conversation [data-testid="stChatMessage"] strong,
.st-key-assistant_conversation [data-testid="stChatMessage"] td,
.st-key-assistant_conversation [data-testid="stChatMessage"] th{color:var(--basin-text-strong, #182127)!important;-webkit-text-fill-color:var(--basin-text-strong, #182127)!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] table{border-collapse:collapse!important;width:100%!important;margin:8px 0!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] th,.st-key-assistant_conversation [data-testid="stChatMessage"] td{border:1px solid var(--basin-border, #8796A0)!important;padding:6px 10px!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] th{background:var(--basin-surface-soft, #E2EAF2)!important;font-weight:700!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] code{background:var(--basin-surface-soft, #E2EAF2)!important;color:var(--basin-text-strong, #182127)!important;padding:2px 5px!important;border-radius:4px!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] pre{background:var(--basin-surface-soft, #E2EAF2)!important;color:var(--basin-text-strong, #182127)!important;border:1px solid var(--basin-border, #8796A0)!important;border-radius:8px!important;padding:10px!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] pre code{background:transparent!important;padding:0!important}
.st-key-assistant_conversation [data-testid="stChatMessage"] a{color:var(--basin-info-text, #075985)!important;text-decoration:underline!important}
.st-key-assistant_drawer label,.st-key-assistant_drawer [data-testid="stSelectbox"] label,.st-key-assistant_drawer [data-testid="stMarkdownContainer"] p{color:var(--basin-text-strong, #182127)!important}
[data-testid="stChatMessageAvatarUser"]{background-color:var(--basin-user-avatar-bg,#23856d)!important;color:#ffffff!important;border-radius:8px!important;box-shadow:0 1px 3px rgba(0,0,0,0.18)!important}
[data-testid="stChatMessageAvatarUser"] *{color:#ffffff!important;fill:#ffffff!important;-webkit-text-fill-color:#ffffff!important}
[data-testid="stChatMessageAvatarAssistant"]{background-color:#2b7a9e!important;color:#ffffff!important;border-radius:8px!important}
[data-testid="stChatMessageAvatarAssistant"] *{color:#ffffff!important;fill:#ffffff!important;-webkit-text-fill-color:#ffffff!important}
.basin-pipeline-stepper{display:flex;align-items:center;justify-content:space-between;gap:8px;background:color-mix(in srgb,currentColor 3%,transparent);border:1px solid color-mix(in srgb,currentColor 14%,transparent);border-radius:12px;padding:8px 12px;margin:6px 0 16px}
.basin-step-card{flex:1;display:flex;flex-direction:column;padding:6px 10px;border-radius:8px;border:1px solid transparent;transition:background .12s ease}
.basin-step-card.active{background:color-mix(in srgb,#356273 24%,transparent);border-color:color-mix(in srgb,#356273 45%,transparent)}
.basin-step-num{font-size:.65rem;font-weight:800;letter-spacing:.08em;opacity:.75;text-transform:uppercase}
.basin-step-name{font-size:.84rem;font-weight:650;line-height:1.2;margin:1px 0}
.basin-step-status{font-size:.70rem;opacity:.75}
.basin-step-arrow{opacity:.35;font-size:.85rem;user-select:none}
</style>""")
    st.html("""<script>(() => {
const syncBasinTheme = () => {
  const app = document.querySelector('.stApp');
  if (!app) return;
  const match = getComputedStyle(app).backgroundColor.match(/[0-9.]+/g);
  if (!match || match.length < 3) return;
  const [r, g, b] = match.slice(0, 3).map(Number);
  const isLight = (0.2126 * r + 0.7152 * g + 0.0722 * b) > 145;
  document.body.classList.toggle('basin-theme-light', isLight);
  document.body.classList.toggle('basin-theme-dark', !isLight);
};
window.__basinThemeObserver?.disconnect();
syncBasinTheme();
const app = document.querySelector('.stApp');
if (app) {
  window.__basinThemeObserver = new MutationObserver(syncBasinTheme);
  window.__basinThemeObserver.observe(app, {attributes:true, attributeFilter:['class','style']});
}
window.matchMedia?.('(prefers-color-scheme: dark)').addEventListener?.('change', syncBasinTheme);

// Instant zero-latency edge drawer motion controller
if (!window.__basinDrawerControllerAttached) {
  window.__basinDrawerControllerAttached = true;
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn) return;

    if (
      btn.closest('.st-key-assistant_tab_closed') ||
      btn.closest('.st-key-btn_top_assistant') ||
      btn.getAttribute('data-testid') === 'stBaseButton-assistant_open_tab_btn'
    ) {
      document.body.classList.add('basin-assistant-open');
    } else if (
      btn.closest('.st-key-assistant_tab_open') ||
      btn.closest('.st-key-assistant_close_x') ||
      btn.getAttribute('data-testid') === 'stBaseButton-assistant_close_tab_btn' ||
      btn.getAttribute('data-testid') === 'stBaseButton-assistant_close_x'
    ) {
      document.body.classList.remove('basin-assistant-open');
    } else if (
      btn.closest('.st-key-notes_header_btn') ||
      btn.getAttribute('data-testid') === 'stBaseButton-btn_toggle_notes'
    ) {
      document.body.classList.toggle('basin-notes-open');
    }
  }, true);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (document.body.classList.contains('basin-assistant-open')) {
        document.body.classList.remove('basin-assistant-open');
        const closeX = document.querySelector('.st-key-assistant_close_x button');
        if (closeX) closeX.click();
      }
      if (document.body.classList.contains('basin-notes-open')) {
        document.body.classList.remove('basin-notes-open');
        const notesBtn = document.querySelector('.st-key-notes_header_btn button');
        if (notesBtn) notesBtn.click();
      }
    }
  });
}
})();</script>""", unsafe_allow_javascript=True)


def appearance_picker():
    # Main-menu theme items are the native persisted System/Light/Dark choices,
    # plus the high-contrast Black/White theme.
    st.html("""
<div class="basin-theme-picker" aria-label="Appearance">
 <button type="button" data-basin-theme="System"><span class="basin-theme-icon" aria-hidden="true">◐</span><span class="basin-theme-label">System</span></button>
 <button type="button" data-basin-theme="Light"><span class="basin-theme-icon" aria-hidden="true">☀</span><span class="basin-theme-label">Light</span></button>
 <button type="button" data-basin-theme="Dark"><span class="basin-theme-icon" aria-hidden="true">☾</span><span class="basin-theme-label">Dark</span></button>
</div>
<p class="basin-theme-status" role="status" aria-live="polite"></p>
<script>
(() => {
 const script = document.currentScript;
 const root = script.parentElement;
 const status = root.querySelector('.basin-theme-status');
 if (localStorage.getItem('basin-bw-theme') === 'true') {
   document.body.classList.add('basin-theme-bw');
 }
 root.querySelectorAll('[data-basin-theme]').forEach(button => {
   button.addEventListener('click', () => {
     const name = button.dataset.basinTheme;
     document.body.classList.remove('basin-theme-bw');
     localStorage.removeItem('basin-bw-theme');
     const menuButton = document.querySelector('[data-testid="stMainMenuButton"]');
     if (!menuButton) { status.textContent = 'Open the top-right menu to change appearance.'; return; }
     status.textContent = '';
     let observer, timer;
     const choose = () => {
       const item = Array.from(document.querySelectorAll('[role="menuitemradio"]'))
         .find(node => node.getAttribute('data-testid') === 'stMainMenuItem-theme-' + name);
       if (!item) return false;
       observer?.disconnect(); clearTimeout(timer);
       item.click();
       const openMenu = document.querySelector('[data-testid="stMainMenuButton"][aria-expanded="true"]');
       if (openMenu) openMenu.click();
       button.focus();
       status.textContent = name === 'System' ? 'Following your system appearance.' : name + ' appearance selected.';
       return true;
     };
     if (menuButton.getAttribute('aria-expanded') !== 'true') menuButton.click();
     if (choose()) return;
     observer = new MutationObserver(choose);
     observer.observe(document.body, {childList:true, subtree:true});
     timer = setTimeout(() => {
       observer.disconnect();
       status.textContent = 'Choose a theme in the top-right menu. If choices are missing, refresh BASIN.';
     }, 2000);
   });
 });
})();
</script>
""", unsafe_allow_javascript=True)


def accent_foreground(color: str) -> str:
    """Choose the higher-contrast black or white label for an RGB accent."""
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
    light = sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    return "#000000" if (light + .05) / .05 >= 1.05 / (light + .05) else "#FFFFFF"


COLOR_DEFAULTS = {"accent": "#356273", "selection": "#2878A0", "sidebar": "#6088A5"}


def reset_colors():
    for name, value in COLOR_DEFAULTS.items():
        st.session_state[f"appearance_{name}"] = value
        st.session_state[f"draft_{name}"] = value
    st.session_state["appearance_colorblind"] = False
    st.session_state["appearance_bw"] = False


def custom_appearance():
    for name, value in COLOR_DEFAULTS.items():
        st.session_state.setdefault(f"appearance_{name}", value)
        st.session_state.setdefault(f"draft_{name}", st.session_state[f"appearance_{name}"])
    with st.expander("Accessibility and custom colors", expanded=False):
        st.toggle("Color-blind mode", key="appearance_colorblind",
                  help="Uses a consistent blue accent plus chart shapes, line styles and patterns.")
        st.toggle("Black/white high contrast", key="appearance_bw",
                  help="Uses a strict black-and-white presentation with stronger borders.")
        st.markdown("**Custom palette**")
        with st.form("appearance_colors", border=False):
            buttons, selected, sidebar = st.columns(3, gap="small")
            buttons.color_picker("Buttons", key="draft_accent")
            selected.color_picker("Selected", key="draft_selection")
            sidebar.color_picker("Sidebar", key="draft_sidebar")
            if st.form_submit_button("Apply colors", width="stretch"):
                for name in COLOR_DEFAULTS:
                    st.session_state[f"appearance_{name}"] = st.session_state[f"draft_{name}"]
                st.success("Colors applied")
        st.button("Reset custom colors", on_click=reset_colors, width="stretch")
        st.caption("Custom colors last for this session. Light, Dark and System are saved in this browser.")
    enabled = st.session_state.appearance_colorblind
    bw_enabled = st.session_state.appearance_bw
    accent = "#356273" if enabled else st.session_state.appearance_accent
    selection = "#0072B2" if enabled else st.session_state.appearance_selection
    sidebar = "#6088A5" if enabled else st.session_state.appearance_sidebar
    foreground = accent_foreground(accent)
    selected_text = accent_foreground(selection)
    st.html(
        f"<script>document.body.classList.toggle('basin-theme-bw', {str(bw_enabled).lower()});</script>",
        unsafe_allow_javascript=True,
    )
    st.html(f"""<style>
button[kind="primary"],button[data-testid="stBaseButton-primary"] {{background:{accent}!important;border-color:{accent}!important;color:{foreground}!important}}
button[kind="primary"] *,button[data-testid="stBaseButton-primary"] * {{color:{foreground}!important}}
[data-tag] {{background:{selection}!important;color:{selected_text}!important}}
[data-tag] * {{color:{selected_text}!important}}
.st-key-welcome {{border:1px solid color-mix(in srgb,{accent} 45%,currentColor);background:color-mix(in srgb,{accent} 5%,transparent)}}
[data-testid="stSidebar"] {{background-image:linear-gradient(color-mix(in srgb,{sidebar} 14%,transparent),color-mix(in srgb,{sidebar} 14%,transparent));border-right:3px solid {sidebar}}}
[data-testid="stSidebar"] [role="radiogroup"] label:has([aria-checked="true"]) {{background:color-mix(in srgb,{selection} 18%,transparent);box-shadow:inset 3px 0 {selection};font-weight:700}}
[role="radio"][aria-checked="true"] {{border-color:{selection}!important;background-color:{selection}!important}}
input[type="radio"],input[type="checkbox"] {{accent-color:{selection}}}
</style>""")


def accessible_chart(fig):
    if not st.session_state.get("appearance_colorblind", False):
        return fig
    colors = ["#0072B2", "#E69F00", "#56B4E9", "#CC79A7", "#D55E00", "#009E73"]
    dashes = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
    symbols = ["circle", "square", "diamond", "cross", "triangle-up", "x"]
    for index, trace in enumerate(fig.data):
        color = colors[index % len(colors)]
        if trace.type == "scatter":
            trace.line.color = color
            trace.line.dash = dashes[index % len(dashes)]
            trace.marker.color = color
            trace.marker.symbol = symbols[index % len(symbols)]
        elif trace.type == "bar":
            patterns = ["", "/", "x", "-", ".", "|"]
            if isinstance(trace.marker.color, (tuple, list)):
                trace.marker.color = colors[:len(trace.marker.color)]
                trace.marker.pattern.shape = patterns[:len(trace.marker.color)]
            else:
                trace.marker.color = color
                trace.marker.pattern.shape = patterns[index % 6]
    for frame in getattr(fig, "frames", ()):
        accessible_chart(frame)
    return fig


def reveal_tour_target(target_id: str, visit: str):
    # Only internal target identifiers enter this script. Observe late Streamlit
    # rendering, then disconnect; do not repeatedly steal focus on widget edits.
    import json
    st.html("""<script>(() => {
const id = """ + json.dumps("tour-" + target_id) + """;
const visit = """ + json.dumps(visit) + """;
if (window.basinTourVisit === visit) return;
let observer, timer;
function reveal() {
 const target = document.getElementById(id);
 if (!target) return false;
 const sidebar = target.closest('[data-testid="stSidebar"]');
 if (sidebar && sidebar.getAttribute('aria-expanded') === 'false') {
   document.querySelector('[data-testid="stExpandSidebarButton"] button, button[data-testid="stExpandSidebarButton"]')?.click();
 }
 let parent = target.parentElement;
 while (parent) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
 if (!target.getClientRects().length) return false;
 observer?.disconnect(); clearTimeout(timer);
 requestAnimationFrame(() => { target.scrollIntoView({block:'start', behavior:'instant'}); target.tabIndex = -1; target.focus({preventScroll:true}); });
 window.basinTourVisit = visit;
 return true;
}
if (!reveal()) {
 observer = new MutationObserver(reveal);
 observer.observe(document.body, {childList:true, subtree:true, attributes:true, attributeFilter:['aria-expanded','open','style']});
 timer = setTimeout(() => observer.disconnect(), 5000);
}
})();</script>""", unsafe_allow_javascript=True)

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
    --basin-warning-text:#92400E;--basin-danger-text:#991B1B
}
body.basin-theme-dark{
    --basin-text-strong:#F7FAFC;--basin-text:#E7ECEF;--basin-muted:#B6C2CA;
    --basin-surface:#171C20;--basin-surface-elevated:#1E262C;--basin-surface-soft:#252D33;
    --basin-border:#65737D;--basin-info-text:#7DD3FC;--basin-success-text:#86EFAC;
    --basin-warning-text:#FCD34D;--basin-danger-text:#FCA5A5
}
body.basin-theme-light{
    --basin-text-strong:#182127;--basin-text:#20292E;--basin-muted:#4D5C66;
    --basin-surface:#F3F6FA;--basin-surface-elevated:#FFFFFF;--basin-surface-soft:#E2EAF2;
    --basin-border:#8796A0;--basin-info-text:#075985;--basin-success-text:#166534;
    --basin-warning-text:#92400E;--basin-danger-text:#991B1B
}
.block-container{padding:4.25rem 2.8rem 6.5rem;max-width:1560px}
[data-testid="stAppDeployButton"]{display:none}
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
.basin-top-logo-wrap{display:flex;justify-content:center;align-items:center;padding:4px 0;margin:0 auto}
.basin-top-logo-dark{height:46px;width:auto;max-width:260px;object-fit:contain;display:block;background:#20292E;padding:7px 12px;border-radius:8px;box-sizing:content-box}
.basin-top-logo-light{display:none;width:210px;height:60px;object-fit:cover;object-position:center 48.5%;background:transparent}
body.basin-theme-light .basin-top-logo-dark{display:none}
body.basin-theme-light .basin-top-logo-light{display:block}
body.basin-theme-dark .basin-top-logo-dark{display:block}
body.basin-theme-dark .basin-top-logo-light{display:none}
.st-key-notes_slide_drawer{position:fixed!important;bottom:0!important;left:50%!important;transform:translateX(-50%)!important;width:min(680px,94vw)!important;z-index:99995!important;transition:left .35s cubic-bezier(0.16, 1, 0.3, 1)!important;pointer-events:none!important}
.st-key-notes_slide_drawer *{pointer-events:none!important}
.st-key-notes_slide_drawer button, .st-key-notes_slide_drawer textarea, .st-key-notes_slide_drawer input, .st-key-notes_slide_drawer a{pointer-events:auto!important}
body:has(.st-key-assistant_drawer) .st-key-notes_slide_drawer{left:calc((100vw - var(--basin-assistant-width, 500px))/2)!important}
@media(max-width:950px){body:has(.st-key-assistant_drawer) .st-key-notes_slide_drawer{left:50%!important}}
.st-key-notes_drawer_closed,.st-key-notes_drawer_panel{background:var(--basin-surface-elevated)!important;color:var(--basin-text)!important;border:1.5px solid var(--basin-border)!important;border-bottom:none!important;border-radius:14px 14px 0 0!important;padding:0 16px!important;box-shadow:0 -4px 20px rgba(0,0,0,.25)!important;height:520px!important;max-height:78vh!important;transform:translateY(calc(100% - 44px))!important;overflow:hidden!important;transition:transform .32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow .3s ease!important;will-change:transform}
.st-key-notes_drawer_open,.st-key-notes_drawer_panel.is-open{background:var(--basin-surface-elevated)!important;color:var(--basin-text)!important;border:1.5px solid var(--basin-border)!important;border-bottom:none!important;border-radius:14px 14px 0 0!important;padding:8px 20px 18px 20px!important;box-shadow:0 -8px 36px rgba(0,0,0,.35)!important;height:520px!important;max-height:78vh!important;transform:translateY(0)!important;overflow-y:auto!important;transition:transform .32s cubic-bezier(0.16, 1, 0.3, 1), box-shadow .3s ease!important;will-change:transform}
.st-key-notes_header_btn{display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;height:44px!important}
.st-key-notes_header_btn button{background:transparent!important;border:none!important;font-size:.92rem!important;font-weight:750!important;letter-spacing:-.01em!important;text-align:center!important;display:flex!important;justify-content:center!important;align-items:center!important;width:100%!important;height:44px!important;padding:0 8px!important;cursor:pointer!important;box-shadow:none!important;color:currentColor!important}
.st-key-notes_header_btn button:hover{background:color-mix(in srgb,currentColor 8%,transparent)!important;border-radius:8px!important}
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
.basin-theme-picker{display:flex;gap:6px}
.basin-theme-picker button{font:inherit;font-size:.8rem;cursor:pointer;flex:1;border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-radius:8px;background:transparent;color:inherit;padding:9px 4px}
.basin-theme-picker button:hover{background:color-mix(in srgb,#356273 24%,transparent)}
.basin-theme-status{font-size:.75rem;line-height:1.4;margin:6px 0 0;opacity:.8}
@media(max-width:800px){.block-container{padding:4rem 1rem 5rem}.st-key-welcome{padding:20px}.welcome-title{font-size:1.65rem!important}.st-key-tutorial_guide{padding:14px}h3{font-size:1.3rem!important}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
.st-key-assistant_drawer{position:fixed!important;top:0!important;right:0!important;width:var(--basin-assistant-width, 520px);min-width:360px;max-width:92vw;height:100vh!important;background:color-mix(in srgb,var(--background-color,#1e262c) 98%,#000)!important;border-left:2px solid color-mix(in srgb,currentColor 16%,transparent)!important;box-shadow:-8px 0 35px rgba(0,0,0,.45)!important;z-index:99998!important;padding:1.25rem 1.25rem 2rem!important;resize:horizontal!important;overflow-x:auto!important;overflow-y:auto!important;animation:basinDrawerSlideIn .4s cubic-bezier(0.2, 0.9, 0.3, 1) both!important;transition:width .25s cubic-bezier(0.2, 0.9, 0.3, 1), transform .4s cubic-bezier(0.2, 0.9, 0.3, 1)!important;will-change:transform,width}
@keyframes basinDrawerSlideIn{0%{transform:translateX(100%);opacity:0}100%{transform:translateX(0);opacity:1}}
body:has(.st-key-assistant_drawer) .block-container,body:has(.st-key-assistant_drawer) [data-testid="stMainBlockContainer"]{margin-right:calc(var(--basin-assistant-width, 500px) + 5px)!important;max-width:calc(100% - var(--basin-assistant-width, 500px) - 15px)!important;padding-right:1.5rem!important}
@media(max-width:950px){body:has(.st-key-assistant_drawer) .block-container,body:has(.st-key-assistant_drawer) [data-testid="stMainBlockContainer"]{margin-right:0!important;max-width:100%!important}}
.st-key-assistant_tab_closed,.st-key-assistant_tab_open{position:fixed!important;top:50%!important;transform:translateY(-50%)!important;width:42px!important;max-width:42px!important;height:120px!important;min-height:120px!important;overflow:visible!important;z-index:99999!important;pointer-events:none!important;margin:0!important;padding:0!important;transition:right .35s cubic-bezier(0.16, 1, 0.3, 1)!important}
.st-key-assistant_tab_closed *,.st-key-assistant_tab_open *{pointer-events:none!important}
.st-key-assistant_tab_closed > div,.st-key-assistant_tab_open > div{width:42px!important;margin:0!important;padding:0!important}
.st-key-assistant_tab_closed [data-testid="stElementContainer"],.st-key-assistant_tab_open [data-testid="stElementContainer"]{width:42px!important;margin:0!important;padding:0!important}
.st-key-assistant_tab_closed button,.st-key-assistant_tab_open button{pointer-events:auto!important;width:42px!important;margin:0!important}
.st-key-assistant_tab_closed{right:0!important}
.st-key-assistant_tab_open{right:var(--basin-assistant-width, 500px)!important}
@media(max-width:550px){.st-key-assistant_tab_open{right:92vw!important}.st-key-assistant_drawer{width:92vw!important}}
.st-key-assistant_tab_closed button,.st-key-assistant_tab_open button{border-radius:12px 0 0 12px!important;padding:18px 8px!important;writing-mode:vertical-rl!important;text-orientation:mixed!important;transform:none!important;font-size:.78rem!important;font-weight:700!important;letter-spacing:.1em!important;text-transform:uppercase!important;background:#356273!important;color:#fff!important;border:1px solid color-mix(in srgb,#fff 20%,transparent)!important;border-right:none!important;box-shadow:-4px 0 16px rgba(0,0,0,.35)!important;cursor:pointer!important;min-height:120px!important}
.st-key-assistant_tab_closed button:hover,.st-key-assistant_tab_open button:hover{background:#2878A0!important;box-shadow:-6px 0 20px rgba(40,120,160,.45)!important}
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
    .basin-top-logo-light{width:175px;height:48px}
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
.basin-assistant-badge{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:20px;font-size:.73rem;font-weight:700;background:var(--basin-surface-soft);border:1px solid var(--basin-border);margin-bottom:.5rem}
.basin-status-info{color:var(--basin-info-text)!important}.basin-status-success{color:var(--basin-success-text)!important}.basin-status-warning{color:var(--basin-warning-text)!important}.basin-status-danger{color:var(--basin-danger-text)!important}
.basin-assistant-avatar{width:52px;height:52px;object-fit:contain;filter:drop-shadow(0 3px 8px rgba(0,0,0,.4));flex:0 0 auto}
.basin-assistant-title{font-size:1.55rem;font-weight:800;letter-spacing:-.03em;line-height:1.08;margin:0}
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
})();</script>""", unsafe_allow_javascript=True)


def appearance_picker():
    # Main-menu theme items are the native persisted System/Light/Dark choices,
    # plus the high-contrast Black/White theme.
    st.html("""
<div class="basin-theme-picker" aria-label="Appearance">
 <button type="button" data-basin-theme="Light">Light</button>
 <button type="button" data-basin-theme="Dark">Dark</button>
 <button type="button" data-basin-theme="System">System</button>
 <button type="button" data-basin-theme="BW">Black/White</button>
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
     if (name === 'BW') {
       const isBW = document.body.classList.toggle('basin-theme-bw');
       localStorage.setItem('basin-bw-theme', isBW ? 'true' : 'false');
       status.textContent = isBW ? 'Black / White high-contrast theme active.' : 'Black / White theme removed.';
       return;
     }
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
    accent = "#356273" if enabled else st.session_state.appearance_accent
    selection = "#0072B2" if enabled else st.session_state.appearance_selection
    sidebar = "#6088A5" if enabled else st.session_state.appearance_sidebar
    foreground = accent_foreground(accent)
    selected_text = accent_foreground(selection)
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

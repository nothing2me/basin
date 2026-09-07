"""Presentation styles and a shortcut to Streamlit's native theme picker.

Native themes keep canvas dataframes, popup menus and plots in sync. The small
browser-only shortcut uses the installed Streamlit menu instead of changing
server config or reloading a user's workspace.
"""
import streamlit as st


def apply_design():
    st.html("""<style>
.block-container{padding:2.5rem 2.8rem 2rem;max-width:1560px}
[data-testid="stAppDeployButton"]{display:none}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{border-right:1px solid color-mix(in srgb,currentColor 12%,transparent)}
[data-testid="stSidebarUserContent"]{padding-top:.25rem!important}
[data-testid="stVerticalBlock"]{gap:1rem}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{gap:.65rem}
.basin-brand{margin:0 0 1.8rem}
.basin-brand img{display:block;width:min(100%,230px);height:auto;margin-bottom:.55rem}
.basin-brand small{font-size:.73rem;opacity:.68;letter-spacing:.08em;text-transform:uppercase}
.basin-eyebrow{font-size:.67rem;font-weight:700;letter-spacing:.14em;opacity:.62;margin-top:8px}
h1,h2,h3{letter-spacing:-.025em}
h3{font-size:1.6rem!important;font-weight:650!important}
[data-testid="stMetric"]{border:1px solid color-mix(in srgb,currentColor 12%,transparent);border-radius:13px;padding:16px 18px;background:color-mix(in srgb,currentColor 2%,transparent)}
[data-testid="stMetricValue"]{font-size:1.7rem;font-weight:600;font-variant-numeric:tabular-nums;letter-spacing:-.025em}
[data-testid="stMetricLabel"]{font-size:.76rem;opacity:.78}
[data-testid="stCaptionContainer"]{font-size:.78rem}
[data-testid="stSidebar"] [role="radiogroup"]{gap:5px}
[data-testid="stSidebar"] [role="radiogroup"] label{border-radius:9px;padding:7px 10px;margin:0;transition:background .15s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:has([aria-checked="true"]){background:color-mix(in srgb,#2D6683 28%,transparent);font-weight:650}
[data-testid="stExpander"]{border-radius:11px!important}
[data-testid="stExpander"] details summary{font-size:.86rem;padding-block:10px}
[data-testid="stDataFrame"],[data-testid="stDataEditor"]{border-radius:11px;overflow:hidden}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{font-size:.86rem;font-weight:550;min-height:2.5rem}
[data-testid="stButton"] button[kind="primary"],[data-testid="stFormSubmitButton"] button[kind="primary"],[data-testid="stDownloadButton"] button[kind="primary"],button[data-testid="stBaseButton-primary"]{color:#fff!important}
[data-testid="stButton"] button[kind="primary"] *,[data-testid="stFormSubmitButton"] button[kind="primary"] *,[data-testid="stDownloadButton"] button[kind="primary"] *,button[data-testid="stBaseButton-primary"] *{color:#fff!important}
[data-tag]{background:#2D6683!important;color:#fff!important}
[data-tag] *{color:#fff!important}
button:focus-visible,a:focus-visible{outline:2px solid #6FA8C2!important;outline-offset:3px}
.st-key-welcome{padding:30px 34px;border:1px solid color-mix(in srgb,currentColor 24%,transparent);border-radius:18px;background:color-mix(in srgb,currentColor 3%,transparent);margin:6px 0 16px}
.welcome-title{font-size:2.4rem!important;line-height:1.15!important;margin:8px 0 14px!important;font-weight:650!important}
.welcome-copy{max-width:610px;line-height:1.6;opacity:.8;font-size:1rem}
.welcome-steps{display:flex;flex-wrap:wrap;gap:14px 32px;padding-top:18px;border-top:1px solid color-mix(in srgb,currentColor 12%,transparent);font-size:.8rem;opacity:.85}
.welcome-steps b{font-variant-numeric:tabular-nums;color:inherit;margin-right:8px}
.st-key-tutorial_guide{background:color-mix(in srgb,currentColor 4%,transparent);border:1px solid color-mix(in srgb,currentColor 30%,transparent);border-left:4px solid currentColor;border-radius:12px;padding:18px 22px;margin:4px 0 12px}
.tutorial-meta{font-size:.67rem;letter-spacing:.09em;opacity:.65;margin-bottom:7px}
.tutorial-title{font-size:1.06rem;font-weight:650;margin:0 0 6px}
.tutorial-description{font-size:.83rem;opacity:.72;margin:0 0 10px;line-height:1.5;max-width:960px}
.tutorial-action{font-size:.88rem;margin:0 0 10px;line-height:1.5}
.tutorial-location,.tutorial-target-label{font-size:.75rem;font-weight:650;opacity:.85;line-height:1.4}
.tutorial-anchor{scroll-margin-top:5rem}
.st-key-tutorial_guide a{color:inherit;text-decoration-color:currentColor;text-underline-offset:3px}
.basin-theme-picker{display:flex;gap:6px}
.basin-theme-picker button{font:inherit;font-size:.8rem;cursor:pointer;flex:1;border:1px solid color-mix(in srgb,currentColor 20%,transparent);border-radius:8px;background:transparent;color:inherit;padding:9px 4px}
.basin-theme-picker button:hover{background:color-mix(in srgb,#2D6683 24%,transparent)}
.basin-theme-status{font-size:.75rem;line-height:1.4;margin:6px 0 0;opacity:.8}
@media(max-width:800px){.block-container{padding:2.4rem 1rem 1.5rem}.st-key-welcome{padding:20px}.welcome-title{font-size:1.9rem!important}.st-key-tutorial_guide{padding:14px}h3{font-size:1.3rem!important}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>""")


def appearance_picker():
    # Main-menu theme items are the native persisted System/Light/Dark choices.
    # Bounded observation tolerates rendering delay; failure leaves a usable
    # native menu and clear directions, never a second conflicting CSS theme.
    st.html("""
<div class="basin-theme-picker" aria-label="Appearance">
 <button type="button" data-basin-theme="Light">Light</button>
 <button type="button" data-basin-theme="Dark">Dark</button>
 <button type="button" data-basin-theme="System">System</button>
</div>
<p class="basin-theme-status" role="status" aria-live="polite"></p>
<script>
(() => {
 const script = document.currentScript;
 const root = script.parentElement;
 const status = root.querySelector('.basin-theme-status');
 root.querySelectorAll('[data-basin-theme]').forEach(button => {
   button.addEventListener('click', () => {
     const name = button.dataset.basinTheme;
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

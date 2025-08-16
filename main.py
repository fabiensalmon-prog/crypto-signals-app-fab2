import streamlit as st, yaml, os, math
import pandas as pd
from src.data.loader import load_or_fetch
from src.strategies import ALL
from src.risk.levels import adaptive_levels, risk_position_size
from src.journal.db import add_trade, list_trades, update_trade_result, init_db

st.set_page_config(page_title='Crypto Signals — Mobile Deploy', layout='centered', initial_sidebar_state='collapsed')
cfg = yaml.safe_load(open('configs/default.yml'))

st.title('Crypto Signals — Mobile (Deploy-ready)')
st.caption('Manual trades only — mobile-first.')

# Sidebar collapsed controls
with st.expander('Settings', expanded=False):
    exchange = st.selectbox('Exchange', ['okx','bybit','kraken','coinbase','kucoin','binance'], index=0)
    symbols = st.multiselect('Pairs', cfg['app']['symbols'], default=cfg['app']['symbols'][:6])
    tf = st.selectbox('Timeframe', cfg['app']['timeframes'], index=1)
    account_equity = st.number_input('Account USD', value=float(cfg['backtest']['initial_cash']), step=1000.0)
    risk_pct = st.slider('Risk % per trade', 0.1, 5.0, float(cfg['risk']['risk_pct_per_trade']), 0.1)

# Tabs: Scan / Journal / Backtest
tab_scan, tab_journal, tab_bt = st.tabs(['Scanner', 'Journal', 'Backtest'])

with tab_scan:
    st.subheader('Scan rapide — 1 clic')
    strat = st.selectbox('Strategy', list(ALL.keys()), index=2)
    if st.button('🚀 Scan maintenant'):
        rows = []
        for s in symbols:
            try:
                df = load_or_fetch(exchange, s, tf, limit=1500)
            except Exception as e:
                st.warning(f'Erreur fetch {s}: {e}'); continue
            sig = ALL[strat](df); direction = int(sig.iloc[-1])
            lvl = adaptive_levels(df, direction, atr_mult_sl=cfg['risk']['atr_k_sl'], atr_mult_tp=cfg['risk']['atr_k_tp'])
            if lvl:
                qty = risk_position_size(account_equity, lvl['entry'], lvl['sl'], risk_pct)
                r = abs(lvl['entry']-lvl['sl']); rr = abs(lvl['tp']-lvl['entry'])/max(r,1e-9)
                rows.append({'symbol': s, 'dir': 'LONG' if direction>0 else 'SHORT' if direction<0 else 'FLAT', 'entry': lvl['entry'], 'sl': lvl['sl'], 'tp': lvl['tp'], 'atr': lvl['atr'], 'rr': rr, 'qty': qty})
        if not rows:
            st.info('No strong signals now.')
        else:
            df_rows = pd.DataFrame(rows).sort_values('rr', ascending=False)
            st.dataframe(df_rows[['symbol','dir','entry','sl','tp','rr','qty']].round(6))
            # Add quick ticket action
            sym_choice = st.selectbox('Choisir symbole pour ticket', df_rows['symbol'].tolist())
            sel = df_rows[df_rows['symbol']==sym_choice].iloc[0]
            st.markdown(f"**Ticket pour {sym_choice} — {sel['dir']}**\nEntry: {sel['entry']:.6f}  SL: {sel['sl']:.6f}  TP: {sel['tp']:.6f}  Qty: {sel['qty']:.6f}  R/R: {sel['rr']:.2f}")
            if st.button('📌 Enregistrer ce trade dans le journal'):
                add_trade(sym_choice, sel['dir'], float(sel['entry']), float(sel['sl']), float(sel['tp']), float(sel['qty']), float(sel['rr']), note='created from scan')
                st.success('Trade ajouté au journal.')
    if st.button('🔁 Régénérer signaux & checker positions'):
        st.info('Régénération: recalcul en cours...')
        # simple behavior: re-run scan and compare to journal positions
        trades = list_trades(limit=500)
        open_trades = trades[trades['result']=='']
        checked = []
        for idx, t in open_trades.iterrows():
            s = t['symbol']
            try:
                df = load_or_fetch(exchange, s, tf, limit=1500)
            except Exception:
                continue
            sig = ALL['Composite (vote)'](df)
            dir_now = 'LONG' if int(sig.iloc[-1])>0 else 'SHORT' if int(sig.iloc[-1])<0 else 'FLAT'
            checked.append({'id': t['id'], 'symbol': s, 'prev_side': t['side'], 'now': dir_now})
        st.write(pd.DataFrame(checked))

with tab_journal:
    st.subheader('Trade Journal')
    if st.button('🔄 Rafraîchir journal'):
        st.experimental_rerun()
    trades = list_trades(limit=200)
    if trades.empty:
        st.info('Journal vide.')
    else:
        st.dataframe(trades[['id','ts','symbol','side','entry','sl','tp','qty','rr','result','pnl','note']].round(6))
        st.markdown('---')
        st.markdown('Mettre à jour un trade (result/pnl)')
        tid = st.number_input('Trade ID', min_value=1, step=1)
        r = st.selectbox('Result', ['', 'WIN','LOSS','CLOSE'])
        pnl = st.number_input('P&L (USD)', value=0.0, step=0.01)
        if st.button('Mettre à jour trade'):
            update_trade_result(tid, r, float(pnl))
            st.success('Trade mis à jour.')

with tab_bt:
    st.subheader('Backtest rapide (symbole unique)')
    sym = st.selectbox('Symbole BT', options=symbols)
    if st.button('▶️ Lancer backtest (train/test)'):
        try:
            df = load_or_fetch(exchange, sym, tf, limit=2500)
        except Exception as e:
            st.warning(f'Erreur fetch {sym}: {e}'); df = None
        if df is not None:
            sig = ALL['Composite (vote)'](df)
            from src.backtest.engine import backtest
            bt = backtest(df, sig, initial_cash=cfg['backtest']['initial_cash'], fee_bps=cfg['risk']['fee_bps'], slippage_bps=cfg['risk']['slippage_bps'])
            st.line_chart(bt['equity'])
            st.download_button('Télécharger equity CSV', bt['equity'].to_csv().encode('utf-8'), file_name=f'equity_{sym}.csv', mime='text/csv')

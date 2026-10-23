import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
from .formatters import format_inr as inr_formatter

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
PRICES = DATA / 'prices'

# Modern Light Theme Color Tokens (Tailored for Institutional Financial Dashboards)
CHART_THEME = {
    'bg': '#FFFFFF',
    'paper': '#FFFFFF',
    'canvas': '#F8FAFC',
    'text': '#0F172A',
    'subtext': '#475569',
    'muted': '#94A3B8',
    'grid': '#F1F5F9',
    'border': '#E2E8F0',
    'brand': '#2563EB',       # Primary Trust Blue
    'brand_tint': '#EFF6FF',
    'buy': '#059669',         # Vibrant Emerald Green (WCAG AA on white)
    'buy_light': 'rgba(5, 150, 105, 0.15)',
    'hold': '#D97706',        # Warm Amber
    'hold_light': 'rgba(217, 119, 6, 0.15)',
    'sell': '#DC2626',        # Clean Coral Red
    'sell_light': 'rgba(220, 38, 38, 0.15)',
    'review': '#0284C7',      # Sky Blue
    'palette': [
        '#2563EB', '#059669', '#D97706', '#7C3AED', 
        '#0284C7', '#DB2777', '#0D9488', '#EA580C', '#4B5563'
    ],
    'font_family': "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
}

def format_inr(val):
    """Format numeric values into Lakhs or Thousands for clean chart annotations."""
    if abs(val) >= 10000000:
        return f"₹{val/10000000:.2f} Cr"
    elif abs(val) >= 100000:
        return f"₹{val/100000:.2f} L"
    elif abs(val) >= 1000:
        return f"₹{val/1000:.1f} k"
    return f"₹{val:,.0f}"

def plot_portfolio_allocation(holdings):
    """
    Executive Donut chart showing asset allocation with center AUM annotation
    and custom institutional tooltips.
    """
    if not holdings:
        fig = go.Figure()
        fig.update_layout(title="No holdings available", template="plotly_white")
        return fig
    
    df = pd.DataFrame(holdings)
    df = df[df['market_value'] > 0].sort_values('market_value', ascending=False)
    total_val = df['market_value'].sum()
    
    fig = go.Figure(go.Pie(
        labels=df['symbol'],
        values=df['market_value'],
        hole=0.62,
        marker=dict(
            colors=CHART_THEME['palette'][:len(df)],
            line=dict(color='#FFFFFF', width=2.5)
        ),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(size=11, family=CHART_THEME['font_family'], color=CHART_THEME['text']),
        hovertemplate="<b>%{label}</b><br>Market Value: ₹%{value:,.2f}<br>Portfolio Share: %{percent}<extra></extra>"
    ))
    
    # Center text annotation for Total Portfolio Value
    fig.add_annotation(
        text=f"<span style='font-size:11px;color:{CHART_THEME['subtext']};font-weight:600;text-transform:uppercase;letter-spacing:0.05em;'>Total Value</span><br>"
             f"<span style='font-size:18px;font-weight:800;color:{CHART_THEME['text']};'>{format_inr(total_val)}</span><br>"
             f"<span style='font-size:11px;color:{CHART_THEME['subtext']};'>{len(df)} Holdings</span>",
        x=0.5, y=0.5,
        font=dict(family=CHART_THEME['font_family']),
        showarrow=False
    )
    
    fig.update_layout(
        title=dict(
            text="Portfolio Allocation by Stock",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        showlegend=False,
        margin=dict(t=50, b=25, l=25, r=25),
        height=360
    )
    return fig

def plot_holdings_treemap(holdings):
    """
    Interactive TradingView/Finviz-style Market Heatmap (Treemap).
    Boxes are sized by current market value and colored by unrealized return (green/red).
    """
    if not holdings:
        return go.Figure()

    df = pd.DataFrame(holdings)
    df = df[df['market_value'] > 0].copy()
    if df.empty:
        return go.Figure()

    df['return_str'] = df['pnl_percent'].apply(lambda x: f"{x:+.1f}%")
    df['value_str'] = df['market_value'].apply(format_inr)
    df['hover_text'] = (
        "<b>" + df['symbol'] + "</b> (" + df['sector'] + ")<br>" +
        "Market Value: " + df['market_value'].apply(lambda v: inr_formatter(v, decimals=2)) + "<br>" +
        "Invested Cost: " + df['invested_value'].apply(lambda v: inr_formatter(v, decimals=2)) + "<br>" +
        "Unrealized P&L: " + df['unrealized_pnl'].apply(lambda v: inr_formatter(v, decimals=2, show_plus=True)) + " (" + df['return_str'] + ")<br>" +
        "Portfolio Weight: " + df['weight'].apply(lambda w: f"{w:.1f}%")
    )

    # Bound color scale between -25% and +25% for high visual contrast
    fig = px.treemap(
        df,
        path=[px.Constant("All Holdings"), 'sector', 'symbol'],
        values='market_value',
        color='pnl_percent',
        color_continuous_scale=[
            (0.0, '#DC2626'),   # Deep Red for large loss
            (0.40, '#FCA5A5'),  # Soft Red
            (0.50, '#F8FAFC'),  # Neutral off-white at 0%
            (0.60, '#86EFAC'),  # Soft Green
            (1.0, '#059669')    # Vibrant Emerald for strong gains
        ],
        range_color=[-25, 25],
        custom_data=['hover_text', 'return_str', 'value_str']
    )

    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]}<br>%{customdata[1]}",
        textfont=dict(family=CHART_THEME['font_family'], size=12),
        marker=dict(line=dict(width=1.5, color='#FFFFFF')),
        hovertemplate="%{customdata[0]}<extra></extra>"
    )

    fig.update_layout(
        title=dict(
            text="Portfolio Heatmap (Sized by Market Value · Colored by Unrealized Return)",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        coloraxis_colorbar=dict(
            title=dict(text="Return %", side="top"),
            ticks="outside",
            tickformat="+.0f",
            ticksuffix="%",
            len=0.7,
            thickness=14,
            tickfont=dict(size=10, family=CHART_THEME['font_family'], color=CHART_THEME['subtext'])
        ),
        margin=dict(t=50, b=20, l=15, r=15),
        height=380
    )
    return fig

def plot_holdings_pnl(holdings):
    """
    Horizontal bar chart showing Unrealized P&L in absolute rupees and return %.
    Sorted from top gainers to biggest laggards with rounded bar styling.
    """
    if not holdings:
        return go.Figure()
        
    df = pd.DataFrame(holdings).copy()
    df = df.sort_values('unrealized_pnl', ascending=True)
    
    colors = [CHART_THEME['buy'] if pnl >= 0 else CHART_THEME['sell'] for pnl in df['unrealized_pnl']]
    
    fig = go.Figure(go.Bar(
        x=df['unrealized_pnl'],
        y=df['symbol'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='#FFFFFF', width=1),
            opacity=0.9
        ),
        text=[f"₹{p:+,.0f} ({r:+.1f}%)" for p, r in zip(df['unrealized_pnl'], df['pnl_percent'])],
        textposition='outside',
        textfont=dict(family=CHART_THEME['font_family'], size=11, color=CHART_THEME['text']),
        hovertemplate="<b>%{y}</b><br>Unrealized P&L: ₹%{x:+,.2f}<extra></extra>"
    ))
    
    # Dynamic axis padding for text labels
    max_val = max(abs(df['unrealized_pnl'].min()), abs(df['unrealized_pnl'].max())) * 1.35
    
    fig.update_layout(
        title=dict(
            text="Unrealized Profit & Loss by Holding (₹ and % Return)",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        xaxis=dict(
            gridcolor=CHART_THEME['grid'],
            zerolinecolor='#94A3B8',
            zerolinewidth=1.5,
            title=dict(text="Unrealized P&L (₹)", font=dict(size=11, color=CHART_THEME['subtext'])),
            tickfont=dict(size=10, color=CHART_THEME['subtext']),
            range=[-max_val, max_val]
        ),
        yaxis=dict(
            gridcolor=CHART_THEME['grid'],
            tickfont=dict(size=11, family=CHART_THEME['font_family'], weight=600, color=CHART_THEME['text'])
        ),
        margin=dict(t=50, b=30, l=85, r=40),
        height=360
    )
    return fig

def plot_sector_exposure_chart(holdings, max_sector_limit=0.25):
    """
    Displays sector concentration weights vs the institutional 25% guideline cap.
    Highlights any sectors exceeding the concentration ceiling in warning amber/red.
    """
    if not holdings:
        return go.Figure()

    df = pd.DataFrame(holdings)
    sector_sums = df.groupby('sector')['market_value'].sum().reset_index()
    total_val = sector_sums['market_value'].sum()
    if total_val <= 0:
        return go.Figure()

    sector_sums['weight_pct'] = (sector_sums['market_value'] / total_val) * 100.0
    sector_sums = sector_sums.sort_values('weight_pct', ascending=True)

    limit_pct = max_sector_limit * 100.0
    colors = [CHART_THEME['sell'] if w > limit_pct else (CHART_THEME['hold'] if w > limit_pct * 0.85 else CHART_THEME['brand']) for w in sector_sums['weight_pct']]

    fig = go.Figure(go.Bar(
        x=sector_sums['weight_pct'],
        y=sector_sums['sector'],
        orientation='h',
        marker=dict(color=colors, line=dict(color='#FFFFFF', width=1)),
        text=[f"{w:.1f}% ({format_inr(v)})" for w, v in zip(sector_sums['weight_pct'], sector_sums['market_value'])],
        textposition='outside',
        textfont=dict(family=CHART_THEME['font_family'], size=11, color=CHART_THEME['text']),
        hovertemplate="<b>%{y}</b><br>Portfolio Weight: %{x:.1f}%<br>Market Value: ₹%{customdata:,.2f}<extra></extra>",
        customdata=sector_sums['market_value']
    ))

    # Add vertical reference line for 25% guideline cap
    fig.add_vline(
        x=limit_pct,
        line_dash="dash",
        line_color=CHART_THEME['sell'],
        line_width=2,
        annotation_text=f"Max Limit ({limit_pct:.0f}%)",
        annotation_position="top right",
        annotation_font=dict(size=10, color=CHART_THEME['sell'], family=CHART_THEME['font_family'], weight=700)
    )

    max_x = max(sector_sums['weight_pct'].max() * 1.3, limit_pct * 1.25)

    fig.update_layout(
        title=dict(
            text="Sector Diversification vs. Risk Guideline Cap (25%)",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        xaxis=dict(
            gridcolor=CHART_THEME['grid'],
            title=dict(text="Portfolio Weight (%)", font=dict(size=11, color=CHART_THEME['subtext'])),
            ticksuffix="%",
            tickfont=dict(size=10, color=CHART_THEME['subtext']),
            range=[0, max_x]
        ),
        yaxis=dict(
            tickfont=dict(size=11, family=CHART_THEME['font_family'], weight=600, color=CHART_THEME['text'])
        ),
        margin=dict(t=50, b=30, l=95, r=40),
        height=320
    )
    return fig

def plot_stock_price_history(symbol, prices_df=None):
    """
    Institutional 2-panel chart:
    - Panel 1 (Top 78%): Candlestick price action with 200 DMA, 50 DMA, and 52W High/Low.
    - Panel 2 (Bottom 22%): Trading volume bars colored green/red by day's direction.
    """
    if prices_df is None or prices_df.empty:
        p_file = PRICES / f"{symbol}.csv"
        if p_file.exists():
            prices_df = pd.read_csv(p_file)
        else:
            return None

    df = prices_df.copy()
    if 'close' not in df.columns:
        return None
        
    if 'date' not in df.columns:
        df['date'] = range(len(df))

    # Calculate moving averages & 52w bounds
    df['sma200'] = df['close'].rolling(200, min_periods=50).mean()
    df['sma50'] = df['close'].rolling(50, min_periods=20).mean()
    high_52w = float(df['close'].tail(252).max()) if len(df) >= 252 else float(df['close'].max())
    low_52w = float(df['close'].tail(252).min()) if len(df) >= 252 else float(df['close'].min())

    has_ohlc = {'open', 'high', 'low', 'close'}.issubset(df.columns)
    has_vol = 'volume' in df.columns and (df['volume'] > 0).any()

    if has_vol:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.78, 0.22]
        )
    else:
        fig = go.Figure()

    # 1. Price Trace (Candlestick or Line)
    if has_ohlc:
        trace_price = go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color=CHART_THEME['buy'],
            decreasing_line_color=CHART_THEME['sell'],
            increasing_fillcolor=CHART_THEME['buy'],
            decreasing_fillcolor=CHART_THEME['sell']
        )
    else:
        trace_price = go.Scatter(
            x=df['date'],
            y=df['close'],
            mode='lines',
            name='Price',
            line=dict(color=CHART_THEME['brand'], width=2)
        )

    if has_vol:
        fig.add_trace(trace_price, row=1, col=1)
    else:
        fig.add_trace(trace_price)

    # 200-Day SMA (Anchor of Long-Term Uptrend)
    trace_sma200 = go.Scatter(
        x=df['date'],
        y=df['sma200'],
        mode='lines',
        name='200 DMA',
        line=dict(color='#D97706', width=2, dash='dash')
    )

    # 50-Day SMA (Medium-Term Momentum)
    trace_sma50 = go.Scatter(
        x=df['date'],
        y=df['sma50'],
        mode='lines',
        name='50 DMA',
        line=dict(color='#7C3AED', width=1.5)
    )

    if has_vol:
        fig.add_trace(trace_sma200, row=1, col=1)
        fig.add_trace(trace_sma50, row=1, col=1)
    else:
        fig.add_trace(trace_sma200)
        fig.add_trace(trace_sma50)

    # Add 52W High and Low reference lines
    fig.add_hline(
        y=high_52w, line_dash="dot", line_color="#059669", line_width=1,
        annotation_text="52W High", annotation_position="top left",
        annotation_font=dict(size=9, color="#059669", family=CHART_THEME['font_family'])
    )
    fig.add_hline(
        y=low_52w, line_dash="dot", line_color="#DC2626", line_width=1,
        annotation_text="52W Low", annotation_position="bottom left",
        annotation_font=dict(size=9, color="#DC2626", family=CHART_THEME['font_family'])
    )

    # 2. Volume trace (Panel 2)
    if has_vol:
        vol_colors = []
        for i in range(len(df)):
            if has_ohlc:
                vol_colors.append(CHART_THEME['buy'] if df['close'].iloc[i] >= df['open'].iloc[i] else CHART_THEME['sell'])
            else:
                prev = df['close'].iloc[i-1] if i > 0 else df['close'].iloc[i]
                vol_colors.append(CHART_THEME['buy'] if df['close'].iloc[i] >= prev else CHART_THEME['sell'])
                
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Trading Volume',
            marker=dict(color=vol_colors, opacity=0.7),
            showlegend=False,
            hovertemplate="Volume: %{y:,.0f}<extra></extra>"
        ), row=2, col=1)

    fig.update_layout(
        title=dict(
            text=f"<b>{symbol}</b> — Price Action & Technical Trend",
            font=dict(size=13, family=CHART_THEME['font_family'], color=CHART_THEME['text']),
            x=0,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        xaxis=dict(gridcolor=CHART_THEME['grid'], rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor=CHART_THEME['grid'], title=dict(text="Price (₹)", font=dict(size=11, color=CHART_THEME['subtext']))),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.14,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color=CHART_THEME['subtext'], family=CHART_THEME['font_family'])
        ),
        margin=dict(t=45, b=45, l=55, r=20),
        height=470
    )
    if has_vol:
        fig.update_yaxes(title_text="Vol", row=2, col=1, gridcolor=CHART_THEME['grid'], tickfont=dict(size=9))
    return fig

def plot_factor_radar(scores_dict):
    """
    Multidimensional 5-factor radar scorecard with soft gradient area fill
    and institutional benchmark comparison line at 50/100.
    """
    categories = ['Business Quality', 'Valuation Safety', 'Growth Stability', 'Trend / 200 DMA', 'Financial Solvency']
    values = [
        float(scores_dict.get('quality', 50)),
        float(scores_dict.get('valuation', 50)),
        float(scores_dict.get('growth', 50)),
        float(scores_dict.get('technical', 50)),
        float(scores_dict.get('health', 50))
    ]
    # Close loops for polygon rendering
    values_closed = values + [values[0]]
    categories_closed = categories + [categories[0]]
    benchmark_closed = [50] * 5 + [50]

    fig = go.Figure()

    # Benchmark polygon (50 Neutral Baseline)
    fig.add_trace(go.Scatterpolar(
        r=benchmark_closed,
        theta=categories_closed,
        mode='lines',
        line=dict(color='#CBD5E1', width=1.5, dash='dot'),
        name='Neutral Baseline (50)',
        hoverinfo='skip'
    ))

    # Company factor polygon
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(37, 99, 235, 0.18)',
        line=dict(color=CHART_THEME['brand'], width=2.5),
        name='Stock Score',
        hovertemplate="<b>%{theta}</b>: %{r:.1f} / 100<extra></extra>"
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(size=9, color=CHART_THEME['subtext'], family=CHART_THEME['font_family'])
            ),
            angularaxis=dict(
                gridcolor='#E2E8F0',
                linecolor='#CBD5E1',
                tickfont=dict(size=11, color=CHART_THEME['text'], family=CHART_THEME['font_family'], weight=600)
            ),
            bgcolor='#F8FAFC'
        ),
        paper_bgcolor=CHART_THEME['paper'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        title=dict(
            text="Multidimensional Factor Scorecard (0–100)",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, xanchor="center", x=0.5, font=dict(size=10, color=CHART_THEME['subtext'])),
        margin=dict(t=50, b=40, l=45, r=45),
        height=380
    )
    return fig

def plot_risk_return(recommendations):
    """
    Scatter matrix mapping 52-Week Maximum Drawdown Risk vs. 6-Month Compounding Return.
    Allows instant visual identification of high-momentum low-risk compounders.
    """
    recs_valid = [r for r in recommendations if r.get('return_6m') is not None and r.get('drawdown_52w') is not None]
    if not recs_valid:
        return go.Figure()

    df = pd.DataFrame(recs_valid).copy()
    df['return_6m_pct'] = df['return_6m'] * 100.0
    df['drawdown_52w_pct'] = df['drawdown_52w'] * 100.0
    df['size'] = df['market_value'].apply(lambda x: max(12, min(42, (x ** 0.5) / 5)) if x > 0 else 14)

    color_map = {
        'BUY': CHART_THEME['buy'],
        'BUY_CANDIDATE': CHART_THEME['buy'],
        'HOLD': CHART_THEME['hold'],
        'SELL': CHART_THEME['sell'],
        'REVIEW': CHART_THEME['review']
    }

    fig = px.scatter(
        df,
        x='drawdown_52w_pct',
        y='return_6m_pct',
        color='action',
        color_discrete_map=color_map,
        size='size',
        text='symbol',
        hover_data=['score', 'market_value', 'reason'],
        title="Risk vs. Momentum Matrix (52W Max Drawdown vs. 6-Month Return)"
    )

    fig.update_traces(
        textposition='top center',
        textfont=dict(family=CHART_THEME['font_family'], size=11, color=CHART_THEME['text']),
        marker=dict(line=dict(width=1.5, color='#FFFFFF'))
    )

    # Reference crosshairs at 0% return and -20% drawdown
    fig.add_hline(y=0, line_dash="solid", line_color="#CBD5E1", line_width=1)
    fig.add_vline(x=-20, line_dash="dash", line_color="#FCA5A5", line_width=1)

    fig.update_layout(
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        xaxis=dict(
            gridcolor=CHART_THEME['grid'],
            title=dict(text="52-Week Max Drawdown Risk (%)", font=dict(size=11, color=CHART_THEME['subtext'])),
            ticksuffix="%",
            zeroline=False
        ),
        yaxis=dict(
            gridcolor=CHART_THEME['grid'],
            title=dict(text="6-Month Return (%)", font=dict(size=11, color=CHART_THEME['subtext'])),
            ticksuffix="%",
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=CHART_THEME['subtext'], family=CHART_THEME['font_family'])
        ),
        margin=dict(t=50, b=30, l=45, r=20),
        height=390
    )
    return fig

def plot_budget_gauge(spent, limit=50000.0):
    """
    Precision monthly capital deployment gauge with soft color stages.
    """
    spent = float(spent)
    limit = float(limit)
    avail = max(0.0, limit - spent)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=spent,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Monthly Deployment Gauge", 'font': {'size': 14, 'color': CHART_THEME['text'], 'family': CHART_THEME['font_family'], 'weight': 700}},
        number={'prefix': "₹", 'valueformat': ",.0f", 'font': {'size': 24, 'color': CHART_THEME['text'], 'family': CHART_THEME['font_family']}},
        gauge={
            'axis': {'range': [0, limit], 'tickwidth': 1, 'tickcolor': "#CBD5E1", 'tickformat': ",.0f"},
            'bar': {'color': CHART_THEME['brand'], 'thickness': 0.28},
            'bgcolor': '#F8FAFC',
            'borderwidth': 1,
            'bordercolor': "#E2E8F0",
            'steps': [
                {'range': [0, limit * 0.60], 'color': 'rgba(5, 150, 105, 0.12)'},
                {'range': [limit * 0.60, limit * 0.90], 'color': 'rgba(217, 119, 6, 0.12)'},
                {'range': [limit * 0.90, limit], 'color': 'rgba(220, 38, 38, 0.15)'}
            ],
            'threshold': {
                'line': {'color': CHART_THEME['sell'], 'width': 3},
                'thickness': 0.8,
                'value': limit
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor=CHART_THEME['paper'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        margin=dict(t=35, b=20, l=25, r=25),
        height=240
    )
    return fig

def plot_capital_flow(budget):
    """
    Visual capital flow bar showing how the ₹50,000 monthly purchase budget is deployed:
    - Already Spent
    - Proposed Buys
    - Remaining Unallocated Cash Buffer
    - Capital Harvested from Sells
    """
    spent = float(budget.get('spent', 0.0))
    limit = float(budget.get('monthly_limit', 50000.0))
    allocations = budget.get('allocations', [])
    proposed_buys = sum(a.get('estimated_gross', 0.0) for a in allocations)
    unallocated = max(0.0, limit - spent - proposed_buys)
    freed_capital = float(budget.get('potential_freed_capital', 0.0))

    fig = go.Figure()

    # Stacked bar representing monthly budget utilization
    fig.add_trace(go.Bar(
        name='Already Spent',
        y=['Monthly Deployment'],
        x=[spent],
        orientation='h',
        marker=dict(color='#64748B'),
        text=[f"Spent: ₹{spent:,.0f}" if spent > 0 else ""],
        textposition='inside',
        insidetextanchor='middle',
        hovertemplate="Already Spent: ₹%{x:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name='Proposed Buys',
        y=['Monthly Deployment'],
        x=[proposed_buys],
        orientation='h',
        marker=dict(color=CHART_THEME['buy']),
        text=[f"Buys: ₹{proposed_buys:,.0f}" if proposed_buys > 0 else ""],
        textposition='inside',
        insidetextanchor='middle',
        hovertemplate="Proposed Buys: ₹%{x:,.2f}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        name='Cash Buffer',
        y=['Monthly Deployment'],
        x=[unallocated],
        orientation='h',
        marker=dict(color='#E2E8F0'),
        text=[f"Available: ₹{unallocated:,.0f}" if unallocated > 0 else ""],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='#334155'),
        hovertemplate="Available Buffer: ₹%{x:,.2f}<extra></extra>"
    ))

    fig.update_layout(
        barmode='stack',
        title=dict(
            text=f"Capital Deployment Plan (₹{limit:,.0f} Budget Cap)",
            font=dict(size=14, family=CHART_THEME['font_family'], color=CHART_THEME['text'], weight=700)
        ),
        paper_bgcolor=CHART_THEME['paper'],
        plot_bgcolor=CHART_THEME['bg'],
        font=dict(color=CHART_THEME['text'], family=CHART_THEME['font_family']),
        xaxis=dict(
            gridcolor=CHART_THEME['grid'],
            title=dict(text="Capital (₹)", font=dict(size=11, color=CHART_THEME['subtext'])),
            tickformat=",.0f",
            range=[0, limit * 1.05]
        ),
        yaxis=dict(showticklabels=False),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=CHART_THEME['subtext'], family=CHART_THEME['font_family'])
        ),
        margin=dict(t=45, b=40, l=20, r=20),
        height=180
    )
    return fig

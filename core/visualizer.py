"""
core/visualizer.py
Next-Gen Cyber-Fintech Visualizations for SPECTER.AI.
Renders neon donut charts, leak severity bars, and before/after hike delta graphics.
"""

from typing import List, Dict
import plotly.graph_objects as go
from core.detector import RecurringItem

# Modern Cyber-Fintech Palette
CYBER_PALETTE = [
    '#6366F1',  # Neon Indigo
    '#EC4899',  # Cyber Pink
    '#06B6D4',  # Electric Cyan
    '#10B981',  # Emerald Matrix
    '#8B5CF6',  # Deep Violet
    '#F59E0B',  # Amber Alert
    '#3B82F6',  # Tech Blue
    '#14B8A6',  # Teal Glow
]


def create_category_donut_chart(categories: Dict[str, float]) -> go.Figure:
    """Renders a sleek cyberpunk donut chart of recurring spend by category."""
    if not categories:
        fig = go.Figure()
        fig.add_annotation(
            text="No recurring subscriptions detected",
            showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=360)
        return fig

    labels = list(categories.keys())
    values = list(categories.values())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                textinfo='label+percent',
                textposition='inside',
                insidetextorientation='radial',
                hovertemplate="<b>%{label}</b><br>Annual Burn: $%{value:,.2f}<br>Share of Total: %{percent}<extra></extra>",
                marker=dict(
                    colors=CYBER_PALETTE,
                    line=dict(color='#0F172A', width=2)
                )
            )
        ]
    )

    # Center label annotation
    total_val = sum(values)
    fig.add_annotation(
        text=f"<span style='font-size:12px;color:#94A3B8;'>TOTAL BURN</span><br><b style='font-size:20px;color:#F8FAFC;'>${total_val:,.0f}</b>",
        x=0.5, y=0.5,
        font=dict(size=14, color="#F8FAFC", family="Inter, sans-serif"),
        showarrow=False
    )

    fig.update_layout(
        title=dict(
            text="<b>⚡ RECURRING SPEND BY CATEGORY</b>",
            font=dict(size=14, color="#94A3B8", family="Inter, monospace"),
            x=0.02, y=0.96
        ),
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=False,
        height=360,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#F8FAFC")
    )
    return fig


def create_subscriptions_bar_chart(items: List[RecurringItem]) -> go.Figure:
    """Horizontal bar chart ranking top subscriptions with glow markers for price hikes & trial traps."""
    if not items:
        fig = go.Figure()
        fig.add_annotation(
            text="No subscriptions to display",
            showarrow=False,
            font=dict(color="#94A3B8", size=14)
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=380)
        return fig

    sorted_items = sorted(items, key=lambda x: x.annualized_cost, reverse=True)[:10]

    merchants = [item.merchant for item in sorted_items]
    annual_costs = [item.annualized_cost for item in sorted_items]

    colors = [
        '#EF4444' if item.has_price_hike else ('#F59E0B' if item.is_trial_rollover else '#6366F1')
        for item in sorted_items
    ]

    custom_hover = [
        f"<b>{item.merchant}</b> ({item.cadence})<br>Rate: ${item.current_amount:.2f}/cycle<br>Annualized: ${item.annualized_cost:,.2f}"
        + (f"<br>🚨 <b>PRICE HIKE:</b> +${item.price_hike_amount:.2f} (+{item.price_hike_pct:.0f}%)" if item.has_price_hike else "")
        + ("<br>⚠️ <b>TRIAL TRAP:</b> Intro rate auto-converted" if item.is_trial_rollover else "")
        for item in sorted_items
    ]

    fig = go.Figure(
        go.Bar(
            x=annual_costs[::-1],
            y=merchants[::-1],
            orientation='h',
            marker=dict(
                color=colors[::-1],
                line=dict(width=1.5, color='rgba(255,255,255,0.2)'),
                cornerradius=4
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=custom_hover[::-1]
        )
    )

    fig.update_layout(
        title=dict(
            text="<b>🎯 TOP COMMITMENTS (Red = Hike | Yellow = Trap | Purple = Normal)</b>",
            font=dict(size=14, color="#94A3B8", family="Inter, monospace"),
            x=0.02, y=0.96
        ),
        xaxis=dict(
            title="",
            tickprefix="$",
            gridcolor="rgba(148, 163, 184, 0.1)",
            tickfont=dict(color="#94A3B8")
        ),
        yaxis=dict(
            title="",
            tickfont=dict(color="#E2E8F0", size=12)
        ),
        margin=dict(t=50, b=30, l=130, r=20),
        height=360,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    return fig


def create_price_hike_comparison_chart(items: List[RecurringItem]) -> go.Figure:
    """Cyberpunk grouped comparison bar chart of Original vs Hiked price tiers."""
    hike_items = [i for i in items if i.has_price_hike]
    if not hike_items:
        fig = go.Figure()
        fig.add_annotation(
            text="✨ Shield Active: No stealth price hikes detected in this dataset.",
            showarrow=False,
            font=dict(size=14, color="#10B981")
        )
        fig.update_layout(height=240, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        return fig

    merchants = [i.merchant for i in hike_items]
    initial_amts = [i.initial_amount for i in hike_items]
    current_amts = [i.current_amount for i in hike_items]

    fig = go.Figure(data=[
        go.Bar(
            name='Initial Rate',
            x=merchants,
            y=initial_amts,
            marker_color='#64748B',
            marker_line=dict(width=1, color='rgba(255,255,255,0.1)'),
            cornerradius=4
        ),
        go.Bar(
            name='Stealth Hiked Rate',
            x=merchants,
            y=current_amts,
            marker_color='#EF4444',
            marker_line=dict(width=1, color='rgba(239,68,68,0.4)'),
            cornerradius=4
        )
    ])

    fig.update_layout(
        barmode='group',
        title=dict(
            text="<b>🚨 STEALTH PRICE INFLATION (Original vs Hiked Rate)</b>",
            font=dict(size=14, color="#EF4444", family="Inter, monospace"),
            x=0.02, y=0.96
        ),
        yaxis=dict(
            title="",
            tickprefix="$",
            gridcolor="rgba(148, 163, 184, 0.1)",
            tickfont=dict(color="#94A3B8")
        ),
        xaxis=dict(tickfont=dict(color="#E2E8F0", size=12)),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#94A3B8")
        ),
        margin=dict(t=50, b=40, l=40, r=20),
        height=320,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    return fig

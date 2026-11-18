import plotly.graph_objects as go
import plotly.io as pio

def create_province_chart(df):
    """
    Membuat grafik batang horizontal (Plotly Bar Chart)
    menampilkan 8 provinsi dengan rata-rata harga tertinggi.
    """
    try:
        prov_grouped = df.groupby('province')['price_idr'].agg(['mean', 'count']).reset_index()
        prov_grouped = prov_grouped[prov_grouped['count'] >= 5]
        prov_top8 = prov_grouped.sort_values(by='mean', ascending=False).head(8)

        prov_names = prov_top8['province'].tolist()
        prov_prices_juta = [round(float(p) / 1_000_000, 1) for p in prov_top8['mean'].tolist()]

        prov_names.reverse()
        prov_prices_juta.reverse()

        max_price = max(prov_prices_juta) if prov_prices_juta else 1000

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=prov_prices_juta,
            y=prov_names,
            orientation='h',
            text=[f"Rp {int(val):,} Jt" for val in prov_prices_juta],
            textposition='outside',
            cliponaxis=False,
            textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
            marker=dict(
                color=prov_prices_juta,
                colorscale=[
                    [0.0, '#60A5FA'],
                    [0.35, '#3B82F6'],
                    [0.7, '#2563EB'],
                    [1.0, '#1D4ED8']
                ],
                line=dict(color='#1D4ED8', width=1.2)
            ),
            hovertemplate="<b>%{y}</b><br>Rata-rata: Rp %{x:,.1f} Juta<extra></extra>"
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=175, r=60, t=20, b=45),
            height=420,
            bargap=0.25,
            xaxis=dict(
                title=dict(text='Rata-rata Harga (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=12, color='#0F2744', weight='bold')),
                gridcolor='#E2E8F0',
                zerolinecolor='#CBD5E1',
                range=[0, max_price * 1.25],
                tickfont=dict(color='#1E293B', family='Plus Jakarta Sans', size=11, weight='bold')
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0)',
                ticksuffix='   ',
                tickfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold')
            ),
            font=dict(family='Plus Jakarta Sans')
        )
        return pio.to_json(fig)
    except Exception as e:
        print("Error create_province_chart:", e)
        return None


def create_price_scatter_chart(df):
    """
    Membuat grafik sebaran korelasi luas bangunan vs harga pasar (Plotly Scatter Plot).
    """
    try:
        scatter_df = df[
            (df['building_area_m2'] >= 20) & (df['building_area_m2'] <= 400) &
            (df['price_idr'] >= 100_000_000) & (df['price_idr'] <= 10_000_000_000)
        ]

        sample_size = min(1000, len(scatter_df))
        sampled = scatter_df.sample(sample_size, random_state=42)

        x_building = [float(x) for x in sampled['building_area_m2'].tolist()]
        y_price_miliar = [round(float(p) / 1_000_000_000, 2) for p in sampled['price_idr'].tolist()]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_building,
            y=y_price_miliar,
            mode='markers',
            marker=dict(
                size=7,
                color='#2563EB',
                opacity=0.65,
                line=dict(width=1, color='#1E40AF')
            ),
            hovertemplate="Luas Bangunan: <b>%{x} m²</b><br>Harga: <b>Rp %{y:.2f} Miliar</b><extra></extra>"
        ))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=75, r=40, t=25, b=50),
            height=420,
            xaxis=dict(
                title=dict(text='Luas Bangunan (m²)', font=dict(family='Plus Jakarta Sans', size=12, color='#0F2744', weight='bold')),
                gridcolor='#E2E8F0',
                zerolinecolor='#CBD5E1',
                tickfont=dict(color='#1E293B', family='Plus Jakarta Sans', size=11, weight='bold')
            ),
            yaxis=dict(
                title=dict(text='Harga Pasar (Miliar Rp)', font=dict(family='Plus Jakarta Sans', size=12, color='#0F2744', weight='bold')),
                gridcolor='#E2E8F0',
                zerolinecolor='#CBD5E1',
                tickfont=dict(color='#1E293B', family='Plus Jakarta Sans', size=11, weight='bold')
            ),
            font=dict(family='Plus Jakarta Sans')
        )
        return pio.to_json(fig)
    except Exception as e:
        print("Error create_price_scatter_chart:", e)
        return None


def create_distribution_chart(comp_prices_juta, comp_count, q1_juta, q3_juta, median_juta, pred_juta, percentile_display):
    """
    Membuat grafik histogram sebaran harga properti pembanding lokal (Plotly Histogram)
    dengan penanda garis kuartil, median, dan pin rumah pengguna.
    """
    try:
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=comp_prices_juta,
            nbinsx=min(25, max(8, comp_count // 3)),
            name='Unit Pasar Pembanding',
            marker=dict(
                color='#DBEAFE',
                line=dict(color='#60A5FA', width=1)
            ),
            hovertemplate="Rentang: Rp %{x:,.0f} Juta<br>Frekuensi: %{y} unit<extra></extra>"
        ))

        # Garis Kuartil
        fig.add_vline(x=q1_juta, line_width=1.5, line_dash="dash", line_color="#94A3B8")
        fig.add_vline(x=q3_juta, line_width=1.5, line_dash="dash", line_color="#94A3B8")

        # Garis Median Pasar
        fig.add_vline(x=median_juta, line_width=2, line_dash="dot", line_color="#0F2744")

        # Marker Pin Rumah Pengguna
        fig.add_vline(
            x=pred_juta,
            line_width=3,
            line_color="#2563EB",
            annotation_text=f"Rumah Anda: Rp {int(pred_juta):,} Jt ({percentile_display})",
            annotation_position="top right",
            annotation_font=dict(family="Plus Jakarta Sans", size=11, color="#2563EB", weight="bold"),
            annotation_bgcolor="#EFF6FF",
            annotation_bordercolor="#2563EB",
            annotation_borderwidth=1.2
        )

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=45, r=30, t=35, b=40),
            height=320,
            bargap=0.08,
            showlegend=False,
            xaxis=dict(
                title=dict(text='Rentang Harga Properti Pembanding (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                gridcolor='#DBEAFE',
                zerolinecolor='#DBEAFE',
                tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
            ),
            yaxis=dict(
                title=dict(text='Jumlah Unit', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                gridcolor='#DBEAFE',
                zerolinecolor='#DBEAFE',
                tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
            ),
            font=dict(family='Plus Jakarta Sans')
        )
        return pio.to_json(fig)
    except Exception as e:
        print("Error create_distribution_chart:", e)
        return None


def create_factors_chart(contributions):
    """
    Membuat grafik dual bar chart untuk analisis faktor Explainable AI (TreeSHAP)
    menampilkan kontribusi positif (biru) dan penahan (abu-abu).
    """
    try:
        labels_list = [c['label'] for c in contributions][::-1]
        deltas_list = [c['delta_juta'] for c in contributions][::-1]

        max_abs_delta = max([abs(d) for d in deltas_list]) if deltas_list and max([abs(d) for d in deltas_list]) > 0 else 50

        pos_x = [d if d >= 0 else None for d in deltas_list]
        neg_x = [d if d < 0 else None for d in deltas_list]
        pos_text = [f"+Rp {int(d):,} Jt" if d is not None else "" for d in pos_x]
        neg_text = [f"-Rp {abs(int(d)):,} Jt" if d is not None else "" for d in neg_x]

        fig = go.Figure()

        # Trace Bar Positif
        fig.add_trace(go.Bar(
            x=pos_x,
            y=labels_list,
            orientation='h',
            text=pos_text,
            textposition='outside',
            cliponaxis=False,
            textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
            marker=dict(color='#2563EB', line=dict(color='#1D4ED8', width=1)),
            hovertemplate="<b>%{y}</b><br>Dampak Valuasi: %{text}<extra></extra>",
            showlegend=False
        ))

        # Trace Bar Negatif
        fig.add_trace(go.Bar(
            x=neg_x,
            y=labels_list,
            orientation='h',
            text=neg_text,
            textposition='outside',
            cliponaxis=False,
            textfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11, weight='bold'),
            marker=dict(color='#94A3B8', line=dict(color='#64748B', width=1)),
            hovertemplate="<b>%{y}</b><br>Dampak Valuasi: %{text}<extra></extra>",
            showlegend=False
        ))

        fig.add_vline(x=0, line_width=1.5, line_color="#0F2744")

        max_neg = max([abs(d) for d in deltas_list if d < 0]) if any(d < 0 for d in deltas_list) else 0
        neg_range = max(max_neg * 3.5, max_abs_delta * 0.35)

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=180, r=100, t=15, b=35),
            height=320,
            barmode='overlay',
            bargap=0.3,
            xaxis=dict(
                title=dict(text='Dampak Valuasi terhadap Harga Dasar (Juta Rp)', font=dict(family='Plus Jakarta Sans', size=11, color='#5B708B')),
                gridcolor='#DBEAFE',
                zerolinecolor='#0F2744',
                range=[-neg_range, max_abs_delta * 1.5],
                tickfont=dict(color='#5B708B', family='Plus Jakarta Sans', size=11)
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0)',
                ticksuffix='  ',
                tickfont=dict(color='#0F2744', family='Plus Jakarta Sans', size=11)
            ),
            font=dict(family='Plus Jakarta Sans')
        )
        return pio.to_json(fig)
    except Exception as e:
        print("Error create_factors_chart:", e)
        return None

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from scipy import stats
import os

# สร้างแอป Dash พร้อม Theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])
server = app.server

current_dir = os.path.dirname(os.path.abspath(__file__))
exchange_rates_path = os.path.join(current_dir, "Foreign_Exchange_Rates.csv")
inflation_path = os.path.join(current_dir, "Filtered_Inflation_Data.csv")

exchange_data = pd.read_csv(exchange_rates_path)
inflation_data = pd.read_csv(inflation_path)

# ทำความสะอาดข้อมูล Exchange Rates
exchange_data.rename(columns={'Time Serie': 'Date'}, inplace=True)
exchange_data['Date'] = pd.to_datetime(exchange_data['Date'])
exchange_data = exchange_data.replace('ND', None).dropna()

# แปลงคอลัมน์เป็นตัวเลข
for column in exchange_data.columns[2:]:
    exchange_data[column] = pd.to_numeric(exchange_data[column], errors='coerce')

# Melt Inflation Data เพื่อทำให้ง่ายต่อการใช้งาน
inflation_data_melted = pd.melt(
    inflation_data, 
    id_vars=['Country', 'Series_Name'], 
    var_name='Year', 
    value_name='Inflation_Rate'
)

# กำหนดธีมสีใหม่ที่มองเห็นได้ง่าย - ใช้ชุดสี ColorBrewer ที่เป็นมิตรกับทุกคน
# ชุดสีที่มีความแตกต่างมากขึ้น และเป็นมิตรกับผู้มีปัญหาตาบอดสี
enhanced_palette = [
    '#1f77b4',  # สีน้ำเงินเข้มอมฟ้า
    '#ff7f0e',  # สีส้ม
    '#2ca02c',  # สีเขียว
    '#d62728',  # สีแดง
    '#9467bd',  # สีม่วง
    '#8c564b',  # สีน้ำตาล
    '#e377c2',  # สีชมพู
    '#7f7f7f',  # สีเทา
    '#bcbd22',  # สีเหลืองอมเขียว
    '#17becf'   # สีฟ้า
]

# Layout ของ Dashboard
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("💱 Global Financial Exchange Dashboard", 
                        className="text-center text-primary my-4 fw-bold"), 
                width=12)
    ]),

    # Currency Selector
    dbc.Row([
        dbc.Col([
            html.Label("Select Currencies:", className="fw-bold"),
            dcc.Dropdown(
                id='currency-dropdown',
                options=[{'label': col, 'value': col} for col in exchange_data.columns[2:]],
                value=[exchange_data.columns[2], exchange_data.columns[3]],
                multi=True,
                className="mb-3",
                style={'color': 'black'}
            )
        ], width=12)       
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Label("Select Date Range:", className="fw-bold"),
            # เปลี่ยนจาก DatePickerRange เป็น RangeSlider
            dcc.RangeSlider(
                id='date-range-slider',
                min=0,
                max=len(exchange_data) - 1,  # ใช้ index ของข้อมูลแทนวันที่จริง
                step=1,
                value=[0, len(exchange_data) - 1],  # เริ่มต้นด้วยช่วงข้อมูลทั้งหมด
                marks={
                    0: {'label': exchange_data['Date'].min().strftime('%Y-%m-%d')},
                    len(exchange_data) - 1: {'label': exchange_data['Date'].max().strftime('%Y-%m-%d')},
                    len(exchange_data) // 4: {'label': exchange_data['Date'].iloc[len(exchange_data) // 4].strftime('%Y-%m-%d')},
                    len(exchange_data) // 2: {'label': exchange_data['Date'].iloc[len(exchange_data) // 2].strftime('%Y-%m-%d')},
                    3 * len(exchange_data) // 4: {'label': exchange_data['Date'].iloc[3 * len(exchange_data) // 4].strftime('%Y-%m-%d')}
                },
                className="mb-3"
            ),
            # เพิ่มข้อความแสดงวันที่ที่เลือก
            html.Div(id='date-range-display', className="text-center mb-3")
        ], width=12)
    ], className="mb-4"),

    # Graphs Grid - เลือกแค่กราฟที่จำเป็นและใช้ง่าย
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Exchange Rate Trends Over Time"),
            dcc.Graph(id='line-chart')
        ], className="shadow-sm"), width=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Histogram of Currency Distribution"),
            dcc.Graph(id='histogram-chart')
        ], className="shadow-sm"), width=12, lg=6),
        
        dbc.Col(dbc.Card([
            dbc.CardHeader("Exchange Rate Distribution"),
            dcc.Graph(id='box-plot')
        ], className="shadow-sm"), width=12, lg=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Currency Correlation (Select 2 Currencies)"),
            dcc.Graph(id='bubble-chart')
        ], className="shadow-sm"), width=12, lg=6),
        
        dbc.Col(dbc.Card([
            dbc.CardHeader("Monthly Change Overview"),
            dcc.Graph(id='area-chart')
        ], className="shadow-sm"), width=12, lg=6),
    ], className="mb-4"),

    # Inflation Section
    dbc.Row([
        dbc.Col([
            html.Label("Select Inflation Series:", className="fw-bold"),
            dcc.Dropdown(
                id='inflation-series-dropdown',
                options=[{'label': series, 'value': series} for series in inflation_data['Series_Name'].unique()],
                value='Headline Consumer Price Inflation',
                multi=False,
                className="mb-3",
                style={'color': 'black'}
            )
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Inflation Trends Across Countries"),
            dcc.Graph(id='inflation-line-chart')
        ], className="shadow-sm"), width=12),
    ], className="mb-4"),
    
    
    dbc.Row([
        dbc.Col([
            html.Label("Select currency for forecasting :", className="fw-bold"),
            dcc.Dropdown(
                id='forecast-currency-dropdown',
                options=[],  # เราจะอัปเดตตัวเลือกนี้ตาม callback
                value=None,  # ค่าเริ่มต้นจะถูกกำหนดโดย callback
                multi=False,
                className="mb-3",
                style={'color': 'black'}
            )
        ], width=12)
    ], className="mb-3"),
    
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("Trend Analysis & Forecasting"),
            dcc.Graph(id='forecast-chart')
        ], className="shadow-sm"), width=12),
    ], className="mb-4"),

    # Simple Statistics Section
    dbc.Row([
        dbc.Col(html.Div(id='statistics-output', 
                         className="p-3 bg-light rounded"), 
                width=12)
    ]),

    dbc.Row([
        dbc.Col(html.H3("Key Insights", className="mt-4 mb-3 text-primary"), width=12),
        dbc.Col(html.Div(id='key-insights'), width=12)
    ], className="mb-4"),
    
    # Footer
    html.Footer(
        "© 2025 Global Financial Dashboard - All Rights Reserved",
        className="text-center text-light py-3 bg-dark mt-4"
    )   
], fluid=True)

# Callback สำหรับแสดงวันที่ที่เลือกจาก RangeSlider
@app.callback(
    Output('date-range-display', 'children'),
    [Input('date-range-slider', 'value')]
)
def update_date_display(date_indices):
    if date_indices is None:
        return "Please select a date range"
    
    start_date = exchange_data['Date'].iloc[date_indices[0]].strftime('%Y-%m-%d')
    end_date = exchange_data['Date'].iloc[date_indices[1]].strftime('%Y-%m-%d')
    
    return html.P([
        "Selected period: ",
        html.Strong(f"{start_date} to {end_date}")
    ])
    
@app.callback(
    [Output('forecast-currency-dropdown', 'options'),
     Output('forecast-currency-dropdown', 'value')],
    [Input('currency-dropdown', 'value')]
)
def update_forecast_dropdown(selected_currencies):
    options = [{'label': currency, 'value': currency} for currency in selected_currencies] if selected_currencies else []
    default_value = selected_currencies[0] if selected_currencies else None
    return options, default_value

# Callback สำหรับอัปเดตกราฟและสถิติ
@app.callback(
    [Output('line-chart', 'figure'),
     Output('histogram-chart', 'figure'),
     Output('bubble-chart', 'figure'),
     Output('box-plot', 'figure'),
     Output('area-chart', 'figure'),
     Output('inflation-line-chart', 'figure'),
     Output('forecast-chart', 'figure'),
     Output('statistics-output', 'children')],
    [Input('currency-dropdown', 'value'),
     Input('inflation-series-dropdown', 'value'),
     Input('date-range-slider', 'value'),
     Input('forecast-currency-dropdown', 'value')]
)

def update_dashboard(selected_currencies, selected_inflation_series, date_indices, forecast_currency):
    # ตรวจสอบว่ามีการเลือกสกุลเงินหรือไม่
    if not selected_currencies:
        selected_currencies = [exchange_data.columns[2]]  # default to first currency
    
    # กรองข้อมูลตามช่วงวันที่จาก slider
    if date_indices:
        start_idx, end_idx = date_indices
        filtered_exchange_data = exchange_data.iloc[start_idx:end_idx+1]
    else:
        filtered_exchange_data = exchange_data
        
    
    # 1. กราฟเส้น - แสดงแนวโน้มตามเวลา (รองรับทุกจำนวนสกุลเงิน)
    line_fig = go.Figure()
    max_currencies_to_show = 10  # จำกัดจำนวนเส้นในกราฟเพื่อความชัดเจน
    
    for i, currency in enumerate(selected_currencies[:max_currencies_to_show]):
        line_fig.add_trace(go.Scatter(
            x=filtered_exchange_data['Date'], 
            y=filtered_exchange_data[currency], 
            mode='lines', 
            name=currency,
            line=dict(
                color=enhanced_palette[i % len(enhanced_palette)],
                width=2
            )
        ))
    
    line_fig.update_layout(
        title=f"Exchange Rates for {len(selected_currencies)} Selected Currencies", 
        xaxis_title="Date",
        yaxis_title="Exchange Rate Value",
        legend_title="Currencies",
        hovermode="x unified",
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    if len(selected_currencies) > max_currencies_to_show:
        line_fig.add_annotation(
            text=f"Showing first {max_currencies_to_show} out of {len(selected_currencies)} selected currencies",
            xref="paper", yref="paper",
            x=1, y=1.1, showarrow=False,
            font=dict(size=12, color=enhanced_palette[3])  # ใช้สีแดงจากชุดสีใหม่
        )

    # 2. Histogram - แสดงการกระจายตัวของข้อมูลสำหรับแต่ละสกุลเงิน
    histogram_fig = go.Figure()

    # ใช้สีจากชุดสีใหม่เพื่อให้มองเห็นได้ชัดเจนขึ้น
    for i, currency in enumerate(selected_currencies):
        histogram_fig.add_trace(go.Histogram(
            x=filtered_exchange_data[currency],
            name=currency,
            opacity=0.7,
            marker_color=enhanced_palette[i % len(enhanced_palette)],
            xbins=dict(
                size=0.02  # ให้ bin size เล็กลงเพื่อให้ได้รายละเอียดมากขึ้น
            ),
            autobinx=False  # ปิดการกำหนด bin อัตโนมัติ
        ))

    histogram_fig.update_layout(
        title="Histogram of Currency Distribution",
        xaxis_title="Exchange Rate Value",
        yaxis_title="Frequency",
        template="plotly_white",
        barmode='overlay',  # ใช้ overlay เสมอเพื่อให้เห็นการซ้อนทับ
        bargap=0.05,  # ลดช่องว่างระหว่างแท่ง
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        # เพิ่มขอบเขตของแกน x เพื่อให้มีความกว้างเหมือนในรูป
        xaxis=dict(range=[0.5, 2.1])
    )

    # 3. Bubble Chart - แสดงความสัมพันธ์ระหว่างสกุลเงิน
    bubble_fig = go.Figure()
    if len(selected_currencies) >= 2:
        # เลือกเฉพาะสองสกุลเงินแรกที่ถูกเลือก
        curr1 = selected_currencies[0]
        curr2 = selected_currencies[1]
        
        # คำนวณค่า correlation ระหว่างสองสกุลเงิน
        corr_value = filtered_exchange_data[[curr1, curr2]].corr().iloc[0, 1]
        
        # สร้าง scatter plot แสดงความสัมพันธ์ - ใช้ Viridis colorscale ที่มองเห็นได้ง่าย
        bubble_fig.add_trace(go.Scatter(
            x=filtered_exchange_data[curr1],
            y=filtered_exchange_data[curr2],
            mode='markers',
            name=f"{curr1} vs {curr2} (corr: {corr_value:.2f})",
            marker=dict(
                size=8,
                opacity=0.7,
                color=filtered_exchange_data[curr1],
                colorscale='Plasma',  # เปลี่ยนเป็น Plasma ที่มีความคมชัดมากขึ้น
                colorbar=dict(title="Value"),
                showscale=True
            )
        ))
        
        bubble_fig.update_layout(
            title=f"Bubble Chart: {curr1} vs {curr2}",
            xaxis_title=f"{curr1} Value",
            yaxis_title=f"{curr2} Value",
            template="plotly_white",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    else:
        bubble_fig.add_annotation(
            text="Please select at least 2 currencies to view correlation",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color=enhanced_palette[3])  # ใช้สีแดงจากชุดสีใหม่
        )
    
    # 4. Box Plot - แสดงการกระจายตัวของข้อมูล (รองรับทุกจำนวนสกุลเงิน)
    box_fig = go.Figure()
    if len(selected_currencies) > 20:  # ถ้ามีมากกว่า 20 สกุล จัดกลุ่มตามค่าเฉลี่ย
        mean_values = filtered_exchange_data[selected_currencies].mean().sort_values()
        low_currencies = mean_values.head(10).index.tolist()
        medium_currencies = mean_values[10:-10].index.tolist()
        high_currencies = mean_values.tail(10).index.tolist()
            
        groups = [
            ('Low Range', low_currencies),
            ('Medium Range', []),  # ไม่แสดงสกุลกลุ่มกลางถ้ามีมากเกินไป
            ('High Range', high_currencies)
        ]
            
        for i, (group_name, currencies) in enumerate(groups):
            if currencies:
                box_fig.add_trace(go.Box(
                    y=filtered_exchange_data[currencies].values.flatten(), 
                    name=group_name,
                    marker_color=enhanced_palette[i % len(enhanced_palette)]
                ))
    else:  # แสดงปกติสำหรับสกุลเงินจำนวนน้อย
        for i, currency in enumerate(selected_currencies):
            box_fig.add_trace(go.Box(
                y=filtered_exchange_data[currency], 
                name=currency,
                marker_color=enhanced_palette[i % len(enhanced_palette)]
            ))
        
    box_fig.update_layout(
        title="Exchange Rate Distribution" + (" (Grouped)" if len(selected_currencies) > 20 else ""),
        yaxis_title="Exchange Rate Value",
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # 5. Area Chart - แสดงการเปลี่ยนแปลงรายเดือน (รองรับทุกจำนวนสกุลเงิน)
    filtered_exchange_data['Month'] = filtered_exchange_data['Date'].dt.strftime('%Y-%m')
    monthly_pct_change = filtered_exchange_data.groupby('Month')[selected_currencies].mean().pct_change() * 100
    monthly_pct_change = monthly_pct_change.dropna()
    
    area_fig = go.Figure()
    if len(selected_currencies) <= 5:  # ถ้ามีไม่เกิน 5 สกุล แสดงเป็น area chart
        for i, currency in enumerate(selected_currencies):
            area_fig.add_trace(go.Scatter(
                x=monthly_pct_change.index, 
                y=monthly_pct_change[currency], 
                fill='tozeroy', 
                name=currency,
                line=dict(color=enhanced_palette[i % len(enhanced_palette)])
            ))
    else:  # ถ้ามีมากกว่า 5 สกุล แสดงเป็นค่าเฉลี่ยการเปลี่ยนแปลง
        avg_change = monthly_pct_change.mean(axis=1)
        area_fig.add_trace(go.Scatter(
            x=monthly_pct_change.index, 
            y=avg_change, 
            fill='tozeroy', 
            name='Average Change',
            line=dict(color=enhanced_palette[0])
        ))
        
        # เพิ่มช่วงความผันผวน (standard deviation) - ใช้สีที่มองเห็นได้ชัดเจนขึ้น
        std_change = monthly_pct_change.std(axis=1)
        
        # แปลงสี HEX เป็น RGB เพื่อกำหนดค่า alpha
        hex_color = enhanced_palette[1].lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        area_fig.add_trace(go.Scatter(
            x=monthly_pct_change.index.tolist() + monthly_pct_change.index.tolist()[::-1],
            y=(avg_change + std_change).tolist() + (avg_change - std_change).tolist()[::-1],
            fill='toself',
            fillcolor=f'rgba({r}, {g}, {b}, 0.3)',  # เพิ่มค่า alpha เป็น 0.3 เพื่อให้มองเห็นชัดขึ้น
            line=dict(color='rgba(255, 255, 255, 0)'),
            hoverinfo="skip",
            showlegend=False
        ))
    
    area_fig.update_layout(
        title="Monthly Percentage Change" if len(selected_currencies) <= 5 else "Average Monthly Change",
        xaxis_title="Month",
        yaxis_title="Change (%)",
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # 6. Inflation Line Chart - ใช้ชุดสีที่มองเห็นได้ง่ายขึ้น
    inflation_series_data = inflation_data_melted[
        inflation_data_melted['Series_Name'] == selected_inflation_series
    ]
    
    # ใช้ px.line โดยกำหนด color_discrete_sequence เป็นชุดสีใหม่
    inflation_line_fig = px.line(
        inflation_series_data, 
        x='Year', 
        y='Inflation_Rate', 
        color='Country',
        title=f'{selected_inflation_series} Trends',
        template="plotly_white",
        color_discrete_sequence=enhanced_palette  # ใช้ชุดสีที่มองเห็นได้ง่ายขึ้น
    )
    
    inflation_line_fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Inflation Rate (%)",
        legend_title="Countries"
    )
    
    # ส่วนของกราฟพยากรณ์
    forecast_fig = go.Figure()

    # ตรวจสอบว่ามีการเลือกสกุลเงินสำหรับการพยากรณ์หรือไม่
    if forecast_currency:
        from scipy import stats as scipy_stats
        currency = forecast_currency  # ใช้สกุลเงินที่เลือกจาก dropdown สำหรับการพยากรณ์
        
        # ดึงข้อมูลเฉพาะสกุลเงินที่เลือก
        currency_data = filtered_exchange_data[['Date', currency]].dropna()
        
        # เช็คว่ามีข้อมูลพอหรือไม่
        if len(currency_data) > 10:  # ต้องมีข้อมูลอย่างน้อย 10 จุดในการสร้างการพยากรณ์
            # สร้าง array ของ index สำหรับการคำนวณแนวโน้ม (0, 1, 2, 3, ...)
            x_values = np.arange(len(currency_data))
            y_values = currency_data[currency].values
            
            try:
                # คำนวณเส้นแนวโน้มแบบเชิงเส้น (linear regression)
                slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x_values, y_values)
                trend_line = intercept + slope * x_values
                
                # เพิ่มกราฟเส้นแสดงข้อมูลจริง
                forecast_fig.add_trace(go.Scatter(
                    x=currency_data['Date'],
                    y=y_values,
                    mode='lines',
                    name=f'{currency} (Actual Data)',
                    line=dict(color=enhanced_palette[0], width=2)
                ))
                
                # เพิ่มเส้นแนวโน้ม
                forecast_fig.add_trace(go.Scatter(
                    x=currency_data['Date'],
                    y=trend_line,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color=enhanced_palette[2], width=2, dash='dash')
                ))
                
                # สร้างข้อมูลพยากรณ์ล่วงหน้า 30 วัน
                last_date = currency_data['Date'].iloc[-1]
                future_dates = pd.date_range(start=last_date, periods=31)[1:]  # สร้างวันที่ล่วงหน้า 30 วัน
                future_indices = np.arange(len(x_values), len(x_values) + 30)  # สร้าง index ต่อจากข้อมูลจริง
                future_values = intercept + slope * future_indices  # คำนวณค่าพยากรณ์จากสมการเส้นตรง
                
                # เพิ่มเส้นพยากรณ์
                forecast_fig.add_trace(go.Scatter(
                    x=future_dates,
                    y=future_values,
                    mode='lines',
                    name='30-Day Forecast',
                    line=dict(color=enhanced_palette[1], width=2)
                ))
                
                # เพิ่มช่วงความเชื่อมั่น 95% (confidence interval) - ใช้สีที่มองเห็นได้ชัดเจนขึ้น
                ci = 1.96 * std_err  # ช่วงความเชื่อมั่น 95%
                
                # แปลงสี HEX เป็น RGB
                hex_color = enhanced_palette[1].lstrip('#')
                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                
                forecast_fig.add_trace(go.Scatter(
                    x=list(future_dates) + list(future_dates)[::-1],
                    y=list(future_values + ci) + list(future_values - ci)[::-1],
                    fill='toself',
                    fillcolor=f'rgba({r}, {g}, {b}, 0.3)',  # เพิ่มค่า alpha เพื่อให้มองเห็นชัดขึ้น
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    hoverinfo='skip',
                    showlegend=False,
                    name='95% Confidence Interval'
                ))
                
            except Exception as e:
                # จัดการกรณีมีปัญหาในการคำนวณ
                forecast_fig.add_annotation(
                    text=f"Cannot calculate forecast: insufficient data or calculation error",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color=enhanced_palette[3])  # ใช้สีแดงจากชุดสีใหม่
                )
        else:
            # กรณีข้อมูลไม่เพียงพอ
            forecast_fig.add_annotation(
                text=f"Insufficient data for {currency} to create forecast",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color=enhanced_palette[3])
            )
    else:
        # กรณีไม่มีการเลือกสกุลเงิน
        forecast_fig.add_annotation(
            text="กรุณาเลือกสกุลเงินเพื่อดูการพยากรณ์",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#E63946")
        )

    # กำหนดรูปแบบของกราฟ
    forecast_fig.update_layout(
        title=f"การวิเคราะห์แนวโน้มและพยากรณ์ 30 วัน" + (f" สำหรับ {forecast_currency}" if forecast_currency else ""),
        xaxis_title="วันที่",
        yaxis_title="อัตราแลกเปลี่ยน",
        template="plotly_white",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    

    # สร้างสถิติอย่างง่าย
    statistics_cards = []
    
    if len(selected_currencies) == 1:
        # สำหรับสกุลเงินเดียว แสดงข้อมูลละเอียด
        currency = selected_currencies[0]
        stats = filtered_exchange_data[currency].describe()
        
        stats_card = dbc.Card([
            dbc.CardHeader(f"Statistics for {currency}", className="text-white", style={'background-color': red_blue_palette[0]}),
            dbc.CardBody([
                html.Div([
                    html.P(f"Average: {stats['mean']:.4f}"),
                    html.P(f"Current (latest): {filtered_exchange_data[currency].iloc[-1]:.4f}"),
                    html.P(f"Highest: {stats['max']:.4f}"),
                    html.P(f"Lowest: {stats['min']:.4f}"),
                    html.P(f"Standard Deviation: {stats['std']:.4f}")
                ])
            ])
        ], className="mb-3")
        
        statistics_cards.append(stats_card)
    else:
        # สำหรับหลายสกุลเงิน แสดงภาพรวม
        overall_stats = dbc.Card([
            dbc.CardHeader(f"Overview of {len(selected_currencies)} Selected Currencies", 
                         className="text-white", style={'background-color': red_blue_palette[1]}),
            dbc.CardBody([
                html.Div([
                    html.P(f"Highest average rate: {filtered_exchange_data[selected_currencies].mean().max():.4f} ({filtered_exchange_data[selected_currencies].mean().idxmax()})"),
                    html.P(f"Lowest average rate: {filtered_exchange_data[selected_currencies].mean().min():.4f} ({filtered_exchange_data[selected_currencies].mean().idxmin()})"),
                    html.P(f"Most volatile: {filtered_exchange_data[selected_currencies].std().idxmax()} (SD: {filtered_exchange_data[selected_currencies].std().max():.4f})"),
                    html.P(f"Most stable: {filtered_exchange_data[selected_currencies].std().idxmin()} (SD: {filtered_exchange_data[selected_currencies].std().min():.4f})")
                ])
            ])
        ], className="mb-3")
        
        statistics_cards.append(overall_stats)
    
    return line_fig, histogram_fig, bubble_fig, box_fig, area_fig, inflation_line_fig, forecast_fig, statistics_cards

@app.callback(
    Output('key-insights', 'children'),
    [Input('currency-dropdown', 'value'),
     Input('date-range-slider', 'value')]  # เปลี่ยนจาก date-range-picker เป็น date-range-slider
)

def update_insights(selected_currencies, date_indices):
    if not selected_currencies:
        return html.P("Please select at least one currency to see insights.")
    
    # กรองข้อมูลตามช่วงวันที่จาก slider
    if date_indices:
        start_idx, end_idx = date_indices
        filtered_data = exchange_data.iloc[start_idx:end_idx+1]
    else:
        filtered_data = exchange_data
    
    insights = []
    
    # วิเคราะห์แนวโน้มสำหรับสกุลเงินที่เลือก
    for currency in selected_currencies:
        trend_data = filtered_data[[currency]].pct_change().dropna()
        
        # คำนวณแนวโน้มล่าสุด (30 วันล่าสุด)
        recent_trend = trend_data.tail(30).mean().values[0] * 100
        trend_direction = "upward" if recent_trend > 0 else "downward"
        
        # คำนวณความผันผวน
        volatility = trend_data.std().values[0] * 100
        
        # สร้าง insight card สำหรับแต่ละสกุลเงิน
        currency_card = dbc.Card([
            dbc.CardHeader(f"{currency} Analysis", 
                          className="bg-primary text-white"),
            dbc.CardBody([
                html.H5(f"{currency} Trends", className="card-title"),
                html.P([
                    f"The {currency} shows a {trend_direction} trend of {abs(recent_trend):.2f}% over the recent period.",
                    html.Br(),
                    f"Volatility: {volatility:.2f}% (standard deviation of daily returns)"
                ]),
                
                # เพิ่มการเปรียบเทียบกับสกุลเงินอื่น (ถ้ามีมากกว่า 1 สกุลเงิน)
                html.Div([
                    html.H5("Comparative Analysis", className="card-title mt-3"),
                    html.P([
                        f"Compared to other selected currencies, {currency} "
                        f"{'has higher volatility' if volatility > trend_data.std().mean() else 'is more stable'}."
                    ])
                ]) if len(selected_currencies) > 1 else html.Div()
            ])
        ], className="shadow-sm mb-3")
        
        insights.append(currency_card)
    
    # สร้าง Key Findings จากการวิเคราะห์ทั้งหมด
    if len(selected_currencies) > 1:
        # คำนวณความสัมพันธ์ระหว่างสกุลเงินที่เลือก
        correlation_matrix = filtered_data[selected_currencies].corr()
        
        # หาคู่สกุลเงินที่มีความสัมพันธ์มากที่สุด
        corr_pairs = []
        for i in range(len(selected_currencies)):
            for j in range(i+1, len(selected_currencies)):
                curr1 = selected_currencies[i]
                curr2 = selected_currencies[j]
                corr = correlation_matrix.loc[curr1, curr2]
                corr_pairs.append((curr1, curr2, corr))
        
        # เรียงลำดับตามค่าสัมบูรณ์ของความสัมพันธ์
        corr_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        
        # สร้าง overall insights
        overall_card = dbc.Card([
            dbc.CardHeader("Overall Analysis", className="bg-primary text-white"),
            dbc.CardBody([
                html.H5("Currency Relationships", className="card-title"),
                html.P([
                    "Key correlations between selected currencies:",
                    html.Ul([
                        html.Li([
                            f"{pair[0]} and {pair[1]}: ",
                            html.Strong(f"{pair[2]:.2f}"),
                            f" ({('Strong positive' if pair[2] > 0.7 else 'Strong negative' if pair[2] < -0.7 else 'Moderate positive' if pair[2] > 0.3 else 'Moderate negative' if pair[2] < -0.3 else 'Weak')} correlation)"
                        ]) for pair in corr_pairs[:3]  # แสดงเฉพาะ 3 อันดับแรก
                    ])
                ]),
                
                html.H5("Volatility Comparison", className="card-title mt-3"),
                html.P([
                    f"Most volatile: {filtered_data[selected_currencies].std().idxmax()} (SD: {filtered_data[selected_currencies].std().max():.4f})",
                    html.Br(),
                    f"Most stable: {filtered_data[selected_currencies].std().idxmin()} (SD: {filtered_data[selected_currencies].std().min():.4f})"
                ])
            ])
        ], className="shadow-sm mb-3")
        
        insights.append(overall_card)
    
    return insights

# รัน app
if __name__ == '__main__':
    # ใช้พอร์ตจาก environment variable (สำคัญสำหรับ Render)
    port = int(os.environ.get('PORT', 8080))
    app.run_server(host='0.0.0.0', port=port, debug=False)

# price_dash.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

### ----- 1. データ読み込み & 前処理 -----
df = pd.read_excel('/Users/yojihamanishi/Library/Mobile Documents/com~apple~CloudDocs/仕事/Database/Price_List.xlsx', sheet_name='Data Base')

# 異常値除外
df = df[
    (df['ARR (Rack Rate)']<=4000) &
    (df['ARR (Lowest)'] <= 4000)
]

# サイズ帯を件数ベースで等分割
df['SizeBucket'] = pd.qcut(df['Size'], q=6)
df['SizeBucket'] = df['SizeBucket'].astype(str)  # 表示を文字列化してわかりやすく

# # 簡易エリアタグ
# def area(branch):
#     for kw in ['Pattaya','PTY','Chon','Laem','Pattaya']:
#         if kw.lower() in branch.lower(): return 'Pattaya/Chon'
#     for kw in ['Phuket','PTG']:
#         if kw.lower() in branch.lower(): return 'Phuket'
#     return 'Bangkok'
# df['Area'] = df['Branch'].apply(area)

### ----- 2. SIDEBAR コントロール -----
st.sidebar.header('Filters')

# A/C フィルタ
ac_options = st.sidebar.multiselect('A/C', df['A/C'].unique().tolist(),
                                    default=df['A/C'].unique().tolist())

# Type フィルタ
type_options = st.sidebar.multiselect('Type', df['Type'].unique().tolist(),
                                      default=df['Type'].unique().tolist())

# ---------------------------------
# Size range: number inputs + slider
# ---------------------------------
size_abs_min, size_abs_max = int(df['Size'].min()), int(df['Size'].max())

# セッション初期化
if 'size_min' not in st.session_state:
    st.session_state['size_min'] = size_abs_min
if 'size_max' not in st.session_state:
    st.session_state['size_max'] = size_abs_max

st.sidebar.write('Size range (m²)')
col_min, col_max = st.sidebar.columns(2)

# 数値入力ボックス
with col_min:
    st.session_state['size_min'] = st.number_input(
        'Min', value=st.session_state['size_min'],
        min_value=size_abs_min, max_value=size_abs_max, step=1, key='size_min_box'
    )
with col_max:
    st.session_state['size_max'] = st.number_input(
        'Max', value=st.session_state['size_max'],
        min_value=size_abs_min, max_value=size_abs_max, step=1, key='size_max_box'
    )

# スライダー
size_range = st.sidebar.slider(
    'Adjust with slider', size_abs_min, size_abs_max,
    (st.session_state['size_min'], st.session_state['size_max']),
    key='size_slider'
)

# 双方向同期
if size_range != (st.session_state['size_min'], st.session_state['size_max']):
    st.session_state['size_min'], st.session_state['size_max'] = size_range
else:
    size_range = (st.session_state['size_min'], st.session_state['size_max'])

# ---------------------------------
# Branch フィルタ（Select‑all 対応）
# ---------------------------------
branches_all = sorted(df['Branch'].unique().tolist())

# セッション初期化
if 'branch_sel' not in st.session_state:
    st.session_state['branch_sel'] = branches_all

# ボタン行
col_a, col_b = st.sidebar.columns(2)
if col_a.button('Select all'):
    st.session_state['branch_sel'] = branches_all
if col_b.button('Clear'):
    st.session_state['branch_sel'] = []

# マルチセレクト本体
branch_sel = st.sidebar.multiselect(
    'Branch',
    options=branches_all,
    default=st.session_state['branch_sel'],
    key='branch_sel'
)

# Rack / Lowest トグル
rate_col = st.sidebar.radio('Rate column', ['ARR (Rack Rate)', 'ARR (Lowest)'])

### ----- 3. フィルタ反映 -----
f = df[
    (df['A/C'].isin(ac_options)) &
    (df['Type'].isin(type_options)) &
    (df['Size'].between(*size_range)) &
    (df['Branch'].isin(branch_sel))
].copy()

### ----- 4. MeSpace 基準との差分 -----
mespace_med = (
    f[f['Brand']=='MeSpace']
    .groupby(['SizeBucket','A/C'])[rate_col].median()
    .rename('MeSpace_Median').reset_index()
)
f = f.merge(mespace_med,on=['SizeBucket','A/C'],how='left')
f['PctDiff'] = (f[rate_col]-f['MeSpace_Median'])/f['MeSpace_Median']

### ----- 5. 散布図 -----
fig = px.scatter(f, x='Size', y=rate_col,
                 color='Brand', symbol='Brand',
                 hover_data={
                     'Branch': True,
                     'A/C': True,
                     'Type': True,
                     'Size': ':.2f',
                     rate_col: ':.2f',
                     'PctDiff': ':.1%'
                 },
                 color_discrete_map={
                     'MeSpace': 'green',
                     'i-Store': 'blue',
                     'Leo': 'orange',
                     'REED': 'red'
                 })
st.plotly_chart(fig, use_container_width=True)

# ✅ 散布図の保存ボタン（この位置に追加）
if st.button('Save scatter plot as PNG'):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scatter_{timestamp}.png"
    fig.write_image(filename, scale=2)
    st.success(f'Scatter plot saved as {filename}')

### ----- 6. 箱ひげ -----
fig2 = px.box(f[f['Brand']!='MeSpace'], x='Brand', y='PctDiff',
              points='all', title='Price Difference vs MeSpace',
              color='Brand',
              hover_data={
                  'Size': ':.2f',
                  rate_col: ':.2f',
                  'PctDiff': ':.1%'
              },
              color_discrete_map={
                  'MeSpace': 'green',
                  'i-Store': 'blue',
                  'Leo': 'orange',
                  'REED': 'red'
              })
fig2.add_hline(y=0, line_dash='dash')
fig2.update_yaxes(tickformat='.0%')

# --- format hover template for box traces ---
for tr in fig2.data:
    # Apply only to box traces
    if tr.type == 'box':
        tr.hovertemplate = (
            'Brand=%{x}<br>' +
            'PctDiff=%{y:.1%}<extra></extra>'
        )

st.plotly_chart(fig2, use_container_width=True)

# ✅ 箱ひげ図の保存ボタン（この位置に追加）
if st.button('Save box plot as PNG'):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"boxplot_{timestamp}.png"
    fig2.write_image(filename, scale=2)
    st.success(f'Box plot saved as {filename}')

### ----- 7. Top5 テーブル & 画像保存 -----
col1, col2 = st.columns(2)
with col1:
    st.subheader('Highest Premium (Top 5)')
    st.dataframe(
        f[f['Brand']!='MeSpace']
        .nlargest(5,'PctDiff')
        [['Brand','Branch','Size',rate_col,'PctDiff']]
        .style.format({
            'Size': '{:.2f}',
            rate_col: '{:.2f}',
            'PctDiff': '{:.1%}'
        })
    )
with col2:
    st.subheader('Largest Discount (Top 5)')
    st.dataframe(
        f[f['Brand']!='MeSpace']
        .nsmallest(5,'PctDiff')
        [['Brand','Branch','Size',rate_col,'PctDiff']]
        .style.format({
            'Size': '{:.2f}',
            rate_col: '{:.2f}',
            'PctDiff': '{:.1%}'
        })
    )

### ----- 8. Full Comparison Table -----
st.subheader('Full Comparison Table')
st.dataframe(
    f[f['Brand']!='MeSpace'][['Brand','Branch','Size',rate_col,'PctDiff']]
    .sort_values('PctDiff', ascending=False)
    .style.format({
        'Size': '{:.2f}',
        rate_col: '{:.2f}',
        'PctDiff': '{:.1%}'
    })
)
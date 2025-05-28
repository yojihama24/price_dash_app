# price_dash.py
import streamlit as st
import pandas as pd
import plotly.express as px

### ----- 1. データ読み込み & 前処理 -----
df = pd.read_excel('/Users/yojihamanishi/Library/Mobile Documents/com~apple~CloudDocs/仕事/Database/Price_List.xlsx', sheet_name='Data Base')

# 異常値除外
df = df[df['ARR (Rack Rate)']<=4000]

# サイズ帯
bins = [0,1,3,5,10,20,100]
labels = ['<1','1-3','3-5','5-10','10-20','20+']
df['SizeBucket'] = pd.cut(df['Size'], bins=bins, labels=labels)

# 簡易エリアタグ
def area(branch):
    for kw in ['Pattaya','PTY','Chon','Laem','Pattaya']:
        if kw.lower() in branch.lower(): return 'Pattaya/Chon'
    for kw in ['Phuket','PTG']:
        if kw.lower() in branch.lower(): return 'Phuket'
    return 'Bangkok'
df['Area'] = df['Branch'].apply(area)

### ----- 2. SIDEBAR コントロール -----
st.sidebar.header('Filters')

# A/C フィルタ
ac_options = st.sidebar.multiselect('A/C', df['A/C'].unique().tolist(),
                                    default=df['A/C'].unique().tolist())

# Type フィルタ
type_options = st.sidebar.multiselect('Type', df['Type'].unique().tolist(),
                                      default=df['Type'].unique().tolist())

# Size 誤差スライダー
size_min, size_max = int(df['Size'].min()), int(df['Size'].max())
size_range = st.sidebar.slider('Size range (m²)', size_min, size_max,
                               (size_min, size_max))

# エリア
area_sel = st.sidebar.multiselect('Area', df['Area'].unique().tolist(),
                                  default=df['Area'].unique().tolist())

# Rack / Lowest トグル
rate_col = st.sidebar.radio('Rate column', ['ARR (Rack Rate)', 'ARR (Lowest)'])

### ----- 3. フィルタ反映 -----
f = df[
    (df['A/C'].isin(ac_options)) &
    (df['Type'].isin(type_options)) &
    (df['Size'].between(*size_range)) &
    (df['Area'].isin(area_sel))
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
st.plotly_chart(fig2, use_container_width=True)

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

# 保存ボタン
if st.button('Save current scatter as PNG'):
    fig.write_image('scatter_current.png', scale=2)
    st.success('Saved to scatter_current.png')

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
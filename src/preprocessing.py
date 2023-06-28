# Стандартный стэк
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

FILES_TO_COMBINE = [1, 2, 3, 4, 5, 9]

#Считываем файлы в один датасет
df = pd.DataFrame(pd.read_csv(f'../data/raw/{files[0]}_rooms_full.csv'))
for i in files[1:]:
    data = pd.read_csv(f'../data/raw/{i}_rooms_full.csv')
    df_temp = pd.DataFrame(data)
    df = pd.concat([df, df_temp], axis = 0)

df = df.reset_index(drop=True)
df = df[df['processed']=='y']
df = df.drop(['title','subtitle', 'link', 'processed'], axis=1)
df = df.replace(-1.0, '-1').replace('-1', None)

# Убираем лишние символы и знаки рубля, приводим к нужному формату
df.price = df.price.apply(lambda x: x.replace(' ', '')).str.extract('(\d+)').apply(int, axis=1)
df["price"] = df.price.astype(float)

# Обрабатываем миссинги в метро
df.loc[df["district"] == "Десеновское поселение", "subway"] = 'Нет'
df.loc[(df["district"] == "р-н Алексеевский") & (df['subway'].isna()), "subway"] = 'ВДНХ'
df.loc[(df["district"] == "р-н Гольяново") & (df['subway'].isna()), "subway"] = 'Щёлковская'
df.loc[(df["district"] == "р-н Текстильщики") & (df['subway'].isna()), "subway"] = 'Текстильщики'
df.loc[(df["district"] == "р-н Южное Бутово") & (df['subway'].isna()), "subway"] = 'Бунинские аллеи'

# и странные названия в станциях
# Заменяем названия станций не метро и МЦК на ближайшие метро
subway_replaces = {'Москва (Киевский вокзал)': 'Киевская',
                   'Москва (Павелецкий вокзал)' : 'Павелецкая',
                   'Площадь трёх вокзалов': 'Комсомольская'}
subway_list = df.subway.unique()
df.subway = df.subway.replace(subway_replaces)

# Distance to subway
df['dist_to_subway'].fillna('', inplace=True)
df['dist_to_subway, min'] = df.dist_to_subway.str.extract('(\d+)')

def get_dist_to_subway_by(x):
    if 'пешком' in x:
        return 'пешком'
    elif 'на транспорте' in x:
        return 'на транспорте'
    else:
        return ''
df['way_to_subway'] = df['dist_to_subway'].apply(get_dist_to_subway_by)

df.loc[ (df["district"] == "р-н Алексеевский") & (df["dist_to_subway"] == ""), "dist_to_subway, min"] = 15
df.loc[ (df["district"] == "р-н Алексеевский") & (df["dist_to_subway"] == ""), "way_to_subway"] = 'пешком'

df.loc[ (df["district"] == "р-н Гольяново") & (df["dist_to_subway"] == ""), "dist_to_subway, min"] = 30
df.loc[ (df["district"] == "р-н Гольяново") & (df["dist_to_subway"] == ""), "way_to_subway"] = 'пешком'

df.loc[ (df["district"] == "р-н Южное Бутово") & (df["dist_to_subway"] == ""), "dist_to_subway, min"] = 30
df.loc[ (df["district"] == "р-н Южное Бутово") & (df["dist_to_subway"] == ""), "way_to_subway"] = 'пешком'

df.drop('dist_to_subway', axis=1, inplace=True)
df["dist_to_subway, min"] = df['dist_to_subway, min'].astype(float)

# City
df.drop('city', axis=1, inplace=True)

# Admin okrug
subways_okrug = {
    'Рассказовка':'НАО (Новомосковский)',
    'Саларьево':'ЗАО',
    'Прокшино':'НАО (Новомосковский)',
    'Бунинская аллея':'ЮЗАО',
    'Румянцево':'НАО (Новомосковский)',
    'Коммунарка':'НАО (Новомосковский)',
    'Филатов Луг':'НАО (Новомосковский)',
    'Силикатная':'НАО (Новомосковский)',
    'Щербинка':'НАО (Новомосковский)',
    'Улица Скобелевская':'ЮЗАО',
    'Ольховая':'НАО (Новомосковский)',
    'Улица Горчакова':'ЮЗАО',
    'Тёплый Стан':'ЮЗАО',
    'Новопеределкино':'ЗАО',
    'Сокольники':'ВАО',
    ''
}
df.admin_okrug = df.admin_okrug.fillna(df.subway.map(subways_okrug))
df.dropna(subset=['admin_okrug'], inplace=True)

# District
subways_district = {
    'Рассказовка':'м. Рассказовка',
    'Саларьево':'м. Саларьево',
    'Прокшино':'м. Прокшино',
    'Бунинская аллея':'м. Бунинская аллея',
    'Румянцево':'м. Румянцево',
    'Коммунарка':'м. Коммунарка',
    'Филатов Луг':'м. Филатов Луг',
    'Силикатная':'Рязановское поселение',
    'Щербинка':'р-н Южное Бутово',
    'Улица Скобелевская':'р-н Южное Бутово',
    'Ольховая':'м. Ольховая',
    'Улица Горчакова':'р-н Южное Бутово'
}

df.district = df.district.fillna(df.subway.map(subways_district))
df.dropna(subset=['district'], inplace=True)

# Year
df = df.drop(axis = 0, index = df[df['year_of_construction']<1800].index)

### №1 Функция возвращает наиболее часто встречаемое значение в колонке to_find среди домов с тем же адресом, что и x
def find_something(x, to_find):
    if x.loc['home_number'] != '0': # Проводим поиск только для адресов с номером дома
        if df[(df.street == x.loc['street']) & (df.home_number == x.loc['home_number'])][to_find] \
        .dropna().empty == False: # Инициализируем поиск, только если есть дома с таким же адресом
            return(df[(df.street == x.loc['street']) & (df.home_number == x.loc['home_number'])][to_find] \
                   .dropna().value_counts().idxmax())
        else:
            return np.nan
    else:
        return np.nan
    
# Попробуем найти дома по тем же адресам с указанным годом
df.loc[df['year_of_construction'].isnull(), 'year_of_construction'] = \
df[df['year_of_construction'].isnull()].apply(find_something, **{'to_find' : 'year_of_construction'}, axis = 1)


# Meters
df.living_meters = df.living_meters.astype(float)
df.kitchen_meters = df.kitchen_meters.astype(float)

df['living_meters'][ (df['living_meters'].isna()) & (df['kitchen_meters'].notna())] = df['total_meters'] - df['kitchen_meters']
df['kitchen_meters'][ (df['kitchen_meters'].isna()) & (df['living_meters'].notna())] = df['total_meters'] - df['living_meters']

df.loc[(df["rooms"] == 1) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 1) & df.kitchen_meters.notna()]['kitchen_meters'].median()
df.loc[(df["rooms"] == 2) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 2) & df.kitchen_meters.notna()]['kitchen_meters'].median()
df.loc[(df["rooms"] == 3) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 3) & df.kitchen_meters.notna()]['kitchen_meters'].median()
df.loc[(df["rooms"] == 4) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 4) & df.kitchen_meters.notna()]['kitchen_meters'].median()
df.loc[(df["rooms"] == 5) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 5) & df.kitchen_meters.notna()]['kitchen_meters'].median()
df.loc[(df["rooms"] == 6) & df.kitchen_meters.isna(), "kitchen_meters"] = df[(df["rooms"] == 6) & df.kitchen_meters.notna()]['kitchen_meters'].median()

df.loc[(df["rooms"] == 9) & df.kitchen_meters.isna(), "kitchen_meters"] = 2.0
df['is_euro'] = df['kitchen_meters'] > df['living_meters']

df.drop('living_meters', axis=1, inplace=True)

# Floors & Floors Count
df['is_skyscraper'] = df['floors_count'] > 60
def get_floor_type (row):
    if row['floor'] < 3 :
        return 'ground'
    elif  3 <= row['floor'] < 15:
        return 'usual'
    elif 15 <= row['floor'] < 30:
        return 'view'
    elif 30 <= row['floor']:
        return 'sky'
    return 'other'
df['floor_type'] = df.apply (lambda row: get_floor_type(row), axis=1)

df.drop(['floor'], axis=1, inplace=True)
df.drop(['floors_count'], axis=1, inplace=True)

# Flat type, House type
house_types = {
    'Монолитный':'Монолитный',
    'Монолитно-кирпичный':'Монолитный',
    'Монолитно-кирпичный, монолитный':'Монолитный',
    'Монолитно-кирпичный, монолитный, кирпичный':'Монолитный',
    'Панельный, монолитный':'Панельный',
    'Панельный, кирпичный':'Панельный',
}
df.house_type = df.house_type.replace(house_types)

# WC
wc_count = {
    None: 1,
    '1 совмещенный':1,
    '1 раздельный':1,
    '2 совмещенных':2,                  
    '1 совмещенный, 1 раздельный':2,    
    '2 раздельных':2,                   
    '3 совмещенных':3,                  
    '2 совмещенных, 1 раздельный':2,    
    '3 раздельных':3,                   
    '1 совмещенный, 2 раздельных':3,    
    '2 совмещенных, 2 раздельных':4,    
    '4 раздельных':4,                   
    '4 совмещенных':4,                  
    '3 совмещенных, 3 раздельных':6,    
    '3 совмещенных, 1 раздельный':4,    
    '1 совмещенный, 4 раздельных':5,
    
    '4 совмещенных, 1 раздельный':5,
    '4 совмещенных, 4 раздельных':8,
    '3 совмещенных, 2 раздельных':5,
    '1 совмещенный, 3 раздельных':4,
    '2 совмещенных, 4 раздельных':6,
    '4 совмещенных, 2 раздельных':6,
    '2 совмещенных, 3 раздельных':5,
    '4 совмещенных, 3 раздельных':7
}


wc_type = {
    None:'совмещенный',
    '1 совмещенный':'совмещенный',
    '1 раздельный':'раздельный',
    '2 совмещенных':'совмещенный',                  
    '1 совмещенный, 1 раздельный':'совмещенный',    
    '2 раздельных':'раздельный',                   
    '3 совмещенных':'совмещенный',                  
    '2 совмещенных, 1 раздельный':'совмещенный',    
    '3 раздельных':'раздельный',                   
    '1 совмещенный, 2 раздельных':'раздельный',    
    '2 совмещенных, 2 раздельных':'совмещенный',    
    '4 раздельных':'раздельный',                   
    '4 совмещенных':'совмещенный',                  
    '3 совмещенных, 3 раздельных':'совмещенный',    
    '3 совмещенных, 1 раздельный':'совмещенный',    
    '1 совмещенный, 4 раздельных':'раздельный',
    '4 совмещенных, 1 раздельный':'совмещенный',
    '4 совмещенных, 4 раздельных':'совмещенный',
    '3 совмещенных, 2 раздельных':'совмещенный',
    '1 совмещенный, 3 раздельных':'раздельный',
    '2 совмещенных, 4 раздельных':'раздельный',
    '4 совмещенных, 2 раздельных':'совмещенный',
    '2 совмещенных, 3 раздельных':'раздельный',
    '4 совмещенных, 3 раздельных':'совмещенный'
}

df['wc_count'] = df.wc.replace(wc_count)
df['wc_type'] = df.wc.replace(wc_type)

df.drop(['wc'], axis=1, inplace=True)

def get_class (row):
    if row['price']/row['total_meters'] < 240000 :
        return 'эконом'
    elif  row['price']/row['total_meters'] < 290000 :
        return 'комфорт'
    elif row['price']/row['total_meters'] < 400000 :
        return 'бизнес'
    elif row['price']/row['total_meters'] < 700000 :
        return 'премиум'
    return 'элитный'

# Class
df['class_real'] = df.apply (lambda row: get_class(row), axis=1)
df['class_real'].value_counts()
df.drop(['class'], axis=1, inplace=True)

# Drop columns
df.drop(['ceiling'], axis=1, inplace=True)